// API Configuration - Updated for production
export const API_BASE_URL = import.meta.env.VITE_API_URL;

// PostgreSQL Database Configuration
export const DATABASE_URL = 'postgresql://fashion_jvy9_user:0d2Nn5mvyw6KMBDT21l9olpHaxrTPEzh@dpg-d1vhvpbuibrs739dkn3g-a.oregon-postgres.render.com/fashion_jvy9';

console.log('API_BASE_URL:', API_BASE_URL);

// API endpoints
export const API_ENDPOINTS = {
  ANALYZE_SKIN_TONE: `${API_BASE_URL}/analyze-skin-tone`,
  COLOR_SUGGESTIONS: `${API_BASE_URL}/color-suggestions`,
  COLOR_RECOMMENDATIONS: `${API_BASE_URL}/api/color-recommendations`,
  COLOR_PALETTES_DB: `${API_BASE_URL}/api/color-palettes-db`,
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
