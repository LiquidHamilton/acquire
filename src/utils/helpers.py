import pygame
from utils.constants import *

# Helper to draw a small tile icon for the player's hand.
def draw_tile_icon(surface, tile_coord, rect, font):
    col, row = tile_coord
    pygame.draw.rect(surface, TILE_COLOR, rect)
    pygame.draw.rect(surface, (0, 0, 0), rect, 2)  # border
    label = f"{col+1}{chr(65+row)}"
    text_surface = font.render(label, True, (0, 0, 0))
    text_rect = text_surface.get_rect(center=rect.center)
    surface.blit(text_surface, text_rect)

def absorb_independents(board, col, row, chain_name):
    """Flood-fill from placed tile to absorb ALL contiguous independents"""
    stack = [(col, row)]
    visited = set()
    absorbed_count = 0

    while stack:
        c, r = stack.pop()
        if (c, r) in visited:
            continue
        visited.add((c, r))

        # Skip invalid coordinates
        if not (0 <= c < BOARD_WIDTH and 0 <= r < BOARD_HEIGHT):
            continue

        cell = board.state[c][r]
        if cell and cell["chain"] is None:
            # Convert to chain and count
            cell["chain"] = chain_name
            absorbed_count += 1
            
            # Add orthogonal neighbors
            for (nc, nr) in board.get_neighbors(c, r):
                stack.append((nc, nr))

    return absorbed_count


