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
import logging

from grid import Grid, ActionNotAllowedError, InvalidMoveError, RuleViolationError
from captain_sonar.constants import SUBMARINE_SYSTEMS_CHARGE


# Logging Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')



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
    logging.info(f"Attempting to start new game with teams: {team_names}")
    if len(team_names) != 2:
        logging.error(f"RuleViolationError: start_game requires 2 teams, but was called with {len(team_names)}: {team_names}")
        raise RuleViolationError("Captain Sonar requires exactly two teams.")

    # Create a fresh grid from the predefined map file
    logging.info("Loading grid from predefined_map.txt")
    game = Grid.load_from_file("predefined_map.txt")
    game.db_path = DB_PATH # Assign db_path to enable saving

    game.teams = {}
    for i, t in enumerate(team_names):
        while True:
            x = random.randint(0, game.width - 1)
            y = random.randint(0, game.height - 1)
            if not game.is_island(x, y):
                game.add_team(t, (x, y))
                logging.info(f"Placed Team '{t}' at starting position ({x}, {y})")
                break

    game.current_turn = team_names[0]
    game.save_to_db() # Save the initial state
    logging.info(f"New game started successfully. First turn: Team '{game.current_turn}'.")

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
    
    Note: This action does NOT end the turn. The First Mate must charge a system to complete the turn.

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
    logging.info(f"Team '{team}' attempting to move {direction}.")
    g = get_game()
    if g.current_turn != team:
        logging.warning(f"ActionNotAllowedError: Team '{team}' tried to move but it is '{g.current_turn}'s turn.")
        raise ActionNotAllowedError(f"It's not {team}'s turn.")
    
    try:
        g.move_submarine(team, direction)
        logging.info(f"Team '{team}' successfully moved {direction}.")
    except (InvalidMoveError, RuleViolationError) as e:
        logging.warning(f"Invalid move for Team '{team}' moving {direction}: {e}")
        raise e

    g.save_to_db() # Save state after move
    return {
        "turn": g.current_turn, # Turn does not change
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
def first_mate_charge_system(team: str, system: str) -> Dict:
    """Charge a specific system by one point. This action completes the team's turn.

    Args:
        team (str): The team performing the action.
        system (str): The name of the system to charge (e.g., "torpedo").

    Returns:
        Dict: Updated game state.

    Raises:
        ActionNotAllowedError: If it's not the team's turn.
        RuleViolationError: If the chosen system is invalid or already fully charged.
    """
    logging.info(f"Team '{team}' attempting to charge system '{system}'.")
    g = get_game()
    if g.current_turn != team:
        logging.warning(f"ActionNotAllowedError: Team '{team}' tried to charge a system but it is '{g.current_turn}'s turn.")
        raise ActionNotAllowedError(f"It's not {team}'s turn.")

    if system not in SUBMARINE_SYSTEMS_CHARGE:
        logging.error(f"RuleViolationError: Team '{team}' tried to charge invalid system '{system}'.")
        raise RuleViolationError(f"Invalid system: {system}")

    sub = g.teams[team]
    
    # Check if system is already charged
    if sub.systems.get(system, False):
        logging.warning(f"RuleViolationError: Team '{team}' tried to charge system '{system}' which is already fully charged.")
        raise RuleViolationError(f"System '{system}' is already fully charged and ready.")

    # Charge the system
    sub.gauges[system] = sub.gauges.get(system, 0) + 1
    logging.info(f"System '{system}' for Team '{team}' is now at charge {sub.gauges[system]}/{SUBMARINE_SYSTEMS_CHARGE[system]}.")

    # Check if the system is now fully charged
    if sub.gauges[system] >= SUBMARINE_SYSTEMS_CHARGE[system]:
        sub.systems[system] = True
        sub.gauges[system] = SUBMARINE_SYSTEMS_CHARGE[system] # Cap at max charge
        logging.info(f"System '{system}' for Team '{team}' is now fully charged.")

    g.switch_turn()
    g.save_to_db()
    logging.info(f"Turn ended for Team '{team}'. New turn for Team '{g.current_turn}'.")
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
    logging.info(f"Team '{team}' attempting to surface.")
    g = get_game()
    if g.current_turn != team:
        logging.warning(f"ActionNotAllowedError: Team '{team}' tried to surface but it is '{g.current_turn}'s turn.")
        raise ActionNotAllowedError(f"It's not {team}'s turn.")

    sub = g.teams[team]
    sub.path.clear()
    logging.info(f"Team '{team}' surfaced. Path has been cleared.")
    
    g.switch_turn()
    g.save_to_db()
    logging.info(f"Turn ended for Team '{team}'. New turn for Team '{g.current_turn}'.")
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
    logging.info(f"Team '{team}' attempting to drop a mine at ({x}, {y}).")
    g = get_game()
    if g.current_turn != team:
        logging.warning(f"ActionNotAllowedError: Team '{team}' tried to drop a mine but it is '{g.current_turn}'s turn.")
        raise ActionNotAllowedError(f"It's not {team}'s turn.")
    
    sub = g.teams[team]
    if not sub.systems["mine"]:
        logging.warning(f"RuleViolationError: Team '{team}' tried to drop a mine but the system is not charged.")
        raise RuleViolationError("Mine system is not charged.")

    px, py = sub.position
    if abs(px - x) + abs(py - y) != 1:
        logging.warning(f"InvalidMoveError: Team '{team}' tried to drop a mine at non-adjacent space ({x}, {y}).")
        raise InvalidMoveError("Mines can only be dropped in adjacent spaces.")

    if g.is_island(x, y) or (x, y) in sub.path:
        logging.warning(f"InvalidMoveError: Team '{team}' tried to drop a mine on an island or its own path at ({x}, {y}).")
        raise InvalidMoveError("Cannot drop a mine on an island or your own path.")

    sub.mines.append((x, y))
    sub.systems["mine"] = False
    sub.gauges["mine"] = 0
    logging.info(f"Team '{team}' successfully dropped a mine at ({x}, {y}). Mine system is now discharged.")

    g.switch_turn()
    g.save_to_db()
    logging.info(f"Turn ended for Team '{team}'. New turn for Team '{g.current_turn}'.")
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
    logging.info(f"Team '{team}' attempting to trigger a mine at ({x}, {y}).")
    g = get_game()
    if g.current_turn != team:
        logging.warning(f"ActionNotAllowedError: Team '{team}' tried to trigger a mine but it is '{g.current_turn}'s turn.")
        raise ActionNotAllowedError(f"It's not {team}'s turn.")

    sub = g.teams[team]
    if (x, y) not in sub.mines:
        logging.warning(f"InvalidMoveError: Team '{team}' tried to trigger a non-existent mine at ({x}, {y}).")
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
        logging.info(f"Mine at ({x}, {y}) hit Team '{other_team}' for {damage} damage.")
        other_sub.health -= damage
        if other_sub.health <= 0:
            logging.warning(f"Team '{other_team}' has been sunk by a mine! Team '{team}' wins!")
            print(f"{other_team} has been sunk! {team} wins!")
    else:
        logging.info(f"Mine at ({x}, {y}) hit nothing.")

    sub.mines.remove((x,y))
    g.switch_turn()
    g.save_to_db()
    logging.info(f"Turn ended for Team '{team}'. New turn for Team '{g.current_turn}'.")
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
    logging.info(f"Team '{team}' attempting to launch a torpedo at ({x}, {y}).")
    g = get_game()
    if g.current_turn != team:
        logging.warning(f"ActionNotAllowedError: Team '{team}' tried to launch a torpedo but it is '{g.current_turn}'s turn.")
        raise ActionNotAllowedError(f"It's not {team}'s turn.")

    sub = g.teams[team]
    if not sub.systems["torpedo"]:
        logging.warning(f"RuleViolationError: Team '{team}' tried to launch a torpedo but the system is not charged.")
        raise RuleViolationError("Torpedo system is not charged.")

    px, py = sub.position
    if not (abs(px - x) <= 4 and py == y) and not (abs(py - y) <= 4 and px == x):
        logging.warning(f"InvalidMoveError: Team '{team}' tried to fire a torpedo to an invalid location ({x}, {y}).")
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
        logging.info(f"Torpedo from Team '{team}' hit Team '{other_team}' at ({x}, {y}) for {damage} damage.")
        other_sub.health -= damage
        if other_sub.health <= 0:
            logging.warning(f"Team '{other_team}' has been sunk by a torpedo! Team '{team}' wins!")
            print(f"{other_team} has been sunk! {team} wins!")
    else:
        logging.info(f"Torpedo from Team '{team}' fired at ({x}, {y}) missed.")

    sub.systems["torpedo"] = False
    sub.gauges["torpedo"] = 0
    logging.info(f"Torpedo system for Team '{team}' is now discharged.")

    g.switch_turn()
    g.save_to_db()
    logging.info(f"Turn ended for Team '{team}'. New turn for Team '{g.current_turn}'.")
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
    logging.info("Fetching current game state.")
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
def get_grid_with_submarines() -> List[List[str]]:
    """Return a 2D array representation of the grid, including submarine positions.

    Returns:
        List[List[str]]: The grid as a list of lists.
    """
    logging.info("Fetching grid with submarine positions.")
    g = get_game()
    grid_repr = [row[:] for row in g.grid] # Create a copy
    for team, sub in g.teams.items():
        x, y = sub.position
        if 0 <= y < g.height and 0 <= x < g.width:
            grid_repr[y][x] = team[0].upper()
    return grid_repr


if __name__ == "__main__":
    # Run MCP server
    app.run()
