from fastmcp import FastMCP
from typing import Dict

# Initialize the FastMCP server
app = FastMCP("CounterServer")

# Shared state (kept in memory)
state = {
    "counter": 0
}

# Define an "agent" function
def increment_agent(amount: int = 1) -> int:
    """Agent that increments a counter by a given amount."""
    state["counter"] += amount
    return state["counter"]

# Expose an MCP tool that calls the agent
@app.tool
def increment_counter(amount: int = 1) -> Dict[str, int]:
    """
    Increment the global counter by `amount` using the agent.
    Returns the new counter value.
    """
    new_value = increment_agent(amount)
    return {"counter": new_value}

# Optional: a getter tool
@app.tool
def get_counter() -> Dict[str, int]:
    """Returns the current counter value."""
    return {"counter": state["counter"]}


if __name__ == "__main__":
    # Run MCP server
    app.run(transport="http", host="127.0.0.1", port=8000)
