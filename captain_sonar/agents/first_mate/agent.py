from google.adk.agents import Agent
from captain_sonar.agents.first_mate.tools.systems_tools import charge_system, reset_system
from captain_sonar.agents.first_mate.tools.damage_tools import take_damage

from captain_sonar.agents.first_mate import prompt

first_mate_agent = Agent(
    model="gemini-2.5-flash",
    name="first_mate_agent",
    description="The First Mate in the submarine",
    instruction=prompt.FIRST_MATE_INSTURCTIONS,
    tools=[charge_system, reset_system, take_damage]
)
