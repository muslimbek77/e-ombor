import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// Backend manzili. Odatda o'zgartirish shart emas — faqat backend boshqa
// portda/mashinada turgan bo'lsa BACKEND_URL bilan almashtiriladi.
const BACKEND_URL = process.env.BACKEND_URL ?? "http://127.0.0.1:3000";

export default defineConfig({
  server: {
    // Bir xil Wi-Fi'dagi boshqa qurilmalar ham kira olishi uchun barcha
    // tarmoq interfeyslarida tinglaymiz (0.0.0.0), faqat localhost'da emas.
    host: true,
    port: 5173,
    strictPort: true,
    // Frontend API'ni o'z origin'i orqali chaqiradi (/api/...), Vite esa uni
    // backendga uzatadi. Shu sabab telefon/noutbukda ham ishlaydi va CORS
    // kerak bo'lmaydi — IP o'zgarsa hech narsani tahrirlash shart emas.
    proxy: {
      "/api": {
        target: BACKEND_URL,
        changeOrigin: true,
      },
    },
  },
  plugins: [
    react({
      babel: {
        plugins: [
          [
            "@locator/babel-jsx/dist",
            {
              env: "development",
            },
          ],
        ],
      },
    }),
    tailwindcss(),
  ],
});
