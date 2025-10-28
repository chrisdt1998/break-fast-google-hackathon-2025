import json
import os
from typing import Dict, List, Any
from fastmcp import FastMCP


# --- Game State Management and Logic ---
class TicTacToeLogic:
    def __init__(self):
        # Initializing state in memory for the server
        self.board = [[' ' for _ in range(3)] for _ in range(3)]
        self.status = "CONTINUE"
        self.player = 'X'
        self.move_count = 0

    def _check_win(self, board: List[List[str]]) -> bool:
        """Checks for a win condition."""
        lines = (
            board +
            list(zip(*board)) +
            [[board[i][i] for i in range(3)], [board[i][2 - i] for i in range(3)]]
        )
        for line in lines:
            if all(m == line[0] and m != ' ' for m in line):
                return True
        return False

    def get_board_status(self) -> Dict[str, Any]:
        """Returns the current board and status."""
        board_str = "\n".join(["|".join(row) for row in self.board])
        return {
            "board": board_str,
            "status": self.status,
            "player": self.player,
            "move_count": self.move_count
        }

    def reset_game(self) -> str:
        """Resets the game state."""
        self.board = [[' ' for _ in range(3)] for _ in range(3)]
        self.status = "CONTINUE"
        self.player = 'X'
        self.move_count = 0
        return "Game reset successfully. Player X starts."

    def make_move(self, row: int, col: int) -> str:
        """Executes a move and updates the game state, returning the full status dictionary."""
        
        # 1. Validation and Game Over Check
        if self.status != "CONTINUE":
            # Return error and current status
            return json.dumps({
                "status": "ERROR", 
                "message": f"Game is already over. Status: {self.status}. Call 'reset_game' to start anew."
            })
        if not (0 <= row <= 2 and 0 <= col <= 2):
            return json.dumps({"status": "ERROR", "message": "Invalid row/col. Must be 0, 1, or 2."})
        if self.board[row][col] != ' ':
            return json.dumps({"status": "ERROR", "message": "Cell already occupied. Choose a new move."})
        
        current_marker = self.player
        
        # 2. Execute Move
        self.board[row][col] = current_marker
        self.move_count += 1
        
        # 3. Check Status
        if self._check_win(self.board):
            self.status = f"{current_marker} WINS"
        elif self.move_count == 9:
            self.status = "DRAW"
        else:
            # 4. Switch Player
            self.player = 'O' if self.player == 'X' else 'X'

        # 5. Return the full status for the LLM to read
        return json.dumps(self.get_board_status())


# --- MCP Server Initialization ---
# Initialize the game logic instance
game = TicTacToeLogic()

# Create the MCP Server instance
mcp_app = FastMCP(name="tictactoe_mcp_server")

# Expose Tool 1: Get Status
@mcp_app.tool(
    name="get_board_status",
    description="Returns the current 3x3 board layout, the current game status (WIN/DRAW/CONTINUE), and whose turn it is (X/O) as a JSON string.",
)
def get_status_tool() -> str:
    """Returns the current board and status as a JSON string."""
    return json.dumps(game.get_board_status())

# Expose Tool 2: Make Move
@mcp_app.tool(
    name="make_move",
    description="Place a marker (X or O) on the board at a specific (row, col) coordinate (0 to 2). Returns updated status as a JSON string.",
)
def make_move_tool(row: int, col: int) -> str:
    """Makes a move and returns the outcome."""
    return game.make_move(row, col)

# Expose Tool 3: Reset Game
@mcp_app.tool(
    name="reset_game",
    description="Resets the Tic-Tac-Toe board and starts a new game with Player X.",
)
def reset_game_tool() -> str:
    """Resets the game."""
    return game.reset_game()

@mcp_app.tool(
    name="print_board",
    description='Prints the board as a grid.',
)
def print_board(board: List[List[str]]) -> str:
    """Prints the board as a grid."""
    board_str = "\n".join(["|".join(row) for row in board])
    return f"Board:\n{board_str}"

# If running directly (not via ADK stdio), start the server
if __name__ == "__main__":
    # In a typical ADK setup, the ADK framework handles server launch via StdIOTransport.
    # This block is here for local testing of the server itself.
    mcp_app.run()
