import random
from utils.constants import BOARD_HEIGHT, BOARD_WIDTH

class TileDeck:
    def __init__(self):
        # Create a list of all building tile coordinates (each represented as a tuple)
        self.tiles = [(col, row) for col in range(BOARD_WIDTH) for row in range(BOARD_HEIGHT)]
        random.shuffle(self.tiles)

    def draw_tile(self):
        """Draw a single tile from the deck (or return None if empty)"""
        if self.tiles:
            return self.tiles.pop()
        return None
    
    def draw_tiles(self, count):
        """Draw up to 'count' tiles from the deck."""
        drawn = []
        for _ in range(count):
            tile = self.draw_tile()
            if tile is None:
                break
            drawn.append(tile)
        return drawn
    
    def remaining(self):
        """Return the number of tiles left in the deck."""
        return len(self.tiles)