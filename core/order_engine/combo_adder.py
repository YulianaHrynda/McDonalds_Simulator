from typing import Optional, List
from core.models import Menu, OrderState, OrderItem, SelectedIngredient

def add_combo_to_order(
    menu: Menu,
    order: OrderState,
    combo_name: str,
    drink_name: Optional[str] = None,
    side_name: Optional[str] = None,
    remove_ingredients: Optional[List[str]] = None,
    add_ingredients: Optional[List[str]] = None,
    quantity: int = 1,
) -> List[OrderItem]:
    """Add one or more combos to the order."""
    combo = next((c for c in menu.combos if c.name == combo_name), None)
    if not combo:
        return []

    burger = next((i for i in menu.items if i.name == combo.burger), None)
    if not burger:
        return []

    remove_ingredients = remove_ingredients or []
    add_ingredients = add_ingredients or []
    optional_ingredient_map = {i.name: i.extra_price for i in burger.optional_ingredients}
    added_ing_objs: List[SelectedIngredient] = []
    extra_price = 0.0

    for name in add_ingredients:
        if name in optional_ingredient_map:
            price = optional_ingredient_map[name]
            extra_price += price
            added_ing_objs.append(SelectedIngredient(name=name, extra_price=price))

    side_item = next((i for i in menu.items if i.name == (side_name or combo.side_default)), None)
    drink_item = next((i for i in menu.items if i.name == drink_name), None) if drink_name else None

    name_parts = [burger.name]
    if side_item:
        name_parts.append(side_item.name)
    if drink_item:
        name_parts.append(drink_item.name)
    name = f"{combo.name}: " + " + ".join(name_parts)

    computed_price = round(combo.price + extra_price, 2)

    created_items = []
    for _ in range(quantity):
        item = OrderItem(
            name=name,
            type="combo",
            size=None,
            ingredients_removed=remove_ingredients,
            ingredients_added=added_ing_objs,
            extras=[],
            base_price=combo.price,
            computed_price=computed_price,
            drink_name=drink_item.name if drink_item else None,
            side_name=side_item.name if side_item else None,
        )
        order.add_item(item)
        created_items.append(item)

    return created_items
