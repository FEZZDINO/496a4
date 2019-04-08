"""
gtp_connection.py
Module for playing games of Go using GoTextProtocol
Parts of this code were originally based on the gtp module
in the Deep-Go project by Isaac Henrion and Amos Storkey
at the University of Edinburgh.
"""
import traceback
from sys import stdin, stdout, stderr
from board_util import GoBoardUtil, BLACK, WHITE, EMPTY, BORDER, PASS, \
                       MAXSIZE, coord_to_point
import numpy as np
import re
class GtpConnection():

    def __init__(self, go_engine, board, debug_mode = False):
        """
        Manage a GTP connection for a Go-playing engine
        Parameters
        ----------
        go_engine:
            a program that can reply to a set of GTP commandsbelow
        board:
            Represents the current board state.
        """
        self._debug_mode = debug_mode
        self.go_engine = go_engine
        self.board = board
        self.policytype="random"
        self.commands = {
            "protocol_version": self.protocol_version_cmd,
            "quit": self.quit_cmd,
            "name": self.name_cmd,
            "boardsize": self.boardsize_cmd,
            "showboard": self.showboard_cmd,
            "clear_board": self.clear_board_cmd,
            "komi": self.komi_cmd,
            "version": self.version_cmd,
            "known_command": self.known_command_cmd,
            "genmove": self.genmove_cmd,
            "list_commands": self.list_commands_cmd,
            "play": self.play_cmd,
            "legal_moves": self.legal_moves_cmd,
            "gogui-rules_game_id": self.gogui_rules_game_id_cmd,
            "gogui-rules_board_size": self.gogui_rules_board_size_cmd,
            "gogui-rules_legal_moves": self.gogui_rules_legal_moves_cmd,
            "gogui-rules_side_to_move": self.gogui_rules_side_to_move_cmd,
            "gogui-rules_board": self.gogui_rules_board_cmd,
            "gogui-rules_final_result": self.gogui_rules_final_result_cmd,
            "gogui-analyze_commands": self.gogui_analyze_cmd,
            "policy": self.policy_cmd,
            "policy_moves": self.policy_moves_cmd
        }

        # used for argument checking
        # values: (required number of arguments,
        #          error message on argnum failure)
        self.argmap = {
            "boardsize": (1, 'Usage: boardsize INT'),
            "komi": (1, 'Usage: komi FLOAT'),
            "known_command": (1, 'Usage: known_command CMD_NAME'),
            "genmove": (1, 'Usage: genmove {w,b}'),
            "play": (2, 'Usage: play {b,w} MOVE'),
            "legal_moves": (1, 'Usage: legal_moves {w,b}')
        }

    def write(self, data):
        stdout.write(data)

    def flush(self):
        stdout.flush()

    def start_connection(self):
        """
        Start a GTP connection.
        This function continuously monitors standard input for commands.
        """
        line = stdin.readline()
        while line:
            self.get_cmd(line)
            line = stdin.readline()

    def get_cmd(self, command):
        """
        Parse command string and execute it
        """
        if len(command.strip(' \r\t')) == 0:
            return
        if command[0] == '#':
            return
        # Strip leading numbers from regression tests
        if command[0].isdigit():
            command = re.sub("^\d+", "", command).lstrip()

        elements = command.split()
        if not elements:
            return
        command_name = elements[0]; args = elements[1:]
        if self.has_arg_error(command_name, len(args)):
            return
        if command_name in self.commands:
            try:
                self.commands[command_name](args)
            except Exception as e:
                self.debug_msg("Error executing command {}\n".format(str(e)))
                self.debug_msg("Stack Trace:\n{}\n".
                               format(traceback.format_exc()))
                raise e
        else:
            self.debug_msg("Unknown command: {}\n".format(command_name))
            self.error('Unknown command')
            stdout.flush()

    def has_arg_error(self, cmd, argnum):
        """
        Verify the number of arguments of cmd.
        argnum is the number of parsed arguments
        """
        if cmd in self.argmap and self.argmap[cmd][0] != argnum:
            self.error(self.argmap[cmd][1])
            return True
        return False

    def debug_msg(self, msg):
        """ Write msg to the debug stream """
        if self._debug_mode:
            stderr.write(msg)
            stderr.flush()

    def error(self, error_msg):
        """ Send error msg to stdout """
        stdout.write('? {}\n\n'.format(error_msg))
        stdout.flush()

    def respond(self, response=''):
        """ Send response to stdout """
        stdout.write('= {}\n\n'.format(response))
        stdout.flush()

    def reset(self, size):
        """
        Reset the board to empty board of given size
        """
        self.board.reset(size)

    def board2d(self):
        return str(GoBoardUtil.get_twoD_board(self.board))

    def protocol_version_cmd(self, args):
        """ Return the GTP protocol version being used (always 2) """
        self.respond('2')

    def quit_cmd(self, args):
        """ Quit game and exit the GTP interface """
        self.respond()
        exit()

    def name_cmd(self, args):
        """ Return the name of the Go engine """
        self.respond(self.go_engine.name)

    def version_cmd(self, args):
        """ Return the version of the  Go engine """
        self.respond(self.go_engine.version)

    def clear_board_cmd(self, args):
        """ clear the board """
        self.reset(self.board.size)
        self.respond()

    def boardsize_cmd(self, args):
        """
        Reset the game with new boardsize args[0]
        """
        self.reset(int(args[0]))
        self.respond()

    def showboard_cmd(self, args):
        self.respond('\n' + self.board2d())

    def komi_cmd(self, args):
        """
        Set the engine's komi to args[0]
        """
        self.go_engine.komi = float(args[0])
        self.respond()

    def known_command_cmd(self, args):
        """
        Check if command args[0] is known to the GTP interface
        """
        if args[0] in self.commands:
            self.respond("true")
        else:
            self.respond("false")

    def list_commands_cmd(self, args):
        """ list all supported GTP commands """
        self.respond(' '.join(list(self.commands.keys())))

    def legal_moves_cmd(self, args):
        """
        List legal moves for color args[0] in {'b','w'}
        """
        board_color = args[0].lower()
        color = color_to_int(board_color)
        moves = GoBoardUtil.generate_legal_moves(self.board, color)
        gtp_moves = []
        for move in moves:
            coords = point_to_coord(move, self.board.size)
            gtp_moves.append(format_point(coords))
        sorted_moves = ' '.join(sorted(gtp_moves))
        self.respond(sorted_moves)

    def play_cmd(self, args):
        """
        play a move args[1] for given color args[0] in {'b','w'}
        """
        try:
            board_color = args[0].lower()
            board_move = args[1]
            if board_color != "b" and board_color !="w":
                self.respond("illegal move: \"{}\" wrong color".format(board_color))
                return
            color = color_to_int(board_color)
            if args[1].lower() == 'pass':
                self.board.play_move(PASS, color)
                self.board.current_player = GoBoardUtil.opponent(color)
                self.respond()
                return
            coord = move_to_coord(args[1], self.board.size)
            if coord:
                move = coord_to_point(coord[0],coord[1], self.board.size)
            else:
                self.error("Error executing move {} converted from {}"
                           .format(move, args[1]))
                return
            if not self.board.play_move_gomoku(move, color):
                self.respond("illegal move: \"{}\" occupied".format(board_move))
                return
            else:
                self.debug_msg("Move: {}\nBoard:\n{}\n".
                                format(board_move, self.board2d()))
            self.respond()
        except Exception as e:
            self.respond('{}'.format(str(e)))

    def genmove_cmd(self, args):
        """
        Generate a move for the color args[0] in {'b', 'w'}, for the game of gomoku.
        """
        board_color = args[0].lower()
        color = color_to_int(board_color)
        game_end, winner = self.board.check_game_end_gomoku()
        if game_end:
            if winner == color:
                self.respond("pass")
            else:
                self.respond("resign")
            return
        move = GoBoardUtil.generate_legal_moves_gomoku(self.board)
        if (self.policytype == "random"):
            best = None
            cur_max = 0
            for i in move:
                if best == None:
                    best = i
                gmax = 0
                for _ in range(10):
                    result = self.random(self.board, color, color)
                    gmax += result
                if (gmax/10) > cur_max:
                    best = i
                    cur_max = (gmax/10)
        elif (self.policytype == "rule_based"):
            best = None
            cur_max = 0
            for i in move:
                if best == None:
                    best = i
                gmax = 0
                self.board.play_move_gomoku(i, color)

                for _ in range(10):
                    result = self.rules(self.board, color,  GoBoardUtil.opponent(color))
                    gmax += result
                    #print(wins)

                if (gmax/10) > cur_max:
                    best = i
                    #print(best_move)
                    cur_max = (gmax/10)
                self.board.reset_point_gomoku(i, color)



        if best == PASS:
            self.respond("pass")
            return
        move_coord = point_to_coord(best, self.board.size)
        move_as_string = format_point(move_coord)
        if self.board.is_legal_gomoku(best, color):
            self.board.play_move_gomoku(best, color)
            self.respond(move_as_string)
        else:
            self.respond("illegal move: {}".format(move_as_string))

    def gogui_rules_game_id_cmd(self, args):
        self.respond("Gomoku")

    def gogui_rules_board_size_cmd(self, args):
        self.respond(str(self.board.size))

    def legal_moves_cmd(self, args):
        """
            List legal moves for color args[0] in {'b','w'}
            """
        board_color = args[0].lower()
        color = color_to_int(board_color)
        moves = GoBoardUtil.generate_legal_moves(self.board, color)
        gtp_moves = []
        for move in moves:
            coords = point_to_coord(move, self.board.size)
            gtp_moves.append(format_point(coords))
        sorted_moves = ' '.join(sorted(gtp_moves))
        self.respond(sorted_moves)

    def gogui_rules_legal_moves_cmd(self, args):
        game_end,_ = self.board.check_game_end_gomoku()
        if game_end:
            self.respond()
            return
        moves = GoBoardUtil.generate_legal_moves_gomoku(self.board)
        gtp_moves = []
        for move in moves:
            coords = point_to_coord(move, self.board.size)
            gtp_moves.append(format_point(coords))
        sorted_moves = ' '.join(sorted(gtp_moves))
        self.respond(sorted_moves)

    def gogui_rules_side_to_move_cmd(self, args):
        color = "black" if self.board.current_player == BLACK else "white"
        self.respond(color)

    def gogui_rules_board_cmd(self, args):
        size = self.board.size
        str = ''
        for row in range(size-1, -1, -1):
            start = self.board.row_start(row + 1)
            for i in range(size):
                point = self.board.board[start + i]
                if point == BLACK:
                    str += 'X'
                elif point == WHITE:
                    str += 'O'
                elif point == EMPTY:
                    str += '.'
                else:
                    assert False
            str += '\n'
        self.respond(str)

    def gogui_rules_final_result_cmd(self, args):
        game_end, winner = self.board.check_game_end_gomoku()
        moves = self.board.get_empty_points()
        board_full = (len(moves) == 0)
        if board_full and not game_end:
            self.respond("draw")
            return
        if game_end:
            color = "black" if winner == BLACK else "white"
            self.respond(color)
        else:
            self.respond("unknown")

    def gogui_analyze_cmd(self, args):
        self.respond("pstring/Legal Moves For ToPlay/gogui-rules_legal_moves\n"
                     "pstring/Side to Play/gogui-rules_side_to_move\n"
                     "pstring/Final Result/gogui-rules_final_result\n"
                     "pstring/Board Size/gogui-rules_board_size\n"
                     "pstring/Rules GameID/gogui-rules_game_id\n"
                     "pstring/Show Board/gogui-rules_board\n"
                     )


    #from assignment2
    def Win(self, color):
        legal_moves = GoBoardUtil.generate_legal_moves_gomoku(self.board)
        shuai = []
        for point in legal_moves:
            rt_moves = self.detect_immediate_win_for_a_point(point, color)
            if len(rt_moves) != 0:
                shuai.append(rt_moves[0])
        if len(shuai) >0:
            # print("shuai:", shuai)
            return shuai
        return False
    # input the current point that want to check , and the color u wnat to check
    def detect_immediate_win_for_a_point(self, current, color):# BLACK or WHITE, aka 1 or 2
        occu = GoBoardUtil.generate_current_color(self.board, color) # #
        i_win_list=[]
        # print(current, color)
        check = self.four_in_5(current, occu)
        #print(check)
        upper = (self.board.size+1)**2
        if (0 < check) and (check< upper):
            # print("pass")
            if check not in i_win_list:
                i_win_list.append(check)
        # print(i_win_list)
        return i_win_list   #the list with points that fits


    def four_in_5(self, cur, list1):
        c_list = [0,0,0,0,0,0,0,0]
        size = self.board.size+1
        target = [0,0,0,0,0,0,0,0]
        for i in range(5):
            if (cur + i) in list1:
                c_list[0] +=1
            else:
                target[0] = cur + i
            if (cur + size*i ) in list1:
                c_list[1] +=1
            else:
                target[1] = cur + size*i
            if (cur + (size*i)+i) in list1:
                c_list[2] +=1
            else:
                target[2] = cur + (size*i)+i
            if (cur + size*i -i) in list1:
                c_list[3] +=1
            else:
                target[3] = cur + size*i -i
            if (cur - i) in list1:
                c_list[4] +=1
            else:
                target[4] = cur - i
            if (cur - size*i) in list1:
                c_list[5] +=1
            else:
                target[5] = cur - size*i
            if (cur - (size*i)+i) in list1:
                c_list[6] +=1
            else:
                target[6] = cur - (size*i)+i
            if (cur - size*i -i) in list1:
                c_list[7] +=1
            else:
                target[7] = cur - size*i -i
        #print(target, c_list)
        for i in range(8):
            if c_list[i] == 4 :
                #print("yes", type(target[i]))
                return target[i].item()
        return False




    #return the point
    def BlockWin(self):
        legal_moves = GoBoardUtil.generate_legal_moves_gomoku(self.board)
        opp = GoBoardUtil.opponent(self.board.current_player)
        result = self.Win(opp)
        if result:
            return result
        return False



    def OpenFour(self, color):
        nodes_of_a_color = GoBoardUtil.generate_current_color(self.board, color)

        # print("nodes_of_a_color: ", nodes_of_a_color)
        i_win_list = []
        for node in nodes_of_a_color:
            good = self.board.check_win_in_two_for_a_node(node, color)
            if good:
                for each in good:
                    if each not in i_win_list:
                        i_win_list.append(each)
        if len(i_win_list) !=False:
            return i_win_list
        return False



    def OpenFour_my(self, color):
        nodes_of_a_color = GoBoardUtil.generate_current_color(self.board, color)

        # print("nodes_of_a_color: ", nodes_of_a_color)
        i_win_list = []
        for node in nodes_of_a_color:
            good = self.board.check_win_in_two_for_a_node_my(node, color)
            if good:
                for each in good:
                    if each not in i_win_list:
                        i_win_list.append(each)
        if len(i_win_list) !=False:
            return i_win_list
        return False

    def BlockOpenFour(self,color):
        legal_moves = GoBoardUtil.generate_legal_moves_gomoku(self.board)
        opp = GoBoardUtil.opponent(color)
        result = self.OpenFour_my(opp)
        if result:
            if len(result) == 1:
                for node in legal_moves:
                    check_3_connect(point)
                
            else:
                return result
        return False

    def policy_cmd(self, args):
        if args[0] == "random":
            self.policytype = "random"
            self.respond("")


        if args[0] == "rule_based":
            self.policytype = "rule_based"
            self.respond("")

    def policy_moves_cmd(self,args):
        checkpoint = "Random"

        moves = GoBoardUtil.generate_legal_moves_gomoku(self.board)
        color = self.board.current_player
        if self.policytype=="rule_based":
            if self.Win(color):
                checkpoint = "Win"
                moves = self.Win(color)
            elif self.BlockWin():
                checkpoint = "BlockWin"
                moves =self.BlockWin()
            elif self.OpenFour(color):
                checkpoint = "OpenFour"
                moves =self.OpenFour(color)
            elif self.BlockOpenFour(color):
                checkpoint = "BlockOpenFour"
                moves =self.BlockOpenFour(color)

        move = []

        for i in moves:
            move_coord = point_to_coord(i, self.board.size)
            move_as_string = format_point(move_coord)
            move.append(move_as_string)

        move.sort()
        for i in move:
            checkpoint += " " + i
        if checkpoint== "Random":
            checkpoint = ""
        self.respond(checkpoint)


    def random(self,board, original, color):

        game_end, winner = self.board.check_game_end_gomoku()# check if the game ends or not
        if game_end:
            if winner == original:
                return True
        move = GoBoardUtil.generate_random_move_gomoku(board)
        if move == PASS:
            return False



        #play move
        self.board.play_move_gomoku(move, color)
        status = self.random(self.board, original, GoBoardUtil.opponent(color))

        self.board.reset_point_gomoku(move, color)
        return status


    def rules(self,board, original, color):


        game_end, win = self.board.check_game_end_gomoku()#check if the game ends or not
        if game_end:
            if win == original:
                return 1
            else:
                return 0
        if self.Win(color):
            checkpoint = "Win"
            moves = self.Win(color)
        elif self.BlockWin():
            checkpoint = "BlockWin"
            moves =self.BlockWin()
        elif self.OpenFour(color):
            checkpoint = "OpenFour"
            moves =self.OpenFour(color)
        elif self.BlockOpenFour(color):
            checkpoint = "BlockOpenFour"
            moves =self.BlockOpenFour(color)
        else:
            moves = GoBoardUtil.generate_legal_moves_gomoku(self.board)
        if len(moves) == 0:
            return 0.5
        #print(moves)
        move = moves.pop()

        if move == PASS:
            return 0.5
        self.board.play_move_gomoku(move, color)
        status = self.rules(board, original, GoBoardUtil.opponent(color))
        #print(original,color)
        self.board.reset_point_gomoku(move, color)

        return status


