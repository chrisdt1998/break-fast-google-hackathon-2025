from google.adk.tools import ToolContext
from captain_sonar.constants import SUBMARINE_SYSTEMS_CHARGE


def charge_system(system_to_charge: str, tool_context: ToolContext):
    assert system_to_charge in SUBMARINE_SYSTEMS_CHARGE
    if not 'systems' in tool_context.state:
        tool_context.state['systems'] = dict.fromkeys(SUBMARINE_SYSTEMS_CHARGE, 0)
    tool_context.state['systems'][system_to_charge] += 1
    if tool_context.state['systems'][system_to_charge] == SUBMARINE_SYSTEMS_CHARGE[system_to_charge]:
        return "The system has charged but is not ready yet"
    return f"The system {system_to_charge} is ready"


def reset_system(system_to_reset: str, tool_context: ToolContext):
    """Resets the given system after usage"""
    assert system_to_reset in SUBMARINE_SYSTEMS_CHARGE
    tool_context.state['systems'][system_to_reset] = 0


def get_charged_systems(tool_context: ToolContext):
    """Get the list of systems that are charged."""
    if not tool_context.state.get('systems'):
        return "No system is charged"
    return [system for system in tool_context.state['system'] if tool_context.state['system'] == SUBMARINE_SYSTEMS_CHARGE[system]]
