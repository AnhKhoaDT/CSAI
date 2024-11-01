import support_function as spf
import time

'''
//========================//
//           BFS          //
//        ALGORITHM       //
//     IMPLEMENTATION     //
//========================//
'''
def BFS_search(board, list_check_point):
    start_time = time.time()
    ''' BFS SEARCH SOLUTION '''
    ''' IF START BOARD IS GOAL OR DON'T HAVE CHECK POINT '''
    if spf.check_win(board, list_check_point):
        print("Found win")
        return [board], {
            "steps": 0,
            "weight": 0,  # Adjust if weight tracking is required
            "nodes": 1,
            "solution_path": ""
        }
    
    ''' INITIALIZE START STATE '''
    start_state = spf.state(board, None, list_check_point)
    
    ''' INITIALIZE 2 LISTS USED FOR BFS SEARCH '''
    list_state = [start_state]
    list_visit = [start_state]
    nodes_generated = 1  # Start with the initial node

    ''' LOOP THROUGH VISITED LIST '''
    while len(list_visit) != 0:
        ''' GET NOW STATE TO SEARCH '''
        now_state = list_visit.pop(0)
        
        ''' GET THE PLAYER'S CURRENT POSITION '''
        cur_pos = spf.find_position_player(now_state.board)
        
        ''' GET LIST POSITION THAT PLAYER CAN MOVE TO '''
        list_can_move = spf.get_next_pos(now_state.board, cur_pos)
        
        ''' MAKE NEW STATES FROM LIST CAN MOVE '''
        for next_pos in list_can_move:
            ''' MAKE NEW BOARD '''
            new_board = spf.move(now_state.board, next_pos, cur_pos, list_check_point)
            
            ''' IF THIS BOARD ALREADY EXISTS IN LIST --> SKIP STATE '''
            if spf.is_board_exist(new_board, list_state):
                continue
            
            ''' IF ONE OR MORE BOXES ARE STUCK IN THE CORNER --> SKIP STATE '''
            if spf.is_board_can_not_win(new_board, list_check_point):
                continue
            
            ''' IF ALL BOXES ARE STUCK --> SKIP STATE '''
            if spf.is_all_boxes_stuck(new_board, list_check_point):
                continue

            ''' MAKE NEW STATE '''
            new_state = spf.state(new_board, now_state, list_check_point)
            nodes_generated += 1  # Count each generated state
            
            ''' CHECK WHETHER THE NEW STATE IS GOAL OR NOT '''
            if spf.check_win(new_board, list_check_point):
                print("Found win")
                solution_path = new_state.get_line()  # Get solution path string
                end_time = time.time()
                elapsed_time = (end_time - start_time) * 1000  # Convert to milliseconds

                # Create stats dictionary
                stats = {
                    "steps": len(solution_path),       # Count of steps in solution path
                    "weight": 0,                       # Adjust if weight tracking is required
                    "nodes": nodes_generated,          # Total nodes generated
                    "solution_path": solution_path     # Solution path as a string
                }
                
                return new_state.get_board_sequence(), stats  # Return sequence of boards and stats
            
            ''' APPEND NEW STATE TO VISITED LIST AND TRAVERSED LIST '''
            list_state.append(new_state)
            list_visit.append(new_state)

            ''' CHECK FOR TIMEOUT '''
            end_time = time.time()
            if end_time - start_time > spf.TIME_OUT:
                return [], {"error": "timeout"}

    ''' SOLUTION NOT FOUND '''
    print("Not Found")
    return [], {"error": "not_found"}
