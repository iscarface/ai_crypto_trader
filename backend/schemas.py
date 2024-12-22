from datetime import datetime
from typing import Optional

from pydantic import BaseModel, computed_field


class TradeResponse(BaseModel):
    id: int
    symbol: str
    action: str
    entry_price: Optional[float]
    exit_price: Optional[float]
    quantity: float
    stop_loss_price: Optional[float]
    take_profit_price: Optional[float]
    profit_loss: Optional[float]
    timestamp: datetime

    # Add a computed status field
    @computed_field
    def status(self) -> str:
        return "CLOSED" if self.exit_price is not None else "OPEN"

    # def dict(self, **kwargs):
    #     data = super().dict(**kwargs)  # Get the original fields
    #     data["status"] = self.status  # Add the computed status field
    #     return data

    class Config:
        orm_mode = True
        from_attributes = True
