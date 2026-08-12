const isLocalHost = ['localhost', '127.0.0.1'].includes(window.location.hostname);

export const API_BASE_URL =
  import.meta.env.VITE_API_URL || (isLocalHost ? 'http://127.0.0.1:8000' : window.location.origin);
