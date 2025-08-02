from core.models import OrderState

# In-memory session stores
user_sessions: dict[int, OrderState] = {}
user_contexts: dict[int, dict] = {}

def get_user_order(user_id: int) -> OrderState:
    """Повертає або ініціалізує поточне замовлення користувача."""
    if user_id not in user_sessions:
        user_sessions[user_id] = OrderState()
    return user_sessions[user_id]

def reset_user_order(user_id: int):
    """Очищає замовлення користувача (наприклад, після завершення)."""
    user_sessions[user_id] = OrderState()

def get_user_context(user_id: int) -> dict:
    """Повертає словник контексту користувача для тимчасових слотів/станів."""
    if user_id not in user_contexts:
        user_contexts[user_id] = {}
    return user_contexts[user_id]

def reset_user_context(user_id: int):
    """Очищає тимчасовий контекст (наприклад, pending_slot)."""
    user_contexts[user_id] = {}
