# ./adk_agent_samples/mcp_client_agent/agent.py
import os
from google.adk.agents import LlmAgent, SequentialAgent, LoopAgent, BaseAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

# IMPORTANT: Replace this with the ABSOLUTE path to your my_adk_mcp_server.py script
PATH_TO_YOUR_MCP_SERVER_SCRIPT = "/home/odoo/src/break-fast-google-hackathon-2025/my_agent/server.py" # <<< REPLACE

mcp_submarine = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command='python3',  # Command to run your MCP server script
            args=[PATH_TO_YOUR_MCP_SERVER_SCRIPT],  # Argument is the path to the script
        )
    )
    # tool_filter=['load_web_page'] # Optional: ensure only specific tools are loaded
)

llm_model = 'gemini-2.5-flash'

def create_player_agent(player_marker: str, opponent_marker: str) -> LlmAgent:
    """Creates a player LlmAgent with access to the MCP tools."""
    return LlmAgent(
        name=f"Player{player_marker}",
        model=llm_model,
        instruction=(
            f"You are the strategic Tic-Tac-Toe player '{player_marker}'. Your goal is to win. "
            f"First, use the 'get_board_status' tool to check the board. "
            f"The status and current player is in the tool's JSON result. "
            f"If it is your turn ('{player_marker}') AND the status is 'CONTINUE', "
            f"you MUST use the 'make_move' tool to make a valid, strategic move. "
            f"If the game is over (WIN or DRAW), or if it is the opponent's ('{opponent_marker}') turn, do nothing. "
            "Always include the current board status in your final response if the game is still CONTINUING."
        ),
        tools=[mcp_submarine] # Provide access to the MCP tools
    )


player_x = create_player_agent('X', 'O')
player_o = create_player_agent('O', 'X')

# The sequential agent runs one full turn (X then O)
turn_sequence = SequentialAgent(
    name="TurnSequence",
    sub_agents=[
        player_x,
        player_o
    ]
)

# The orchestrator first resets the game, then loops the turns.
# FIX: Changed 'sub_agent' to 'sub_agents' (list) for LoopAgent to match strict ADK versions.
root_agent = SequentialAgent(
    name="TicTacToeGame_Orchestrator",
    sub_agents=[
        LoopAgent(
            name="GameLoop",
            sub_agents=[turn_sequence], # <-- FIX APPLIED HERE
            max_iterations=10 # Max 9 moves, plus a buffer
        )
    ]
)
