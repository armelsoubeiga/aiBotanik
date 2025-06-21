"use client";

import { API_URL, debugLog } from '@/lib/config';

interface AuthToken {
  access_token: string;
  token_type: string;
}

interface UserCredentials {
  email: string;
  password: string;
}

interface SignupData extends UserCredentials {
  name: string;
  confirmPassword: string;
}

interface PasswordChangeData {
  email: string;
  new_password: string;
  // Le mot de passe actuel n'est plus requis
}

export interface User {  id: string;
  email: string;
  name: string;
}

export class AuthService {
  private static instance: AuthService;
  private token: string | null = null;
  private user: User | null = null;

  // Récupérer l'instance singleton
  public static getInstance(): AuthService {
    if (!AuthService.instance) {
      AuthService.instance = new AuthService();
    }
    return AuthService.instance;
  }

  constructor() {
    // Initialiser le token depuis localStorage lors de la création du service
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem("auth_token");
    }
  }

  // Vérifier si l'utilisateur est connecté
  public isAuthenticated(): boolean {
    return !!this.token;
  }

  // Récupérer le token d'authentification
  public getToken(): string | null {
    return this.token;
  }

  // Définir manuellement le token (utile pour les tests)
  public setToken(token: string): void {
    this.token = token;
    if (typeof window !== 'undefined') {
      localStorage.setItem("auth_token", token);
    }
  }
  // Se connecter
  public async login(credentials: UserCredentials): Promise<{success: boolean, errorMessage?: string}> {
    try {
      const response = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(credentials),
      });

      if (!response.ok) {
        // Si l'erreur est 401 Unauthorized, c'est une tentative de connexion échouée normale
        // Pas besoin de logger une erreur dans la console
        if (response.status === 401) {
          const errorData = await response.json();
          return {
            success: false, 
            errorMessage: errorData.detail || "Email ou mot de passe incorrect"
          };
        }
        
        // Pour les autres erreurs, on peut logger
        const errorData = await response.json();
        console.error("Erreur serveur lors de la connexion:", errorData);
        return {
          success: false,
          errorMessage: "Erreur de connexion au serveur"
        };
      }

      const data: AuthToken = await response.json();
      this.token = data.access_token;
      
      // Enregistrer le token dans localStorage
      if (typeof window !== 'undefined') {
        localStorage.setItem("auth_token", data.access_token);
      }

      return { success: true };
    } catch (error) {
      console.error("Erreur inattendue lors de la connexion:", error);
      return { 
        success: false, 
        errorMessage: "Erreur de connexion inattendue"
      };
    }
  }

  // S'inscrire
  public async signup(userData: SignupData): Promise<{success: boolean, errorMessage?: string}> {
    try {
      const response = await fetch(`${API_URL}/auth/signup`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(userData),
      });

      if (!response.ok) {
        // Si l'erreur est 400 ou 409, c'est probablement un problème d'utilisateur existant
        // ou des données d'inscription invalides
        const errorData = await response.json();
        console.error("Échec de l'inscription:", errorData);
        
        return {
          success: false,
          errorMessage: errorData.detail || "Échec de l'inscription. Cet email est peut-être déjà utilisé."
        };
      }

      const data: AuthToken = await response.json();
      this.token = data.access_token;
      
      // Enregistrer le token dans localStorage
      if (typeof window !== 'undefined') {
        localStorage.setItem("auth_token", data.access_token);
      }

      return { success: true };
    } catch (error) {
      console.error("Erreur inattendue lors de l'inscription:", error);
      return { 
        success: false, 
        errorMessage: "Erreur de connexion au serveur lors de l'inscription"
      };
    }
  }
  // Se déconnecter
  public logout(): void {
    // Émettre un événement personnalisé avant de supprimer le token
    // pour permettre aux composants (comme ChatInterface) de sauvegarder les données
    if (typeof window !== 'undefined') {
      console.log("Émission de l'événement aiBotanikLogout avant déconnexion");
      window.dispatchEvent(new Event('aiBotanikLogout'));
      
      // Petit délai pour laisser le temps aux gestionnaires d'événements de s'exécuter
      setTimeout(() => {
        this.token = null;
        this.user = null;
        
        // Supprimer le token du localStorage
        localStorage.removeItem("auth_token");
        console.log("Token supprimé du localStorage, déconnexion effectuée");
      }, 300);
    } else {
      this.token = null;
      this.user = null;
    }
  }

  // Obtenir les informations de l'utilisateur courant
  public async getCurrentUser(): Promise<User | null> {
    if (!this.token) {
      return null;
    }

    if (this.user) {
      return this.user;
    }

    try {
      const response = await fetch(`${API_URL}/users/me`, {
        headers: {
          "Authorization": `Bearer ${this.token}`,
        },
      });

      if (!response.ok) {
        if (response.status === 401) {
          // Token expiré ou invalide
          this.logout();
        }
        return null;
      }

      this.user = await response.json();
      return this.user;
    } catch (error) {
      console.error("Erreur lors de la récupération du profil:", error);
      return null;
    }
  }
  // Vérifier si le token est valide
  public async validateToken(): Promise<boolean> {
    if (!this.token) {
      return false;
    }

    try {
      const response = await fetch(`${API_URL}/auth/validate`, {
        headers: {
          "Authorization": `Bearer ${this.token}`,
        },
      });

      if (!response.ok) {
        this.logout();
        return false;
      }

      return true;
    } catch (error) {
      console.error("Erreur lors de la validation du token:", error);
      return false;
    }
  }

  // Changer le mot de passe
  public async changePassword(data: PasswordChangeData): Promise<boolean> {
    if (!this.token) {
      console.error("Token non disponible pour modifier le mot de passe");
      return false;
    }

    try {
      const response = await fetch(`${API_URL}/auth/change-password`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${this.token}`,
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error("Échec du changement de mot de passe:", errorData);
        throw new Error(errorData.detail || "Échec du changement de mot de passe");
      }

      return true;
    } catch (error) {
      console.error("Erreur lors du changement de mot de passe:", error);
      return false;
    }
  }
}

// Exporter une instance par défaut du service
export const authService = AuthService.getInstance();
