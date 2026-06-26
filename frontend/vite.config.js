import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  // Excalidraw reads these at runtime; Vite must inline them or it throws on `process`.
  define: {
    "process.env.IS_PREACT": JSON.stringify("false"),
  },
  server: {
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
});
