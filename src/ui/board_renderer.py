import pygame
from pygame.locals import *
from utils.constants import *
from utils.helpers import *

class BoardRenderer:
    def __init__(self, game):
        self.game = game
        self.stock_buy_buttons = None
        self.pass_button_rect = None
        self.pass_button_rect = None
        self.merger_ui_buttons = None
        self.chain_options = []
        self.tile_rects = []

        

    def draw(self):
            self.game.screen.fill((30, 30, 30))
            
            # --- Define Sidebar Areas ---
            right_sidebar = pygame.Rect(
                self.game.window_width - self.game.right_sidebar_width, 0,
                self.game.right_sidebar_width, self.game.window_height
            )
            pygame.draw.rect(self.game.screen, (70, 70, 70), right_sidebar)
            
            # Hotel Status Area (top of right sidebar)
            status_area = pygame.Rect(
                self.game.window_width - self.game.right_sidebar_width, 0,
                self.game.right_sidebar_width, self.game.status_area_height
            )
            pygame.draw.rect(self.game.screen, (100, 100, 100), status_area)
            
            # Log Area (remaining part of right sidebar)
            log_area = pygame.Rect(
                self.game.window_width - self.game.right_sidebar_width, self.game.status_area_height,
                self.game.right_sidebar_width, self.game.window_height - self.game.status_area_height
            )
            pygame.draw.rect(self.game.screen, (90, 90, 90), log_area)
            
            # --- Left Main Area (Grid and Player Info) ---
            left_area = pygame.Rect(
                0, 0,
                self.game.window_width - self.game.right_sidebar_width, self.game.window_height
            )
            
            # Grid Area: the upper part of left_area (above the player info area)
            grid_area = pygame.Rect(
                0, 0,
                left_area.width, left_area.height - self.game.bottom_info_height
            )
            pygame.draw.rect(self.game.screen, (30, 30, 30), grid_area)
            
            # Player Info Area: at the bottom of left_area
            player_info_area = pygame.Rect(
                0, left_area.height - self.game.bottom_info_height,
                left_area.width, self.game.bottom_info_height
            )
            pygame.draw.rect(self.game.screen, (60, 60, 60), player_info_area)
            
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
                    tile = self.game.grid_tiles[col][row]
                    cell = self.game.board.state[col][row]
                    if cell is None:
                        # Draw the empty grid background (or skip drawing a tile)
                        tile.color = BOARD_BACKGROUND_COLOR
                    else:
                        if cell["chain"] is not None:
                            # Get the color of the corresponding hotel chain
                            chain_name = cell["chain"]
                            tile.color = self.game.corporations[chain_name].color  # Use the corporation's assigned color
                        else:
                            tile.color = (TILE_COLOR_INDEPENDENT)  # Default color for independent tiles
                    tile.draw(self.game.screen, offset_x, offset_y, scale, grid_font)
            
            # --- Draw Hotel Status from Corporations ---
            sidebar_font = pygame.font.SysFont(None, 20)
            line_height = 22
            for i, corp in enumerate(self.game.corporations.values()):
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
                
                self.game.screen.blit(combined_surface, (status_area.x + 5, status_area.y + 5 + i * line_height))

            
            # --- Draw Log Messages in the Log Area ---
            log_font = pygame.font.SysFont(None, 20)
            max_log_lines = (log_area.height - 10) // line_height
            log_to_display = self.game.log_messages[-max_log_lines:]
            for i, msg in enumerate(log_to_display):
                text_surface = log_font.render(msg, True, (255, 255, 255))
                self.game.screen.blit(text_surface, (log_area.x + 5, log_area.y + 5 + i * line_height))
            
            # --- Draw Human Player Status ---
            human_player = self.game.players[0]
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
                self.game.screen.blit(text_surface, (player_info_area.x + 5, player_info_area.y + 5 + i * line_height))

            # Stocks with colored names
            stock_start_y = player_info_area.y + 5 + (len(info_lines)) * line_height
            current_y = stock_start_y

            for corp in self.game.corporations.values():
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
                
                self.game.screen.blit(combined_surface, (player_info_area.x + 5, current_y))
                current_y += line_height
            
            # Right half: hand area
            hand_area = pygame.Rect(
                player_info_area.x + player_info_area.width / 2,
                player_info_area.y,
                player_info_area.width / 2,
                player_info_area.height
            )
            pygame.draw.rect(self.game.screen, (0, 0, 0), hand_area, 2)

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

            self.tile_rects = []

            # Draw each tile icon
            for i, tile_coord in enumerate(human_player.tiles_in_hand):
                icon_x = start_x + i * (icon_size + spacing)
                icon_rect = pygame.Rect(icon_x, hand_area.y + 5, icon_size, icon_size)
                self.tile_rects.append((icon_rect, tile_coord))
                draw_tile_icon(self.game.screen, tile_coord, icon_rect, hand_font)

            if self.game.founding_phase:
                self._draw_chain_selection()

            # --- Draw Stock Market UI if in Buy Stock Phase and at least 1 chain is founded ---
            if self.game.logic.turn_phase == "buy_stock" and any(corp.size >= 2 for corp in self.game.corporations.values()):
                # Darken the log area
                overlay = pygame.Surface((log_area.width, log_area.height), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 128))  # Semi-transparent black
                self.game.screen.blit(overlay, (log_area.x, log_area.y))
                
                # Draw the stock market UI
                stock_market_rect = pygame.Rect(
                    self.game.window_width - self.game.right_sidebar_width, self.game.status_area_height,
                    self.game.right_sidebar_width, self.game.window_height - self.game.status_area_height
                )
                self.draw_stock_market(self.game.screen, stock_market_rect)

            if self.game.logic.merger_state:
                # Check if ANY human player has stocks in the current dissolving chain
                current_chain = self.game.logic.merger_state['losing_chains'][self.game.logic.merger_state['current_chain_idx']][0]
                human_has_stocks = any(p.is_human and p.stocks.get(current_chain, 0) > 0 
                                    for p in self.game.players)
                
                if human_has_stocks:
                    self._draw_merger_resolution()

            if self.game.logic.turn_phase == "end_game":
                self._draw_final_scores()

    def _draw_chain_selection(self):
        # Darken background
        overlay = pygame.Surface((self.game.window_width, self.game.window_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))  # Semi-transparent black
        self.game.screen.blit(overlay, (0, 0))
        
        # Draw selection box
        box_width = 400
        box_height = 150
        box_x = (self.game.window_width - box_width) // 2
        box_y = (self.game.window_height - box_height) // 2
        box_rect = pygame.Rect(box_x, box_y, box_width, box_height)
        pygame.draw.rect(self.game.screen, (70, 70, 70), box_rect)
        pygame.draw.rect(self.game.screen, (200, 200, 200), box_rect, 2)
        
        # Draw prompt text
        font = pygame.font.SysFont(None, 32)
        text = font.render("Choose hotel chain to found:", True, (255, 255, 255))
        self.game.screen.blit(text, (box_x + 20, box_y + 20))
        
        # Draw chain options
        self.chain_options = []
        x = box_x + 20
        y = box_y + 60
        for chain in self.game.available_chains:
            # Create button rect
            btn_width = 100
            btn_rect = pygame.Rect(x, y, btn_width, 40)
            
            # Draw colored button
            pygame.draw.rect(self.game.screen, chain.color, btn_rect)
            pygame.draw.rect(self.game.screen, (255, 255, 255), btn_rect, 2)
            
            # Draw chain name
            label = font.render(chain.name, True, (255, 255, 255))
            self.game.screen.blit(label, (x + 5, y + 5))
            
            self.chain_options.append((btn_rect, chain))
            x += btn_width + 20

    def draw_stock_market(self, surface, rect):
        font = pygame.font.SysFont(None, 24)
        header = font.render("Stock Market", True, (255, 255, 255))
        surface.blit(header, (rect.x + 10, rect.y + 10))
        
        y = rect.y + 40
        # Store button rectangles for click detection
        self.stock_buy_buttons = {}
        
        for corp in self.game.corporations.values():
            if corp.size < 2:  # Skip inactive chains
                continue
            
            # Colored name + price
            name_text = font.render(f"{corp.name}:", True, corp.color)
            price_text = font.render(f"${corp.get_stock_price()}", True, (255, 255, 255))
            stocks_text = font.render(f"Stocks: {corp.stocks_remaining}", True, (255, 255, 255))
            
            # Draw corporation info
            surface.blit(name_text, (rect.x + 10, y))
            surface.blit(price_text, (rect.x + 150, y))
            surface.blit(stocks_text, (rect.x + 10, y + 20))
            
            # Draw buy button
            button_rect = pygame.Rect(rect.x + 200, y, 80, 30)  # Make buttons bigger
            pygame.draw.rect(surface, (0, 200, 0), button_rect)
            button_text = font.render("Buy", True, (0, 0, 0))
            surface.blit(button_text, (button_rect.x + 30, button_rect.y + 8))  # Center text
            
            # Store button reference for this corporation
            self.stock_buy_buttons[corp.name] = button_rect
            
            y += 50
        
        # Draw "Pass" button
        self.pass_button_rect = pygame.Rect(rect.x + 10, y + 20, 100, 40)  # Make button bigger
        pygame.draw.rect(surface, (200, 60, 60), self.pass_button_rect)
        pass_text = font.render("Pass", True, (255, 255, 255))
        surface.blit(pass_text, (self.pass_button_rect.x + 30, self.pass_button_rect.y + 12))  # Center text

    def show_merger_resolution_ui(self, dominant, losing_chains):
        """Display merger resolution UI with bonuses and stock conversion"""
        if not losing_chains:
            return

    def _draw_merger_resolution(self):
        """Draw the merger resolution UI"""
        if not self.game.logic.merger_state:
            return
        
        state = self.game.logic.merger_state
        chain_name, original_size = state['losing_chains'][state['current_chain_idx']]
        chain = self.game.logic.corporations[chain_name]
        
        # Darken background
        overlay = pygame.Surface((self.game.window_width, self.game.window_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        self.game.screen.blit(overlay, (0, 0))
        
        # Draw resolution box
        box_width = 600
        box_height = 400
        box_x = (self.game.window_width - box_width) // 2
        box_y = (self.game.window_height - box_height) // 2
        box_rect = pygame.Rect(box_x, box_y, box_width, box_height)
        pygame.draw.rect(self.game.screen, (50, 50, 50), box_rect)
        pygame.draw.rect(self.game.screen, (200, 200, 200), box_rect, 2)
        
        font = pygame.font.SysFont(None, 32)
        small_font = pygame.font.SysFont(None, 24)
        
        if state['phase'] == 'bonuses':
            # Draw chain info
            title = font.render(f"Merger Resolution: {chain_name} (Size {original_size})", True, chain.color)
            self.game.screen.blit(title, (box_x + 10, box_y + 20))
            
            # Get shareholders
            shareholders = sorted(self.game.players,
                                key=lambda p: p.stocks[chain_name],
                                reverse=True)
            
            # Draw bonuses
            y = box_y + 60
            if len(shareholders) > 0 and shareholders[0].stocks[chain_name] > 0:
                majority_bonus = chain.current_bonus
                text = small_font.render(
                    f"Majority: {shareholders[0].name} - ${majority_bonus}",
                    True, (255, 255, 255)
                )
                self.game.screen.blit(text, (box_x + 40, y))
                y += 30
                
            if len(shareholders) > 1 and shareholders[1].stocks[chain_name] > 0:
                minority_bonus = chain.current_bonus // 2
                text = small_font.render(
                    f"Minority: {shareholders[1].name} - ${minority_bonus}",
                    True, (255, 255, 255)
                )
                self.game.screen.blit(text, (box_x + 40, y))
                y += 30
            
            # Draw next button
            next_button = pygame.Rect(box_x + box_width - 120, box_y + box_height - 50, 100, 30)
            pygame.draw.rect(self.game.screen, (0, 200, 0), next_button)
            next_text = font.render("Next", True, (255, 255, 255))
            self.game.screen.blit(next_text, (next_button.x + 20, next_button.y + 5))
            
            # Store button position for click detection
            self.merger_ui_buttons = {'next': next_button}
            
        elif state['phase'] == "stock_conversion":
            # Draw chain info
            title = font.render(f"Stock Conversion: {chain_name}", True, chain.color)
            self.game.screen.blit(title, (box_x + 20, box_y + 20))
            
            # Get player stocks
            current_player = self.game.logic.get_current_player()
            player_stocks = current_player.stocks.get(chain_name, 0)
            dominant_chain = self.game.logic.corporations[state['dominant']]
            
            # Draw stock info
            y = box_y + 60
            text = small_font.render(
                f"You have: {player_stocks} {chain_name} stocks",
                True, (255, 255, 255)
            )
            self.game.screen.blit(text, (box_x + 40, y))
            y += 30
            
            # Draw conversion options
            text = small_font.render(
                f"Convert 2:1 to {state['dominant']} or sell for half price (${chain.get_stock_price() // 2} each)",
                True, (255, 255, 255)
            )
            self.game.screen.blit(text, (box_x + 40, y))
            y += 40
            
            # Draw conversion buttons
            convert_button = pygame.Rect(box_x + 40, y, 200, 30)
            convert_enabled = player_stocks >= 2 and dominant_chain.stocks_remaining > 0
            btn_color = (0, 200, 0) if convert_enabled else (100, 100, 100)
            pygame.draw.rect(self.game.screen, btn_color, convert_button)
            convert_text = font.render("Convert", True, (255, 255, 255))
            self.game.screen.blit(convert_text, (convert_button.x + 20, convert_button.y + 5))
            
            sell_button = pygame.Rect(box_x + 260, y, 200, 30)
            sell_enabled = player_stocks > 0
            btn_color = (200, 0, 0) if sell_enabled else (100, 100, 100)
            pygame.draw.rect(self.game.screen, btn_color, sell_button)
            sell_text = font.render("Sell", True, (255, 255, 255))
            self.game.screen.blit(sell_text, (sell_button.x + 20, sell_button.y + 5))

            keep_button = pygame.Rect(box_x + 40, y + 40, 200, 30)
            pygame.draw.rect(self.game.screen, (0,0,200), keep_button)
            keep_text = font.render("Keep", True, (255,255,255))
            self.game.screen.blit(keep_text, (keep_button.x+20, keep_button.y+5))
            self.merger_ui_buttons['keep'] = keep_button

            if not convert_enabled and not sell_enabled:
                pass_button = pygame.Rect(box_x + 40, y + 40, 200, 30)
                pygame.draw.rect(self.game.screen, (100,100,100), pass_button)
                pass_text = font.render("Pass", True, (255,255,255))
                self.game.screen.blit(pass_text, (pass_button.x + 20, pass_button.y + 5))
                self.merger_ui_buttons['pass'] = pass_button
            
            # Store button positions for click detection
            self.merger_ui_buttons = {
                'convert': convert_button,
                'sell': sell_button
            }
            
        # Update display
        pygame.display.flip()