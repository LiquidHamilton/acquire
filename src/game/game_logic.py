# src/game_logic.py

class GameLogic:
    def __init__(self, players, tile_deck, board, corporations):
        self.players = players
        self.tile_deck = tile_deck
        self.board = board
        self.current_turn_index = 0
        self.corporations = corporations
        # Turn phases: "tile_placement", "draw_tile", "end_turn"
        self.turn_phase = "tile_placement"

    def get_current_player(self):
        return self.players[self.current_turn_index]

    def process_turn(self, log_messages):
        current_player = self.get_current_player()
        # Only wait for input if it's a human player's tile placement phase.
        if current_player.is_human and self.turn_phase == "tile_placement":
            return

        # Process the turn for both AI players and for human players after tile placement.
        if self.turn_phase == "tile_placement":
            # (This branch will now only run for AI players.)
            if current_player.tiles_in_hand:
                tile_coord = current_player.tiles_in_hand[0]
                col, row = tile_coord
                if self.board.place_tile(col, row, "AI"):
                    msg = f"{current_player.name} placed tile at {col+1}{chr(65+row)}."
                    log_messages.append(msg)
                    current_player.remove_tile(tile_coord)
                    self.turn_phase = "draw_tile"
                else:
                    msg = f"{current_player.name} tried to place tile at {col+1}{chr(65+row)}, but it was occupied."
                    log_messages.append(msg)
                    self.turn_phase = "draw_tile"
        elif self.turn_phase == "draw_tile":
            new_tile = self.tile_deck.draw_tile()
            if new_tile is not None:
                current_player.add_tile(new_tile)
            log_messages.append(f"{current_player.name} draws a new tile.")
            self.turn_phase = "end_turn"
        elif self.turn_phase == "end_turn":
            # Handle dead tiles before passing turn
            current_player = self.get_current_player()
            dead_tiles = current_player.get_dead_tiles(self.board, self.corporations)
            
            if dead_tiles:
                # Remove dead tiles
                for tile in dead_tiles:
                    current_player.remove_tile(tile)
                    self.tile_deck.discard(tile)
                
                # Draw replacements
                num_to_draw = len(dead_tiles)
                new_tiles = self.tile_deck.draw_tiles(num_to_draw)
                for t in new_tiles:
                    current_player.add_tile(t)
                
                log_messages.append(
                    f"{current_player.name} discarded {len(dead_tiles)} dead tiles "
                    f"and drew {len(new_tiles)} replacements"
                )
            
            # Proceed to next player
            self.current_turn_index = (self.current_turn_index + 1) % len(self.players)
            self.turn_phase = "tile_placement"

