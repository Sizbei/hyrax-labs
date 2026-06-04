import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

const API_PORT = process.env.PORT ?? "4000";

// When deploying to GitHub Pages the app is served from /<repo>/, so the asset
// base must be set. Override with BASE_PATH; defaults to "/" for local/server use.
const BASE_PATH = process.env.BASE_PATH ?? "/";

export default defineConfig({
  base: BASE_PATH,
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Forward API + SSE calls to the synthetic Express server in dev.
      "/api": {
        target: `http://localhost:${API_PORT}`,
        changeOrigin: true,
      },
    },
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./test/setup.ts"],
    include: ["test/**/*.test.{ts,tsx}"],
  },
});
