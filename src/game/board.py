# src/board.py
from utils.constants import BOARD_WIDTH, BOARD_HEIGHT

class Board:
    def __init__(self):
        # Each cell will be None if empty, else a dict with keys: "owner" and "chain"
        self.state = [[None for _ in range(BOARD_HEIGHT)] for _ in range(BOARD_WIDTH)]
    
    def is_tile_empty(self, col, row):
        return self.state[col][row] is None

    def get_neighbors(self, col, row):
        neighbors = []
        if col > 0:
            neighbors.append((col-1, row))
        if col < BOARD_WIDTH - 1:
            neighbors.append((col+1, row))
        if row > 0:
            neighbors.append((col, row-1))
        if row < BOARD_HEIGHT - 1:
            neighbors.append((col, row+1))
        return neighbors

    def place_tile(self, col, row, placer):
        """
        Place a tile at (col, row) and determine hotel chain affiliation.
        Returns:
         - True if the tile is placed normally (joins or extends an existing chain).
         - "new_chain" if the tile is adjacent only to independent buildings,
           signaling that a new hotel chain should be founded.
         - "merge" if the tile touches tiles from two or more chains,
           signaling a merger.
         - False if the tile is already occupied.
        """
        if not self.is_tile_empty(col, row):
            return False
        
        neighbors = self.get_neighbors(col, row)
        adjacent_chains = set()
        adjacent_independents = []
        for (nc, nr) in neighbors:
            cell = self.state[nc][nr]
            if cell is not None:
                if cell["chain"] is not None:
                    adjacent_chains.add(cell["chain"])
                else:
                    adjacent_independents.append((nc, nr))
        
        # Case 1: No adjacent placed tiles – independent placement.
        if len(adjacent_chains) == 0 and len(adjacent_independents) == 0:
            self.state[col][row] = {"owner": placer, "chain": None}
            return True

        # Case 2: Exactly one chain adjacent: join that chain.
        if len(adjacent_chains) == 1:
            chain_name = adjacent_chains.pop()
            self.state[col][row] = {"owner": placer, "chain": chain_name}
            return chain_name

        # Case 3: Multiple chains adjacent: a merger.
        if len(adjacent_chains) > 1:
            # We'll signal a merger.
            return "merge"

        # Case 4: Adjacent independents (and no chain) – new chain founding.
        if len(adjacent_chains) == 0 and len(adjacent_independents) > 0:
            # Place tile as independent temporarily
            self.state[col][row] = {"owner": placer, "chain": None}
            return "new_chain"

    def found_chain(self, col, row, chain_name):
        """Convert ALL connected independents (including the placed tile) to this chain"""
        stack = [(col, row)]
        visited = set()
        absorbed = 0

        while stack:
            c, r = stack.pop()
            if (c, r) in visited:
                continue
            visited.add((c, r))

            # Skip invalid or empty tiles
            if not (0 <= c < BOARD_WIDTH and 0 <= r < BOARD_HEIGHT):
                continue
            if self.is_tile_empty(c, r):
                continue

            cell = self.state[c][r]
            if cell["chain"] is None:
                cell["chain"] = chain_name
                absorbed += 1
                # Add neighbors
                stack.extend(self.get_neighbors(c, r))

        return absorbed

    def merge_chains(self, col, row, adjacent_chains, corporations):
        # Determine dominant chain by size then stock price
        dominant = None
        max_size = -1
        max_value = -1
        
        for chain in adjacent_chains:
            corp = corporations[chain]
            if corp.size > max_size or (corp.size == max_size and corp.current_value > max_value):
                dominant = chain
                max_size = corp.size
                max_value = corp.current_value

        losing_chains = [c for c in adjacent_chains if c != dominant]
        absorbed_count = 0

        # Update board state
        for c in range(BOARD_WIDTH):
            for r in range(BOARD_HEIGHT):
                cell = self.state[c][r]
                if cell and cell["chain"] in losing_chains:
                    cell["chain"] = dominant
                    absorbed_count += 1

        return dominant, absorbed_count, losing_chains

    def would_cause_merger_of_safe_chains(self, col, row, corporations):
        if not self.is_tile_empty(col, row):
            return False
            
        neighbors = self.get_neighbors(col, row)
        adjacent_chains = set()
        
        for (nc, nr) in neighbors:
            cell = self.state[nc][nr]
            if cell and cell["chain"]:
                corp = corporations[cell["chain"]]
                if corp.is_safe():
                    adjacent_chains.add(cell["chain"])
        
        return len(adjacent_chains) >= 2

    def get_connected_independents(self, col, row):
        """Get all connected independent tiles"""
        stack = [(col, row)]
        visited = set()
        connected = []
        
        while stack:
            c, r = stack.pop()
            if (c, r) in visited:
                continue
            visited.add((c, r))
            
            if self.is_tile_empty(c, r) or self.state[c][r]["chain"] is not None:
                continue
                
            connected.append((c, r))
            stack.extend(self.get_neighbors(c, r))
        
        return connected