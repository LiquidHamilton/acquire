from game.player import Player
from utils.constants import CORPORATION_COLORS

class AIPlayer(Player):
    def __init__(self, name):
        super().__init__(name, is_human=False)

    def decide_move(self, board, corporations):
        """
        Basic AI logic for tile placement:
        1. Try to place the first playable tile in hand
        2. Prefer mergers > founding > expansion
        3. Skip tiles that would illegally found a new chain
        """
        for tile in self.tiles_in_hand:
            col, row = tile
            if not board.is_tile_empty(col, row):
                continue

            # Simulate placement to check for blocked state
            result = self._simulate_placement(col, row, board, corporations)
            
            if result == "blocked":
                continue  # Skip this tile, can't place right now
            else:
                return tile  # Return first playable tile
        
        # If all tiles are blocked, return None (handle dead tiles elsewhere)
        return None

    def _simulate_placement(self, col, row, board, corporations):
        """Helper to predict placement result without modifying state"""
        neighbors = board.get_neighbors(col, row)
        adjacent_chains = set()
        adjacent_independents = []
        
        for (nc, nr) in neighbors:
            cell = board.state[nc][nr]
            if cell:
                if cell["chain"]:
                    adjacent_chains.add(cell["chain"])
                else:
                    adjacent_independents.append((nc, nr))

        # Check for new chain founding validity
        if len(adjacent_chains) == 0 and len(adjacent_independents) > 0:
            if all(corp.size > 0 for corp in corporations.values()):
                return "blocked"
        
        return "valid"  # Simplified check for demonstration