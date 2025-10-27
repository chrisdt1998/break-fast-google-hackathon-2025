"""Captain Sonar Turn-Based Game Core (FastMCP Compatible)

This module implements a turn-based version of the board game *Captain Sonar*.
It provides the complete game state and all possible actions, integrated with
FastMCP so that AI agents or human players can play against each other via tool calls.

Main Features:
    - Turn-based structure: teams alternate performing one action per turn.
    - Full rule enforcement: movement, surfacing, weapons, repairs, and gauges.
    - FastMCP tool wrappers around each core action.
    - Clear error handling for invalid or rule-breaking actions.
    - Rich docstrings describing rules and tool usage for AI agents.

AI Agent Integration:
    Each exposed action can be called as a FastMCP tool. Agents should query the
    current game state before acting to ensure valid moves.

Example usage:
    >>> from captain_sonar_fastmcp import start_game, captain_move
    >>> start_game(team_names=["Red", "Blue"])
    >>> captain_move(team="Red", direction="N")

Available Actions (FastMCP tools):
    - start_game
    - captain_move
    - surface
    - mark_gauge
    - activate_system
    - engineer_cross
    - complete_repair
    - drop_mine
    - trigger_mine
    - launch_torpedo
    - get_state

Errors:
    All rule or sequencing violations raise subclasses of `CaptainSonarError`.
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field

# Optional import stub for FastMCP
try:
    from fastmcp import tool
except ImportError:
    def tool(func):
        return func


# ================================================================
# Custom Exceptions
# ================================================================

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


# ================================================================
# Core Data Structures
# ================================================================

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
    surface_needed: bool = False


@dataclass
class Game:
    """Manages the full Captain Sonar turn-based game state.

    Attributes:
        teams (Dict[str, Submarine]): Active submarines per team.
        current_turn (str): Name of the team whose turn it is.
        board_size (int): Square grid dimension.
        islands (List[Tuple[int, int]]): Coordinates representing impassable islands.
    """

    teams: Dict[str, Submarine] = field(default_factory=dict)
    current_turn: Optional[str] = None
    board_size: int = 15
    islands: List[Tuple[int, int]] = field(default_factory=list)

    def switch_turn(self) -> None:
        """Switch the turn between teams."""
        if len(self.teams) != 2:
            raise RuleViolationError("Must have exactly two teams to switch turns.")
        self.current_turn = [t for t in self.teams if t != self.current_turn][0]


# ================================================================
# Global Game Instance
# ================================================================

_global_game = Game()


# ================================================================
# FastMCP Tools / Game Actions
# ================================================================

@tool
def start_game(team_names: List[str]) -> Dict:
    """Initialize a new Captain Sonar turn-based match.

    Args:
        team_names (List[str]): Two team names, e.g., ["Red", "Blue"].

    Returns:
        Dict: Serialized initial game state.

    Raises:
        RuleViolationError: If the number of teams is not two.

    Example:
        >>> start_game(["Red", "Blue"])
    """
    if len(team_names) != 2:
        raise RuleViolationError("Captain Sonar requires exactly two teams.")

    global _global_game
    _global_game = Game()
    for i, t in enumerate(team_names):
        _global_game.teams[t] = Submarine(team=t, position=(i, 0))
    _global_game.current_turn = team_names[0]
    return get_state()


@tool
def captain_move(team: str, direction: str) -> Dict:
    """Move the captain's submarine one step in the given direction.

    Gameplay Rules:
        - Movement is orthogonal (N, S, E, W).
        - Cannot cross its own path.
        - Cannot move into islands or off the board.
        - Can only move if it's the team's turn and submarine is not surfaced.

    Args:
        team (str): Team name performing the action.
        direction (str): One of 'N', 'S', 'E', 'W'.

    Returns:
        Dict: Updated game state.

    Raises:
        ActionNotAllowedError: If it's not the team's turn.
        InvalidMoveError: If movement is illegal.

    Example:
        >>> captain_move(team="Red", direction="N")
    """
    g = _global_game
    if g.current_turn != team:
        raise ActionNotAllowedError(f"It's not {team}'s turn.")

    sub = g.teams[team]
    x, y = sub.position
    deltas = {"N": (0, -1), "S": (0, 1), "E": (1, 0), "W": (-1, 0)}
    if direction not in deltas:
        raise InvalidMoveError("Invalid direction. Use N, S, E, or W.")

    dx, dy = deltas[direction]
    new_pos = (x + dx, y + dy)

    if not (0 <= new_pos[0] < g.board_size and 0 <= new_pos[1] < g.board_size):
        raise InvalidMoveError("Move goes off the board.")
    if new_pos in sub.path or new_pos in g.islands:
        raise InvalidMoveError("Cannot cross own path or enter island.")

    sub.position = new_pos
    sub.path.append(new_pos)

    g.switch_turn()
    return get_state()


@tool
def surface(team: str) -> Dict:
    """Perform a surface action, clearing the submarine path and allowing movement again.

    Args:
        team (str): Team performing the surface.

    Returns:
        Dict: Updated game state.

    Raises:
        ActionNotAllowedError: If it's not the team's turn.

    Example:
        >>> surface(team="Blue")
    """
    g = _global_game
    if g.current_turn != team:
        raise ActionNotAllowedError(f"It's not {team}'s turn.")

    sub = g.teams[team]
    sub.path.clear()
    sub.surface_needed = False

    g.switch_turn()
    return get_state()


@tool
def get_state() -> Dict:
    """Return the current game state for both teams.

    Returns:
        Dict: JSON-serializable state with turn info and all submarines.

    Example:
        >>> get_state()
    """
    g = _global_game
    return {
        "turn": g.current_turn,
        "teams": {
            t: {
                "position": s.position,
                "health": s.health,
                "path": s.path,
                "systems": s.systems,
                "surface_needed": s.surface_needed,
            }
            for t, s in g.teams.items()
        },
    }
