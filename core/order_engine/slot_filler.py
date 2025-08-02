from typing import Optional
from core.models import OrderState, Menu

def check_combo_missing_slots(order: OrderState) -> Optional[str]:
    for item in order.items:
        if item.type != "combo":
            continue

        if not item.drink_name:
            return "Which drink would you like with your combo?"

        if not item.side_name:
            return "Would you like French Fries or a different side with your combo?"

    return None


def check_missing_sizes(order: OrderState, menu: Menu) -> Optional[str]:
    for item in order.items:
        if item.type not in ["drink", "side"]:
            continue

        if item.size is not None:
            continue

        menu_item = next((m for m in menu.items if m.name == item.name), None)
        if not menu_item or not menu_item.sizes:
            continue

        return f"What size would you like for your {item.name}?"

    return None

