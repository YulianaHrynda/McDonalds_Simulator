from typing import Optional
from core.models import OrderState, Menu


def maybe_apply_double_deal(menu: Menu, order: OrderState) -> Optional[str]:
    # Знайти перший доступний deal, який потребує 2 елементи
    deal = next((d for d in menu.deals if d.required_items == 2), None)
    if not deal:
        return None

    # Знайти 2 бургери, які ще не є частиною deal
    eligible_burgers = [
        item for item in order.items
        if item.type == "burger" and item.part_of_deal is None
    ]

    if len(eligible_burgers) < 2:
        return None

    burger_1, burger_2 = eligible_burgers[:2]

    # Застосувати знижку до кожного з двох
    for burger in [burger_1, burger_2]:
        burger.part_of_deal = deal.name
        discount = round(burger.computed_price * (deal.discount_percent / 100), 2)
        burger.computed_price = round(burger.computed_price - discount, 2)

    order.applied_deals.append(deal.name)
    return f"A Double Deal has been applied! You saved {int(deal.discount_percent)}% on two burgers."
