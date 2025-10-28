import random
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field

# ================================================= ================
# Custom Exceptions
# ================================================= ================

class CaptainSonarError(Exception):
    """Base class for all Captain Sonar errors."""
    pass

class InvalidMoveError(CaptainSonarError):
    """Raised when a movement violates the map or rule constraints."""
    pass

class RuleViolationError(CaptainSonarError):
    """Raised when an action breaks game rules (e.g., crossing path, invalid repair)."""
    pass

class ActionNotAllowedError(CaptainSonarError):
    """Raised when a team attempts an action outside its allowed turn or sequence."""
    pass


# ================================================= ================
# Core Data Structures
# ================================================= ================

@dataclass
class Submarine:
    """Represents a team's submarine and its current state.

    Attributes:
        team (str): Name of the team controlling this submarine.
        position (Tuple[int, int]): Current coordinates of the submarine on the map.
        health (int): Remaining health points (max 4).
        path (List[Tuple[int, int]]): Historical movement path to prevent crossing.
        systems (Dict[str, bool]): Whether each weapon/system is charged.
        surface_needed (bool): Whether submarine must surface before moving again.

    """

    team: str
    position: Tuple[int, int]
    health: int = 4
    path: List[Tuple[int, int]] = field(default_factory=list)
    systems: Dict[str, bool] = field(default_factory=lambda: {
        "torpedo": False,
        "mine": False,
        "drone": False,
        "sonar": False
    })
    gauges: Dict[str, int] = field(default_factory=lambda: {
        "torpedo": 0,
        "mine": 0,
        "drone": 0,
        "sonar": 0
    })
    mines: List[Tuple[int, int]] = field(default_factory=list)
    surface_needed: bool = False


class Grid:
    """
    Represents a Captain Sonar map and game state.
    """
    def __init__(self, width=15, height=15):
        """
        Initializes an empty map.
        """
        self.width = width
        self.height = height
        self.grid = [['.' for _ in range(width)] for _ in range(height)]

        self.teams: Dict[str, Submarine] = {}
        self.current_turn: Optional[str] = None

    def __str__(self):
        """
        Returns a string representation of the map, including submarine positions.
        """
        grid_repr = [row[:] for row in self.grid]
        for team, sub in self.teams.items():
            x, y = sub.position
            if 0 <= y < self.height and 0 <= x < self.width:
                grid_repr[y][x] = team[0].upper()
        grid_str = "\n".join("".join(row) for row in grid_repr)
        if self.teams:
            grid_str += "\n\nTeams on the grid:"
            for team_name, sub in self.teams.items():
                grid_str += f"\n- {team_name}: {team_name[0].upper()}"
        return grid_str

    def switch_turn(self) -> None:
        """Switch the turn between teams."""
        if len(self.teams) != 2:
            raise RuleViolationError("Must have exactly two teams to switch turns.")
        self.current_turn = [t for t in self.teams if t != self.current_turn][0]

    def is_island(self, x, y):
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
        return self.grid[y][x] == 'X'

    @staticmethod
    def load_from_file(file_path: str) -> "Grid":
        """
        Loads a map from a text file.
        'X' represents an island, '.' represents water.
        """
        with open(file_path, 'r') as f:
            lines = [line.strip() for line in f.readlines()]


        height = len(lines)
        width = len(lines[0]) if height > 0 else 0
        grid = Grid(width, height)
        grid.grid = [list(line) for line in lines]
        return grid

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

    def add_team(self, team_name: str, position: Tuple[int, int]):
        """Adds a new team and their submarine to the game."""
        if team_name in self.teams:
            raise RuleViolationError(f"Team {team_name} already exists.")
        self.teams[team_name] = Submarine(team=team_name, position=position)

    def move_submarine(self, team: str, direction: str):
        sub = self.teams[team]
        x, y = sub.position
        deltas = {"N": (0, -1), "S": (0, 1), "E": (1, 0), "W": (-1, 0)}
        if direction not in deltas:
            raise InvalidMoveError("Invalid direction. Use N, S, E, or W.")

        dx, dy = deltas[direction]
        new_pos = (x + dx, y + dy)

        if not self._is_valid(new_pos[0], new_pos[1]):
            raise InvalidMoveError("Move goes off the board.")
        if new_pos in sub.path or self.is_island(new_pos[0], new_pos[1]):
            raise InvalidMoveError("Cannot cross own path or enter island.")

        sub.position = new_pos
        sub.path.append(new_pos)

    def _get_neighbors(self, x, y):
        return [(x+1, y), (x-1, y), (x, y-1), (x, y+1)]

    def _is_valid(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height and self.grid[y][x] == '.'
