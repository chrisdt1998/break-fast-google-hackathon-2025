from google.adk.agents import Agent
from captain_sonar.agents.radio_operator.tools import detect_enemy

from captain_sonar.agents.radio_operator.prompt import RADIO_OPERATOR_AGENT_PROMPT

radio_operator_agent = Agent(
    model="gemini-2.5-flash",
    name="radio_operator_agent",
    description="The Radio Operator in the submarine",
    instruction=RADIO_OPERATOR_AGENT_PROMPT,
    tools=[detect_enemy]
)
