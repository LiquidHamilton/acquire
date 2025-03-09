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
        if self.size < 2:
            self.current_value = 0
        elif self.size < 11:
            # Lookup table based on the rulebook chart.
            price_chart = {
                2: 2000,
                3: 3000,
                4: 4000,
                5: 5000,
                6: 6000,
                7: 7000,
                8: 8000,
                9: 9000,
                10: 10000,
            }
            self.current_value = price_chart.get(self.size, 0)
        else:
            self.current_value = 11000

    
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
    
    def __str__(self):
        return (f"Corporation {self.name} | Size: {self.size} | Value: ${self.current_value} | "
                f"Stocks remaining: {self.stocks_remaining} | Safe: {self.is_safe()}")
