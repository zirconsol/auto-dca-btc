from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Trade(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    buy_timestamp: datetime
    fiat_spent: float
    fiat_spent_usd: Optional[float] = Field(default=None, nullable=True)
    btc_bought: float
    price_fiat_per_btc: float
    wallet: str
    transfer_timestamp: Optional[datetime] = None


class TradeCreate(SQLModel):
    buy_timestamp: datetime
    fiat_spent: float
    fiat_spent_usd: Optional[float] = None
    btc_bought: float
    price_fiat_per_btc: float
    wallet: str
    transfer_timestamp: Optional[datetime] = None


class Metrics(SQLModel):
    total_fiat: float
    total_btc: float
    current_price: float
    current_value: float
    pnl_abs: float
    pnl_pct: float
    trades_count: int
