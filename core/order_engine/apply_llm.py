from typing import Dict, Any
from core.models import Menu, OrderState
from core.order_engine.adder import add_menu_item_to_order
from core.order_engine.combo_adder import add_combo_to_order

def apply_llm_result(llm_result: Dict[str, Any], menu: Menu, order: OrderState) -> list[str]:
    messages = []

    for item in llm_result.get("items", []):
        item_type = item.get("type")
        item_name = item.get("name")
        size = item.get("size")
        remove_ingredients = item.get("remove_ingredients", [])
        add_ingredients = item.get("add_ingredients", [])
        quantity = item.get("quantity", 1)

        # === Combo (explicit or implied)
        if item.get("combo") is True or item_type == "combo":
            combo = next((c for c in menu.combos if c.name.lower().startswith(item_name.lower())), None)
            if combo:
                added = add_combo_to_order(
                    menu=menu,
                    order=order,
                    combo_name=combo.name,
                    drink_name=None,
                    side_name=None,
                    remove_ingredients=remove_ingredients,
                    add_ingredients=add_ingredients,
                    quantity=quantity,
                )
                if added:
                    messages.append(f"✅ Added combo: {combo.name} x{quantity}")
                else:
                    messages.append(f"⚠️ Couldn't add combo: {item_name}")
                continue

        # === Regular item
        added_items = add_menu_item_to_order(
            menu=menu,
            order=order,
            item_name=item_name,
            size=size,
            remove_ingredients=remove_ingredients,
            add_ingredients=add_ingredients,
            quantity=quantity,
        )

        if added_items:
            messages.append(f"✅ Added {item_type}: {item_name} x{len(added_items)}")
        else:
            messages.append(f"⚠️ Item not found or invalid: {item_name}")

    return messages
