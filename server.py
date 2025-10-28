'''Captain Sonar Turn-Based Game Core (FastMCP Compatible)


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
'''
from fastmcp import FastMCP
from typing import List, Dict
import random
import sqlite3

from grid import Grid, ActionNotAllowedError, InvalidMoveError, RuleViolationError


# Initialize the FastMCP server
app = FastMCP("Captain Sonar Server")

# ================================================================
# Database Setup
# ================================================================

DB_PATH = "captain_sonar.db"

def init_db():
    """Initializes the database and creates tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS grid (
            width INTEGER,
            height INTEGER,
            grid_data TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS game_state (
            current_turn TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS submarines (
            team_name TEXT PRIMARY KEY,
            position_x INTEGER,
            position_y INTEGER,
            health INTEGER,
            systems TEXT,
            gauges TEXT,
            surface_needed INTEGER
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS submarine_paths (
            team_name TEXT,
            path_order INTEGER,
            x INTEGER,
            y INTEGER,
            PRIMARY KEY (team_name, path_order)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS submarine_mines (
            team_name TEXT,
            x INTEGER,
            y INTEGER,
            PRIMARY KEY (team_name, x, y)
        )
    """)
    conn.commit()
    conn.close()

# Initialize the database on server start
init_db()


def get_game() -> Grid:
    """Factory function to get a Grid instance representing the current game state."""
    return Grid(db_path=DB_PATH)

# ================================================================
# FastMCP Tools / Game Actions
# ================================================================

