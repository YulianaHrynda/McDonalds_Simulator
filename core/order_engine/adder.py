from typing import Optional
from core.models import (
    Menu,
    OrderState,
    OrderItem,
    SelectedIngredient,
)

def add_menu_item_to_order(
    menu: Menu,
    order: OrderState,
    item_name: str,
    size: Optional[str] = None,
    remove_ingredients: Optional[list[str]] = None,
    add_ingredients: Optional[list[str]] = None,
    quantity: int = 1,
) -> list[OrderItem]:
    menu_item = next((item for item in menu.items if item.name == item_name), None)
    if not menu_item:
        return []

    remove_ingredients = remove_ingredients or []
    add_ingredients = add_ingredients or []
    optional_ingredient_map = {i.name: i.extra_price for i in menu_item.optional_ingredients}

    added_items: list[OrderItem] = []

    for _ in range(quantity):
        base_price = menu_item.price
        added_ing_objs: list[SelectedIngredient] = []

        for name in add_ingredients:
            if name in optional_ingredient_map:
                price = optional_ingredient_map[name]
                base_price += price
                added_ing_objs.append(SelectedIngredient(name=name, extra_price=price))

        computed_price = round(base_price, 2)

        item = OrderItem(
            name=menu_item.name,
            type=menu_item.category,
            size=size,
            ingredients_removed=remove_ingredients,
            ingredients_added=added_ing_objs,
            base_price=menu_item.price,
            computed_price=computed_price,
        )

        order.add_item(item)
        added_items.append(item)

    return added_items
