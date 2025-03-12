from utils.constants import CORPORATION_COLORS

class Corporation:
    def __init__(self, name, initial_stocks=25):
        self.name = name
        self.stocks_remaining = initial_stocks
        self.size = 0  # Number of tiles in the chain
        self.current_value = 0  # Stock price, updated based on size
        self._size = 0
        self.headquarters_placed = False
        self.hq_position = None

    @property
    def color(self):
        return CORPORATION_COLORS.get(self.name, (128,128,128))
    
    def place_headquarters(self, col, row):
        self.headquarters_placed = True
        self.hq_position = (col, row)

    @property
    def size(self):
        return self._size
    
    @size.setter
    def size(self, value):
        self._size = max(0, value)
        self.update_value() # Auto-update value when size changes

    def add_tile(self, count=1):
        """Add one or more tiles to the hotel chain and update its value."""
        self.size += count
    
    def update_value(self):
        self.current_value = self.get_stock_price()

    
    def remove_stocks(self, quantity):
        """
        Remove stocks from the corporation when players buy them.
        Return True if the removal was successful.
        """
        if self.stocks_remaining >= quantity:
            self.stocks_remaining -= quantity
            return True
        return False

    def add_stocks(self, quantity):
        """Add stocks back (for example, after a merger resolution)."""
        self.stocks_remaining += quantity
    
    def is_safe(self):
        """A hotel chain is 'safe' if it has 11 or more tiles."""
        return self.size >= 11
    
    def place_headquarters(self, col, row):
        if not self.headquarters_placed:
            self.headquarters_placed = True
            self.hq_position = (col, row)

    def get_shareholders_bonus(self):
        pass

    def set_shareholder_bonus(self):
        pass

    def get_stock_price(self):
        if self.size < 2:
            return 0
        if self.name == "Worldwide" or "Sackson":
            price_chart = {2: 200, 3: 300, 4: 400, 5: 500,
                        6: 600, 7: 700, 8: 800, 9: 900,
                        10: 1000, 11: 1100
            }
        elif self.name == "Festival" or "Imperial" or "American":
            price_chart = {2: 200, 3: 300, 4: 400, 5: 500,
                        6: 600, 7: 700, 8: 800, 9: 900,
                        10: 1000, 11: 1100
            }
        elif self.name == "Continental" or "Tower":
            price_chart = {2: 200, 3: 300, 4: 400, 5: 500,
                        6: 600, 7: 700, 8: 800, 9: 900,
                        10: 1000, 11: 1100
            }
        return price_chart.get(self.size, 1100)

    def __str__(self):
        return (f"Corporation {self.name} | Size: {self.size} | Value: ${self.current_value} | "
                f"Stocks remaining: {self.stocks_remaining} | Safe: {self.is_safe()}")
