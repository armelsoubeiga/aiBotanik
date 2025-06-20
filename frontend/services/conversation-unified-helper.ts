// This file contains the new functionality for saving unified conversations 
// It will be imported and used in the ChatInterface component

import { conversationUnifiedService, UnifiedConversation } from "./conversation-unified-service";
import type { Message } from "./consultation-service";

/**
 * Sauvegarde une conversation complète dans la table conversations unifiées
 * Cette fonction est appelée lors de la création d'une nouvelle conversation (bouton +)
 * et lors de la déconnexion de l'utilisateur
 */
export async function saveUnifiedConversation(messages: Message[], chatMode: "discussion" | "consultation"): Promise<string | null> {
  // Ne rien faire s'il n'y a pas de messages
  if (!messages || messages.length === 0) {
    console.log("saveUnifiedConversation: Aucun message à sauvegarder");
    return null;
  }
  
  // Vérifier qu'il y a au moins un message utilisateur et un message bot
  const hasUserMessage = messages.some(m => m.sender === "user");
  const hasBotMessage = messages.some(m => m.sender === "bot");
  
  if (!hasUserMessage || !hasBotMessage) {
    console.log("saveUnifiedConversation: Conversation incomplète, sauvegarde ignorée");
    return null;
  }

  try {
    // Créer un titre à partir du premier message utilisateur
    const firstUserMessage = messages.find(m => m.sender === "user");
    const title = firstUserMessage 
      ? firstUserMessage.content.substring(0, 50) + (firstUserMessage.content.length > 50 ? "..." : "") 
      : "Nouvelle conversation";
    
    // Créer un résumé à partir du premier message utilisateur
    const summary = firstUserMessage 
      ? firstUserMessage.content.substring(0, 100) + (firstUserMessage.content.length > 100 ? "..." : "") 
      : "Pas de résumé disponible";
    
    // Déterminer le type de conversation
    // Si certains messages bot ont des recommandations, c'est une consultation
    // Si certains messages bot n'ont pas de recommandations, c'est une discussion
    // Si les deux types sont présents, c'est une conversation mixte
    const hasConsultation = messages.some(m => m.sender === "bot" && m.recommendation);
    const hasDiscussion = messages.some(m => m.sender === "bot" && !m.recommendation);
    
    let type: "discussion" | "consultation" | "mixed" = "discussion";
    if (hasConsultation && hasDiscussion) {
      type = "mixed";
    } else if (hasConsultation) {
      type = "consultation";
    }
    
    // Trouver la dernière recommandation si elle existe
    const lastRecommendation = [...messages]
      .reverse()
      .find(m => m.recommendation)?.recommendation || null;
    
    // Créer la conversation unifiée
    console.log(`saveUnifiedConversation: Sauvegarde d'une conversation de type ${type} avec ${messages.length} messages`);
    
    const conversation: UnifiedConversation = {
      title,
      summary,
      type,
      messages: messages.map(m => ({
        content: m.content,
        sender: m.sender,
        timestamp: m.timestamp ? new Date(m.timestamp) : new Date(),
        recommendation: m.recommendation
      })),
      messages_count: messages.length,
      chat_mode: chatMode,
      last_recommendation: lastRecommendation
    };
      // Sauvegarder la conversation
    const savedConversation = await conversationUnifiedService.saveConversation(conversation);
    
    if (savedConversation) {
      console.log(`saveUnifiedConversation: Conversation sauvegardée avec succès, ID: ${savedConversation.id}`);
      return savedConversation.id || null;
    } else {
      console.error("saveUnifiedConversation: Échec de la sauvegarde de la conversation");
      return null;
    }
  } catch (error) {
    console.error("saveUnifiedConversation: Erreur lors de la sauvegarde de la conversation:", error);
    
    // Si l'erreur indique un problème d'authentification, on peut retourner un code d'erreur spécial
    if (error instanceof Error && error.message.includes("Session expirée")) {
      console.warn("saveUnifiedConversation: Session expirée détectée");
      // On pourrait émettre un événement ou notifier l'interface utilisateur ici
    }
    
    return null;
  }
}
