# ./adk_agent_samples/mcp_client_agent/agent.py
import os
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

# IMPORTANT: Replace this with the ABSOLUTE path to your my_adk_mcp_server.py script
PATH_TO_YOUR_MCP_SERVER_SCRIPT = "/home/dpro/workspaces/break-fast-google-hackathon-2025/server.py" # <<< REPLACE

mcp_submarine = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command='python3',  # Command to run your MCP server script
            args=[PATH_TO_YOUR_MCP_SERVER_SCRIPT],  # Argument is the path to the script
        )
    )
    # tool_filter=['load_web_page'] # Optional: ensure only specific tools are loaded
)

root_agent = LlmAgent(
    model='gemini-2.5-flash',
    name='web_reader_mcp_client_agent',
    instruction="Use the 'load_web_page' tool to fetch content from a URL provided by the user.",
    tools=[
        mcp_submarine,
    ],
)
