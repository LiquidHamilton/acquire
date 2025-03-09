from utils.helpers import *

class GameLogic:
    def __init__(self, players, tile_deck, board, corporations):
        self.players = players
        self.tile_deck = tile_deck
        self.board = board
        self.current_turn_index = 0
        self.corporations = corporations
        self.turn_phase = "tile_placement"

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
                self.turn_phase = "draw_tile"
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
                self.turn_phase = "draw_tile"

            elif result == "merge":
                neighbors = self.board.get_neighbors(col, row)
                adjacent_chains = set()
                for (nc, nr) in neighbors:
                    cell = self.board.state[nc][nr]
                    if cell and cell["chain"]:
                        adjacent_chains.add(cell["chain"])

                dominant, absorbed_count, losing_chains = self.board.merge_chains(
                    col, row, adjacent_chains, self.corporations
                )
                merged_absorption = absorb_independents(self.board, col, row, dominant)
                
                self.corporations[dominant].size += absorbed_count + merged_absorption
                for chain in losing_chains:
                    self.corporations[chain].size = 0
                
                current_player.remove_tile(tile_coord)
                log_messages.append(
                    f"{current_player.name} merged chains into {dominant}"
                )
                self.turn_phase = "draw_tile"

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
                self.turn_phase = "draw_tile"

            elif result is True:  # Independent placement (no absorption)
                current_player.remove_tile(tile_coord)
                log_messages.append(
                    f"{current_player.name} placed independent tile at {col+1}{chr(65+row)}"
                )
                self.turn_phase = "draw_tile"

            else:  # Invalid placement
                log_messages.append(
                    f"{current_player.name} failed to place tile at {col+1}{chr(65+row)}"
                )
                self.turn_phase = "draw_tile"

        elif self.turn_phase == "draw_tile":
            new_tile = self.tile_deck.draw_tile()
            if new_tile:
                current_player.add_tile(new_tile)
                log_messages.append(f"{current_player.name} drew a tile")
            self.turn_phase = "end_turn"

        elif self.turn_phase == "end_turn":
            self.current_turn_index = (self.current_turn_index + 1) % len(self.players)
            self.turn_phase = "tile_placement"