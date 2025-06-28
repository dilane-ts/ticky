import { defineConfig } from "vite";
import { resolve } from "path";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
    base: "/static/",
    resolve: {
        alias: {
            '@': resolve('./static')
        }
    },
    build: {
      manifest: "manifest.json",
      assetsDir: "ticky_assets",
      outDir: resolve("./assets"),
      rollupOptions: {
        input: {
          ticky: resolve('./static/js/main.js')
        }
      }
    },
    plugins: [
        tailwindcss()
    ]
  })