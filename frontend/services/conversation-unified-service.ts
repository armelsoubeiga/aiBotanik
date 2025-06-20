"use client";

import { authService } from "./auth-service";

export interface UnifiedMessage {
  id?: string;
  content: string;
  sender: "user" | "bot";
  timestamp?: Date;
  recommendation?: any;
}

export interface UnifiedConversation {
  id?: string;
  title: string;
  type: "discussion" | "consultation" | "mixed";
  created_at?: string;
  updated_at?: string;
  summary?: string;
  messages?: UnifiedMessage[];
  messages_count?: number;
  user_id?: string;
  chat_mode: "discussion" | "consultation";
  last_recommendation?: any;
}

const API_URL = "http://localhost:8000/api";

/**
 * Service pour la gestion des conversations unifiées
 * Cette classe ne remplace pas le service de consultation existant,
 * elle le complète pour gérer la nouvelle table conversations.
 */
class ConversationUnifiedService {
  private static instance: ConversationUnifiedService;

  public static getInstance(): ConversationUnifiedService {
    if (!ConversationUnifiedService.instance) {
      ConversationUnifiedService.instance = new ConversationUnifiedService();
    }
    return ConversationUnifiedService.instance;
  }
  /**
   * Sauvegarde une conversation complète
   */
  public async saveConversation(conversation: UnifiedConversation): Promise<UnifiedConversation | null> {
    if (!authService.isAuthenticated()) {
      console.error("saveConversation: Utilisateur non authentifié");
      return null;
    }

    try {
      const token = authService.getToken();
      console.log("saveConversation: Tentative de sauvegarde avec token", token?.substring(0, 15) + "...");
      
      // Vérifier le type de conversation en fonction des messages
      // Si certains messages ont une recommandation, c'est une consultation, sinon c'est une discussion
      // Si les deux types de messages sont présents, c'est mixte
      let type = "discussion";
      const hasConsultation = conversation.messages?.some(m => m.recommendation);
      const hasDiscussion = conversation.messages?.some(m => m.sender === "bot" && !m.recommendation);
      
      if (hasConsultation && hasDiscussion) {
        type = "mixed";
      } else if (hasConsultation) {
        type = "consultation";
      }
      
      // Trouver la dernière recommandation si elle existe
      const lastRecommendation = conversation.messages
        ? [...conversation.messages]
            .reverse()
            .find(m => m.recommendation)?.recommendation || null
        : null;
      
      const response = await fetch(`${API_URL}/conversations`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
          ...conversation,
          type,
          last_recommendation: lastRecommendation
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error("saveConversation: Erreur lors de la sauvegarde de la conversation:", response.status, errorText);
        
        // Gérer les erreurs spécifiques
        if (response.status === 404 || response.status === 400) {
          // Problème d'authentification ou utilisateur non trouvé
          console.warn("saveConversation: Problème d'authentification détecté, déconnexion de l'utilisateur");
          authService.logout();
          throw new Error("Session expirée. Veuillez vous reconnecter.");
        }
        
        throw new Error(`Erreur ${response.status}: ${errorText}`);
      }

      const data = await response.json();
      console.log("saveConversation: Conversation sauvegardée avec succès:", data);
      return data;
    } catch (error) {
      console.error("saveConversation: Erreur lors de la sauvegarde de la conversation:", error);
      return null;
    }
  }

  /**
   * Récupère toutes les conversations unifiées
   */
  public async getConversations(): Promise<UnifiedConversation[]> {
    if (!authService.isAuthenticated()) {
      console.log("getConversations: Utilisateur non authentifié");
      return [];
    }

    try {
      const token = authService.getToken();
      console.log("getConversations: Récupération des conversations avec token", token?.substring(0, 15) + "...");
      
      const response = await fetch(`${API_URL}/conversations`, {
        method: "GET",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json",
          "Accept": "application/json"
        },
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error("getConversations: Réponse non valide:", response.status, errorText);
        throw new Error(`Erreur ${response.status}: ${errorText}`);
      }

      const data = await response.json();
      console.log(`getConversations: ${data.length} conversations récupérées avec succès`);
      return data;
    } catch (error) {
      console.error("getConversations: Erreur lors de la récupération des conversations:", error);
      return [];
    }
  }

