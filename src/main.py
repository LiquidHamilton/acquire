import pygame
from pygame.locals import *
from utils.constants import *
from utils.constants import CORPORATION_COLORS
from utils.helpers import *
import ui.board_renderer as br
from ui.board_renderer import BoardRenderer
from utils.handle_events import EventHandler

#TODO: Allow choice when merged chains are equal in size.
#TODO: The game doesn't seem to be iterating through players properly during a merge. (Maybe add a print(player) statement before and after each player's convert/sell action to verify)
#TODO: Hotels not being put back into available chains after a merger. (Maybe the HQ needs to be set to False)
#TODO: When a human player initiates a merge, AI players are not iterating through and processing their conversion logic.
#TODO: When a merger happens, no players are gaining money for bonuses. (or sales)
#TODO: It doesn't seem to be recognizing the correct amount of held stocks for the human player when the AI initiates a merger.
#TODO: It is not selling stocks properly when player ineracts with merger dialog
#TODO: AI seems to buy too many stocks at once? It shows they're only adding 3 to their holdings, but more than 3 are removed from chain.
#TODO: Technically, when merging you can Keep/Sell/Trade, need to implement the "Keep" option as well as how many of each for each function.
#TODO: If all tiles would cause a new chain but no chains are avaiable (i.e. no playable tiles), reset hand.
#TODO: Make the AI Smarter.
#TODO: Endgame & Scoring Not Yet Implemented.


class Game:
    def __init__(self):
        pygame.init()
        self.window_width = 1200
        self.window_height = 800
        self.right_sidebar_width = 300
        self.bottom_info_height = 150
        self.status_area_height = 250

        self.renderer = BoardRenderer(self)
        self.event_handler = EventHandler(self)

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

    def run(self):
        try:
            while self.running:
                self.clock.tick(60)
                self.event_handler.handle_events()
                # Process AI turns and human draw/end phases.
                self.logic.process_turn(self.log_messages)
                self.renderer.draw()
                pygame.display.flip()
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()
