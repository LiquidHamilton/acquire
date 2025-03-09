import pygame
from pygame.locals import *
from utils.constants import *
from utils.constants import CORPORATION_COLORS
from utils.helpers import *

#TODO: Not properly absorbing independent tiles.

class Game:
    def __init__(self):
        pygame.init()
        # Window and layout settings...
        self.window_width = 1200
        self.window_height = 800
        self.right_sidebar_width = 300
        self.bottom_info_height = 150
        self.status_area_height = 250

        self.founding_phase = False
        self.available_chains = []
        self.founding_tile_pos = None

        self.screen = pygame.display.set_mode(
            (self.window_width, self.window_height),
            pygame.RESIZABLE | pygame.SCALED,
            vsync=1
        )
        pygame.display.set_caption("Acquire")
        self.clock = pygame.time.Clock()
        self.running = True

        # Initialize Board state.
        from game.board import Board
        self.board = Board()

        # Create a grid of Tile objects for rendering.
        from game.tile import Tile
        self.grid_tiles = []
        for col in range(BOARD_WIDTH):
            col_tiles = []
            for row in range(BOARD_HEIGHT):
                tile = Tile(col, row, TILE_SIZE, (TILE_COLOR))
                col_tiles.append(tile)
            self.grid_tiles.append(col_tiles)

        # Initialize players.
        self.players = []
        self.initialize_players(num_players=3)

        # Create the tile deck and distribute 6 tiles to each player.
        from game.tile_deck import TileDeck
        self.tile_deck = TileDeck()
        for player in self.players:
            initial_tiles = self.tile_deck.draw_tiles(6)
            for tile_coord in initial_tiles:
                player.add_tile(tile_coord)
            print(f"{player.name} initial hand: {player.tiles_in_hand}")

        # Initialize corporations (hotel chains).
        from game.corporation import Corporation
        self.corporations = {name: Corporation(name) for name in CORPORATION_COLORS.keys()}

        # Initialize game log.
        self.log_messages = []
        self.log_messages.append("Game started.")

        # Initialize game logic.
        from game.game_logic import GameLogic
        self.logic = GameLogic(self.players, self.tile_deck, self.board, self.corporations)

        # For UI: selected tile index (for human player)
        self.selected_tile_index = None

    def initialize_players(self, num_players):
        from game.player import Player
        from game.ai_player import AIPlayer
        self.players.append(Player("Human Player", is_human=True))
        for i in range(1, num_players):
            self.players.append(AIPlayer(f"AI Player {i}"))
        for player in self.players:
            print(player)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False
            elif event.type == VIDEORESIZE:
                self.window_width, self.window_height = event.w, event.h
                self.screen = pygame.display.set_mode(
                    (self.window_width, self.window_height),
                    pygame.RESIZABLE | pygame.SCALED,
                    vsync=1
                )
            elif event.type == MOUSEBUTTONDOWN:
                current_player = self.players[self.logic.current_turn_index]
                # Allow the human player to choose a new hotel to found
                if self.founding_phase:
                    mouse_x, mouse_y = event.pos
                    for i, (rect, chain) in enumerate(self.chain_options):
                        if rect.collidepoint(mouse_x, mouse_y):
                            self._finalize_chain_founding(chain)
                            return
                # Only handle input for human player's tile placement.
                if current_player.is_human and self.logic.turn_phase == "tile_placement":
                    # Define player info area and hand area.
                    left_area_width = self.window_width - self.right_sidebar_width
                    player_info_area = pygame.Rect(
                        0, self.window_height - self.bottom_info_height,
                        left_area_width, self.bottom_info_height
                    )
                    hand_area = pygame.Rect(
                        player_info_area.x + player_info_area.width / 2, player_info_area.y,
                        player_info_area.width / 2, player_info_area.height
                    )
                    mouse_x, mouse_y = event.pos
                    if hand_area.collidepoint(mouse_x, mouse_y):
                        hand = current_player.tiles_in_hand
                        if not hand:
                            return
                        num_tiles = len(hand)
                        max_icon_size = hand_area.height - 10
                        spacing = 5
                        if num_tiles > 0:
                            total_spacing = spacing * (num_tiles - 1)
                            available_width = hand_area.width - total_spacing
                            icon_size = min(available_width / num_tiles, max_icon_size)
                            start_x = hand_area.x + (hand_area.width - (num_tiles * icon_size + total_spacing)) / 2
                        else:
                            return
                        for i, tile_coord in enumerate(hand):
                            icon_x = start_x + i * (icon_size + spacing)
                            icon_rect = pygame.Rect(icon_x, hand_area.y + 5, icon_size, icon_size)
                            
                            if icon_rect.collidepoint(mouse_x, mouse_y):
                                self.selected_tile_index = i
                                col, row = tile_coord
                                result = self.board.place_tile(col, row, "HumanTile", self.corporations)

                                if result == "blocked":
                                    msg = f"Cannot place {col+1}{chr(65+row)}: All corporations active. Keep tile for later."
                                    self.log_messages.append(msg)
                                    self.selected_tile_index = None # Deselect tile
                                    return # Stay in tile placement phase
                                
                                if result == "new_chain":
                                    self.available_chains = [c for c in self.corporations.values() if c.size == 0 and c.stocks_remaining > 0]
                                    if not self.available_chains:
                                        msg = "Cannot found new chain - all corporations are active!"
                                        self.log_messages.append(msg)
                                        print(msg)
                                        self.selected_tile_index = None
                                        return
                                    
                                    self.founding_phase = True
                                    self.founding_tile_pos = (col, row)

                                elif result == "merge":
                                    neighbors = self.board.get_neighbors(col, row)
                                    adjacent_chains = set()
                                    for (nc, nr) in neighbors:
                                        cell = self.board.state[nc][nr]
                                        if cell is not None and cell["chain"] is not None:
                                            adjacent_chains.add(cell["chain"])
                                    
                                    dominant, absorbed_count, losing_chains = self.board.merge_chains(
                                        col, row, adjacent_chains, self.corporations
                                    )
                                                                    
                                    # After merger resolution, absorb independents around merged area
                                    merged_absorption = absorb_independents(self.board, col, row, dominant)
                                    self.corporations[dominant].size += (absorbed_count + merged_absorption)
                                    
                                    for chain in losing_chains:
                                        self.corporations[chain].size = 0  # Reset absorbed chains
                                        self.corporations[chain].update_value()

                                    absorbed_from_merge = absorb_independents(self.board, col, row, dominant)
                                    self.corporations[dominant].size += absorbed_from_merge

                                    msg = f"Human triggered a merger. {dominant} is dominant."
                                    self.log_messages.append(msg)
                                    print(msg)

                                    current_player.remove_tile(tile_coord)
                                    self.logic.turn_phase = "draw_tile"
                                elif result == True:
                                    # This brance handles independent placement
                                    msg = f"Human placed tile at {col+1}{chr(65+row)}"
                                    self.log_messages.append(msg)
                                    print(msg)
                                    current_player.remove_tile(tile_coord)
                                    self.logic.turn_phase = "draw_tile"
                                elif isinstance(result, str):  # result is the chain name
                                    chain_name = result
                                    self.board.state[col][row] = {"owner": "HumanTile", "chain": chain_name}

                                    msg = f"Human placed tile at {col+1}{chr(65+row)}."
                                    self.log_messages.append(msg)
                                    print(msg)
                                    current_player.remove_tile(tile_coord)
                                    
                                    # Absorb adjacent independents and count them.
                                    absorbed_count = absorb_independents(self.board, col, row, chain_name)
                                    
                                    # Update corporation size (placed tile + absorbed)
                                    self.corporations[chain_name].size += 1 + absorbed_count
                                    
                                    self.logic.turn_phase = "draw_tile"
                                else:
                                    msg = f"Tile {col+1}{chr(65+row)} already occupied."
                                    self.log_messages.append(msg)
                                    print(msg)
                                break

    def _finalize_chain_founding(self, chosen_chain):
        col, row = self.founding_tile_pos
        current_player = self.players[0]

        # Remove the placed tile from hand
        if self.selected_tile_index is not None:
            tile_coord = current_player.tiles_in_hand[self.selected_tile_index]
            current_player.remove_tile(tile_coord)
        
        # Absorb all connected independents (including the placed tile)
        absorbed_count = self.board.found_chain(col, row, chosen_chain.name)
        chosen_chain.size = absorbed_count  # No +1 needed

        # Set headquarters
        chosen_chain.place_headquarters(col, row)

            
        # Place the initial tile
        #self.board.state[col][row] = {"owner": "HumanTile", "chain": chosen_chain.name}
        
        # Deduct stock for founder's bonus
        chosen_chain.stocks_remaining -= 1
        self.players[0].stocks[chosen_chain.name] += 1
        
        msg = f"Founded {chosen_chain.name} at {col+1}{chr(65+row)}"
        self.log_messages.append(msg)
        
        # Cleanup
        self.founding_phase = False
        self.founding_tile_pos = None
        self.selected_tile_index = None
        self.logic.turn_phase = "draw_tile"

    def run(self):
        try:
            while self.running:
                self.clock.tick(60)
                self.handle_events()
                # Process AI turns and human draw/end phases.
                self.logic.process_turn(self.log_messages)
                self.draw()
                pygame.display.flip()
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            pygame.quit()

    def draw(self):
        self.screen.fill((30, 30, 30))
        
        # --- Define Sidebar Areas ---
        right_sidebar = pygame.Rect(
            self.window_width - self.right_sidebar_width, 0,
            self.right_sidebar_width, self.window_height
        )
        pygame.draw.rect(self.screen, (70, 70, 70), right_sidebar)
        
        # Hotel Status Area (top of right sidebar)
        status_area = pygame.Rect(
            self.window_width - self.right_sidebar_width, 0,
            self.right_sidebar_width, self.status_area_height
        )
        pygame.draw.rect(self.screen, (100, 100, 100), status_area)
        
        # Log Area (remaining part of right sidebar)
        log_area = pygame.Rect(
            self.window_width - self.right_sidebar_width, self.status_area_height,
            self.right_sidebar_width, self.window_height - self.status_area_height
        )
        pygame.draw.rect(self.screen, (90, 90, 90), log_area)
        
        # --- Left Main Area (Grid and Player Info) ---
        left_area = pygame.Rect(
            0, 0,
            self.window_width - self.right_sidebar_width, self.window_height
        )
        
        # Grid Area: the upper part of left_area (above the player info area)
        grid_area = pygame.Rect(
            0, 0,
            left_area.width, left_area.height - self.bottom_info_height
        )
        pygame.draw.rect(self.screen, (30, 30, 30), grid_area)
        
        # Player Info Area: at the bottom of left_area
        player_info_area = pygame.Rect(
            0, left_area.height - self.bottom_info_height,
            left_area.width, self.bottom_info_height
        )
        pygame.draw.rect(self.screen, (60, 60, 60), player_info_area)
        
        # --- Calculate Scale and Offsets for the Grid ---
        grid_native_width = BOARD_WIDTH * TILE_SIZE
        grid_native_height = BOARD_HEIGHT * TILE_SIZE
        scale_x = grid_area.width / grid_native_width
        scale_y = grid_area.height / grid_native_height
        scale = min(scale_x, scale_y)
        
        scaled_grid_width = grid_native_width * scale
        scaled_grid_height = grid_native_height * scale
        offset_x = grid_area.x + (grid_area.width - scaled_grid_width) / 2
        offset_y = grid_area.y + (grid_area.height - scaled_grid_height) / 2
        
        grid_font = pygame.font.SysFont(None, int(24 * scale))
        
        # --- Draw the Grid using the Tile objects ---
        for col in range(BOARD_WIDTH):
            for row in range(BOARD_HEIGHT):
                tile = self.grid_tiles[col][row]
                cell = self.board.state[col][row]
                if cell is None:
                    # Draw the empty grid background (or skip drawing a tile)
                    tile.color = BOARD_BACKGROUND_COLOR
                else:
                    if cell["chain"] is not None:
                        # Get the color of the corresponding hotel chain
                        chain_name = cell["chain"]
                        tile.color = self.corporations[chain_name].color  # Use the corporation's assigned color
                    else:
                        tile.color = (TILE_COLOR_INDEPENDENT)  # Default color for independent tiles
                tile.draw(self.screen, offset_x, offset_y, scale, grid_font)
        
        # --- Draw Hotel Status from Corporations ---
        sidebar_font = pygame.font.SysFont(None, 20)
        line_height = 22
        for i, corp in enumerate(self.corporations.values()):
            # Render corporation name in its color
            name_surface = sidebar_font.render(corp.name, True, corp.color)
            # Render other details in white
            details_text = f": Size {corp.size}, Value ${corp.current_value}, Stocks {corp.stocks_remaining}"
            details_surface = sidebar_font.render(details_text, True, (255, 255, 255))
            
            # Combine surfaces horizontally
            total_width = name_surface.get_width() + details_surface.get_width()
            combined_surface = pygame.Surface((total_width, line_height), pygame.SRCALPHA)
            combined_surface.blit(name_surface, (0, 0))
            combined_surface.blit(details_surface, (name_surface.get_width(), 0))
            
            self.screen.blit(combined_surface, (status_area.x + 5, status_area.y + 5 + i * line_height))

        
        # --- Draw Log Messages in the Log Area ---
        log_font = pygame.font.SysFont(None, 20)
        max_log_lines = (log_area.height - 10) // line_height
        log_to_display = self.log_messages[-max_log_lines:]
        for i, msg in enumerate(log_to_display):
            text_surface = log_font.render(msg, True, (255, 255, 255))
            self.screen.blit(text_surface, (log_area.x + 5, log_area.y + 5 + i * line_height))
        
        # --- Draw Human Player Status ---
        human_player = self.players[0]
        player_font = pygame.font.SysFont(None, 20)
        line_height = 22

        # Left half: text info
        info_lines = [
            f"Player: {human_player.name}",
            f"Money: ${human_player.money}",
            "Stocks:"
        ]
        for i, line in enumerate(info_lines):
            text_surface = player_font.render(line, True, (255, 255, 255))
            self.screen.blit(text_surface, (player_info_area.x + 5, player_info_area.y + 5 + i * line_height))

        # Stocks with colored names
        stock_start_y = player_info_area.y + 5 + (len(info_lines)) * line_height
        current_y = stock_start_y

        for corp in self.corporations.values():
            if human_player.stocks[corp.name] == 0:
                continue
            
            # Render corporation name in its color
            name_surface = player_font.render(f"{corp.name}: ", True, corp.color)
            # Render stock count in white
            count_surface = player_font.render(str(human_player.stocks[corp.name]), True, (255, 255, 255))
            
            # Combine and blit
            total_width = name_surface.get_width() + count_surface.get_width()
            combined_surface = pygame.Surface((total_width, line_height), pygame.SRCALPHA)
            combined_surface.blit(name_surface, (0, 0))
            combined_surface.blit(count_surface, (name_surface.get_width(), 0))
            
            self.screen.blit(combined_surface, (player_info_area.x + 5, current_y))
            current_y += line_height
        
        # Right half: hand area
        hand_area = pygame.Rect(
            player_info_area.x + player_info_area.width / 2,
            player_info_area.y,
            player_info_area.width / 2,
            player_info_area.height
        )
        pygame.draw.rect(self.screen, (0, 0, 0), hand_area, 2)

        # Calculate tile rendering parameters
        num_tiles = len(human_player.tiles_in_hand)
        spacing = 5
        max_icon_size = hand_area.height - 10  # This is the vertical limit
        hand_font = pygame.font.SysFont(None, 16)  # Define the font here

        if num_tiles > 0:
            total_spacing = spacing * (num_tiles - 1)
            available_width = hand_area.width - total_spacing
            icon_size = min(available_width / num_tiles, max_icon_size)
            start_x = hand_area.x + (hand_area.width - (num_tiles * icon_size + total_spacing)) / 2
        else:
            icon_size = max_icon_size
            start_x = hand_area.x

        # Draw each tile icon
        for i, tile_coord in enumerate(human_player.tiles_in_hand):
            icon_x = start_x + i * (icon_size + spacing)
            icon_rect = pygame.Rect(icon_x, hand_area.y + 5, icon_size, icon_size)
            draw_tile_icon(self.screen, tile_coord, icon_rect, hand_font)

        if self.founding_phase:
            self._draw_chain_selection()

    def _draw_chain_selection(self):
        # Darken background
        overlay = pygame.Surface((self.window_width, self.window_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))  # Semi-transparent black
        self.screen.blit(overlay, (0, 0))
        
        # Draw selection box
        box_width = 400
        box_height = 150
        box_x = (self.window_width - box_width) // 2
        box_y = (self.window_height - box_height) // 2
        box_rect = pygame.Rect(box_x, box_y, box_width, box_height)
        pygame.draw.rect(self.screen, (70, 70, 70), box_rect)
        pygame.draw.rect(self.screen, (200, 200, 200), box_rect, 2)
        
        # Draw prompt text
        font = pygame.font.SysFont(None, 32)
        text = font.render("Choose hotel chain to found:", True, (255, 255, 255))
        self.screen.blit(text, (box_x + 20, box_y + 20))
        
        # Draw chain options
        self.chain_options = []
        x = box_x + 20
        y = box_y + 60
        for chain in self.available_chains:
            # Create button rect
            btn_width = 100
            btn_rect = pygame.Rect(x, y, btn_width, 40)
            
            # Draw colored button
            pygame.draw.rect(self.screen, chain.color, btn_rect)
            pygame.draw.rect(self.screen, (255, 255, 255), btn_rect, 2)
            
            # Draw chain name
            label = font.render(chain.name, True, (255, 255, 255))
            self.screen.blit(label, (x + 5, y + 5))
            
            self.chain_options.append((btn_rect, chain))
            x += btn_width + 20


if __name__ == "__main__":
    game = Game()
    game.run()
