from google.adk.agents import Agent
from captain_sonar.agents.first_mate.tools.systems_tools import charge_system, reset_system, get_charged_systems
from captain_sonar.agents.first_mate.tools.damage_tools import take_damage
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

from captain_sonar.agents.first_mate import prompt

# IMPORTANT: Replace this with the ABSOLUTE path to your my_adk_mcp_server.py script
PATH_TO_YOUR_MCP_SERVER_SCRIPT = "/home/dpro/workspaces/break-fast-google-hackathon-2025/captain_sonar/server.py" # <<< REPLACE

mcp_first_mate = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command='python3',  # Command to run your MCP server script
            args=[PATH_TO_YOUR_MCP_SERVER_SCRIPT],  # Argument is the path to the script
        )
    ),
    tool_filter=['get_state', 'first_mate_charge_system'] # Optional: ensure only specific tools are loaded
)

first_mate_agent = Agent(
    model="gemini-2.5-flash",
    name="first_mate_agent",
    description="The First Mate in the submarine",
    instruction=prompt.FIRST_MATE_INSTURCTIONS,
    tools=[mcp_first_mate]
)
