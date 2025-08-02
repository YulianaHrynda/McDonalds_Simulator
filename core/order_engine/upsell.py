from typing import Optional
from core.models import OrderState, Menu, OrderItem
from core.order_engine.combo_adder import add_combo_to_order
from core.order_engine.adder import add_menu_item_to_order


def get_upsell_suggestion(order: OrderState) -> Optional[str]:
    for item in order.items:
        if item.type == "burger" and not item.is_combo_upgrade:
            return "Would you like to make it a combo?"

    for item in order.items:
        if item.type == "combo" and "sauce" not in item.extras:
            return "Would you like a dipping sauce with your combo?"

    if not order.upsell_flags.get("dessert_offered", False):
        if order.has_combo() or order.has_burger():
            order.upsell_flags["dessert_offered"] = True
            return "Would you like a dessert today?"

    return None


def upgrade_burger_to_combo(
    menu: Menu,
    order: OrderState,
    burger_name: str
) -> Optional[OrderItem]:
    burger = next((i for i in order.items if i.name == burger_name and i.type == "burger"), None)
    if not burger:
        return None

    matching_combo = next((c for c in menu.combos if c.burger == burger.name), None)
    if not matching_combo:
        return None

    order.items.remove(burger)

    combo = add_combo_to_order(
        menu=menu,
        order=order,
        combo_name=matching_combo.name,
        drink_name=None,
        side_name=None,
        remove_ingredients=burger.ingredients_removed,
        add_ingredients=[i.name for i in burger.ingredients_added]
    )

    if combo:
        combo.is_combo_upgrade = True

    return combo


def add_sauce_to_combo(order: OrderState, combo_name: str, sauce_name: str) -> bool:
    combo = next(
        (i for i in order.items if i.type == "combo" and i.name.startswith(combo_name)),
        None
    )
    
    if not combo:
        return False

    if "sauce" not in combo.extras:
        combo.extras.append("sauce")
    return True



def add_dessert_to_order(
    menu: Menu,
    order: OrderState,
    dessert_name: str
) -> Optional[OrderItem]:
    if order.upsell_flags.get("dessert_added", False):
        return None

    dessert_item = add_menu_item_to_order(menu, order, item_name=dessert_name)
    if dessert_item:
        order.upsell_flags["dessert_added"] = True
    return dessert_item
