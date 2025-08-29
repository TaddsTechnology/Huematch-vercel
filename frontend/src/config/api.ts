// API Configuration - Updated for Vercel deployment
const isDevelopment = import.meta.env.DEV;
const isLocalhost = window?.location?.hostname === 'localhost' || window?.location?.hostname === '127.0.0.1';

// Determine API base URL based on environment
export const API_BASE_URL = (() => {
  // Check for explicit environment variable first
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }
  
  // In development, use localhost backend
  if (isDevelopment && isLocalhost) {
    return 'http://localhost:10000';
  }
  
  // In production on Vercel, use relative API paths
  if (typeof window !== 'undefined') {
    return window.location.origin;
  }
  
  // Fallback to Render backend
  return 'https://ai-fashion-backend-d9nj.onrender.com';
})();

console.log('API_BASE_URL:', API_BASE_URL);
console.log('Environment:', { isDevelopment, isLocalhost });

// API endpoints
export const API_ENDPOINTS = {
  ANALYZE_SKIN_TONE: `${API_BASE_URL}/analyze-skin-tone`,
  COLOR_SUGGESTIONS: `${API_BASE_URL}/color-suggestions`,
  COLOR_RECOMMENDATIONS: `${API_BASE_URL}/api/color-recommendations`,
  COLOR_PALETTES_DB: `${API_BASE_URL}/api/color-palettes-db`,
  ALL_COLORS: `${API_BASE_URL}/api/colors/all`,
  MAKEUP_DATA: `${API_BASE_URL}/data/`,
  APPAREL: `${API_BASE_URL}/apparel`,
  HEALTH: `${API_BASE_URL}/health`,
};

// Helper function to build API URLs
export const buildApiUrl = (endpoint: string, params?: Record<string, any>): string => {
  const url = new URL(endpoint);
  
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== null && value !== undefined) {
        url.searchParams.append(key, String(value));
      }
    });
  }
  
  return url.toString();
};
