// vite.config.ts
import { defineConfig } from "file:///C:/Users/jp151/lab/el_rincon/SISTEMA-GESTION-CESAR/panel%20admin%20y%20operativo/node_modules/vite/dist/node/index.js";
import react from "file:///C:/Users/jp151/lab/el_rincon/SISTEMA-GESTION-CESAR/panel%20admin%20y%20operativo/node_modules/@vitejs/plugin-react/dist/index.js";
import tailwindcss from "file:///C:/Users/jp151/lab/el_rincon/SISTEMA-GESTION-CESAR/panel%20admin%20y%20operativo/node_modules/@tailwindcss/vite/dist/index.mjs";
import { VitePWA } from "file:///C:/Users/jp151/lab/el_rincon/SISTEMA-GESTION-CESAR/panel%20admin%20y%20operativo/node_modules/vite-plugin-pwa/dist/index.js";
import { fileURLToPath, URL } from "url";
var __vite_injected_original_import_meta_url = "file:///C:/Users/jp151/lab/el_rincon/SISTEMA-GESTION-CESAR/panel%20admin%20y%20operativo/vite.config.ts";
var vite_config_default = defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    VitePWA({
      registerType: "autoUpdate",
      injectRegister: "auto",
      devOptions: {
        enabled: true,
        type: "module"
      },
      workbox: {
        globPatterns: ["**/*.{js,css,html,ico,png,svg}"],
        cleanupOutdatedCaches: true,
        clientsClaim: true,
        skipWaiting: true
      },
      includeAssets: ["favicon.ico", "pwa-icon.png"],
      manifest: {
        name: "FastOps - Gesti\xF3n Restaurante",
        short_name: "FastOps",
        description: "Sistema de Gesti\xF3n y Operaciones para Restaurante",
        theme_color: "#0f172a",
        background_color: "#0f172a",
        display: "standalone",
        orientation: "portrait",
        icons: [
          {
            src: "pwa-icon.png",
            sizes: "192x192",
            type: "image/png"
          },
          {
            src: "pwa-icon.png",
            sizes: "512x512",
            type: "image/png",
            purpose: "any maskable"
          }
        ]
      }
    })
  ],
  server: {
    host: true,
    port: 5173
  },
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", __vite_injected_original_import_meta_url))
    }
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          "vendor-react": ["react", "react-dom", "react-router-dom"],
          "vendor-state": ["@reduxjs/toolkit", "react-redux", "@tanstack/react-query"],
          "vendor-utils": ["axios", "date-fns", "zod", "socket.io-client"]
        }
      }
    },
    chunkSizeWarningLimit: 1e3
  }
});
export {
  vite_config_default as default
};
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsidml0ZS5jb25maWcudHMiXSwKICAic291cmNlc0NvbnRlbnQiOiBbImNvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9kaXJuYW1lID0gXCJDOlxcXFxVc2Vyc1xcXFxqcDE1MVxcXFxsYWJcXFxcZWxfcmluY29uXFxcXFNJU1RFTUEtR0VTVElPTi1DRVNBUlxcXFxwYW5lbCBhZG1pbiB5IG9wZXJhdGl2b1wiO2NvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9maWxlbmFtZSA9IFwiQzpcXFxcVXNlcnNcXFxcanAxNTFcXFxcbGFiXFxcXGVsX3JpbmNvblxcXFxTSVNURU1BLUdFU1RJT04tQ0VTQVJcXFxccGFuZWwgYWRtaW4geSBvcGVyYXRpdm9cXFxcdml0ZS5jb25maWcudHNcIjtjb25zdCBfX3ZpdGVfaW5qZWN0ZWRfb3JpZ2luYWxfaW1wb3J0X21ldGFfdXJsID0gXCJmaWxlOi8vL0M6L1VzZXJzL2pwMTUxL2xhYi9lbF9yaW5jb24vU0lTVEVNQS1HRVNUSU9OLUNFU0FSL3BhbmVsJTIwYWRtaW4lMjB5JTIwb3BlcmF0aXZvL3ZpdGUuY29uZmlnLnRzXCI7aW1wb3J0IHsgZGVmaW5lQ29uZmlnIH0gZnJvbSAndml0ZSdcclxuaW1wb3J0IHJlYWN0IGZyb20gJ0B2aXRlanMvcGx1Z2luLXJlYWN0J1xyXG5pbXBvcnQgdGFpbHdpbmRjc3MgZnJvbSAnQHRhaWx3aW5kY3NzL3ZpdGUnXHJcbmltcG9ydCB7IFZpdGVQV0EgfSBmcm9tICd2aXRlLXBsdWdpbi1wd2EnXHJcbmltcG9ydCB7IGZpbGVVUkxUb1BhdGgsIFVSTCB9IGZyb20gJ3VybCdcclxuXHJcbi8vIGh0dHBzOi8vdml0ZWpzLmRldi9jb25maWcvXHJcbmV4cG9ydCBkZWZhdWx0IGRlZmluZUNvbmZpZyh7XHJcbiAgICBwbHVnaW5zOiBbXHJcbiAgICAgICAgcmVhY3QoKSxcclxuICAgICAgICB0YWlsd2luZGNzcygpLFxyXG4gICAgICAgIFZpdGVQV0Eoe1xyXG4gICAgICAgICAgICByZWdpc3RlclR5cGU6ICdhdXRvVXBkYXRlJyxcclxuICAgICAgICAgICAgaW5qZWN0UmVnaXN0ZXI6ICdhdXRvJyxcclxuICAgICAgICAgICAgZGV2T3B0aW9uczoge1xyXG4gICAgICAgICAgICAgICAgZW5hYmxlZDogdHJ1ZSxcclxuICAgICAgICAgICAgICAgIHR5cGU6ICdtb2R1bGUnXHJcbiAgICAgICAgICAgIH0sXHJcbiAgICAgICAgICAgIHdvcmtib3g6IHtcclxuICAgICAgICAgICAgICAgIGdsb2JQYXR0ZXJuczogWycqKi8qLntqcyxjc3MsaHRtbCxpY28scG5nLHN2Z30nXSxcclxuICAgICAgICAgICAgICAgIGNsZWFudXBPdXRkYXRlZENhY2hlczogdHJ1ZSxcclxuICAgICAgICAgICAgICAgIGNsaWVudHNDbGFpbTogdHJ1ZSxcclxuICAgICAgICAgICAgICAgIHNraXBXYWl0aW5nOiB0cnVlXHJcbiAgICAgICAgICAgIH0sXHJcbiAgICAgICAgICAgIGluY2x1ZGVBc3NldHM6IFsnZmF2aWNvbi5pY28nLCAncHdhLWljb24ucG5nJ10sXHJcbiAgICAgICAgICAgIG1hbmlmZXN0OiB7XHJcbiAgICAgICAgICAgICAgICBuYW1lOiAnRmFzdE9wcyAtIEdlc3RpXHUwMEYzbiBSZXN0YXVyYW50ZScsXHJcbiAgICAgICAgICAgICAgICBzaG9ydF9uYW1lOiAnRmFzdE9wcycsXHJcbiAgICAgICAgICAgICAgICBkZXNjcmlwdGlvbjogJ1Npc3RlbWEgZGUgR2VzdGlcdTAwRjNuIHkgT3BlcmFjaW9uZXMgcGFyYSBSZXN0YXVyYW50ZScsXHJcbiAgICAgICAgICAgICAgICB0aGVtZV9jb2xvcjogJyMwZjE3MmEnLFxyXG4gICAgICAgICAgICAgICAgYmFja2dyb3VuZF9jb2xvcjogJyMwZjE3MmEnLFxyXG4gICAgICAgICAgICAgICAgZGlzcGxheTogJ3N0YW5kYWxvbmUnLFxyXG4gICAgICAgICAgICAgICAgb3JpZW50YXRpb246ICdwb3J0cmFpdCcsXHJcbiAgICAgICAgICAgICAgICBpY29uczogW1xyXG4gICAgICAgICAgICAgICAgICAgIHtcclxuICAgICAgICAgICAgICAgICAgICAgICAgc3JjOiAncHdhLWljb24ucG5nJyxcclxuICAgICAgICAgICAgICAgICAgICAgICAgc2l6ZXM6ICcxOTJ4MTkyJyxcclxuICAgICAgICAgICAgICAgICAgICAgICAgdHlwZTogJ2ltYWdlL3BuZydcclxuICAgICAgICAgICAgICAgICAgICB9LFxyXG4gICAgICAgICAgICAgICAgICAgIHtcclxuICAgICAgICAgICAgICAgICAgICAgICAgc3JjOiAncHdhLWljb24ucG5nJyxcclxuICAgICAgICAgICAgICAgICAgICAgICAgc2l6ZXM6ICc1MTJ4NTEyJyxcclxuICAgICAgICAgICAgICAgICAgICAgICAgdHlwZTogJ2ltYWdlL3BuZycsXHJcbiAgICAgICAgICAgICAgICAgICAgICAgIHB1cnBvc2U6ICdhbnkgbWFza2FibGUnXHJcbiAgICAgICAgICAgICAgICAgICAgfVxyXG4gICAgICAgICAgICAgICAgXVxyXG4gICAgICAgICAgICB9XHJcbiAgICAgICAgfSlcclxuICAgIF0sXHJcbiAgICBzZXJ2ZXI6IHtcclxuICAgICAgICBob3N0OiB0cnVlLFxyXG4gICAgICAgIHBvcnQ6IDUxNzMsXHJcbiAgICB9LFxyXG4gICAgcmVzb2x2ZToge1xyXG4gICAgICAgIGFsaWFzOiB7XHJcbiAgICAgICAgICAgIFwiQFwiOiBmaWxlVVJMVG9QYXRoKG5ldyBVUkwoXCIuL3NyY1wiLCBpbXBvcnQubWV0YS51cmwpKSxcclxuICAgICAgICB9LFxyXG4gICAgfSxcclxuICAgIGJ1aWxkOiB7XHJcbiAgICAgICAgcm9sbHVwT3B0aW9uczoge1xyXG4gICAgICAgICAgICBvdXRwdXQ6IHtcclxuICAgICAgICAgICAgICAgIG1hbnVhbENodW5rczoge1xyXG4gICAgICAgICAgICAgICAgICAgICd2ZW5kb3ItcmVhY3QnOiBbJ3JlYWN0JywgJ3JlYWN0LWRvbScsICdyZWFjdC1yb3V0ZXItZG9tJ10sXHJcbiAgICAgICAgICAgICAgICAgICAgJ3ZlbmRvci1zdGF0ZSc6IFsnQHJlZHV4anMvdG9vbGtpdCcsICdyZWFjdC1yZWR1eCcsICdAdGFuc3RhY2svcmVhY3QtcXVlcnknXSxcclxuICAgICAgICAgICAgICAgICAgICAndmVuZG9yLXV0aWxzJzogWydheGlvcycsICdkYXRlLWZucycsICd6b2QnLCAnc29ja2V0LmlvLWNsaWVudCddLFxyXG4gICAgICAgICAgICAgICAgfVxyXG4gICAgICAgICAgICB9XHJcbiAgICAgICAgfSxcclxuICAgICAgICBjaHVua1NpemVXYXJuaW5nTGltaXQ6IDEwMDAsXHJcbiAgICB9XHJcbn0pIl0sCiAgIm1hcHBpbmdzIjogIjtBQUFvYSxTQUFTLG9CQUFvQjtBQUNqYyxPQUFPLFdBQVc7QUFDbEIsT0FBTyxpQkFBaUI7QUFDeEIsU0FBUyxlQUFlO0FBQ3hCLFNBQVMsZUFBZSxXQUFXO0FBSnNPLElBQU0sMkNBQTJDO0FBTzFULElBQU8sc0JBQVEsYUFBYTtBQUFBLEVBQ3hCLFNBQVM7QUFBQSxJQUNMLE1BQU07QUFBQSxJQUNOLFlBQVk7QUFBQSxJQUNaLFFBQVE7QUFBQSxNQUNKLGNBQWM7QUFBQSxNQUNkLGdCQUFnQjtBQUFBLE1BQ2hCLFlBQVk7QUFBQSxRQUNSLFNBQVM7QUFBQSxRQUNULE1BQU07QUFBQSxNQUNWO0FBQUEsTUFDQSxTQUFTO0FBQUEsUUFDTCxjQUFjLENBQUMsZ0NBQWdDO0FBQUEsUUFDL0MsdUJBQXVCO0FBQUEsUUFDdkIsY0FBYztBQUFBLFFBQ2QsYUFBYTtBQUFBLE1BQ2pCO0FBQUEsTUFDQSxlQUFlLENBQUMsZUFBZSxjQUFjO0FBQUEsTUFDN0MsVUFBVTtBQUFBLFFBQ04sTUFBTTtBQUFBLFFBQ04sWUFBWTtBQUFBLFFBQ1osYUFBYTtBQUFBLFFBQ2IsYUFBYTtBQUFBLFFBQ2Isa0JBQWtCO0FBQUEsUUFDbEIsU0FBUztBQUFBLFFBQ1QsYUFBYTtBQUFBLFFBQ2IsT0FBTztBQUFBLFVBQ0g7QUFBQSxZQUNJLEtBQUs7QUFBQSxZQUNMLE9BQU87QUFBQSxZQUNQLE1BQU07QUFBQSxVQUNWO0FBQUEsVUFDQTtBQUFBLFlBQ0ksS0FBSztBQUFBLFlBQ0wsT0FBTztBQUFBLFlBQ1AsTUFBTTtBQUFBLFlBQ04sU0FBUztBQUFBLFVBQ2I7QUFBQSxRQUNKO0FBQUEsTUFDSjtBQUFBLElBQ0osQ0FBQztBQUFBLEVBQ0w7QUFBQSxFQUNBLFFBQVE7QUFBQSxJQUNKLE1BQU07QUFBQSxJQUNOLE1BQU07QUFBQSxFQUNWO0FBQUEsRUFDQSxTQUFTO0FBQUEsSUFDTCxPQUFPO0FBQUEsTUFDSCxLQUFLLGNBQWMsSUFBSSxJQUFJLFNBQVMsd0NBQWUsQ0FBQztBQUFBLElBQ3hEO0FBQUEsRUFDSjtBQUFBLEVBQ0EsT0FBTztBQUFBLElBQ0gsZUFBZTtBQUFBLE1BQ1gsUUFBUTtBQUFBLFFBQ0osY0FBYztBQUFBLFVBQ1YsZ0JBQWdCLENBQUMsU0FBUyxhQUFhLGtCQUFrQjtBQUFBLFVBQ3pELGdCQUFnQixDQUFDLG9CQUFvQixlQUFlLHVCQUF1QjtBQUFBLFVBQzNFLGdCQUFnQixDQUFDLFNBQVMsWUFBWSxPQUFPLGtCQUFrQjtBQUFBLFFBQ25FO0FBQUEsTUFDSjtBQUFBLElBQ0o7QUFBQSxJQUNBLHVCQUF1QjtBQUFBLEVBQzNCO0FBQ0osQ0FBQzsiLAogICJuYW1lcyI6IFtdCn0K
