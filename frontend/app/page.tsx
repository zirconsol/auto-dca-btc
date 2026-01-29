"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { ArrowUpRight, ArrowDownRight, Bitcoin, Wallet, Clock3, RefreshCw } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { cn } from "@/lib/utils";

type Trade = {
  id: number;
  buy_timestamp: string;
  fiat_spent: number;
  btc_bought: number;
  price_fiat_per_btc: number;
  wallet: string;
  transfer_timestamp?: string | null;
};

type Metrics = {
  total_fiat: number;
  total_btc: number;
  current_price: number;
  current_value: number;
  pnl_abs: number;
  pnl_pct: number;
  trades_count: number;
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
const MANUAL_WITHDRAW_ADDRESS = "0x8ba1f109551bD432803012645Ac136ddd64DBA72";

export default function Dashboard() {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currency, setCurrency] = useState<"ARS" | "USD">("ARS");
  const tradesRef = useRef<Trade[]>([]);
  const metricsRef = useRef<Metrics | null>(null);
  const [localTime, setLocalTime] = useState<string>("");
  const [mounted, setMounted] = useState(false);
  const [switchingCurrency, setSwitchingCurrency] = useState(false);
  const [showWithdraw, setShowWithdraw] = useState(false);
  const [closingWithdraw, setClosingWithdraw] = useState(false);
  const [withdrawMode, setWithdrawMode] = useState<"ARS" | "BTC">("ARS");
  const [withdrawAmount, setWithdrawAmount] = useState<string>("");
  const [withdrawError, setWithdrawError] = useState<string>("");
  const [showWithdrawConfirm, setShowWithdrawConfirm] = useState(false);
  const [withdrawInProcess, setWithdrawInProcess] = useState(false);
  const [withdrawTransitioning, setWithdrawTransitioning] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const isSameTrades = (a: Trade[], b: Trade[]) => {
    if (a.length !== b.length) return false;
    for (let i = 0; i < a.length; i++) {
      const ta = a[i];
      const tb = b[i];
      if (
        ta.id !== tb.id ||
        ta.buy_timestamp !== tb.buy_timestamp ||
        ta.transfer_timestamp !== tb.transfer_timestamp ||
        ta.fiat_spent !== tb.fiat_spent ||
        ta.btc_bought !== tb.btc_bought ||
        ta.wallet !== tb.wallet
      ) {
        return false;
      }
    }
    return true;
  };

  const isSameMetrics = (a: Metrics | null, b: Metrics | null) => {
    if (!a && !b) return true;
    if (!a || !b) return false;
    return (
      a.total_fiat === b.total_fiat &&
      a.total_btc === b.total_btc &&
      a.current_price === b.current_price &&
      a.current_value === b.current_value &&
      a.pnl_abs === b.pnl_abs &&
      a.pnl_pct === b.pnl_pct &&
      a.trades_count === b.trades_count
    );
  };

  const fetchData = useCallback(async () => {
    setError(null);
    try {
      const [tradesRes, metricsRes] = await Promise.all([
        fetch(`${API_BASE}/trades?currency=${currency}`).then((r) => r.json()),
        fetch(`${API_BASE}/metrics?currency=${currency}`).then((r) => r.json()),
      ]);
      if (!isSameTrades(tradesRef.current, tradesRes)) {
        tradesRef.current = tradesRes;
        setTrades(tradesRes);
      }
      if (!isSameMetrics(metricsRef.current, metricsRes)) {
        metricsRef.current = metricsRes;
        setMetrics(metricsRes);
      }
    } catch (err: any) {
      setError(err?.message || "Error al cargar datos");
    }
    setLoading(false);
  }, [currency]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 15000);
    return () => clearInterval(interval);
  }, [fetchData]);

  useEffect(() => {
    setMounted(true);
    const t = setInterval(() => {
      setLocalTime(new Date().toLocaleString("es-AR"));
    }, 1000);
    return () => clearInterval(t);
  }, []);

  const pnlPositive = (metrics?.pnl_abs || 0) >= 0;
  const walletLabel =
    trades.length > 0 && trades[0].wallet
      ? `${trades[0].wallet.slice(0, 5)}...${trades[0].wallet.slice(-4)}`
      : "—";
  const manualWalletLabel = MANUAL_WITHDRAW_ADDRESS || "No configurada";
  const withdrawNotice =
    "Se ha notificado al equipo de retiros, el mismo puede tardar hasta 24hs en concretarse";

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await fetchData();
    } finally {
      setTimeout(() => setRefreshing(false), 600);
    }
  };
  const isBusy = loading || switchingCurrency;
  const Spinner = () => (
    <span className="inline-flex h-4 w-4 border-2 border-dashed border-accent-500 rounded-full animate-spin" />
  );

  const formattedWithdrawAmount = () => {
    if (!withdrawAmount) return "—";
    const n = parseFloat(withdrawAmount);
    if (Number.isNaN(n)) return withdrawAmount;
    if (withdrawMode === "ARS") {
      return n.toLocaleString("es-AR", { maximumFractionDigits: 2 });
    }
    return n.toFixed(6);
  };

  const numericAmount = parseFloat(withdrawAmount) || 0;
  const price = metrics?.current_price || 0;
  const convertedHint =
    withdrawMode === "ARS"
      ? price > 0
        ? `≈ ${(numericAmount / price || 0).toFixed(6)} BTC`
        : "—"
      : price > 0
        ? `≈ ${(numericAmount * price).toLocaleString("es-AR", {
            maximumFractionDigits: currency === "USD" ? 2 : 0,
          })} ${currency}`
        : "—";

  return (
    <main className="max-w-6xl mx-auto px-6 py-10 space-y-20 text-white">
      <header className="flex flex-col gap-2 mb-8 md:mb-12">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 text-sm uppercase tracking-[0.2em] text-slate-300">
              <Bitcoin className="w-4 h-4 text-accent-500" /> B.O.V.E.D.A
            </div>
            <Badge
              variant="outline"
              className="border-accent-500 text-accent-500 bg-ink-100/40 flex items-center gap-2"
            >
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full rounded-full bg-accent-500/70 animate-ping" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-accent-500" />
              </span>
              Live
            </Badge>
          </div>
          <div className="flex flex-wrap items-center gap-4 text-sm text-slate-200">
            <div className="flex items-center gap-2">
          <span className="uppercase text-xs tracking-[0.2em] text-slate-400">Local Time</span>
          <span className="text-slate-100 font-mono text-sm">{mounted && localTime ? localTime : "—"}</span>
        </div>
            <div className="flex items-center gap-2">
              <span className="uppercase text-xs tracking-[0.2em] text-slate-400">BTC Price</span>
              <span className="text-slate-100 font-mono text-sm">
                {metrics
                  ? `${currency === "USD" ? "USD" : "$"} ${metrics.current_price.toLocaleString("es-AR", {
                      maximumFractionDigits: currency === "USD" ? 2 : 0,
                    })}`
                  : "—"}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="uppercase text-xs tracking-[0.2em] text-slate-400">Currency</span>
              <div className="relative">
                <select
                  value={currency}
                  onChange={(e) => {
                    setCurrency(e.target.value as "ARS" | "USD");
                    setSwitchingCurrency(true);
                    setTimeout(() => setSwitchingCurrency(false), 2000);
                  }}
                  className="bg-ink-100 text-white border border-accent-500/60 rounded-full pl-9 pr-3 py-2 text-sm appearance-none"
                >
                  <option value="ARS">🇦🇷 ARS</option>
                  <option value="USD">🇺🇸 USD</option>
                </select>
                <span className="absolute left-2 top-1/2 -translate-y-1/2 text-lg">💱</span>
              </div>
            </div>
          </div>
        </div>
        <div className="flex flex-wrap items-baseline gap-3">
          <h1 className="text-3xl font-semibold text-white">Panel de rendimiento</h1>
          <button
            onClick={handleRefresh}
            className="inline-flex items-center gap-2 rounded-full bg-accent-600 text-white px-4 py-2 text-sm transition hover:bg-accent-500 disabled:opacity-50"
            disabled={loading}
          >
            <RefreshCw className={cn("w-4 h-4", refreshing && "animate-spin")} />
            Actualizar
          </button>
        </div>
        <p className="text-slate-300 max-w-3xl">
          Seguimiento de compras recurrentes y retiros a BSC. Muestra costo total, BTC acumulado y
          desempeño actual de tu boveda.
        </p>
      </header>

      <section className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        <Card className="gradient-card border-none shadow-sm text-white">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm text-slate-200">Invertido</CardTitle>
            <Wallet className="h-4 w-4 text-slate-200" />
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-semibold text-white">
              {isBusy || !metrics ? (
                <Spinner />
              ) : (
                `${currency === "USD" ? "USD" : "$"} ${metrics.total_fiat.toLocaleString("es-AR", {
                  maximumFractionDigits: currency === "USD" ? 2 : 0,
                })}`
              )}
            </p>
            <p className="text-xs text-slate-300">
              {currency === "USD" ? "USD" : "ARS"} totales usados en compras
            </p>
          </CardContent>
        </Card>

        <Card className="glass shadow-sm text-white">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm text-slate-200">BTC acumulado</CardTitle>
            <Bitcoin className="h-4 w-4 text-accent-500" />
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-semibold text-white">{isBusy || !metrics ? <Spinner /> : `${metrics.total_btc.toFixed(6)} BTC`}</p>
            <p className="text-xs text-slate-300">
              Precio actual:{" "}
              {isBusy || !metrics
                ? "—"
                : `${currency === "USD" ? "USD" : "$"} ${metrics.current_price.toLocaleString("es-AR", {
                    maximumFractionDigits: currency === "USD" ? 2 : 0,
                  })}`}
            </p>
          </CardContent>
        </Card>

        <Card className="glass shadow-sm text-white">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm text-slate-200">Valor actual</CardTitle>
            <ArrowUpRight className="h-4 w-4 text-accent-500" />
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-semibold text-white">
              {isBusy || !metrics
                ? "—"
                : `${currency === "USD" ? "USD" : "$"} ${metrics.current_value.toLocaleString("es-AR", {
                    maximumFractionDigits: currency === "USD" ? 2 : 0,
                  })}`}
            </p>
            <p className="text-xs text-slate-300">Valuado con precio spot</p>
          </CardContent>
        </Card>

        <Card className={cn("glass shadow-sm text-white", pnlPositive ? "border border-emerald-400/50" : "border border-rose-400/50")}>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm text-slate-200">PnL DCA</CardTitle>
            {pnlPositive ? <ArrowUpRight className="h-4 w-4 text-emerald-400" /> : <ArrowDownRight className="h-4 w-4 text-rose-400" />}
          </CardHeader>
          <CardContent>
            <p className={cn("text-2xl font-semibold", pnlPositive ? "text-emerald-400" : "text-rose-400")}>
              {isBusy || !metrics ? "—" : `${metrics.pnl_pct.toFixed(2)}%`}
            </p>
            <p className="text-xs text-slate-300">
              {isBusy || !metrics
                ? "Esperando datos..."
                : `PnL: ${currency === "USD" ? "USD" : "$"} ${metrics.pnl_abs.toLocaleString("es-AR", {
                    maximumFractionDigits: currency === "USD" ? 2 : 0,
                  })}`}
            </p>
          </CardContent>
        </Card>
      </section>

      <div className="flex justify-center">
        <button
          onClick={() => {
            if (withdrawInProcess) return;
            setShowWithdraw(true);
            setShowWithdrawConfirm(false);
            setWithdrawAmount("");
            setWithdrawError("");
            setWithdrawTransitioning(false);
            setClosingWithdraw(false);
          }}
          className="w-full md:w-auto px-6 py-3 rounded-lg bg-accent-600 text-white font-semibold shadow-lg hover:bg-accent-500 transition disabled:opacity-60 disabled:cursor-not-allowed"
          disabled={withdrawInProcess}
        >
          {withdrawInProcess ? "Retiro en proceso" : "Retirar"}
        </button>
      </div>

      {showWithdraw && (
        <div
          className={`fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 ${closingWithdraw ? "fade-out" : "fade-in"}`}
          onClick={() => {
            setClosingWithdraw(true);
            setTimeout(() => {
              setShowWithdraw(false);
              setClosingWithdraw(false);
            }, 200);
          }}
        >
          <div
            className={`bg-ink-100 border border-accent-500/40 rounded-xl p-7 w-full max-w-lg relative min-h-[360px] ${closingWithdraw ? "fade-out" : "fade-in"} ${
              withdrawInProcess ? "flex items-center" : "space-y-5"
            }`}
            onClick={(e) => e.stopPropagation()}
          >
            <button
              className="absolute top-4 right-4 text-slate-400 hover:text-white"
              onClick={() => {
                setClosingWithdraw(true);
                setTimeout(() => {
                  setShowWithdraw(false);
                  setClosingWithdraw(false);
                }, 200);
              }}
            >
              ✕
            </button>
            {!withdrawInProcess ? (
              <div
                className={cn(
                  "transition-all duration-200",
                  withdrawTransitioning && "opacity-0 translate-y-1 pointer-events-none"
                )}
              >
                <h3 className="text-xl font-semibold text-white">Retiro manual (mock)</h3>
                <p className="text-xs text-slate-400">
                  Destino manual (EVM): {manualWalletLabel}
                </p>
                <div className="flex gap-2">
                  <button
                    className={`flex-1 px-3 py-2 rounded-lg border ${
                      withdrawMode === "ARS" ? "border-accent-500 bg-accent-500/20" : "border-slate-600"
                    }`}
                    onClick={() => setWithdrawMode("ARS")}
                  >
                    Retirar en ARS
                  </button>
                  <button
                    className={`flex-1 px-3 py-2 rounded-lg border ${
                      withdrawMode === "BTC" ? "border-accent-500 bg-accent-500/20" : "border-slate-600"
                    }`}
                    onClick={() => setWithdrawMode("BTC")}
                  >
                    Retirar en BTC
                  </button>
                </div>
                <div className="space-y-1">
                  <label className="text-sm text-slate-300">Monto {withdrawMode === "ARS" ? "ARS" : "BTC"}</label>
                  <input
                    className="w-full px-4 py-3 rounded-lg bg-ink-50 border border-slate-600 text-white"
                    type="number"
                    min="0"
                    step="any"
                    value={withdrawAmount}
                    onChange={(e) => {
                      setWithdrawAmount(e.target.value);
                      setWithdrawError("");
                      setShowWithdrawConfirm(false);
                    }}
                    placeholder={withdrawMode === "ARS" ? "Ej: 10000" : "Ej: 0.001"}
                  />
                  <p className="text-xs text-slate-400">{convertedHint}</p>
                  {withdrawError && <p className="text-xs text-rose-400">{withdrawError}</p>}
                </div>
                <button
                  className="w-full px-4 py-3.5 rounded-lg bg-accent-600 text-white font-semibold hover:bg-accent-500 transition disabled:opacity-60 disabled:cursor-not-allowed"
                  onClick={() => {
                    if (!metrics) {
                      setWithdrawError("No hay métricas disponibles.");
                      return;
                    }
                    const amt = numericAmount;
                    const availableBtc = metrics.total_btc;
                    const availableFiat = metrics.total_btc * metrics.current_price;
                    if (withdrawMode === "BTC" && amt > availableBtc) {
                      setWithdrawError(
                        `Monto superior al disponible, intente con un menor a ${availableBtc.toFixed(6)} BTC`
                      );
                      return;
                    }
                    if (withdrawMode === "ARS" && amt > availableFiat) {
                      setWithdrawError(
                        `Monto superior al disponible, intente con un menor a ${availableFiat.toLocaleString("es-AR")} ARS`
                      );
                      return;
                    }
                    setWithdrawError("");
                    setShowWithdrawConfirm(true);
                  }}
                >
                  Retirar {formattedWithdrawAmount()} {withdrawMode}
                </button>
                {showWithdrawConfirm && (
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="absolute inset-0 rounded-xl bg-black/50 backdrop-blur-sm" />
                    <div className="relative w-[90%] max-w-sm rounded-xl border border-accent-500/30 bg-ink-50/95 p-5 text-center text-slate-100 shadow-xl fade-in">
                      <h4 className="text-lg font-semibold text-white">Confirmar retiro?</h4>
                      <p className="mt-3 text-sm text-slate-200 leading-relaxed">
                        Al realizar el retiro, no se podrán realizar retiros hasta consolidado el retiro en proceso. El mismo puede
                        demorar hasta 24hs en consolidarse.
                      </p>
                      <div className="mt-4 flex items-center justify-center gap-3">
                        <button
                          className="px-4 py-2 rounded-full bg-ink-100 text-slate-100 border border-slate-600 hover:border-slate-400 transition"
                          onClick={() => setShowWithdrawConfirm(false)}
                        >
                          No
                        </button>
                        <button
                          className="px-5 py-2 rounded-full bg-accent-600 text-white font-semibold hover:bg-accent-500 transition"
                          onClick={() => {
                            setShowWithdrawConfirm(false);
                            setWithdrawTransitioning(true);
                            setTimeout(() => {
                              setWithdrawInProcess(true);
                              setWithdrawTransitioning(false);
                            }, 220);
                          }}
                        >
                          Si
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="w-full fade-in soft-pulse">
                <p className="text-center text-base text-slate-100 leading-relaxed max-w-md mx-auto">{withdrawNotice}</p>
              </div>
            )}
          </div>
        </div>
      )}

      <section className="grid grid-cols-1 xl:grid-cols-1 gap-4">
        <Card className="glass shadow-sm text-white">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <div className="flex flex-col gap-1">
              <div className="flex items-center gap-2">
                <CardTitle className="text-base text-slate-200">Compras y retiros</CardTitle>
              </div>
              <p className="text-xs text-slate-300">Histórico ordenado por fecha de compra</p>
              <p className="text-xs text-slate-400">Wallet: {walletLabel}</p>
            </div>
            <Badge variant="secondary" className="text-slate-100 bg-ink-100/70">
              {metrics ? `${metrics.trades_count} eventos` : "—"}
            </Badge>
          </CardHeader>
          <CardContent>
            {loading ? (
              <p className="text-sm text-slate-300">Cargando...</p>
            ) : error ? (
              <p className="text-sm text-rose-400">{error}</p>
            ) : trades.length === 0 ? (
              <p className="text-sm text-slate-400">Aún no hay compras registradas.</p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="text-slate-300">Compra</TableHead>
                    <TableHead className="text-slate-300">BTC</TableHead>
                    <TableHead className="text-slate-300">{currency}</TableHead>
                    <TableHead className="text-slate-300">Transferencia</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {trades.map((t) => (
                    <TableRow key={t.id}>
                      <TableCell className="text-sm text-slate-100">
                        {isBusy ? <Spinner /> : new Date(t.buy_timestamp).toLocaleString("es-AR")}
                        <div className="text-xs text-slate-400">
                          {isBusy ? <Spinner /> : <>Precio ${t.price_fiat_per_btc.toLocaleString("es-AR")}</>}
                        </div>
                      </TableCell>
                      <TableCell className="text-sm font-medium text-slate-100">
                        {isBusy ? <Spinner /> : `${t.btc_bought.toFixed(8)} BTC`}
                      </TableCell>
                      <TableCell className="text-sm text-slate-100">
                        {isBusy ? <Spinner /> : `${currency === "USD" ? "USD" : "$"} ${t.fiat_spent.toLocaleString("es-AR")}`}
                      </TableCell>
                      <TableCell className="text-sm">
                        {isBusy ? (
                          <Spinner />
                        ) : (
                          <Badge variant="outline" className="text-emerald-300 border-emerald-500/50 bg-ink-100/40">
                            Completada {t.transfer_timestamp ? `• ${new Date(t.transfer_timestamp).toLocaleString("es-AR")}` : ""}
                          </Badge>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </section>
    </main>
  );
}
