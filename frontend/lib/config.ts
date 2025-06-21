/**
 * Configuration de l'application
 */

// Endpoints API
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000"

// Exports de compatibilité (utilisés dans les composants existants)
export const API_URL = API_BASE_URL
export const BASE_URL = API_BASE_URL

export const API_ENDPOINTS = {
  chat: `${API_BASE_URL}/api/conversation/unified`,
  login: `${API_BASE_URL}/api/auth/login`,
  register: `${API_BASE_URL}/api/auth/register`,
  admin: `${API_BASE_URL}/api/admin/config`
}

// Configuration de l'interface
export const UI_CONFIG = {
  appName: "aiBotanik",
  defaultLanguage: "fr",
  theme: {
    primary: "#00A86B", // Couleur verte pour la thématique plantes
    secondary: "#7FC996",
    background: "#FFFFFF",
    text: "#333333",
  },
  chatConfig: {
    maxMessages: 100,
    initialMessage: "Bonjour ! Comment puis-je vous aider avec vos plantes aujourd'hui ?"
  }
}

// Configuration des fonctionnalités
export const FEATURES_CONFIG = {
  enableAuthentication: true,
  enablePlantRecommendation: true,
  enableDiagnostic: true,
  debugMode: process.env.NODE_ENV === "development"
}
