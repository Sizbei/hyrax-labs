import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

const API_PORT = process.env.PORT ?? "4000";

export default defineConfig({
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
