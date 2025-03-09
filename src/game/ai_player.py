from game.player import Player

class AIPlayer(Player):
    def __init__(self, name):
        super().__init__(name, is_human=False)

    # Placeholder for future AI decision-making methods
    def decide_move(self, board_state):
        # This method will eventually contain logic for making moves
        pass
