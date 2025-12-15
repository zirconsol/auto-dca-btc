# Frontend (DCA Dashboard)

Dashboard en Next.js con Tailwind y componentes estilo shadcn para visualizar las compras DCA y retiros.

## Inicio rápido
```bash
cd frontend
npm install
npm run dev
```

Variable opcional:
- `NEXT_PUBLIC_API_BASE_URL`: URL del backend FastAPI (por defecto `http://localhost:8000`).

## Estructura
- `app/page.tsx`: dashboard principal (cards de métricas, tabla de compras/retiros, último retiro).
- `components/ui/*`: componentes base (card, badge, table).
- `app/globals.css`: estilos y fuentes (Space Grotesk, Inter).

El frontend consulta:
- `GET /trades`
- `GET /metrics`
del backend para poblar los datos.
