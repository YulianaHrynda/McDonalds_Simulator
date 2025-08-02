from core.models import OrderState

user_sessions: dict[int, OrderState] = {}
user_contexts: dict[int, dict] = {}

def get_user_order(user_id: int) -> OrderState:
    if user_id not in user_sessions:
        user_sessions[user_id] = OrderState()
    return user_sessions[user_id]

def reset_user_order(user_id: int):
    user_sessions[user_id] = OrderState()

def get_user_context(user_id: int) -> dict:
    if user_id not in user_contexts:
        user_contexts[user_id] = {}
    return user_contexts[user_id]

def reset_user_context(user_id: int):
    user_contexts[user_id] = {}
