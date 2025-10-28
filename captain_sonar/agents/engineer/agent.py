import random
from captain_sonar.constants import SUBMARINE_SYSTEMS
from google.adk.agents import Agent
from google.adk.tools import ToolContext
from captain_sonar.agents.engineer import prompt


def get_random_damage(tool_context: ToolContext):
    if not 'damaged_systems' in tool_context.state:
        tool_context.state['damaged_systems'] = []
    if random.random() < 0.7:
        undamaged = [system for system in SUBMARINE_SYSTEMS if not tool_context.state['damaged_systems']]
        random_system = random.choice(undamaged)
        tool_context.state['damaged_systems'].append(random_system)
        if len(tool_context.state['damaged_systems']) > 3:
            return "alert: 3 systems are damaged"
        return f"{random_system} is damaged"
    return "No new system was damaged"


def repair_system(system: str, tool_context: ToolContext):
    assert system in SUBMARINE_SYSTEMS
    if system in tool_context.state['damaged_systems']:
        tool_context.state['damaged_systems'].remove(system)
        return True
    return False


def repair_all_systems(tool_context: ToolContext):
    tool_context.state['damaged_systems'] = []


engineer_agent = Agent(
    model="gemini-2.5-flash",
    name="engineer_agent",
    description="The Engineer in the submarine",
    instruction=prompt.ENGINEER_INSTRUCTIONS,
    tools=[get_random_damage, repair_system, repair_all_systems]
)
