from utils.constants import CORPORATION_COLORS

CHAIN_DATA = {
    "Worldwide": {
        "price": [
            (2, 200), (3, 300), (4, 400), (5, 500),
            (6, 600), (11, 700), (21, 800), (31, 900), (41, 1000)
        ],
        "bonus": [
            (2, 2000), (3, 3000), (4, 4000), (5, 5000), (6, 6000), 
            (11, 7000), (21, 8000), (31, 9000), (41, 10000)
        ]
    },
    "Sackson": {
        "price": [
            (2, 200), (3, 300), (4, 400), (5, 500),
            (6, 600), (11, 700), (21, 800), (31, 900), (41, 1000)
        ],
        "bonus": [
            (2, 2000), (3, 3000), (4, 4000), (5, 5000), (6, 6000), 
            (11, 7000), (21, 8000), (31, 9000), (41, 10000)
        ]
    },
    "Festival": {
        "price": [
            (2, 300), (3, 400), (4, 500), (5, 600),
            (6, 700), (11, 800), (21, 900), (31, 1000), (41, 1100)
        ],
        "bonus": [
            (2, 3000), (3, 4000), (4, 5000), (5, 6000), (6, 7000), 
            (11, 8000), (21, 9000), (31, 10000), (41, 11000)
        ]
    },
    "Imperial": {
        "price": [
            (2, 300), (3, 400), (4, 500), (5, 600),
            (6, 700), (11, 800), (21, 900), (31, 1000), (41, 1100)
        ],
        "bonus": [
            (2, 3000), (3, 4000), (4, 5000), (5, 6000), (6, 7000), 
            (11, 8000), (21, 9000), (31, 10000), (41, 11000)
        ]
    },
    "American": {
        "price": [
            (2, 300), (3, 400), (4, 500), (5, 600),
            (6, 700), (11, 800), (21, 900), (31, 1000), (41, 1100)
        ],
        "bonus": [
            (2, 3000), (3, 4000), (4, 5000), (5, 6000), (6, 7000), 
            (11, 8000), (21, 9000), (31, 10000), (41, 11000)
        ]
    },
    "Continental": {
        "price": [
            (2, 400), (3, 500), (4, 600), (5, 700),
            (6, 800), (11, 900), (21, 1000), (31, 1100), (41, 1200)
        ],
        "bonus": [
            (2, 4000), (3, 5000), (4, 6000), (5, 7000), (6, 8000), 
            (11, 9000), (21, 10000), (31, 11000), (41, 12000)
        ]
    },
    "Tower": {
        "price": [
            (2, 400), (3, 500), (4, 600), (5, 700),
            (6, 800), (11, 900), (21, 1000), (31, 1100), (41, 1200)
        ],
        "bonus": [
            (2, 4000), (3, 5000), (4, 6000), (5, 7000), (6, 8000), 
            (11, 9000), (21, 10000), (31, 11000), (41, 12000)
        ]
    }
}

class Corporation:
    def __init__(self, name, initial_stocks=25):
        self.name = name
        self.stocks_remaining = initial_stocks
        self.size = 0  # Number of tiles in the chain
        self.current_value = 0  # Stock price, updated based on size
        self._size = 0
        self.headquarters_placed = False
        self.hq_position = None
        self.current_bonus = 0

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
        self.update_bonus()

    def add_tile(self, count=1):
        """Add one or more tiles to the hotel chain and update its value."""
        self.size += count
    
    def update_value(self):
        self.current_value = self.get_stock_price()

    def update_bonus(self):
        self.current_bonus = self.get_majority_bonus()
    
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

    def get_stock_price(self):
        if self.size < 2:
            return 0
        brackets = CHAIN_DATA[self.name]["price"]
        for min_size, price in reversed(brackets):
            if self.size >= min_size:
                return price
        return 0
    
    def get_majority_bonus(self):
        """Returns majority bonus for a chain based on its tile size"""
        if self.size < 2:
            return 0
        brackets = CHAIN_DATA[self.name]["bonus"]
        for min_size, majority in reversed(brackets):
            if self.size >= min_size:
                return majority
        return 0

    def __str__(self):
        return (f"Corporation {self.name} | Size: {self.size} | Value: ${self.current_value} | "
                f"Stocks remaining: {self.stocks_remaining} | Safe: {self.is_safe()}")
