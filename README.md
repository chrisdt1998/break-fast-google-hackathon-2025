# Captain Sonar - Google AI Hackathon 2025

This project is a turn-based implementation of the board game Captain Sonar, built for the Google AI Hackathon 2025. In this game, you are not just playing as a single entity; you are the commander of a submarine, and your crew is composed of AI agents powered by Google's Gemini models. Each agent has a specific role, and you must work with them to defeat the enemy submarine.

The game uses a client-server architecture with a FastMCP server to manage the game state and expose actions as tools for the AI agents to interact with.

## Your Crew of AI Agents

Your submarine is operated by a team of AI agents, each with a specific role:

-   **The Captain:** (This is you!) You are responsible for the high-level strategy of the submarine. You will give commands to your crew and make the final decisions.
-   **The First Mate:** This agent is responsible for managing the submarine's systems. They will charge weapons, and manage the damage control.
-   **The Engineer:** The engineer is in charge of the submarine's reactor and repairs. They will work to keep the systems online and repair any damage taken.
-   **The Radio Operator:** This agent is your eyes and ears in the deep. They will listen for the enemy submarine and provide you with estimates of their location.

## How to Run

### 1. Installation

Install the required Python libraries:

```bash
pip install fastmcp google-adk
```

### 2. Start the Server

Run the `server.py` file to start the game server:

```bash
python server.py
```

The server will start on `http://127.0.0.1:8000`.

### 3. Run the Client

You can use the `client.py` file to interact with the server. This can be adapted to create your own AI agent.

```bash
python client.py
```

## Project Structure

-   `server.py`: The main game server, built with FastMCP. It manages the game logic and state.
-   `client.py`: An example client that shows how to connect to the server and call tools.
-   `grid.py`: Contains the core game logic and data structures for the game grid and submarines.
-   `predefined_map.txt`: A text file that defines the layout of the game map, including islands.
-   `captain_sonar/`: A directory containing the different agent implementations for your crew.
-   `my_agent/`: A directory for you to create your own custom agent.
-   `tic_tac_toe/`: A separate project for a Tic-Tac-Toe game, which can be used as a reference.

## Available Actions (FastMCP tools)

The following actions are exposed as FastMCP tools that can be called by clients:

-   `start_game(team_names: List[str])`: Initializes a new game with two teams.
-   `captain_move(team: str, direction: str)`: Moves a team's submarine in a given direction.
-   `surface(team: str)`: Clears the submarine's path, allowing it to move freely again.
-   `drop_mine(team: str, x: int, y: int)`: Drops a mine in an adjacent space.
-   `trigger_mine(team: str, x: int, y: int)`: Triggers a mine at a specific location.
-   `launch_torpedo(team: str, x: int, y: int)`: Launches a torpedo at a specific location.
-   `get_state()`: Returns the current game state.
-   `get_grid_string()`: Returns a string representation of the game grid.