import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vite.dev/config/
export default defineConfig({
    plugins: [
        react({
            development: true,
        }),
    ],
    define: {
        "process.env.NODE_ENV": JSON.stringify("development"),
    },
    server: {
        middlewareMode: false,
    },
});
