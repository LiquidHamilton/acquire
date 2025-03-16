from utils.helpers import *

class GameLogic:
    def __init__(self, players, tile_deck, board, corporations):
        self.players = players
        self.tile_deck = tile_deck
        self.board = board
        self.current_turn_index = 0
        self.corporations = corporations
        self.turn_phase = "tile_placement"
        self.turn_phases = ["tile_placement", "buy_stock", "draw_tile", "end_turn", "end_game"]
        self.stocks_to_buy = 3

    def get_current_player(self):
        return self.players[self.current_turn_index]

    def process_turn(self, log_messages):
        current_player = self.get_current_player()
        
        if current_player.is_human and self.turn_phase == "tile_placement":
            return  # Let main.py handle human input

        # AI PLAYER LOGIC
        if self.turn_phase == "tile_placement" and not current_player.is_human:
            tile_coord = current_player.decide_move(self.board, self.corporations)
            
            if not tile_coord:
                # Handle dead tiles
                dead_tiles = current_player.get_dead_tiles(self.board, self.corporations)
                if dead_tiles:
                    for tile in dead_tiles:
                        current_player.remove_tile(tile)
                        self.tile_deck.discard(tile)
                    new_tiles = self.tile_deck.draw_tiles(len(dead_tiles))
                    for t in new_tiles:
                        current_player.add_tile(t)
                    log_messages.append(
                        f"{current_player.name} discarded {len(dead_tiles)} dead tiles"
                    )
                self.turn_phase = "buy_stock"
                return

            col, row = tile_coord
            result = self.board.place_tile(col, row, current_player.name, self.corporations)

            if result == "blocked":
                log_messages.append(
                    f"{current_player.name} skipped tile {col+1}{chr(65+row)} (no available chains)"
                )
                return  # Keep tile in hand

            elif result == "new_chain":
                available_chains = [c for c in self.corporations.values() 
                                  if c.size == 0 and c.stocks_remaining > 0]
                if available_chains:
                    chosen_chain = available_chains[0]
                    absorbed = self.board.found_chain(col, row, chosen_chain.name)
                    chosen_chain.size = absorbed
                    chosen_chain.place_headquarters(col, row)

                    # Deduct founder stock
                    chosen_chain.stocks_remaining -= 1
                    current_player.stocks[chosen_chain.name] += 1

                    current_player.remove_tile(tile_coord)
                    log_messages.append(
                        f"{current_player.name} founded {chosen_chain.name} "
                        f"at {col+1}{chr(65+row)} (size: {chosen_chain.size})"
                    )
                self.turn_phase = "buy_stock"

            elif result == "merge":
                # Common Merger Logic
                neighbors = self.board.get_neighbors(col, row)
                adjacent_chains = set()
                for (nc, nr) in neighbors:
                    cell = self.board.state[nc][nr]
                    if cell and cell["chain"]:
                        adjacent_chains.add(cell["chain"])

                dominant, absorbed_count, losing_chains = self.board.merge_chains(
                    col, row, adjacent_chains, self.corporations
                )
                # Full merger resolution
                self.resolve_merger(
                    self.corporations[dominant],
                    [self.corporations[chain] for chain in losing_chains],
                    log_messages
                )
                
                # Update chain sizes
                self.corporations[dominant].size += absorbed_count
                merged_absorption = absorb_independents(self.board, col, row, dominant)
                self.corporations[dominant].size += merged_absorption
                
                log_messages.append(
                    f"Merger resolved! {dominant} now has {self.corporations[dominant].size} tiles"
                )
                
                current_player.remove_tile(tile_coord)
                log_messages.append(
                    f"{current_player.name} merged chains into {dominant}"
                )
                self.turn_phase = "buy_stock"

            elif isinstance(result, str):  # Joined existing chain
                chain_name = result
                # Absorb independents and update size
                absorbed_count = absorb_independents(self.board, col, row, chain_name)
                self.corporations[chain_name].size += 1 + absorbed_count
                current_player.remove_tile(tile_coord)
                log_messages.append(
                    f"{current_player.name} expanded {chain_name} at {col+1}{chr(65+row)} "
                    f"(+{absorbed_count} tiles)"
                )
                self.turn_phase = "buy_stock"

            elif result is True:  # Independent placement (no absorption)
                current_player.remove_tile(tile_coord)
                log_messages.append(
                    f"{current_player.name} placed independent tile at {col+1}{chr(65+row)}"
                )
                self.turn_phase = "buy_stock"

            else:  # Invalid placement
                log_messages.append(
                    f"{current_player.name} failed to place tile at {col+1}{chr(65+row)}"
                )
                self.turn_phase = "tile_placement"

        elif self.turn_phase == "buy_stock":
            if current_player.is_human:
                # Handled via main.py UI
                pass
            else:
                purchases = current_player.decide_stock_purchases(
                    self.corporations, current_player.money
                )
                for chain_name in purchases[:3]:  # Enforce max 3 purchases
                    corp = self.corporations[chain_name]
                    if corp.stocks_remaining > 0 and current_player.money >= corp.get_stock_price():
                        current_player.buy_stock(chain_name, 1, corp.get_stock_price())
                        corp.stocks_remaining -= 1
                        self.stocks_to_buy -= 1
                        log_messages.append(f"{current_player.name} bought 1 {chain_name} stock")
                        
                # Force exit after processing
                self.stocks_to_buy = 0
                self.turn_phase = "draw_tile"

        elif self.turn_phase == "draw_tile":
            new_tile = self.tile_deck.draw_tile()
            if new_tile:
                current_player.add_tile(new_tile)
                log_messages.append(f"{current_player.name} drew a tile")
            self.turn_phase = "end_turn"

        elif self.turn_phase == "end_turn":
            if self.check_end_game():
                self.turn_phase="end_game"
            self.current_turn_index = (self.current_turn_index + 1) % len(self.players)
            self.stocks_to_buy = 3
            self.turn_phase = "tile_placement"

        elif self.turn_phase== "end_game":
            self.final_scoring()

    def resolve_merger(self, dominant_chain, absorbed_chains, log_messages):
        # Calculate majority/minority bonuses
        for chain in absorbed_chains:
            shareholders = sorted(self.players,
                                key=lambda p: p.stocks[chain.name],
                                reverse=True)
            
            # Award bonuses
            majority_bonus = chain.current_bonus
            minority_bonus = majority_bonus // 2
            
            if len(shareholders) > 0:
                shareholders[0].money += majority_bonus
                log_messages.append(
                    f"{shareholders[0].name} gets {chain.name} majority bonus (${majority_bonus})"
                )
            if len(shareholders) > 1:
                shareholders[1].money += minority_bonus
                log_messages.append(
                    f"{shareholders[1].name} gets {chain.name} minority bonus (${minority_bonus})"
                )
            
            # Handle stock conversion
            self._process_stock_conversion(dominant_chain, chain)
            
            # Reset absorbed chain MAKE SURE TO DIFFERENTIATE BETWEEN HUMAN AND AI ONCE LOGIC IS MOVED
            chain.size = 0
            chain.stocks_remaining += sum(p.stocks[chain.name] for p in self.players)
            chain.headquarters_placed = False

    def _process_stock_conversion(self, dominant, absorbed):
        for player in self.players:
            if player.is_human == True:
                return
            else:
                absorbed_stocks = player.stocks[absorbed.name]
                if absorbed_stocks > 0:
                    # Automatic 2:1 conversion
                    converted = min(absorbed_stocks // 2, dominant.stocks_remaining)
                    player.stocks[dominant.name] += converted
                    player.stocks[absorbed.name] -= converted * 2
                    dominant.stocks_remaining -= converted
                    
                    # Handle remaining odd stock
                    if absorbed_stocks % 2 != 0:
                        player.money += absorbed.get_stock_price() // 2
                        player.stocks[absorbed.name] -= 1

    def check_end_game(self):
        for corp in self.corporations.values():
            if corp.size >= 41:
                return True
        for _ in self.corporations.values():
            if corp.size > 0 and not corp.is_safe():
                return False

    def final_scoring(self):
        print("game over")