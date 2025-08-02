from core.models import OrderState


def calculate_total(order: OrderState) -> float:
    return round(sum(item.computed_price for item in order.items), 2)

def generate_order_summary(order: OrderState) -> str:
    if not order.items:
        return "Your order is empty."

    lines = ["Your Order Summary:"]
    
    for item in order.items:
        line = f"- {item.name}"

        # Add size if applicable
        if item.size:
            line += f" ({item.size})"

        # Show removed ingredients
        if item.ingredients_removed:
            removed = ", ".join(item.ingredients_removed)
            line += f" [no {removed}]"

        # Show added ingredients
        if item.ingredients_added:
            added = ", ".join(f"{i.name}(+${i.extra_price:.2f})" for i in item.ingredients_added)
            line += f" [add {added}]"

        # Show extras (like sauce or dessert)
        if item.extras:
            extras = ", ".join(item.extras)
            line += f" [+ {extras}]"

        # Note if part of deal
        if item.part_of_deal:
            line += f" (part of {item.part_of_deal})"

        # Final price
        line += f" — ${item.computed_price:.2f}"

        lines.append(line)

    total = calculate_total(order)
    lines.append(f"\nTotal: ${total:.2f}")
    return "\n".join(lines)
