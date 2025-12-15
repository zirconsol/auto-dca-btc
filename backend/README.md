# Backend (FastAPI)

API para registrar compras BTC (DCA) y calcular métricas usando precio actual de Binance.

## Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuración (.env opcional)
- `DCA_DB_URL`: URL de la base (por defecto `sqlite:///./dca.db`). Para Supabase usa el connection string con psycopg3, ej:
  `DCA_DB_URL=postgresql+psycopg://USER:PASSWORD@HOST:PORT/DB?sslmode=require`
- `DCA_PRICE_SYMBOL`: símbolo de precio para valuar BTC (por defecto usa `TRADE_SYMBOL` si está definido, si no `BTCUSDT`; pon `BTCARS` para ARS).
- `DCA_PRICE_BASE_URL`: endpoint de Binance para precios (por defecto `https://api.binance.com`).
- `WITHDRAW_NETWORK` / `WITHDRAW_ADDRESS`: opcional, solo para compartir config con el flujo de retiros.

## Ejecutar
```bash
uvicorn app.main:app --reload --port 8000
```

## Endpoints
- `GET /health`
- `POST /trades`: crear trade `{buy_timestamp, fiat_spent, btc_bought, price_fiat_per_btc, wallet, transfer_timestamp?}`
- `GET /trades`: listar
- `GET /trades/{id}`: detalle
- `GET /metrics`: totales, precio actual, PnL
