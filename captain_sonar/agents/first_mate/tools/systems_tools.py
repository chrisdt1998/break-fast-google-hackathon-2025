from google.adk.tools import ToolContext

SUBMARINE_SYSTEMS_CHARGE = {
    "torpedo": 3,
    "mine": 3,
    "sonar": 3,
    "drone": 4,
    "silence": 6,
    "scenario": 4,
}


def charge_system(system_to_charge: str, tool_context: ToolContext):
    """Charge a system"""
    assert system_to_charge in SUBMARINE_SYSTEMS_CHARGE
    if not 'systems' in tool_context.state:
        tool_context.state['systems'] = dict.fromkeys(SUBMARINE_SYSTEMS_CHARGE, 0)
    tool_context.state['systems'][system_to_charge] += 1
    if tool_context.state['systems'][system_to_charge] == SUBMARINE_SYSTEMS_CHARGE[system_to_charge]:
        return "The system is not ready"
    return f"The system {system_to_charge} is ready"


def reset_system(system_to_reset: str, tool_context: ToolContext):
    """Reset a system after usage"""
    assert system_to_reset in SUBMARINE_SYSTEMS_CHARGE
    tool_context.state['systems'][system_to_reset] = 0
