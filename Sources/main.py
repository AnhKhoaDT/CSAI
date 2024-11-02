import numpy as np
import os
from colorama import Fore
from colorama import Style
from copy import deepcopy
import time
import psutil
#sử lý dữ liệu quản lý file, hiển thị màu sắc sao chép dữ liệu
import pygame#hiển thị and quản lý
from pygame.constants import KEYDOWN
import time as time_lib
import bfs
import astar
import dfs
import ucs

''' TIME OUT FOR ALL ALGORITHM : 30 MIN ~ 1800 SECONDS '''
TIME_OUT = 1800# thòi gian giới hạn
''' GET THE TESTCASES AND CHECKPOINTS PATH FOLDERS '''
path_board = os.getcwd() + '\\..\\Testcases'
path_checkpoint = os.getcwd() + '\\..\\Checkpoints'
output_path = os.path.join(os.getcwd(), 'Outputs')
os.makedirs(output_path, exist_ok=True)

''' TRAVERSE TESTCASE FILES AND RETURN A SET OF BOARD '''
# Chuyển cách đọc file bản đồ sang sử dụng hàm `get_board(path)` và `get_boards(mode_path)`
def get_boards_list():
    boards = []
    weights = []

    # Duyệt qua các file trong thư mục `Testcases`
    for filename in os.listdir(path_board):
        if filename.endswith(".txt"):
            path = os.path.join(path_board, filename)
            # Sử dụng hàm get_board để lấy bản đồ và trọng lượng của các viên đá
            board = get_board(path)
            
            # Đọc lại file để lấy trọng lượng từ dòng đầu tiên
            with open(path, 'r') as f:
                rock_weights = list(map(int, f.readline().strip().split()))
                weights.append(rock_weights)

            boards.append(np.array(board, dtype=str))  # Chuyển board thành NumPy array cho dễ quản lý

    return boards, weights

''' Đọc tất cả các file checkpoint và trả về danh sách checkpoint tương ứng '''
def get_check_points():
    check_points = []
    for filename in os.listdir(path_checkpoint):
        if filename.endswith(".txt"):
            path = os.path.join(path_checkpoint, filename)
            with open(path, 'r') as f:
                points = [tuple(map(int, line.strip().split(','))) for line in f if line.strip()]
                check_points.append(points)
    return check_points



''' FORMAT THE INPUT CHECKPOINT TXT FILE '''
def format_check_points(check_points):# chưyen đổi checkpoint thành danh sách các tọa độ
    result = []
    for check_point in check_points:
        result.append((check_point[0], check_point[1]))
    return result

def get_board(path):
    # Đọc file và chuyển mỗi dòng thành danh sách ký tự mà không qua định dạng
    with open(path, 'r') as f:
        lines = f.readlines()
    
    # Chuyển từng dòng thành danh sách ký tự, loại bỏ dòng trống
    board_data = [list(line.strip()) for line in lines if line.strip()]
    
    # Kiểm tra và làm cho các dòng có độ dài bằng nhau
    max_length = max(len(line) for line in board_data)
    for line in board_data:
        # Thêm các ký tự khoảng trắng vào các dòng ngắn hơn để đạt độ dài bằng max_length
        line.extend([' '] * (max_length - len(line)))

    # Chuyển đổi thành mảng NumPy sau khi đảm bảo các dòng có độ dài bằng nhau
    result = np.array(board_data, dtype=str)
    
    return result


''' READ A SINGLE CHECKPOINT TXT FILE '''
def get_pair(path):
    result = np.loadtxt(f"{path}", dtype=int, delimiter=',')
    return result

'''
//========================//
//      DECLARE AND       //
//  INITIALIZE MAPS AND   //
//      CHECK POINTS      //
//========================//
'''
maps,rock_weights_list = get_boards_list()
check_points = get_check_points()


