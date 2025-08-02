from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Dict


class SelectedIngredient(BaseModel):
    name: str
    extra_price: float = 0.0


class OrderItem(BaseModel):
    name: str
    type: Literal["burger", "drink", "side", "dessert", "combo"]
    size: Optional[str] = None
    ingredients_removed: List[str] = []
    ingredients_added: List[SelectedIngredient] = []
    part_of_deal: Optional[str] = None
    is_combo_upgrade: bool = False
    extras: List[str] = []
    base_price: float
    computed_price: float
    quantity: int = 1  # 👈 NEW
    drink_name: Optional[str] = None
    side_name: Optional[str] = None


class OrderState(BaseModel):
    items: List[OrderItem] = []
    applied_deals: List[str] = []
    upsell_flags: Dict[str, bool] = Field(default_factory=lambda: {
        "dessert_offered": False,
        "dessert_added": False
    })

    def total_price(self) -> float:
        return sum(item.computed_price * item.quantity for item in self.items)


    def add_item(self, item: OrderItem):
        self.items.append(item)

    def find_uncompleted_combo(self) -> Optional[OrderItem]:
        for item in self.items:
            if item.type == "combo" and not item.drink_name:
                return item
        return None

    def has_combo(self) -> bool:
        return any(item.type == "combo" for item in self.items)

    def has_burger(self) -> bool:
        return any(item.type == "burger" for item in self.items)

    def burger_names(self) -> List[str]:
        return [item.name for item in self.items if item.type == "burger"]


class Ingredient(BaseModel):
    name: str
    extra_price: float = 0.0


class MenuItem(BaseModel):
    name: str
    category: Literal["burger", "drink", "side", "dessert"]
    price: float
    sizes: Optional[List[str]] = None
    default_ingredients: List[str] = []
    optional_ingredients: List[Ingredient] = []


class Combo(BaseModel):
    name: str
    burger: str
    side_default: str = "French Fries"
    drink_required: bool = True
    price: float


class Upsell(BaseModel):
    trigger: Literal["burger", "combo"]
    offer: Literal["combo", "sauce", "dessert"]
    condition: Optional[str] = None
    price: Optional[float] = None


class Deal(BaseModel):
    name: str
    description: str
    required_items: int = 2
    discount_percent: float


class Menu(BaseModel):
    items: List[MenuItem]
    combos: List[Combo]
    upsells: List[Upsell]
    deals: List[Deal]