def point_to_coord(point, boardsize):
    """
    Transform point given as board array index
    to (row, col) coordinate representation.
    Special case: PASS is not transformed
    """
    if point == PASS:
        return PASS
    else:
        NS = boardsize + 1
        return divmod(point, NS)

def format_point(move):
    """
    Return move coordinates as a string such as 'a1', or 'pass'.
    """
    column_letters = "ABCDEFGHJKLMNOPQRSTUVWXYZ"
    #column_letters = "abcdefghjklmnopqrstuvwxyz"
    if move == PASS:
        return "pass"
    row, col = move
    if not 0 <= row < MAXSIZE or not 0 <= col < MAXSIZE:
        raise ValueError
    return column_letters[col - 1]+ str(row)

def move_to_coord(point_str, board_size):
    """
    Convert a string point_str representing a point, as specified by GTP,
    to a pair of coordinates (row, col) in range 1 .. board_size.
    Raises ValueError if point_str is invalid
    """
    if not 2 <= board_size <= MAXSIZE:
        raise ValueError("board_size out of range")
    s = point_str.lower()
    if s == "pass":
        return PASS
    try:
        col_c = s[0]
        if (not "a" <= col_c <= "z") or col_c == "i":
            raise ValueError
        col = ord(col_c) - ord("a")
        if col_c < "i":
            col += 1
        row = int(s[1:])
        if row < 1:
            raise ValueError
    except (IndexError, ValueError):
        raise ValueError("illegal move: \"{}\" wrong coordinate".format(s))
    if not (col <= board_size and row <= board_size):
        raise ValueError("illegal move: \"{}\" wrong coordinate".format(s))
    return row, col

def color_to_int(c):
    """convert character to the appropriate integer code"""
    color_to_int = {"b": BLACK , "w": WHITE, "e": EMPTY,
                    "BORDER": BORDER}
    return color_to_int[c]
