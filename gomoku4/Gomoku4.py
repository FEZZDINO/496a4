#!/usr/bin/python3
# Set the path to your python3 above

from gtp_connection import GtpConnection
from board_util import GoBoardUtil
from simple_board import SimpleGoBoard

class Gomoku():
    def __init__(self):
        """
        Gomoku player that selects moves randomly
        from the set of legal moves.
        Passe/resigns only at the end of game.

        """
        self.name = "GomokuAssignment2"
        self.version = 1.0

    # changes are here
    def get_move(self, board, color):
        # """
        # The genmove function called by gtp_connection
        # """
        # moves=GoBoardUtil.generate_legal_moves_gomoku(board)
        # toplay=board.current_player
        # best_result, best_move=-1.1, None
        # best_move=moves[0]
        # wins = np.zeros(len(moves))
        # visits = np.zeros(len(moves))
        # while True:
        #     for i, move in enumerate(moves):
        #         play_move(board, move, toplay)
        #         res=game_result(board)
        #         if res == toplay:
        #             undo(board, move)
        #             #This move is a immediate win
        #             self.best_move=move
        #             return move
        #         ret=self._do_playout(board, toplay)
        #         wins[i] += ret
        #         visits[i] += 1
        #         win_rate = wins[i] / visits[i]
        #         if win_rate > best_result:
        #             best_result=win_rate
        #             best_move=move
        #             self.best_move=best_move
        #         undo(board, move)
        # assert(best_move is not None)
        # return best_move
        return GoBoardUtil.generate_random_move_gomoku(board)

def run():
    """
    start the gtp connection and wait for commands.
    """
    board = SimpleGoBoard(7)
    con = GtpConnection(Gomoku(), board)
    con.start_connection()

if __name__=='__main__':
    run()
