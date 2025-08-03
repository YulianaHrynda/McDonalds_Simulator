from aiogram import Router, types
from aiogram.filters import CommandStart
from core.menu_loader import load_menu_data
from pathlib import Path
from bot.session import get_user_order, get_user_context, reset_user_order
from core.order_engine.summary import generate_order_summary
from core.llm_processor import parse_order
from core.order_engine.apply_llm import apply_llm_result
from core.order_engine.slot_filler import check_combo_missing_slots, check_missing_sizes
from core.order_engine.upsell import get_upsell_suggestion, upgrade_burger_to_combo, add_sauce_to_combo, add_dessert_to_order
from core.order_engine.deal_applier import maybe_apply_double_deal

router = Router()

menu = load_menu_data(
    virtual_items_path=Path("menu_data/menu_virtual_items.yaml"),
    ingredients_path=Path("menu_data/menu_ingredients.yaml"),
    upsells_path=Path("menu_data/menu_upsells.yaml"),
    deals_path=Path("menu_data/menu_deals.yaml"),
)

@router.message(CommandStart())
async def start_handler(message: types.Message):
    await message.answer("👋 Welcome to McDonald's! What can I get you started with?")

def is_finalize_intent(text: str) -> bool:
    normalized = text.strip().lower()
    return normalized in {
        "that's all", "done", "finish", "no, that's all",
        "finish ordering", "nothing else", "no", "no thanks", "no thank you",
        "this is it", "that will be all", "all good", "that's it"
    }

