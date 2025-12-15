from datetime import datetime
from typing import Annotated, List

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select

from app.binance_price import fetch_price
from app.config import get_settings
from app.db import get_session, init_db
from app.models import Metrics, Trade, TradeCreate
from app.usd_rate import get_usd_rate

settings = get_settings()

app = FastAPI(title="DCA BTC Dashboard API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "time": datetime.utcnow()}


def _to_float(val) -> float:
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0.0


@app.post("/trades", response_model=Trade)
def create_trade(trade: TradeCreate, session: Annotated[Session, Depends(get_session)]) -> Trade:
    db_trade = Trade.from_orm(trade)
    session.add(db_trade)
    session.commit()
    session.refresh(db_trade)
    return db_trade


@app.get("/trades", response_model=List[Trade])
def list_trades(
    session: Annotated[Session, Depends(get_session)],
    currency: str | None = None,
) -> List[Trade]:
    trades = session.exec(select(Trade).order_by(Trade.buy_timestamp.desc())).all()
    if currency and currency.upper() == "USD":
        usd_rate = get_usd_rate() or 0.0
        converted: list[Trade] = []
        for t in trades:
            # Si fiat_spent_usd está almacenando la tasa de USD en ARS, usamos fiat_spent / tasa.
            if t.fiat_spent_usd not in (None, 0):
                usd_spent = _to_float(t.fiat_spent) / _to_float(t.fiat_spent_usd)
            else:
                usd_spent = _to_float(t.fiat_spent) / usd_rate if usd_rate else 0.0
            price_usd = usd_spent / t.btc_bought if t.btc_bought else 0.0
            converted.append(
                Trade(
                    id=t.id,
                    buy_timestamp=t.buy_timestamp,
                    fiat_spent=usd_spent,
                    fiat_spent_usd=usd_spent,
                    btc_bought=t.btc_bought,
                    price_fiat_per_btc=price_usd,
                    wallet=t.wallet,
                    transfer_timestamp=t.transfer_timestamp,
                )
            )
        return converted
    return trades


@app.get("/metrics", response_model=Metrics)
def metrics(session: Annotated[Session, Depends(get_session)], currency: str | None = None) -> Metrics:
    trades = session.exec(select(Trade)).all()
    currency = (currency or "ARS").upper()
    usd_rate = get_usd_rate() if currency == "USD" else None

    def _fiat(t: Trade) -> float:
        if currency == "USD":
            if t.fiat_spent_usd not in (None, 0):
                return _to_float(t.fiat_spent) / _to_float(t.fiat_spent_usd)
            if usd_rate:
                return _to_float(t.fiat_spent) / usd_rate
        return _to_float(t.fiat_spent)

    total_fiat = sum(_fiat(t) for t in trades)
    total_btc = sum(t.btc_bought for t in trades)
    current_price = fetch_price(settings.price_symbol, base_url=settings.price_base_url) or 0.0
    if currency == "USD" and current_price > 0 and usd_rate:
        current_price = current_price / usd_rate
    current_value = total_btc * current_price
    pnl_abs = current_value - total_fiat
    pnl_pct = (pnl_abs / total_fiat * 100) if total_fiat else 0.0
    return Metrics(
        total_fiat=total_fiat,
        total_btc=total_btc,
        current_price=current_price,
        current_value=current_value,
        pnl_abs=pnl_abs,
        pnl_pct=pnl_pct,
        trades_count=len(trades),
    )


@app.get("/trades/{trade_id}", response_model=Trade)
def get_trade(trade_id: int, session: Annotated[Session, Depends(get_session)]) -> Trade:
    trade = session.get(Trade, trade_id)
    if not trade:
        raise HTTPException(status_code=404, detail="Trade no encontrado")
    return trade
