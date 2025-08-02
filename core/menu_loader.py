import yaml
from pathlib import Path
from core.models import Menu, MenuItem, Combo, Ingredient, Upsell, Deal


def load_yaml_file(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def normalize_category(raw: str) -> str:
    # Перетворює "burgers" -> "burger", "desserts" -> "dessert", тощо
    mapping = {
        "burgers": "burger",
        "drinks": "drink",
        "fries": "side",
        "desserts": "dessert",
        "sides": "side"
    }
    return mapping.get(raw.lower(), raw.lower())



def load_menu_data(
    virtual_items_path: Path,
    ingredients_path: Path,
    upsells_path: Path,
    deals_path: Path
) -> Menu:
    virtual_items_raw = load_yaml_file(virtual_items_path)
    ingredients_raw = load_yaml_file(ingredients_path)
    upsells_raw = load_yaml_file(upsells_path)
    deals_raw = load_yaml_file(deals_path)

    # === Load real menu items (skip virtual ones)
    items = []
    for item in virtual_items_raw.get("items", []):
        if item.get("virtual"):
            continue

        sizes = None
        props = item.get("properties", [])
        for prop in props:
            if prop["name"] == "size":
                sizes = prop["values"]

        items.append(MenuItem(
            name=item["name"],
            category=normalize_category(item["category"]),
            price=item["price"],
            sizes=sizes
        ))

    # === Load combos
    combos = []
    for c in virtual_items_raw.get("combos", []):
        if c.get("virtual"):
            continue
        combos.append(Combo(
            name=c["name"],
            burger=c["name"].replace(" Meal", ""),  # heuristic
            side_default=c.get("slots", {}).get("fries", ["French Fries"])[0],
            drink_required=True,
            price=c["price"]
        ))

    # === Load upsells
    upsells = []
    for u in upsells_raw.get("upsells", []):
        upsells.append(Upsell(
            trigger=u["trigger"],
            offer=u["offer"],
            condition=u.get("condition"),
            price=u.get("price")
        ))

    # === Load deals
    deals = []
    for d in deals_raw.get("deals", []):
        deals.append(Deal(
            name=d["name"],
            description=d.get("description", ""),
            required_items=d.get("required_items", 2),
            discount_percent=d.get("discount_percent", 20.0)
        ))

    # === Attach ingredients to items
    ing_items = ingredients_raw.get("items", [])
    ing_lookup = {i["name"]: i for i in ing_items}

    for item in items:
        raw_item = next((i for i in ing_items if i["name"] == item.name), None)
        if raw_item:
            item.default_ingredients = raw_item.get("default_ingredients", [])
            item.optional_ingredients = []
            for ing in raw_item.get("possible_ingredients", []):
                price = next((v["price"] for v in ingredients_raw["ingredients"] if v["name"] == ing), 0.0)
                item.optional_ingredients.append(Ingredient(name=ing, extra_price=price))

    return Menu(
        items=items,
        combos=combos,
        upsells=upsells,
        deals=deals
    )
