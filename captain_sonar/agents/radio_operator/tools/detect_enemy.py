from google.adk.tools import ToolContext

def detect_enemy(estimated_enemy_position: tuple, tool_context: ToolContext):
    # Listens if the enemy has emerged yet.
    if estimated_enemy_position:
        tool_context['estimated_opponent_position'] = estimated_enemy_position
