import pygame
from pygame.locals import *
from utils.helpers import *

class EventHandler:
    def __init__(self, game):
        self.game = game

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                self.game.running = False
            elif self._handle_merger_resolution_events(event):
                continue
            elif event.type == VIDEORESIZE:
                self.game.window_width, self.game.window_height = event.w, event.h
                self.game.screen = pygame.display.set_mode(
                    (self.game.window_width, self.game.window_height),
                    pygame.RESIZABLE | pygame.SCALED,
                    vsync=1
                )
            elif event.type == MOUSEBUTTONDOWN:
                self._handle_mouse_click(event)

    def _handle_mouse_click(self, event):
        current_player = self.game.players[self.game.logic.current_turn_index]
        if not current_player.is_human:
            return

        # Handle founding phase
        if self.game.founding_phase:
            self._handle_founding_phase_click(event)
            return

        # Handle tile placement
        if self.game.logic.turn_phase == "tile_placement":
            self._handle_tile_placement_click(event, current_player)

        # Handle stock purchases
        if self.game.logic.turn_phase == "buy_stock":
            self._handle_stock_purchase_click(event, current_player)

    def _handle_founding_phase_click(self, event):
        mouse_x, mouse_y = event.pos
        for i, (rect, chain) in enumerate(self.game.renderer.chain_options):
            if rect.collidepoint(mouse_x, mouse_y):
                self.game.logic.finalize_chain_founding(
                    chain, self.game.founding_tile_pos, self.game.players[0], self.game.log_messages
                )
                return

    def _handle_tile_placement_click(self, event, current_player):
        mouse_x, mouse_y = event.pos

        # Check if the click is within the hand area
        left_area_width = self.game.window_width - self.game.right_sidebar_width
        player_info_area = pygame.Rect(
            0, self.game.window_height - self.game.bottom_info_height,
            left_area_width, self.game.bottom_info_height
        )
        hand_area = pygame.Rect(
            player_info_area.x + player_info_area.width / 2, player_info_area.y,
            player_info_area.width / 2, player_info_area.height
        )
        if not hand_area.collidepoint(mouse_x, mouse_y):
            return

        # Check if a tile was clicked
        for icon_rect, tile_coord in self.game.renderer.tile_rects:
            if icon_rect.collidepoint(mouse_x, mouse_y):
                self.game.selected_tile_index = self.game.players[0].tiles_in_hand.index(tile_coord)
                col, row = tile_coord
                result = self.game.board.place_tile(col, row, "HumanTile", self.game.corporations)

                if result == "blocked":
                    msg = f"Cannot place {col+1}{chr(65+row)}: All corporations active. Keep tile for later."
                    self.game.log_messages.append(msg)
                    self.game.selected_tile_index = None
                    return

                if result == "new_chain":
                    self.game.available_chains = [c for c in self.game.corporations.values() if c.size == 0 and c.stocks_remaining > 0]
                    if not self.game.available_chains:
                        msg = "Cannot found new chain - all corporations are active!"
                        self.game.log_messages.append(msg)
                        print(msg)
                        self.game.selected_tile_index = None
                        return
                    
                    self.game.founding_phase = True
                    self.game.founding_tile_pos = (col, row)

                elif result == "merge":
                    current_player.remove_tile(tile_coord)
                    self.game.logic._initiate_merge(col, row, self.game.log_messages)

                elif result == True:
                    msg = f"Human placed tile at {col+1}{chr(65+row)}"
                    self.game.log_messages.append(msg)
                    print(msg)
                    current_player.remove_tile(tile_coord)
                    self.game.logic.turn_phase = "buy_stock"
                elif isinstance(result, str):  # result is the chain name
                    chain_name = result
                    self.game.board.state[col][row] = {"owner": "HumanTile", "chain": chain_name}

                    msg = f"Human placed tile at {col+1}{chr(65+row)}."
                    self.game.log_messages.append(msg)
                    print(msg)
                    current_player.remove_tile(tile_coord)
                    
                    absorbed_count = absorb_independents(self.game.board, col, row, chain_name)
                    self.game.corporations[chain_name].size += 1 + absorbed_count
                    self.game.logic.turn_phase = "buy_stock"
                else:
                    msg = f"Tile {col+1}{chr(65+row)} already occupied."
                    self.game.log_messages.append(msg)
                    print(msg)
                break

    def _handle_stock_purchase_click(self, event, current_player):
        mouse_x, mouse_y = event.pos
        num_of_active_corps = sum(1 for corp in self.game.corporations.values() if corp.size >= 2)
        if num_of_active_corps == 0:
            self.game.logic.turn_phase = "draw_tile"
        
        # Check if the "Pass" button was clicked
        if (self.game.renderer.pass_button_rect is not None and self.game.renderer.pass_button_rect.collidepoint(mouse_x, mouse_y)):
            self.game.logic.stocks_to_buy = 0
            self.game.logic.turn_phase = "draw_tile"
            self.game.log_messages.append(f"{current_player.name} passed on buying stocks")
            return
        
        # Handle stock purchases
        if self.game.renderer.stock_buy_buttons is not None:
            for corp_name, button_rect in self.game.renderer.stock_buy_buttons.items():
                corp = self.game.corporations[corp_name]
                if corp.size < 2:  # Skip inactive chains
                    continue
                
                if button_rect.collidepoint(mouse_x, mouse_y):
                    if self.game.logic.can_afford_stock(current_player, corp):
                        if current_player.buy_stock(corp.name, 1, corp.get_stock_price()) and corp.stocks_remaining > 0:
                            corp.stocks_remaining -= 1
                            self.game.logic.stocks_to_buy -= 1
                            self.game.log_messages.append(
                                f"{current_player.name} bought 1 {corp.name} stock for ${corp.get_stock_price()}"
                            )
                            if self.game.logic.stocks_to_buy == 0:
                                self.game.logic.stocks_to_buy = 3
                                self.game.logic.turn_phase = "draw_tile"
                    else:
                        self.game.log_messages.append(
                            f"{current_player.name} cannot afford {corp.name} stock"
                        )

    def _handle_merger_resolution_events(self, event):
        """Handle events during merger resolution"""
        if not self.game.logic.merger_state:
            return False
        
        state = self.game.logic.merger_state
        current_player = state['players_to_process'][state['current_player_idx']]
        
        if not current_player.is_human:
            return False
            
        if event.type == MOUSEBUTTONDOWN:
            mouse_x, mouse_y = event.pos
            if hasattr(self.game.renderer, 'merger_ui_buttons'):
                if state['phase'] == 'bonuses':
                    if (self.game.renderer.merger_ui_buttons is not None and 
                        'next' in self.game.renderer.merger_ui_buttons and 
                        self.game.renderer.merger_ui_buttons['next'].collidepoint(mouse_x, mouse_y)):
                        state['phase'] = 'stock_conversion'
                        return True
                elif state['phase'] == 'stock_conversion':
                    if (self.game.renderer.merger_ui_buttons is not None and 
                        'convert' in self.game.renderer.merger_ui_buttons and 
                        self.game.renderer.merger_ui_buttons['convert'].collidepoint(mouse_x, mouse_y)):
                        chain_name = state['losing_chains'][state['current_chain_idx']][0]
                        player_stocks = current_player.stocks.get(chain_name, 0)
                        dominant_stocks = self.game.logic.corporations[state['dominant']].stocks_remaining
                        if player_stocks >= 2 and dominant_stocks > 0:
                            self.game.logic.handle_human_stock_choice(convert=True)
                            return True
                    if (self.game.renderer.merger_ui_buttons is not None and 
                        'sell' in self.game.renderer.merger_ui_buttons and 
                        self.game.renderer.merger_ui_buttons['sell'].collidepoint(mouse_x, mouse_y)):
                        chain_name = state['losing_chains'][state['current_chain_idx']][0]
                        player_stocks = current_player.stocks.get(chain_name, 0)
                        if player_stocks > 0:
                            self.game.logic.handle_human_stock_choice(convert=False)
                            return True
                    if (self.game.renderer.merger_ui_buttons is not None and 
                        'keep' in self.game.renderer.merger_ui_buttons and 
                        self.game.renderer.merger_ui_buttons['keep'].collidepoint(mouse_x, mouse_y)):
                        self.game.logic.handle_human_stock_choice(keep=True)
                    if (self.game.renderer.merger_ui_buttons is not None and 
                        'pass' in self.game.renderer.merger_ui_buttons and 
                        self.game.renderer.merger_ui_buttons['pass'].collidepoint(mouse_x, mouse_y)):
                        state['current_chain_idx'] += 1
                        if state['current_chain_idx'] >= len(state['losing_chains']):
                            self.game.logic.merger_state = None
                            self.game.logic.turn_phase = "buy_stock"
                        else:
                            state['phase'] = 'bonuses'
                        return True
                    
                    state['current_player_idx'] += 1
                    if state['current_player_idx'] >= len(state['players_to_process']):
                        state['current_player_idx'] = 0
                        state['current_chain_idx'] += 1
                        if state['current_chain_idx'] >= len(state['losing_chains']):
                            self.game.logic.merger_state = None
                            self.game.logic.turn_phase = "buy_stock"
                        else:
                            state['phase'] = 'bonuses'
                    return True
        
        return False