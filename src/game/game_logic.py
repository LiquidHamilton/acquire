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
        self.merger_state = None

    def get_current_player(self):
        return self.players[self.current_turn_index]

    def process_turn(self, log_messages):
        current_player = self.get_current_player()

        if self.merger_state:
            # Always show UI if ANY human has stocks in ANY dissolving chain
            all_losing_chains = [chain for chain, _ in self.merger_state['losing_chains']]
            human_players = [p for p in self.players if p.is_human]
            
            if any(p.stocks.get(chain, 0) > 0 
            for p in human_players 
            for chain in all_losing_chains):
                return  # Force UI rendering in main.py
            else:
                # Auto-resolve for AI-only mergers
                while self.merger_state:
                    self._process_merger_resolution(log_messages)
                return  # Exit to continue normal turn flow
        
        # Handle human tile placement (main.py will manage this)
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
                self._initiate_merge(col, row, log_messages)
                current_player.remove_tile(tile_coord)  # Remove the tile that initiated the merger
                
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
            print(current_player)
            if self.check_end_game():
                self.turn_phase = "end_game"
            else:
                self.current_turn_index = (self.current_turn_index + 1) % len(self.players)
                self.stocks_to_buy = 3
                self.turn_phase = "tile_placement"

        elif self.turn_phase == "end_game":
            self.final_scoring()

    def _initiate_merge(self, col, row, log_messages):
        current_player = self.get_current_player()
        neighbors = self.board.get_neighbors(col, row)
        adjacent_chains = {self.board.state[nc][nr]["chain"] for (nc, nr) in neighbors 
                        if self.board.state[nc][nr] and self.board.state[nc][nr]["chain"]}

        dominant, absorbed_count, losing_chains = self.board.merge_chains(
            col, row, adjacent_chains, self.corporations
        )

        merged_absorption = absorb_independents(self.board, col, row, dominant)
        self.corporations[dominant].size += absorbed_count + merged_absorption

        # Store original sizes for bonus calculation
        chain_sizes = {}
        for chain in losing_chains:
            chain_sizes[chain] = self.corporations[chain].size
            # Don't reset size yet - we'll do this after bonuses are calculated
        print(f"Merger initiated: {dominant} is dominant. {chain} is absorbed.")
        log_messages.append(f"Merger initiated with {dominant} as dominant chain")
        
        # Set merger state with critical information
        self.merger_state = {
            'dominant': dominant,
            'losing_chains': [(chain, chain_sizes[chain]) for chain in losing_chains],
            'current_chain_idx': 0,
            'phase': 'bonuses',
            #'current_player_idx': self.current_turn_index,  # Store who initiated the merger
            #'players_to_process': self.players[self.current_turn_index:] + self.players[:self.current_turn_index],
            'players_to_process': self.players.copy(),
            'current_player_idx': 0
        }
        
        self.turn_phase = "merger_resolution"

    def _process_merger_resolution(self, log_messages):
        if not self.merger_state:
            return
        
        state = self.merger_state
        current_player = state['players_to_process'][state['current_player_idx']]
        
        # Get current chain info
        chain_name, original_size = state['losing_chains'][state['current_chain_idx']]
        chain = self.corporations[chain_name]
        dominant = self.corporations[state['dominant']]
        
        if state['phase'] == 'bonuses':
            # Calculate bonuses using original pre-merger size
            chain.size = original_size  # Temporary restore for bonus calculation
            
            shareholders = sorted(self.players, 
                                key=lambda p: p.stocks[chain_name], 
                                reverse=True)
            
            # Award bonuses
            majority_shares = 0
            minority_shares = 0
            
            if shareholders:
                majority_shares = shareholders[0].stocks[chain_name]
            
            # Check for ties in majority
            majority_holders = [p for p in shareholders if p.stocks[chain_name] == majority_shares and majority_shares > 0]
            
            if len(majority_holders) > 1:
                # Split majority bonus among tied players
                majority_bonus = chain.current_bonus
                split_bonus = majority_bonus // len(majority_holders)
                for player in majority_holders:
                    player.money += split_bonus
                    log_messages.append(f"{player.name} received ${split_bonus} split majority bonus")
            elif majority_shares > 0:
                # Normal majority/minority
                majority_holder = shareholders[0]
                majority_bonus = chain.current_bonus
                majority_holder.money += majority_bonus
                log_messages.append(f"{majority_holder.name} received ${majority_bonus} majority bonus")
                
                # Find minority holders (exclude majority holder)
                remaining = [p for p in shareholders if p != majority_holder]
                if remaining:
                    minority_shares = remaining[0].stocks[chain_name]
                    minority_holders = [p for p in remaining if p.stocks[chain_name] == minority_shares and minority_shares > 0]
                    
                    if minority_holders:
                        minority_bonus = majority_bonus // 2
                        if len(minority_holders) > 1:
                            # Split minority bonus
                            split_bonus = minority_bonus // len(minority_holders)
                            for player in minority_holders:
                                player.money += split_bonus
                                log_messages.append(f"{player.name} received ${split_bonus} split minority bonus")
                        else:
                            minority_holders[0].money += minority_bonus
                            log_messages.append(f"{minority_holders[0].name} received ${minority_bonus} minority bonus")
            
            # Permanently reset chain size now that bonuses are calculated
            chain.size = 0
            
            # Move to stock conversion phase
            state['phase'] = 'stock_conversion'
            
            # If the current player is human, let main.py handle it
            if current_player.is_human:
                return
            
            # Otherwise, proceed with AI stock conversion
            self._process_merger_resolution(log_messages)
            
        elif state['phase'] == 'stock_conversion':
            if not current_player.is_human:
                # AI stock conversion logic
                absorbed_stocks = current_player.stocks.get(chain_name, 0)
                
                if absorbed_stocks > 0:
                    # AI strategy: Convert 2:1 if possible, sell the rest
                    if dominant.stocks_remaining > 0 and absorbed_stocks >= 2:
                        converted = min(absorbed_stocks // 2, dominant.stocks_remaining)
                        current_player.stocks[state['dominant']] += converted
                        current_player.stocks[chain_name] -= converted * 2
                        dominant.stocks_remaining -= converted
                        chain.stocks_remaining += converted * 2
                        
                        log_messages.append(
                            f"{current_player.name} converted {converted * 2} {chain_name} stocks to "
                            f"{converted} {state['dominant']} stocks"
                        )
                    
                    # Sell remaining stocks
                    remaining = current_player.stocks.get(chain_name, 0)
                    if remaining > 0:
                        total = remaining * (chain.get_stock_price() // 2)
                        current_player.money += total
                        current_player.stocks[chain_name] = 0
                        chain.stocks_remaining += remaining
                        
                        log_messages.append(
                            f"{current_player.name} sold {remaining} {chain_name} stocks for ${total}"
                        )
                    print(current_player)  # Debugging: Print current player
            
            # Move to next player
            state['current_player_idx'] += 1
            
            # Check if all players have processed this chain
            if state['current_player_idx'] >= len(state['players_to_process']):
                # Reset player index for the next chain
                state['current_player_idx'] = 0
                state['current_chain_idx'] += 1
                
                # Check if all chains have been processed
                if state['current_chain_idx'] >= len(state['losing_chains']):
                    # Merger resolution complete
                    self.merger_state = None
                    self.turn_phase = "buy_stock"
                    log_messages.append(f"Merger completed. {state['dominant']} is now size {dominant.size}")
                else:
                    # Move to the next chain's bonuses phase
                    state['phase'] = 'bonuses'
            
            # Continue processing if next is AI
            if not current_player.is_human:
                self._process_merger_resolution(log_messages)

        #chain.headquarters_placed = False
        #chain.hq_position = None

    def handle_human_stock_choice(self, convert):
        if not self.merger_state:
            return
            
        state = self.merger_state
        chain_name, original_size = state['losing_chains'][state['current_chain_idx']]
        chain = self.corporations[chain_name]
        dominant = self.corporations[state['dominant']]
        player = self.get_current_player()
        
        absorbed_stocks = player.stocks.get(chain_name, 0)
        if convert:
            # Convert stocks 2:1 to dominant chain
            converted = min(absorbed_stocks // 2, dominant.stocks_remaining)
            player.stocks[state['dominant']] = player.stocks.get(state['dominant'], 0) + converted
            player.stocks[chain_name] -= converted * 2
            dominant.stocks_remaining -= converted
            chain.stocks_remaining += converted * 2
            
            # Log the conversion
            message = f"{player.name} converted {converted * 2} {chain_name} stocks to {converted} {state['dominant']} stocks"
            print(message)  # Useful for debugging
        else:
            # Sell stocks for cash at half price
            stock_price = chain.get_stock_price()
            total = (absorbed_stocks * stock_price) // 2
            player.money += total
            player.stocks[chain_name] = 0
            chain.stocks_remaining += absorbed_stocks
            
            # Log the sale
            message = f"{player.name} sold {absorbed_stocks} {chain_name} stocks for ${total}"
            print(message)  # Useful for debugging
        
        # Move to next chain or complete merger resolution
        state['current_chain_idx'] += 1
        if state['current_chain_idx'] >= len(state['losing_chains']):
            self.merger_state = None
            self.turn_phase = "buy_stock"
        else:
            state['phase'] = 'bonuses'

    def check_end_game(self):
        for corp in self.corporations.values():
            if corp.size >= 41:
                return True
        for _ in self.corporations.values():
            if corp.size > 0 and not corp.is_safe():
                return False

    def final_scoring(self):
        #Create a dialog with final scores for each player.
        print("game over")

    def can_afford_stock(self, player, corp):
        return player.money >= corp.get_stock_price()
    
    def finalize_chain_founding(self, chosen_chain, founding_tile_pos, current_player, log_messages):
        col, row = founding_tile_pos

        # Remove the placed tile from hand
        if founding_tile_pos in current_player.tiles_in_hand:
            current_player.remove_tile(founding_tile_pos)

        # Absorb all connected independents (including the placed tile)
        absorbed_count = self.board.found_chain(col, row, chosen_chain.name)
        chosen_chain.size = absorbed_count  # No +1 needed

        # Set headquarters
        chosen_chain.place_headquarters(col, row)

        # Deduct stock for founder's bonus
        chosen_chain.stocks_remaining -= 1
        current_player.stocks[chosen_chain.name] += 1

        msg = f"Founded {chosen_chain.name} at {col+1}{chr(65+row)}"
        log_messages.append(msg)
        
        # Cleanup
        self.founding_phase = False
        self.founding_tile_pos = None
        self.selected_tile_index = None
        self.logic.turn_phase = "buy_stock"
    
    def process_stock_conversion(self, convert=True):
        """Process stock conversion choice"""
        chain_name = self.merger_resolution_data['losing_chains'][
            self.merger_resolution_data['current_chain_index']
        ]
        dominant = self.merger_resolution_data['dominant']
        
        player = self.players[0]  # Human player
        stocks = player.stocks.get(chain_name, 0)
        
        if convert:
            # Convert 2:1
            converted = min(stocks // 2, self.corporations[dominant].stocks_remaining)
            player.stocks[dominant] = player.stocks.get(dominant, 0) + converted
            player.stocks[chain_name] = max(0, player.stocks.get(chain_name, 0) - converted * 2)
            self.corporations[dominant].stocks_remaining -= converted
            
            # Log the conversion
            self.log_messages.append(
                f"{player.name} converted {converted * 2} {chain_name} stocks "
                f"to {converted} {dominant} stocks"
            )
        else:
            # Sell for half price
            sell_price = self.corporations[chain_name].get_stock_price() // 2
            total = stocks * sell_price
            player.money += total
            player.stocks[chain_name] = 0
            
            # Log the sale
            self.log_messages.append(
                f"{player.name} sold {stocks} {chain_name} stocks for ${total}"
            )
        
        # Move to next chain or complete
        self.merger_resolution_data['current_chain_index'] += 1
        if self.merger_resolution_data['current_chain_index'] >= len(
            self.merger_resolution_data['losing_chains']):
            # Merger complete
            del self.merger_resolution_data
            self.merger_phase = None
        else:
            # Show next chain's bonuses
            self.merger_phase = "show_bonuses"