  /**
   * Récupère une conversation par son ID
   */
  public async getConversation(id: string): Promise<UnifiedConversation | null> {
    if (!authService.isAuthenticated()) {
      console.error("getConversation: Tentative de récupérer une conversation sans être authentifié");
      return null;
    }

    try {
      const token = authService.getToken();
      
      if (!token) {
        console.error("getConversation: Pas de token disponible pour récupérer la conversation");
        return null;
      }
      
      console.log(`getConversation: Récupération de la conversation ${id} avec token ${token.substring(0, 10)}...`);
      
      const response = await fetch(`${API_URL}/conversations/${id}`, {
        headers: {
          "Authorization": `Bearer ${token}`
        },
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error(`getConversation: Erreur ${response.status} lors de la récupération de la conversation:`, errorText);
        throw new Error(`Erreur ${response.status}: ${errorText}`);
      }
      
      const conversation = await response.json();
      console.log(`getConversation: Conversation ${id} récupérée avec succès:`, conversation);
      return conversation;
    } catch (error) {
      console.error(`getConversation: Erreur lors de la récupération de la conversation ${id}:`, error);
      return null;
    }
  }

  /**
   * Récupère l'historique des conversations pour affichage
   * Retourne seulement les métadonnées (sans les messages complets)
   */
  public async getConversationHistory(): Promise<ConversationHistoryItem[]> {
    if (!authService.isAuthenticated()) {
      console.log("getConversationHistory: Utilisateur non authentifié");
      return [];
    }

    try {
      const token = authService.getToken();
      console.log("getConversationHistory: Récupération de l'historique avec token", token?.substring(0, 15) + "...");
      
      const response = await fetch(`${API_URL}/conversations`, {
        method: "GET",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json",
          "Accept": "application/json"
        },
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error("getConversationHistory: Réponse non valide:", response.status, errorText);
        
        // Gérer les erreurs d'authentification
        if (response.status === 401 || response.status === 403) {
          console.warn("getConversationHistory: Problème d'authentification détecté");
          authService.logout();
          throw new Error("Session expirée. Veuillez vous reconnecter.");
        }
        
        throw new Error(`Erreur ${response.status}: ${errorText}`);
      }

      const conversations = await response.json();
      console.log(`getConversationHistory: ${conversations.length} conversations récupérées`);
      
      // Filtrer et formater pour l'historique
      const validConversations = conversations
        .filter((conv: any) => {
          // Ne conserver que les conversations avec au moins 4 messages (2 échanges complets)
          const messageCount = conv.messages_count || (conv.messages?.length || 0);
          return messageCount >= 4;
        })
        .map((conv: any): ConversationHistoryItem => ({
          id: conv.id,
          title: conv.title || "Conversation sans titre",
          type: conv.type || "mixed",
          summary: conv.summary || "Pas de résumé disponible",
          messages_count: conv.messages_count || (conv.messages?.length || 0),
          created_at: conv.created_at,
          updated_at: conv.updated_at,
          chat_mode: conv.chat_mode || "discussion",
          last_recommendation: conv.last_recommendation
        }))
        // Trier par date de mise à jour, plus récent en premier
        .sort((a: ConversationHistoryItem, b: ConversationHistoryItem) => {
          return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
        });

      console.log(`getConversationHistory: ${validConversations.length} conversations valides après filtrage`);
      return validConversations;
    } catch (error) {
      console.error("getConversationHistory: Erreur lors de la récupération de l'historique:", error);
      return [];
    }
  }

  /**
   * Récupère une conversation complète avec tous ses messages
   * Utilisé pour restaurer une conversation depuis l'historique
   */
  public async getConversationWithMessages(id: string): Promise<UnifiedConversation | null> {
    if (!authService.isAuthenticated()) {
      console.error("getConversationWithMessages: Utilisateur non authentifié");
      return null;
    }

    try {
      const token = authService.getToken();
      
      if (!token) {
        console.error("getConversationWithMessages: Pas de token disponible");
        return null;
      }
        console.log(`getConversationWithMessages: Récupération de la conversation ${id}`);
      
      const response = await fetch(`${API_URL}/conversations/${id}/messages`, {
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json",
          "Accept": "application/json"
        },
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error(`getConversationWithMessages: Erreur ${response.status}:`, errorText);
        
        if (response.status === 401 || response.status === 403) {
          authService.logout();
          throw new Error("Session expirée. Veuillez vous reconnecter.");
        }
        
        throw new Error(`Erreur ${response.status}: ${errorText}`);
      }
      
      const conversation = await response.json();
      console.log(`getConversationWithMessages: Conversation ${id} récupérée avec ${conversation.messages?.length || 0} messages`);
      
      return conversation;
    } catch (error) {
      console.error(`getConversationWithMessages: Erreur lors de la récupération de la conversation ${id}:`, error);
      return null;
    }
  }
}

export const conversationUnifiedService = ConversationUnifiedService.getInstance();

// Type pour l'historique des conversations unifié
export interface ConversationHistoryItem {
  id: string;
  title: string;
  type: "discussion" | "consultation" | "mixed";
  summary?: string;
  messages_count: number;
  created_at: string;
  updated_at: string;
  chat_mode: "discussion" | "consultation";
  last_recommendation?: any;
}
