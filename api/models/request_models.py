from pydantic import BaseModel
from typing import List, Optional

class AddItemRequest(BaseModel):
    name: str
    size: Optional[str] = None
    remove_ingredients: List[str] = []
    add_ingredients: List[str] = []
