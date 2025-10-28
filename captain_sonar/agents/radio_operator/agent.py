from google.adk.agents import Agent
from google.adk.tools import ToolContext
from captain_sonar.agents.radio_operator import prompt


def update_position_estimate(estimate: list, tool_context: ToolContext):
    if 'position' not in tool_context.state:
        tool_context.state['position'] = estimate


def get_estimated_position(tool_context: ToolContext):
    return tool_context.state.get('position')


radio_operator_agent = Agent(
    model="gemini-2.5-flash",
    name="radio_operator_agent",
    description="The Radio Operator of the submarine",
    instruction=prompt.RADIO_OPERATOR_INSTURCTIONS,
    tools=[update_position_estimate, get_estimated_position]
)
