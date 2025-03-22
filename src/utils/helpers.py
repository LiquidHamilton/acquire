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
    """
    Recursively absorb independent tiles adjacent to the given position
    Returns count of independents absorbed
    """
    absorbed_count = 0
    
    # Get all directly adjacent tiles
    neighbors = board.get_neighbors(col, row)
    
    # First pass: mark all independents to be absorbed
    to_absorb = []
    for ncol, nrow in neighbors:
        # Check if neighbor exists and is independent
        if board.state[ncol][nrow] and board.state[ncol][nrow]["chain"] is None:
            to_absorb.append((ncol, nrow))
    
    # Second pass: absorb all marked tiles
    for ncol, nrow in to_absorb:
        board.state[ncol][nrow]["chain"] = chain_name
        absorbed_count += 1
        # Recursively absorb independents adjacent to this newly absorbed tile
        absorbed_count += absorb_independents(board, ncol, nrow, chain_name)
    
    return absorbed_count


