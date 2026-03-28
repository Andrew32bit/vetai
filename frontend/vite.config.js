import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  base: "/vetai/",
  server: {
    port: 5173,
    host: true, // для ngrok/tunneling
  },
  build: {
    outDir: "dist",
    sourcemap: false,
  },
});