'''
//========================//
//         PYGAME         //
//     INITIALIZATIONS    //
//                        //
//========================//
'''
pygame.init()
pygame.font.init()
screen = pygame.display.set_mode((640, 640))
pygame.display.set_caption('Ares’s adventure')
clock = pygame.time.Clock()# điều khiển tốc độ khung hình
BACKGROUND = (0, 0, 0)
WHITE = (255, 255, 255)
'''
GET SOME ASSETS
'''
assets_path = os.getcwd() + "\\..\\Assets"
os.chdir(assets_path)
player = pygame.image.load(os.getcwd() + '\\player.png')
wall = pygame.image.load(os.getcwd() + '\\wall.png')
box = pygame.image.load(os.getcwd() + '\\box.png')
point = pygame.image.load(os.getcwd() + '\\point.png')
space = pygame.image.load(os.getcwd() + '\\space.png')
arrow_left = pygame.image.load(os.getcwd() + '\\arrow_left.png')
arrow_right = pygame.image.load(os.getcwd() + '\\arrow_right.png')
init_background = pygame.image.load(os.getcwd() + '\\init_background.png')
loading_background = pygame.image.load(os.getcwd() + '\\loading_background.png')
notfound_background = pygame.image.load(os.getcwd() + '\\notfound_background.png')
found_background = pygame.image.load(os.getcwd() + '\\found_background.png')
'''
RENDER THE MAP FOR GAMEPLAY
'''
def render_stone(position, weight):
    """Hiển thị cục đá và trọng lượng của nó tại vị trí cụ thể."""
    x, y = position
    indent = (640 - len(maps[mapNumber][0]) * 32) / 2.0

    # Vẽ lại nền trước
    screen.blit(space, (y * 32 + indent, x * 32 + 250))
    # Vẽ lại cục đá
    screen.blit(box, (y * 32 + indent, x * 32 + 250))
    # Hiển thị trọng lượng của cục đá
    weight_text = pygame.font.Font(None, 24).render(str(weight), True, (0, 0, 0))
    screen.blit(weight_text, (y * 32 + indent + 8, x * 32 + 250 + 8))
    

def renderMap(board, rock_weights):
    """Hiển thị bản đồ kèm trọng lượng của từng cục đá ngay lập tức."""

    # Kích thước và căn lề của màn hình
    width = len(board[0])
    height = len(board)
    indent = (640 - width * 32) / 2.0

    # Tìm vị trí các cục đá và kiểm tra nếu có sự không khớp với trọng lượng
    rock_positions = [(i, j) for i in range(height) for j in range(width) if board[i][j] == '$']
    if len(rock_positions) != len(rock_weights):
        print("Lỗi: Số lượng trọng lượng không khớp với số lượng cục đá trên bảng.")
        return

    # Duyệt qua tất cả các ô trên bảng
    for i in range(height):
        for j in range(width):
            # Vẽ nền cho mỗi ô trước
            screen.blit(space, (j * 32 + indent, i * 32 + 250))

            cell = board[i][j]
            if cell == '#':
                # Vẽ tường
                screen.blit(wall, (j * 32 + indent, i * 32 + 250))
            elif cell == '$':
                # Lấy trọng lượng tương ứng của cục đá
                rock_index = rock_positions.index((i, j))
                weight = rock_weights[rock_index]
                render_stone((i, j), weight)
            elif cell == '.':
                # Vẽ điểm đích
                screen.blit(point, (j * 32 + indent, i * 32 + 250))
            elif cell == '@':
                # Vẽ người chơi
                screen.blit(player, (j * 32 + indent, i * 32 + 250))
            else:
                # Vẽ không gian trống
                screen.blit(space, (j * 32 + indent, i * 32 + 250))


def write_output(test_case_num, algorithm, steps, weight, nodes, elapsed_time, memory, solution):
    filename = f"output-{test_case_num + 1:02d}.txt"  # Naming format: output-01.txt, output-02.txt, etc.
    file_path = os.path.join(output_path, filename)

    with open(file_path, 'w') as f:
        f.write(f"{algorithm}\n")
        f.write(f"Steps: {steps}, Weight: {weight}, Nodes: {nodes}, Time (ms): {elapsed_time:.2f}, Memory (MB): {memory:.2f}\n")
        f.write(solution)

button_width = 80
button_height = 40

# Button positions
button_positions = {
    'BFS': (20, 20),
    'DFS': (20, 70),
    'UCS': (20, 120),
    'A*': (20, 170)
}

# Function to draw buttons
def draw_buttons():
    for text, (x, y) in button_positions.items():
        pygame.draw.rect(screen, (255, 255, 255), (x, y, button_width, button_height))  # Draw button
        font = pygame.font.Font(None, 36)
        label = font.render(text, True, (0, 0, 0))
        screen.blit(label, (x + 10, y + 10))  # Center the text
     # Display the selected algorithm text
    

