from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from uuid import uuid4
from pathlib import Path
from typing import Dict

from core.models import OrderState
from core.menu_loader import load_menu_data
from core.order_engine.apply_llm import apply_llm_result
from core.order_engine.summary import generate_order_summary
from core.order_engine.deal_applier import maybe_apply_double_deal
from core.order_engine.slot_filler import check_combo_missing_slots, check_missing_sizes
from core.order_engine.upsell import get_upsell_suggestion
from core.llm_processor import parse_order

app = FastAPI()

ORDERS: Dict[str, OrderState] = {}

menu = load_menu_data(
    virtual_items_path=Path("menu_data/menu_virtual_items.yaml"),
    ingredients_path=Path("menu_data/menu_ingredients.yaml"),
    upsells_path=Path("menu_data/menu_upsells.yaml"),
    deals_path=Path("menu_data/menu_deals.yaml"),
)

class UserMessage(BaseModel):
    text: str


@app.post("/start")
def start_order():
    order_id = str(uuid4())
    ORDERS[order_id] = OrderState()
    return {
        "order_id": order_id,
        "message": "👋 Welcome to McDonald's! What can I get you started with?"
    }



@app.post("/order/new")
def new_order():
    """
    RESTful створення нового замовлення.
    """
    order_id = str(uuid4())
    ORDERS[order_id] = OrderState()
    return {"order_id": order_id}


@app.post("/order/{order_id}/message")
def process_message(order_id: str, message: UserMessage):
    if order_id not in ORDERS:
        raise HTTPException(status_code=404, detail="Order not found")

    order = ORDERS[order_id]
    user_input = message.text.strip()

    # Завершення замовлення
    if user_input.lower() in ["that's all", "done", "finish", "no, that's all"]:
        summary = generate_order_summary(order)
        del ORDERS[order_id]
        return {
            "summary": summary,
            "status": "finished"
        }

    result = parse_order(user_input)
    response_messages = []

    if result.get("intent") == "add_items":
        response_messages.extend(apply_llm_result(result, menu, order))

        deal_msg = maybe_apply_double_deal(menu, order)
        if deal_msg:
            response_messages.append(f"💸 {deal_msg}")

        slot_msg = check_combo_missing_slots(order)
        if slot_msg:
            response_messages.append(slot_msg)
            return {
                "messages": response_messages,
                "status": "waiting_for_slot"
            }

        size_msg = check_missing_sizes(order, menu)
        if size_msg:
            response_messages.append(size_msg)
            return {
                "messages": response_messages,
                "status": "waiting_for_size"
            }

        upsell_msg = get_upsell_suggestion(order)
        if upsell_msg:
            response_messages.append(upsell_msg)
            return {
                "messages": response_messages,
                "status": "waiting_for_upsell"
            }

    elif result.get("intent") == "finalize_order":
        summary = generate_order_summary(order)
        del ORDERS[order_id]
        return {
            "summary": summary,
            "status": "finished"
        }

    else:
        response_messages.append("🤖 Sorry, I didn’t understand that. Can you rephrase?")

    return {
        "messages": response_messages,
        "status": "in_progress"
    }
