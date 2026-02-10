// Auto-detect API URL if not set in environment (useful for mobile testing)
const hostname = typeof window !== 'undefined' ? window.location.hostname : '127.0.0.1';
export const API_URL = import.meta.env.VITE_API_URL || `http://${hostname}:8000`;
export const WS_URL = import.meta.env.VITE_WS_URL || `http://${hostname}:8000`;
export const APP_NAME = import.meta.env.VITE_APP_NAME || 'FastOps Manager';
