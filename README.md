# Auto DCA para BTC desde Argentina
Este proyecto automatiza un flujo de DCA en BTC con Binance mediante el siguiente flujo.

Se configura un sistema de transferencias recurrentes en pesos desde su cuenta bancaria a la cuenta en pesos de Binance, vigila el saldo en ARS esperando cambios, compra BTC al detectar nuevos depositos, lo retira a una wallet de custodia, registra cada operación en un backend (FastAPI + Supabase/SQLite) y muestra un dashboard web (Next.js) con métricas, historial de compras/retiros y conversión ARS/USD (usando dólar blue). Incluye un flujo de retiro manual para retirar BTC a traves de la Binance Smart Chain, se recomienda para ello utilizar una cuenta fintech cripto como Lemon Cash, Belo, o Ripio.


## Requisitos

- Python 3.10+ recomendado.

## Configuración

1. Crea tu entorno y dependencias:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Copia `.env.example` a `.env` y completa tus credenciales:
   ```bash
   cp .env.example .env
   ```
   Variables disponibles:
   - `BINANCE_API_KEY` o `BINANCE_API`: tu API Key de Binance.
   - `BINANCE_API_SECRET` o `BINANCE_SECRET`: tu API Secret.
   - `TARGET_ASSET`: activo a consultar (ej. `ARS`). Por defecto `ARS`.
   - `TRADE_SYMBOL`: par spot a usar para comprar BTC con el activo (por defecto `BTCARS`).
   - `POLL_INTERVAL_SECONDS`: intervalo de consulta. Por defecto `10`.
- `MIN_QUOTE_QTY`: mínimo en moneda de cotización para enviar orden. `0` para sin mínimo (el código también lee el `MinNotional` del exchange y aplica el máximo entre ambos).
- `BINANCE_BASE_URL`: endpoint de Binance (por defecto prod). Usa `https://testnet.binance.vision` si tus credenciales son de testnet.
- `WITHDRAW_ADDRESS`: dirección destino para el retiro automático de BTC (si se omite, no retira).
   - `WITHDRAW_NETWORK`: red para el retiro (por defecto `BSC`).
   - `WITHDRAW_MIN_AMOUNT`: mínimo de BTC para disparar retiro automático (por defecto `0`).
   - `WITHDRAW_COIN`: moneda a retirar (por defecto `BTC`).
   - `WITHDRAW_AMOUNT`: para `src/withdraw_btc_bnb.py`, monto fijo de retiro (si no se define, usa el ejecutado en el swap automático).
    - `BACKEND_API_BASE` (o `DCA_API_BASE`): URL del backend para registrar trades automáticamente (ej. `http://localhost:8000`).

## Uso

Con la venv activada y el `.env` configurado, ejecuta:
```bash
python main.py
```

El monitor registrará en consola el balance libre, bloqueado y total del activo configurado cada intervalo. Si detecta saldo libre igual o superior al mínimo configurado, enviará una orden de mercado BUY con `quoteOrderQty` por todo ese saldo en el par definido. Presiona `Ctrl + C` para detener.

## Estructura

- `main.py`: punto de entrada.
- `src/config.py`: carga de variables de entorno.
- `src/binance_client.py`: cliente firmado hacia la API de Binance (balances y órdenes).
- `src/balance_monitor.py`: loop de sondeo periódico y logging.
- `src/trading.py`: manejador de auto-swap ARS -> BTC usando órdenes de mercado.
- `src/btc_checker.py`: helper para consultar el balance de BTC.
- `src/withdraw_btc_bnb.py`: script para enviar un retiro de BTC por red BNB/BSC.
- `src/withdrawer.py`: lógica de retiro automático posterior al swap.
- `backend/`: API FastAPI para registrar trades y calcular métricas DCA.
- `frontend/`: Dashboard Next.js + componentes estilo shadcn para visualizar trades y métricas.
- `sync_trades.py`: sincroniza compras históricas de Binance hacia el backend (Supabase) si faltan (ejecución manual).

## Retiro manual de BTC por BNB (BSC)

Configura en `.env`:
- `WITHDRAW_COIN` (por defecto `BTC`)
- `WITHDRAW_AMOUNT` (por defecto `0.000001`)
- `WITHDRAW_ADDRESS` (requerido; ejemplo BSC: `0x6da9f54305104509ca03gp5697067c8bba05f6e7`)
- `WITHDRAW_NETWORK` (por defecto `BSC`)

Luego ejecuta:
```bash
python src/withdraw_btc_bnb.py
```

> Esto envía un retiro real; asegúrate de que tu API Key tenga permiso de retiros y que el network/dirección sean correctos.

> Nota: esto envía órdenes reales. Asegúrate de que el par y los mínimos configurados coincidan con las restricciones de Binance para evitar rechazos o ejecuciones no deseadas.

