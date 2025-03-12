from utils.constants import CORPORATION_COLORS

class Player:
    def __init__(self, name, is_human=True):
        self.name = name
        self.is_human = is_human
        # As per Acquire rules, each player starts with $6,000.
        self.money = 6000
        # List of tile IDs or actual Tile objects that the player holds.
        self.tiles_in_hand = []
        self.stocks = {chain: 0 for chain in CORPORATION_COLORS.keys()}

    def get_money(self):
        return self.money

    def add_tile(self, tile):
        """Add a tile to the player's hand."""
        self.tiles_in_hand.append(tuple(tile))

    def remove_tile(self, tile):
        """Remove a tile from the player's hand."""
        tile = tuple(tile)
        if tile in self.tiles_in_hand:
            self.tiles_in_hand.remove(tile)

    def buy_stock(self, chain, quantity, price_per_stock):
        """Attempt to buy a given quantity of stock in a hotel chain."""
        total_cost = quantity * price_per_stock
        if self.money >= total_cost:
            self.money -= total_cost
            self.stocks[chain] = self.stocks.get(chain, 0) + quantity
            return True
        return False

    def sell_stock(self, chain, quantity, price_per_stock):
        """Sell a given quantity of stock, returning the money gained."""
        current_stocks = self.stocks.get(chain, 0)
        if current_stocks >= quantity:
            self.stocks[chain] = current_stocks - quantity
            self.money += quantity * price_per_stock
            return True
        return False
    
    def get_dead_tiles(self, board, corporations):
        dead_tiles = []
        for tile in self.tiles_in_hand:
            col, row = tile
            if board.would_cause_merger_of_safe_chains(col, row, corporations):
                dead_tiles.append(tile)
        return dead_tiles
    
    def __str__(self):
        return(f"Player {self.name} | Money: ${self.money} | "
               f"Tiles in hand: {len(self.tiles_in_hand)} | Stocks: {self.stocks}")
    
