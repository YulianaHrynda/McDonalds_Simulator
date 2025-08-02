from fastapi import APIRouter, HTTPException
from uuid import uuid4

from core.models import OrderState
from api.models.request_models import AddItemRequest

orders = {}
router = APIRouter()

@router.post("/start")
def start_order():
    order_id = str(uuid4())
    orders[order_id] = OrderState()
    return {"order_id": order_id}

@router.get("/{order_id}")
def get_order(order_id: str):
    order = orders.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@router.post("/{order_id}/add")
def add_item(order_id: str, item: AddItemRequest):
    from core.menu_loader import load_menu_data
    from pathlib import Path
    from core.order_engine.adder import add_menu_item_to_order

    order = orders.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    menu = load_menu_data(
        virtual_items_path=Path("menu_data/menu_virtual_items.yaml"),
        ingredients_path=Path("menu_data/menu_ingredients.yaml"),
        upsells_path=Path("menu_data/menu_upsells.yaml"),
        deals_path=Path("menu_data/menu_deals.yaml"),
    )

    added = add_menu_item_to_order(
        menu,
        order,
        item_name=item.name,
        size=item.size,
        remove_ingredients=item.remove_ingredients,
        add_ingredients=item.add_ingredients,
    )

    if not added:
        raise HTTPException(status_code=400, detail="Item could not be added")

    return {"message": f"Added {item.name} to order"}

@router.post("/{order_id}/finalize")
def finalize_order(order_id: str):
    order = orders.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    from core.order_engine.summary import generate_order_summary
    summary = generate_order_summary(order)
    return {"summary": summary}