@app.tool
def start_game(team_names: List[str]) -> Dict:
    """Initialize a new Captain Sonar turn-based match.

    This will clear any existing game data.

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

    # Create a fresh grid from the predefined map file
    game = Grid.load_from_file("predefined_map.txt")
    game.db_path = DB_PATH # Assign db_path to enable saving

    game.teams = {}
    for i, t in enumerate(team_names):
        while True:
            x = random.randint(0, game.width - 1)
            y = random.randint(0, game.height - 1)
            if not game.is_island(x, y):
                game.add_team(t, (x, y))
                break

    game.current_turn = team_names[0]
    game.save_to_db() # Save the initial state

    return {
        "turn": game.current_turn,
        "teams": {
            t: {
                "position": s.position,
                "health": s.health,
                "path": s.path,
                "systems": s.systems,
                "gauges": s.gauges,
                "mines": s.mines,
                "surface_needed": s.surface_needed,
            }
            for t, s in game.teams.items()
        },
    }

@app.tool
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
    g = get_game()
    if g.current_turn != team:
        raise ActionNotAllowedError(f"It's not {team}'s turn.")
    g.move_submarine(team, direction)

    # Charge systems
    sub = g.teams[team]
    for system in sub.gauges:
        if not sub.systems[system]: # if not already charged
            sub.gauges[system] += 1
    g.switch_turn()
    g.save_to_db()
    return {
        "turn": g.current_turn,
        "teams": {
            t: {
                "position": s.position,
                "health": s.health,
                "path": s.path,
                "systems": s.systems,
                "gauges": s.gauges,
                "mines": s.mines,
                "surface_needed": s.surface_needed,
            }
            for t, s in g.teams.items()
        },
    }


@app.tool
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
    g = get_game()
    if g.current_turn != team:
        raise ActionNotAllowedError(f"It's not {team}'s turn.")

    sub = g.teams[team]
    sub.path.clear()
    g.switch_turn()
    g.save_to_db()
    return {
        "turn": g.current_turn,
        "teams": {
            t: {
                "position": s.position,
                "health": s.health,
                "path": s.path,
                "systems": s.systems,
                "gauges": s.gauges,
                "mines": s.mines,
                "surface_needed": s.surface_needed,
            }
            for t, s in g.teams.items()
        },
    }

@app.tool
def drop_mine(team: str, x: int, y: int) -> Dict:
    """Drop a mine in an adjacent space."""
    g = get_game()
    if g.current_turn != team:
        raise ActionNotAllowedError(f"It's not {team}'s turn.")
    
    sub = g.teams[team]
    if not sub.systems["mine"]:
        raise RuleViolationError("Mine system is not charged.")

    px, py = sub.position
    if abs(px - x) + abs(py - y) != 1:
        raise InvalidMoveError("Mines can only be dropped in adjacent spaces.")

    if g.is_island(x, y) or (x, y) in sub.path:
        raise InvalidMoveError("Cannot drop a mine on an island or your own path.")

    sub.mines.append((x, y))
    sub.systems["mine"] = False
    sub.gauges["mine"] = 0
    g.switch_turn()
    g.save_to_db()
    return {
        "turn": g.current_turn,
        "teams": {
            t: {
                "position": s.position,
                "health": s.health,
                "path": s.path,
                "systems": s.systems,
                "gauges": s.gauges,
                "mines": s.mines,
                "surface_needed": s.surface_needed,
            }
            for t, s in g.teams.items()
        },
    }

@app.tool
def trigger_mine(team: str, x: int, y: int) -> Dict:
    """Trigger a mine at a specific location."""
    g = get_game()
    if g.current_turn != team:
        raise ActionNotAllowedError(f"It's not {team}'s turn.")

    sub = g.teams[team]
    if (x, y) not in sub.mines:
        raise InvalidMoveError("No mine at that location.")

    other_team = [t for t in g.teams if t != team][0]
    other_sub = g.teams[other_team]
    ox, oy = other_sub.position

    damage = 0
    if (ox, oy) == (x, y):
        damage = 2
    elif abs(ox - x) + abs(oy - y) == 1:
        damage = 1

    if damage > 0:
        other_sub.health -= damage
        if other_sub.health <= 0:
            print(f"{other_team} has been sunk! {team} wins!")

    sub.mines.remove((x,y))
    g.switch_turn()
    g.save_to_db()
    return {
        "turn": g.current_turn,
        "teams": {
            t: {
                "position": s.position,
                "health": s.health,
                "path": s.path,
                "systems": s.systems,
                "gauges": s.gauges,
                "mines": s.mines,
                "surface_needed": s.surface_needed,
            }
            for t, s in g.teams.items()
        },
    }

@app.tool
def launch_torpedo(team: str, x: int, y: int) -> Dict:
    """Launch a torpedo at a specific location."""
    g = get_game()
    if g.current_turn != team:
        raise ActionNotAllowedError(f"It's not {team}'s turn.")

    sub = g.teams[team]
    if not sub.systems["torpedo"]:
        raise RuleViolationError("Torpedo system is not charged.")

    px, py = sub.position
    if not (abs(px - x) <= 4 and py == y) and not (abs(py - y) <= 4 and px == x):
        raise InvalidMoveError("Torpedo can only be launched up to 4 spaces in a straight line.")

    other_team = [t for t in g.teams if t != team][0]
    other_sub = g.teams[other_team]
    ox, oy = other_sub.position

    damage = 0
    if (ox, oy) == (x, y):
        damage = 2
    elif abs(ox - x) + abs(oy - y) == 1:
        damage = 1

    if damage > 0:
        other_sub.health -= damage
        if other_sub.health <= 0:
            print(f"{other_team} has been sunk! {team} wins!")

    sub.systems["torpedo"] = False
    sub.gauges["torpedo"] = 0
    g.switch_turn()
    g.save_to_db()
    return {
        "turn": g.current_turn,
        "teams": {
            t: {
                "position": s.position,
                "health": s.health,
                "path": s.path,
                "systems": s.systems,
                "gauges": s.gauges,
                "mines": s.mines,
                "surface_needed": s.surface_needed,
            }
            for t, s in g.teams.items()
        },
    }

@app.tool
def get_state() -> Dict:
    """Return the current game state for both teams.

    Returns:
        Dict: JSON-serializable state with turn info and all submarines.

    Example:
        >>> get_state()
    """
    g = get_game()
    return {
        "turn": g.current_turn,
        "teams": {
            t: {
                "position": s.position,
                "health": s.health,
                "path": s.path,
                "systems": s.systems,
                "gauges": s.gauges,
                "mines": s.mines,
                "surface_needed": s.surface_needed,
            }
            for t, s in g.teams.items()
        }
    }

@app.tool
def get_grid_string() -> str:
    """Return the string representation of the grid.

    Returns:
        str: The grid as a string.
    """
    return str(get_game())


if __name__ == "__main__":
    # Run MCP server
    app.run()
