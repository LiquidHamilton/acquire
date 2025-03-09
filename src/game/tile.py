import pygame
from utils.constants import *

class Tile:
    def __init__(self, col, row, tile_size, color):
        self.col = col
        self.row = row
        self.tile_size = tile_size
        self.color = color
        self.label = f"{col + 1}{chr(65 + row)}"

    def draw(self, surface, x_offset, y_offset, scale, font):
        # Calculate scaled rectangle for this tile
        rect = pygame.Rect(
            x_offset + self.col * self.tile_size * scale,
            y_offset + self.row * self.tile_size * scale,
            (self.tile_size - 2) * scale,
            (self.tile_size - 2) * scale,
        )
        # Draw the tile background
        pygame.draw.rect(surface, self.color, rect)

        # Render the label in black
        text_surface = font.render(self.label, True, (0,0,0))
        text_rect = text_surface.get_rect(center=rect.center)
        surface.blit(text_surface, text_rect)

