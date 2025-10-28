from google.adk.tools import ToolContext
from captain_sonar.constants import SUBMARINE_SYSTEMS


def charge_system(system_to_charge: str, tool_context: ToolContext):
    """Charge a system after a move"""
    assert system_to_charge in SUBMARINE_SYSTEMS
    if not 'systems' in tool_context.state:
        tool_context.state['systems'] = dict.fromkeys(SUBMARINE_SYSTEMS, 0)
    tool_context.state['systems'][system_to_charge] = 1
    return f"The system {system_to_charge} is ready"


def reset_system(system_to_reset: str, tool_context: ToolContext):
    """Reset the given system after usage"""
    assert system_to_reset in SUBMARINE_SYSTEMS
    tool_context.state['systems'][system_to_reset] = 0


def get_charged_systems(tool_context: ToolContext):
    """Get the list of systems that are charged."""
    if not tool_context.state.get('systems'):
        return "No system is charged"
    return [system for system in tool_context.state['system'] if tool_context.state['system']]
