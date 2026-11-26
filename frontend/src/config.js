// The API base is baked in at build time by Vite. Override it with
// VITE_API_BASE_URL when building for a non-local deployment.
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const API_BASE_URL = apiBaseUrl.replace(/\/+$/, '');