'''
VARIABLES INITIALIZATIONS
'''
#Map level
mapNumber = 0
#Algorithm to solve the game
algorithm = "Select algorithm"
#Your scene states, including: 
#init for choosing your map and algorithm
#loading for displaying "loading scene"
#executing for solving problem
#playing for displaying the game
sceneState = "init"
loading = False

''' SOKOBAN FUNCTION '''
dboard = None
rock_weights = []


def sokoban():
    global sceneState, loading, algorithm, list_board, mapNumber, board, rock_weights
    
    running = True
    stateLenght = 0
    currentState = 0
    found = True
    message = ""  # Biến để lưu trữ thông báo chọn thuật toán
    
    previous_positions = {}
    rock_positions = [(i, j) for i, row in enumerate(maps[mapNumber]) for j, cell in enumerate(row) if cell == '$']
    for pos, weight in zip(rock_positions, rock_weights_list[mapNumber]):
        previous_positions[pos] = weight

    while running:
        screen.blit(init_background, (0, 0))
        draw_buttons()

        # Hiển thị thông báo thuật toán được chọn trên giao diện Pygame nếu có
        if message:
            font = pygame.font.Font(None, 30)
            message_text = font.render(message, True, (255, 255, 255))  # Màu trắng
            screen.blit(message_text, (200, 50))  # Vị trí hiển thị thông báo

        if sceneState == "init":
            initGame(maps[mapNumber])

        if sceneState == "executing":
            list_check_point = check_points[mapNumber]
            rock_weights = rock_weights_list[mapNumber]
            process = psutil.Process(os.getpid())
            start_time = time_lib.time() 
            initial_memory = process.memory_info().rss / (1024 * 1024)  # Memory in MB


            if algorithm == "BFS":
                message = "Algorithm selected: BFS"  # Hiển thị thông báo chọn thuật toán
                list_board, stats = bfs.BFS_search(maps[mapNumber], list_check_point)
            elif algorithm == "A*":
                message = "Algorithm selected: A*"
                list_board = astar.AStart_Search(maps[mapNumber], list_check_point)
            elif algorithm == "DFS":
                message = "Algorithm selected: DFS"
                # list_board = dfs.DFS_Search(maps[mapNumber], list_check_point)
            elif algorithm == "UCS":
                message = "Algorithm selected: UCS"
                # list_board = ucs.UCS_Search(maps[mapNumber], list_check_point)
            else:
                message = "Please select a valid algorithm"
                stats = None
                
           

             # Extract statistics for output
            if stats is not None:
                steps = stats["steps"]
                weight = stats["weight"]
                nodes = stats["nodes"]
                solution_path = stats["solution_path"]
                elapsed_time = (time_lib.time() - start_time) * 1000 # Time in milliseconds
                final_memory = process.memory_info().rss / (1024 * 1024)
                memory_used = final_memory - initial_memory

              # Write the output file for the current map (test case)
                write_output(mapNumber, algorithm, steps, weight, nodes, elapsed_time, memory_used, solution_path)
            else:
                print("No valid stats were returned by the algorithm.")

            if len(list_board) > 0:
                sceneState = "playing"
                stateLenght = len(list_board[0])
                currentState = 0
            else:
                sceneState = "end"
                found = False

        if sceneState == "loading":
            loadingGame()
            sceneState = "executing"
        
        if sceneState == "end":
            if found:
                foundGame(list_board[0][stateLenght - 1])
            else:
                notfoundGame()
        
        if sceneState == "playing":
            clock.tick(2)
            current_board = list_board[0][currentState]
            # Cập nhật vị trí cục đá chỉ khi có sự thay đổi
            for pos, weight in zip(rock_positions, rock_weights):
                if pos not in previous_positions or previous_positions[pos] != weight:
                    render_stone(pos, weight)
                    previous_positions[pos] = weight

            currentState += 1
            if currentState == stateLenght:
                sceneState = "end"
                found = True

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN:  # Check for mouse button clicks
                if event.button == 1:  # Left mouse button
                    mouse_pos = event.pos
                    # Check if a button was clicked
                    for text, (x, y) in button_positions.items():
                        if x <= mouse_pos[0] <= x + button_width and y <= mouse_pos[1] <= y + button_height:
                            selected_algorithm = text
                            algorithm = text  # Set the algorithm according to the button clicked
                            break  # Exit the loop after the first button click

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT and sceneState == "init":
                    if mapNumber < len(maps) - 1:
                        mapNumber += 1
                if event.key == pygame.K_LEFT and sceneState == "init":
                    if mapNumber > 0:
                        mapNumber -= 1
                if event.key == pygame.K_RETURN:
                    if algorithm == "Select algorithm":
                        print("Please select an algorithm first!")  # Hiển thị thông báo trên console
                    elif sceneState == "init":
                        sceneState = "loading"  # Chỉ thay đổi `sceneState` khi đã chọn thuật toán
                    elif sceneState == "end":
                        sceneState = "init"

        pygame.display.flip()
    pygame.quit()

    
