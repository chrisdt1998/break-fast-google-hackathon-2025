import random

class Grid:
    """
    Represents a Captain Sonar map.
    """
    def __init__(self, width=15, height=15):
        """
        Initializes an empty map.
        """
        self.width = width
        self.height = height
        self.grid = [['.' for _ in range(width)] for _ in range(height)]

    def __str__(self):
        """
        Returns a string representation of the map.
        """
        return "\n".join("".join(row) for row in self.grid)

    def load_from_file(self, file_path):
        """
        Loads a map from a text file.
        'X' represents an island, '.' represents water.
        """
        with open(file_path, 'r') as f:
            lines = [line.strip() for line in f.readlines()]
        self.height = len(lines)
        self.width = len(lines[0]) if self.height > 0 else 0
        self.grid = [list(line) for line in lines]

    def generate_random(self, width, height, num_islands, min_island_size=1, max_island_size=8):
        """
        Generates a random map with a given number of islands.
        """
        self.width = width
        self.height = height
        self.grid = [['.' for _ in range(width)] for _ in range(height)]
        
        island_count = 0
        attempts = 0
        max_attempts = num_islands * 20 # Prevent infinite loops

        while island_count < num_islands and attempts < max_attempts:
            attempts += 1
            
            start_x = random.randint(0, width - 1)
            start_y = random.randint(0, height - 1)

            if self.grid[start_y][start_x] == 'X':
                continue

            island_size = random.randint(min_island_size, max_island_size)
            
            current_island = []
            frontier = []

            self.grid[start_y][start_x] = 'X'
            current_island.append((start_x, start_y))
            
            for nx, ny in self._get_neighbors(start_x, start_y):
                if self._is_valid(nx, ny):
                    frontier.append((nx, ny))

            while len(current_island) < island_size and frontier:
                new_x, new_y = random.choice(frontier)
                frontier.remove((new_x, new_y))

                if self.grid[new_y][new_x] == 'X':
                    continue
                
                self.grid[new_y][new_x] = 'X'
                current_island.append((new_x, new_y))

                for nx, ny in self._get_neighbors(new_x, new_y):
                    if self._is_valid(nx, ny) and (nx, ny) not in frontier:
                        frontier.append((nx, ny))
            
            if len(current_island) > 0:
                island_count += 1

    def _get_neighbors(self, x, y):
        return [(x+1, y), (x-1, y), (x, y-1), (x, y+1)]

    def _is_valid(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height and self.grid[x][y] == '.'