## Dashboard (backend + frontend)

- Backend FastAPI:
  ```bash
  cd backend
  python -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  uvicorn app.main:app --reload --port 8000
  ```
  Variables opcionales: `DCA_DB_URL` (por defecto `sqlite:///./dca.db`; para Supabase usa tu string de Postgres con psycopg3, ej. `postgresql+psycopg://USER:PASSWORD@HOST:PORT/DB?sslmode=require`), `DCA_PRICE_SYMBOL` (por defecto usa `TRADE_SYMBOL` si existe, si no `BTCUSDT`; usa `BTCARS` para ARS), `DCA_PRICE_BASE_URL` (por defecto `https://api.binance.com`).

- Frontend Next.js (shadcn-like):
  ```bash
  cd frontend
  npm install
  npm run dev
  ```
  Variable: `NEXT_PUBLIC_API_BASE_URL` (por defecto `http://localhost:8000`).

El dashboard consume `/trades` y `/metrics` del backend y muestra invertido, BTC acumulado, valor actual, PnL y tabla de compras/retiros (timestamps de compra y transferencia + wallet).

## Arquitectura y decisiones técnicas

- **Backend**: FastAPI + SQLModel. Endpoints: `POST /trades`, `GET /trades`, `GET /trades/{id}`, `GET /metrics`. Aceptan `currency=ARS|USD` (USD convierte montos con tasa guardada en cada trade `fiat_spent_usd`, o cotización blue de Bluelytics si falta).
- **Sincronización histórica**: `sync_trades.py` llama a Binance `/api/v3/myTrades` y registra faltantes en el backend. Útil para poblar Supabase.
- **Autoswap**: `main.py` usa `AutoSwapper` (compra BTC con ARS) y `AutoWithdrawer` (retiro a custodia `WITHDRAW_ADDRESS`), reporta trades al backend.
- **Binance**: se usa `newOrderRespType=FULL` y fills para precio promedio real. Se lee `MinNotional` de `exchangeInfo` y se cruza con `MIN_QUOTE_QTY`.
- **Precios**: spot desde Binance `/api/v3/ticker/price` (`DCA_PRICE_SYMBOL`, fallback `TRADE_SYMBOL` o `BTCUSDT`). Conversión USD usa Bluelytics (`value_sell`).
- **Supabase/Postgres**: driver `psycopg[binary]` (psycopg3) con URL `postgresql+psycopg://...` y `sslmode=require`. Pooler IPv4 recomendado.
- **Frontend**: Next.js + Tailwind (tema oscuro, acentos Bitcoin). Selector ARS/USD con spinner de transición 2s para evitar “rebotes”. Dashboard muestra métricas, tabla y retiro manual (mock). Sin llamada real en el modal.
- **Errores/hidratación**: el reloj local sólo se muestra tras montar el componente para evitar mismatch SSR/CSR. Se cachean datos y se actualizan sólo si cambian para evitar parpadeo.

## Variables de entorno clave

- Trading/autoswap: `BINANCE_API_KEY/BINANCE_API`, `BINANCE_API_SECRET/BINANCE_SECRET`, `TARGET_ASSET`, `TRADE_SYMBOL` (ej. `BTCARS`), `MIN_QUOTE_QTY`, `BINANCE_BASE_URL`.
- Retiros automáticos: `WITHDRAW_ADDRESS` (custodia), `WITHDRAW_NETWORK` (BSC), `WITHDRAW_MIN_AMOUNT`, `WITHDRAW_COIN`.
- Backend: `DCA_DB_URL` (SQLite por defecto o Supabase `postgresql+psycopg://...`), `DCA_PRICE_SYMBOL`, `DCA_PRICE_BASE_URL`.
- Reporter/Sync: `BACKEND_API_BASE` (o `DCA_API_BASE`) para reportar trades desde `main.py` y `sync_trades.py`.
- Frontend: `NEXT_PUBLIC_API_BASE_URL`, `NEXT_PUBLIC_MANUAL_WITHDRAW_ADDRESS` (wallet destino del retiro manual mock).

## Flujos principales

- **Auto DCA**: `python main.py` (con `.env` completo) monitorea ARS, compra BTCARS, retira a custodia, y reporta al backend.
- **Dashboard**: backend `uvicorn app.main:app --reload --port 8000` y frontend `npm run dev`. Selector ARS/USD actualiza `/trades` y `/metrics` con conversión consistente.
- **Sync histórico**: `python sync_trades.py` para poblar la base desde Binance (requiere `BACKEND_API_BASE` y credenciales).
- **Retiro manual (mock)**: botón “Retirar” en frontend con validación de montos (en BTC o ARS) y destino `NEXT_PUBLIC_MANUAL_WITHDRAW_ADDRESS`. No ejecuta retiro real.
