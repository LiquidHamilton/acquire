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
    
    def decide_stock_purchases(self, corporations, available_money):
        purchases = []
        active_chains = [c for c in corporations.values() if c.size >= 2]
        
        # Prioritize chains by stock price growth potential
        prioritized_chains = sorted(
            active_chains,
            key=lambda x: (
                x.get_stock_price() * min(x.size / 10, 1),  # Value growth potential
                -x.stocks_remaining  # Prefer chains with more available stocks
            ),
            reverse=True
        )
        
        remaining_money = available_money
        max_purchases = min(3, available_money // 200)  # At least 200 per stock
        
        for chain in prioritized_chains:
            price = chain.get_stock_price()
            while (remaining_money >= price and 
                chain.stocks_remaining > 0 and 
                len(purchases) < max_purchases):
                purchases.append(chain.name)
                remaining_money -= price
                chain.stocks_remaining -= 1
                if len(purchases) >= 3:
                    break
        
        return purchases

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