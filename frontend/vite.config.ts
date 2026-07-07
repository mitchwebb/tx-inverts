import { defineConfig } from 'vitest/config';
import { svelte } from '@sveltejs/vite-plugin-svelte';
import dotenv from 'dotenv';

dotenv.config();

let proxy = process.env.VITE_API_PROXY || 'http://localhost:8000';

// https://vite.dev/config/
export default defineConfig({
    plugins: [svelte()],
    server: {
        proxy: {
            '/server': {
                target: proxy, // Backend server
                changeOrigin: true, // Needed for virtual host-based backends
                secure: false, // Disable SSL verification if using self-signed certs
                rewrite: (path) => path.replace(/^\/server/, ''), // Optional path rewrite
            },
        },
    },
    test: {
        exclude: ['**/node_modules/**', '**/dist/**', 'ui-tests/**'],
    },
});