@router.message()
async def order_handler(message: types.Message):
    user_id = message.from_user.id
    order = get_user_order(user_id)
    user_input = message.text.strip()

    if is_finalize_intent(user_input):
        result = {"intent": "finalize_order"}
    else:
        result = parse_order(user_input)

    context = get_user_context(user_id)

    if "pending_slot" in context:
        slot = context.pop("pending_slot")

        if slot["type"] == "combo_drink":
            parsed = parse_order(user_input)
            drink_name = parsed.get("items", [{}])[0].get("name")

            for item in reversed(order.items):
                if item.type == "combo" and not item.drink_name:
                    item.drink_name = drink_name
                    item.name += f" + {drink_name}"
                    await message.answer(f"✅ Added drink to your combo: {drink_name}")

                    if not item.side_name:
                        context["pending_slot"] = {"type": "combo_side"}
                        await message.answer("Would you like French Fries or a different side with your combo?")
                    else:
                        upsell_msg = get_upsell_suggestion(order)
                        if upsell_msg:
                            context["pending_slot"] = {
                                "type": "upsell_offer",
                                "offer_text": upsell_msg,
                            }
                            await message.answer(upsell_msg)
                        else:
                            await message.answer("Anything else?")
                    return

        elif slot["type"] == "combo_side":
            parsed = parse_order(user_input)
            side_name = parsed.get("items", [{}])[0].get("name")

            for item in reversed(order.items):
                if item.type == "combo" and not item.side_name:
                    item.side_name = side_name
                    item.name += f" + {side_name}"
                    await message.answer(f"🍟 Added side to your combo: {side_name}")

                    upsell_msg = get_upsell_suggestion(order)
                    if upsell_msg:
                        context["pending_slot"] = {
                            "type": "upsell_offer",
                            "offer_text": upsell_msg,
                        }
                        await message.answer(upsell_msg)
                    else:
                        await message.answer("Anything else?")
                    return

        elif slot["type"] == "upsell_offer":

            if user_input.lower() in ["yes", "sure", "okay", "yep", "please"]:

                if "combo" in slot["offer_text"]:
                    burger = next((i for i in reversed(order.items) if i.type == "burger" and not i.is_combo_upgrade), None)

                    if burger:
                        combo = upgrade_burger_to_combo(menu, order, burger_name=burger.name)
                        if combo:
                            await message.answer("🎉 Your burger is now a combo!")
                            slot_msg = check_combo_missing_slots(order)

                            if slot_msg:

                                if "drink" in slot_msg.lower():
                                    context["pending_slot"] = {"type": "combo_drink"}
                                elif "side" in slot_msg.lower():
                                    context["pending_slot"] = {"type": "combo_side"}
                                await message.answer(slot_msg)

                            return

                if "sauce" in slot["offer_text"]:
                    combo = next((i for i in reversed(order.items) if i.type == "combo"), None)
                    if combo:
                        success = add_sauce_to_combo(order, combo.name, "ketchup")
                        if success:
                            await message.answer("🥫 Added a dipping sauce to your combo!")

                            upsell_msg = get_upsell_suggestion(order)
                            if upsell_msg:
                                context["pending_slot"] = {
                                    "type": "upsell_offer",
                                    "offer_text": upsell_msg,
                                }
                                await message.answer(upsell_msg)
                            return

                desserts = [d.name for d in menu.items if d.category == "dessert"]
                if desserts:
                    context["pending_slot"] = {
                        "type": "dessert_choice",
                        "options": desserts
                    }
                    dessert_list = "\n".join(f"• {d}" for d in desserts)
                    await message.answer(f"Which dessert would you like?\n{dessert_list}")
                    return

                await message.answer("👍 No problem!")
            else:
                await message.answer("👍 No problem!")

                if "combo" in slot["offer_text"]:
                    order.upsell_flags["combo_declined"] = True

                if "sauce" in slot["offer_text"]:
                    combo = next((i for i in reversed(order.items) if i.type == "combo"), None)
                    if combo:
                        combo.extras.append("no_sauce")

                for item in reversed(order.items):
                    if item.type == "combo" and not item.side_name:
                        context["pending_slot"] = {"type": "combo_side"}
                        await message.answer("Would you like French Fries or a different side with your combo?")
                        return

                upsell_msg = get_upsell_suggestion(order)
                if upsell_msg:
                    context["pending_slot"] = {
                        "type": "upsell_offer",
                        "offer_text": upsell_msg,
                    }
                    await message.answer(upsell_msg)
                else:
                    await message.answer("Anything else?")
                return

            return


        elif slot["type"] == "item_size":
            item_name = slot["item_name"]
            selected_size = user_input.lower().strip()

            for item in reversed(order.items):
                if item.name == item_name and item.size is None and item.type in ["drink", "side"]:
                    item.size = selected_size
                    item.name += f" ({selected_size})"
                    await message.answer(f"✅ Size set for your {item_name}: {selected_size}")
                    await message.answer("Anything else?")
                    break
            return

        elif slot["type"] == "dessert_choice":
            parsed = parse_order(user_input)
            dessert_name = parsed.get("items", [{}])[0].get("name")

            desserts = slot.get("options", [])
            dessert_match = next((d for d in desserts if d.lower() == dessert_name.lower()), None)
            if dessert_match:
                added = add_dessert_to_order(menu, order, dessert_match)
                if added:
                    await message.answer(f"🍰 Added {dessert_match} to your order!")
            else:
                await message.answer("Sorry, I couldn't find that dessert. Please pick one from the list.")
                context["pending_slot"] = slot
                return

            await message.answer("Anything else?")
            return

    result = parse_order(user_input)

    if result.get("intent") == "add_items":
        messages = apply_llm_result(result, menu, order)
        for msg in messages:
            await message.answer(msg)

        if messages and all(m.startswith("⚠️") or m.startswith("Sorry") for m in messages):
            return

        deal_msg = maybe_apply_double_deal(menu, order)
        if deal_msg:
            await message.answer(f"💸 {deal_msg}")

        slot_msg = check_combo_missing_slots(order)
        if slot_msg:
            if "drink" in slot_msg.lower():
                context["pending_slot"] = {"type": "combo_drink"}
            elif "side" in slot_msg.lower():
                context["pending_slot"] = {"type": "combo_side"}
            await message.answer(slot_msg)
            return

        slot_msg = check_missing_sizes(order, menu)
        if slot_msg:
            missing_item = next((item for item in order.items if item.type in ["drink", "side"] and item.size is None), None)
            if missing_item:
                context["pending_slot"] = {
                    "type": "item_size",
                    "item_name": missing_item.name,
                }
                await message.answer(slot_msg)
                return

        upsell_msg = get_upsell_suggestion(order)
        if upsell_msg:
            context["pending_slot"] = {
                "type": "upsell_offer",
                "offer_text": upsell_msg,
            }
            await message.answer(upsell_msg)
            return

        await message.answer("Anything else?")
        return

    elif result.get("intent") == "finalize_order":
        summary = generate_order_summary(order)
        await message.answer(summary)

        reset_user_order(user_id)

        await message.answer("🧾 Thank you for your order! We'll start preparing it now. Come back any time 🍟")
        return

    elif result.get("intent") == "start_order":
        await message.answer("👋 Welcome to McDonald's! What can I get you started with?")
        return

    await message.answer("Sorry, I didn’t understand that. Could you please rephrase or clarify your order?")