''' DISPLAY MAIN SCENE '''
#DISPLAY INITIAL SCENE
def initGame(map):
	titleSize = pygame.font.Font('gameFont.ttf', 40)
	titleText = titleSize.render(' Ares’s adventure', True, WHITE)
	titleRect = titleText.get_rect(center=(320, 80))
	screen.blit(titleText, titleRect)

	desSize = pygame.font.Font('gameFont.ttf', 20)
	desText = desSize.render('Now, select your map!!!', True, WHITE)
	desRect = desText.get_rect(center=(320, 140))
	screen.blit(desText, desRect)

	mapSize = pygame.font.Font('gameFont.ttf', 30)
	mapText = mapSize.render("Lv." + str(mapNumber + 1), True, WHITE)
	mapRect = mapText.get_rect(center=(320, 200))
	screen.blit(mapText, mapRect)

	screen.blit(arrow_left, (246, 188))
	screen.blit(arrow_right, (370, 188))

	algorithmSize = pygame.font.Font('gameFont.ttf', 30)
	algorithmText = algorithmSize.render(str(algorithm), True, WHITE)
	algorithmRect = algorithmText.get_rect(center=(320, 600))
	screen.blit(algorithmText, algorithmRect)
	renderMap(map, rock_weights_list[mapNumber])

''' LOADING SCENE '''
#DISPLAY LOADING SCENE
def loadingGame():
	screen.blit(loading_background, (0, 0))

	fontLoading_1 = pygame.font.Font('gameFont.ttf', 40)
	text_1 = fontLoading_1.render('SHHHHHHH!', True, WHITE)
	text_rect_1 = text_1.get_rect(center=(320, 60))
	screen.blit(text_1, text_rect_1)

	fontLoading_2 = pygame.font.Font('gameFont.ttf', 20)
	text_2 = fontLoading_2.render('The problem is being solved, stay right there!', True, WHITE)
	text_rect_2 = text_2.get_rect(center=(320, 100))
	screen.blit(text_2, text_rect_2)

def foundGame(map):
	screen.blit(found_background, (0, 0))

	font_1 = pygame.font.Font('gameFont.ttf', 30)
	text_1 = font_1.render('Yeah! The problem is solved!!!', True, WHITE)
	text_rect_1 = text_1.get_rect(center=(320, 100))
	screen.blit(text_1, text_rect_1)

	font_2 = pygame.font.Font('gameFont.ttf', 20)
	text_2 = font_2.render('Press Enter to continue.', True, WHITE)
	text_rect_2 = text_2.get_rect(center=(320, 600))
	screen.blit(text_2, text_rect_2)

	renderMap(map,rock_weights_list[mapNumber])

def notfoundGame():
	screen.blit(notfound_background, (0, 0))

	font_1 = pygame.font.Font('gameFont.ttf', 40)
	text_1 = font_1.render('Oh no, I tried my best :(', True, WHITE)
	text_rect_1 = text_1.get_rect(center=(320, 100))
	screen.blit(text_1, text_rect_1)

	font_2 = pygame.font.Font('gameFont.ttf', 20)
	text_2 = font_2.render('Press Enter to continue.', True, WHITE)
	text_rect_2 = text_2.get_rect(center=(320, 600))
	screen.blit(text_2, text_rect_2)
    # Define button dimensions and positions




def main():
    sokoban()

if __name__ == "__main__":
    main()