/**
 * Synthetic metrics API server (Express).
 *
 * Endpoints:
 *   GET  /api/health                 -> liveness
 *   GET  /api/metrics                -> metric catalog
 *   GET  /api/assets                 -> all synthetic assets
 *   GET  /api/snapshot               -> current metric values for every asset
 *   GET  /api/timeseries/:metricId   -> historical aggregate series
 *   GET  /api/stream                 -> Server-Sent Events of live aggregates
 *
 * All data is SYNTHETIC and generated deterministically from a fixed seed.
 * Node v22+/v24 strips the TypeScript types of the imported .ts data modules.
 */
import express from "express";
import { METRICS } from "../src/data/metricsCatalog.ts";
import {
  DEFAULT_SEED,
  aggregate,
  generateAssets,
  generateTimeSeries,
  liveTick,
  snapshotAll,
} from "../src/data/generator.ts";

const PORT = Number(process.env.PORT ?? 4000);
const STREAM_INTERVAL_MS = Number(process.env.STREAM_INTERVAL_MS ?? 2000);

const app = express();
const assets = generateAssets(DEFAULT_SEED);

/** Wrap a payload in the standard API envelope. */
const ok = (data) => ({ success: true, data, error: null });
const fail = (error) => ({ success: false, data: null, error });

app.get("/api/health", (_req, res) => {
  res.json(ok({ status: "ok", assets: assets.length, metrics: METRICS.length }));
});

app.get("/api/metrics", (_req, res) => {
  res.json(ok(METRICS));
});

app.get("/api/assets", (_req, res) => {
  res.json(ok(assets));
});

app.get("/api/snapshot", (_req, res) => {
  const now = Date.now();
  const snaps = snapshotAll(assets, now, 0);
  res.json(ok({ timestamp: now, snapshots: snaps, aggregates: aggregate(snaps) }));
});

app.get("/api/timeseries/:metricId", (req, res) => {
  const { metricId } = req.params;
  if (!METRICS.some((m) => m.id === metricId)) {
    res.status(404).json(fail(`Unknown metric: ${metricId}`));
    return;
  }
  const points = Number(req.query.points ?? 60);
  res.json(ok(generateTimeSeries(assets, metricId, Date.now(), points)));
});

/** Server-Sent Events stream of live aggregate ticks. */
app.get("/api/stream", (req, res) => {
  res.set({
    "Content-Type": "text/event-stream",
    "Cache-Control": "no-cache",
    Connection: "keep-alive",
  });
  res.flushHeaders();

  let tick = 0;
  const send = () => {
    tick += 1;
    const payload = liveTick(assets, Date.now(), tick);
    res.write(`data: ${JSON.stringify(payload)}\n\n`);
  };

  send();
  const timer = setInterval(send, STREAM_INTERVAL_MS);
  req.on("close", () => clearInterval(timer));
});

app.listen(PORT, () => {
  // eslint-disable-next-line no-console
  console.log(
    `[metrics-dashboard] synthetic API on http://localhost:${PORT} ` +
      `(${assets.length} assets, ${METRICS.length} metrics, SSE every ${STREAM_INTERVAL_MS}ms)`,
  );
});
