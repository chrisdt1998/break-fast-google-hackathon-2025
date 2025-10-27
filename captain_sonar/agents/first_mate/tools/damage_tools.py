
def take_damage(tool_context):
    if not tool_context.state['damages']:
        tool_context.state['damages'] = 1
    else:
        tool_context.state['damages'] += 1
    return
