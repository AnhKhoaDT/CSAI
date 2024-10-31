import numpy as np
import os
from colorama import Fore
from colorama import Style
from copy import deepcopy
#sử lý dữ liệu quản lý file, hiển thị màu sắc sao chép dữ liệu
import pygame#hiển thị and quản lý
from pygame.constants import KEYDOWN
import bfs
import astar
import dfs
import ucs

''' TIME OUT FOR ALL ALGORITHM : 30 MIN ~ 1800 SECONDS '''
TIME_OUT = 1800# thòi gian giới hạn
''' GET THE TESTCASES AND CHECKPOINTS PATH FOLDERS '''
path_board = os.getcwd() + '\\..\\Testcases'
path_checkpoint = os.getcwd() + '\\..\\Checkpoints'

''' TRAVERSE TESTCASE FILES AND RETURN A SET OF BOARD '''
def get_boards_list():
    boards = []
    weights = []
    
    for filename in os.listdir(path_board):
        if filename.endswith(".txt"):
            path = os.path.join(path_board, filename)
            with open(path, 'r') as f:
                lines = f.readlines()

            # Đọc hàng đầu tiên là trọng lượng của cục đá
            rock_weights = list(map(int, lines[0].strip().split(',')))
            weights.append(rock_weights)

            # Các hàng tiếp theo là bản đồ
            board_data = [line.strip().split(',') for line in lines[1:]]
            board = np.array(board_data, dtype=str)
            
            # Định dạng các ký tự trong bản đồ
            for row in board:
                format_row(row)
            
            boards.append(board)
    
    return boards, weights

''' Đọc tất cả các file checkpoint và trả về danh sách checkpoint tương ứng '''
def get_check_points():
    os.chdir(path_checkpoint)
    list_check_point = []
    for file in os.listdir():
        if file.endswith(".txt"):
            file_path = f"{path_checkpoint}\{file}"
            check_point = get_pair(file_path)
            list_check_point.append(check_point)
    return list_check_point

''' FORMAT THE INPUT TESTCASE TXT FILE '''
def format_row(row):
    for i in range(len(row)):
        if row[i] == '1':
            row[i] = '#'
        elif row[i] == 'p':
            row[i] = '@'
        elif row[i] == 'b':
            row[i] = '$'
        elif row[i] == 'c':
            row[i] = '%'

''' FORMAT THE INPUT CHECKPOINT TXT FILE '''
def format_check_points(check_points):# chưyen đổi checkpoint thành danh sách các tọa độ
    result = []
    for check_point in check_points:
        result.append((check_point[0], check_point[1]))
    return result

''' READ A SINGLE TESTCASE TXT FILE '''#Đọc và xử lý các file .txt để tạo ra các bảng và checkpoint
def get_board(path):
    result = np.loadtxt(f"{path}", dtype=str, delimiter=',')
    for row in result:
        format_row(row)
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
def renderMap(board, rock_weights):
    rock_positions = [(i, j) for i, row in enumerate(board) for j, cell in enumerate(row) if cell == '$']

    if len(rock_positions) != len(rock_weights):
        print("Lỗi: Số lượng trọng lượng không khớp với số lượng cục đá trên bảng.")
        return

    width = len(board[0])
    height = len(board)
    indent = (640 - width * 32) / 2.0

    # Tạo từ điển gán vị trí cục đá với trọng lượng
    rock_weight_dict = {pos: weight for pos, weight in zip(rock_positions, rock_weights)}

    for i in range(height):
        for j in range(width):
            screen.blit(space, (j * 32 + indent, i * 32 + 250))
            if board[i][j] == '#':
                screen.blit(wall, (j * 32 + indent, i * 32 + 250))
            elif board[i][j] == '$':
                screen.blit(box, (j * 32 + indent, i * 32 + 250))
                # Hiển thị trọng lượng lên cục đá
                weight = rock_weight_dict.get((i, j))
                if weight is not None:
                    weight_text = pygame.font.Font(None, 24).render(str(weight), True, (0, 0, 0))
                    screen.blit(weight_text, (j * 32 + indent + 8, i * 32 + 250 + 8))
            elif board[i][j] == '%':
                screen.blit(point, (j * 32 + indent, i * 32 + 250))
            elif board[i][j] == '@':
                screen.blit(player, (j * 32 + indent, i * 32 + 250))


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
   
    while running:
        screen.blit(init_background, (0, 0))
        draw_buttons()
        if sceneState == "init":
            initGame(maps[mapNumber])

        if sceneState == "executing":
            list_check_point = check_points[mapNumber]
            rock_weights = rock_weights_list[mapNumber]
            if algorithm == "BFS":
                print("BFS")
                list_board = bfs.BFS_search(maps[mapNumber], list_check_point)
            elif algorithm=="A*":
                print("AStar")
                list_board = astar.AStart_Search(maps[mapNumber], list_check_point)
            elif algorithm=="DFS":
                print("DFS")
                #list_board = dfs.DFS_Search(maps[mapNumber], list_check_point)
            else:
                print("UCS")
                #list_board = ucs.UCS_Search(maps[mapNumber], list_check_point)
                
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
            renderMap(current_board, rock_weights)  # Truyền `rock_weights` vào renderMap
            currentState += 1
            if currentState == stateLenght:
                sceneState = "end"
                found = True

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # if event.type == pygame.KEYDOWN:
            #     if event.key == pygame.K_RIGHT and sceneState == "init":
            #         if mapNumber < len(maps) - 1:
            #             mapNumber += 1
            #     if event.key == pygame.K_LEFT and sceneState == "init":
            #         if mapNumber > 0:
            #             mapNumber -= 1
            #     if event.key == pygame.K_RETURN:
            #         if sceneState == "init":
            #             sceneState = "loading"
            #         if sceneState == "end":
            #             sceneState = "init"
            #     if event.key == pygame.K_SPACE and sceneState == "init":
            #         algorithm = "A Star Search" if algorithm == "Breadth First Search" else "Breadth First Search"
            #         selected_algorithm = algorithm  # Update the selected algorithm

            if event.type == pygame.MOUSEBUTTONDOWN:  # Check for mouse button clicks
                if event.button == 1:  # Left mouse button
                    mouse_pos = event.pos
                    # Check if a button was clicked
                    for text, (x, y) in button_positions.items():
                        if x <= mouse_pos[0] <= x + button_width and y <= mouse_pos[1] <= y + button_height:
                            selected_algorithm = text  # Update the selected algorithm
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
                    if sceneState == "init":
                        sceneState = "loading"
                    if sceneState == "end":
                        sceneState = "init"

        pygame.display.flip()
    pygame.quit()
    
''' DISPLAY MAIN SCENE '''
#DISPLAY INITIAL SCENE
def initGame(map):
	titleSize = pygame.font.Font('gameFont.ttf', 60)
	titleText = titleSize.render('Among-koban', True, WHITE)
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