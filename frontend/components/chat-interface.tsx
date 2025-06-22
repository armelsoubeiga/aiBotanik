"use client"

import React, { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { Mic, Send, ArrowLeft, Bot, User, MessageCircle, Stethoscope, Loader2, Save, LogIn, PlusCircle } from "lucide-react"
import { PlantRecommendationCard, PlantRecommendation } from "./plant-recommendation"
import { AuthRequiredModal } from "./auth-required-modal"
import { LoginModal } from "./login-modal"
import { authService } from "@/services/auth-service"
import { consultationService } from "@/services/consultation-service"
// Types importés avec des alias pour éviter les conflits
import type { Message as ServiceMessage, Consultation as ServiceConsultation } from "@/services/consultation-service"
// Import du service et helper pour les conversations unifiées
import { conversationUnifiedService } from "@/services/conversation-unified-service"
import { saveUnifiedConversation } from "@/services/conversation-unified-helper"
// Configuration des URLs backend
import { API_URL, BASE_URL } from "@/lib/config"

interface ChatInterfaceProps {
  onBack?: () => void
  onStartChat?: () => void
  isWelcome?: boolean
  isAuthenticated?: boolean
  onAuthChange?: (isAuth: boolean) => void
  consultationId?: string  // ID de la consultation à charger depuis l'historique
  currentConversation?: any  // Conversation en cours pour la persistance
  onConversationChange?: (conversation: any) => void  // Pour mettre à jour la conversation en cours
}

interface Message {
  id: string
  content: string
  sender: "user" | "bot"
  timestamp: Date
  recommendation?: PlantRecommendation
}

export function ChatInterface({ 
  onBack, 
  onStartChat, 
  isWelcome = false,
  isAuthenticated: propIsAuthenticated,
  onAuthChange,
  consultationId, // ID de la consultation à charger depuis l'historique
  currentConversation, // Conversation en cours pour la persistance
  onConversationChange // Pour mettre à jour la conversation en cours
}: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState("")
  const [isListening, setIsListening] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false)
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false)
  const [pendingSaveConversation, setPendingSaveConversation] = useState(false)
  const [pendingMessage, setPendingMessage] = useState("")
  // Utiliser l'état fourni par les props si disponible, sinon utiliser un état local
  const [localIsAuthenticated, setLocalIsAuthenticated] = useState(false)
  const isAuthenticated = propIsAuthenticated !== undefined ? propIsAuthenticated : localIsAuthenticated
  const [userChooseContinueWithoutLogin, setUserChooseContinueWithoutLogin] = useState(false) // Nouvel état pour suivre si l'utilisateur a choisi de continuer sans connexion
  // Définir le mode discussion comme mode par défaut
  const [chatMode, setChatMode] = useState<"discussion" | "consultation">("discussion")
  // Tracker les tentatives pour le système de fallback robuste
  const [attemptCount, setAttemptCount] = useState(1)

  const welcomeText = `Bonjour ! Je suis aiBotanik, votre assistant spécialisé en phytothérapie africaine.

Décrivez vos symptômes et je vous aiderai à trouver des remèdes naturels adaptés.

Comment puis-je vous aider ?`

  // La sauvegarde se fait automatiquement lorsque l'utilisateur est connecté
  // après l'envoi d'un message et la réponse du bot
  
  // Référence à la consultation actuelle
  const [currentConsultation, setCurrentConsultation] = useState<ServiceConsultation | null>(null);
  const [isHistoricalConsultation, setIsHistoricalConsultation] = useState(false);
    // Effet pour créer une nouvelle consultation au démarrage si l'utilisateur est authentifié
  useEffect(() => {
    let isMounted = true; // Flag pour éviter les mises à jour après démontage
    
    const initializeConsultation = async () => {
      // DÉSACTIVÉ: Ne pas créer automatiquement de consultation pour chaque nouveau chat
      // Les conversations ne sont sauvegardées que lors d'actions explicites selon la logique métier
      // 
      // Cette fonction était responsable de la création automatique d'entrées de consultation
      // qui interfère avec la logique métier où les messages sont stockés temporairement
      // et ne sont persistés que lors du bouton +, déconnexion, ou fermeture navigateur
      
      console.log(`🔍 Initialisation consultation désactivée pour respecter la logique métier`, {
        isAuthenticated,
        messagesLength: messages.length,
        currentConsultation: currentConsultation?.id,
        isHistoricalConsultation
      });
    };
    
    initializeConsultation();
    
    // Nettoyer l'effet lors du démontage
    return () => {
      isMounted = false;
    };
  }, [isAuthenticated, messages.length, currentConsultation, isHistoricalConsultation]);
  
  // Écouteur d'événement pour sauvegarder la conversation avant déconnexion
  useEffect(() => {
    // Fonction pour gérer la sauvegarde avant déconnexion
    const handleBeforeUnload = async () => {
      if (isAuthenticated && messages.length >= 4) {
        console.log("Détection de fermeture de page ou déconnexion, sauvegarde de la conversation...");
        // Appel direct à l'API pour éviter les problèmes de promesses non résolues
        await saveConversationBeforeLogout();
      }
    };

    // Fonction pour gérer la déconnexion imminente
    const handleLogoutEvent = async (event: Event) => {
      if (isAuthenticated && messages.length >= 4) {
        console.log("Détection de déconnexion imminente via événement personnalisé, sauvegarde de la conversation...");
        await saveConversationBeforeLogout();
      }
    };

    // Écouter l'événement personnalisé de déconnexion imminente
    window.addEventListener('beforeunload', handleBeforeUnload);
    window.addEventListener('aiBotanikLogout', handleLogoutEvent);
    
    // Nettoyage des écouteurs lors du démontage
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
      window.removeEventListener('aiBotanikLogout', handleLogoutEvent);
    };
  }, [isAuthenticated, messages]);  // Effet pour la sauvegarde automatique des nouveaux messages dans les consultations existantes
  useEffect(() => {
    // Fonction pour sauvegarder automatiquement les nouveaux messages
    const autoSaveNewMessages = async () => {
      console.log(`🔍 Diagnostic sauvegarde automatique:`, {
        isAuthenticated,
        userChooseContinueWithoutLogin,
        currentConsultationId: currentConsultation?.id,
        isHistoricalConsultation,
        messagesLength: messages.length
      });
      
      // IMPORTANTE: La sauvegarde automatique ne doit se faire QUE pour les consultations historiques
      // Les nouvelles conversations utilisent un stockage temporaire et ne sont sauvegardées
      // que lors d'actions explicites (bouton +, déconnexion, fermeture navigateur)
      
      // Conditions pour déclencher la sauvegarde automatique :
      // 1. Utilisateur authentifié
      // 2. Pas en mode "continuer sans connexion"
      // 3. Il s'agit d'une consultation historique (isHistoricalConsultation = true)
      // 4. Il y a une consultation existante
      // 5. Il y a des messages
      // 6. Le dernier message n'est pas un message utilisateur seul (on attend la paire user+bot)
      if (
        isAuthenticated && 
        !userChooseContinueWithoutLogin && 
        isHistoricalConsultation && // AJOUT: Seulement pour les consultations historiques
        currentConsultation?.id && 
        messages.length > 0 &&
        messages.length >= 2 // Au minimum une paire user+bot
      ) {
        const lastMessage = messages[messages.length - 1];
        
        // Ne sauvegarder que si le dernier message est du bot (fin d'un échange complet)
        if (lastMessage.sender === "bot") {
          console.log(`🔄 Sauvegarde automatique déclenchée - Consultation ${currentConsultation.id} - Message bot reçu`);
          
          try {
            // Identifier les nouveaux messages qui ne sont pas encore sauvegardés
            const existingMessageIds = new Set(
              (currentConsultation.messages || [])
                .filter(m => m.id)
                .map(m => m.id?.toString())
            );
            
            // Prendre les 2 derniers messages (user + bot)
            const recentMessages = messages.slice(-2);
            const messagesToSave = recentMessages
              .filter(m => !existingMessageIds.has(m.id?.toString()))
              .map(m => ({
                content: m.content,
                sender: m.sender,
                recommendation: m.recommendation
              }));
              if (messagesToSave.length > 0) {
              console.log(`🔄 Sauvegarde automatique - ${messagesToSave.length} nouveaux messages à sauvegarder`);
              
              // Distinguer entre consultation historique (table conversations) et nouvelle consultation (tables consultation/message)
              if (isHistoricalConsultation && currentConsultation.id) {
                // CAS 1: Consultation historique chargée depuis la table conversations
                // Utiliser le service unifié pour ajouter à une conversation existante
                console.log(`🔄 Sauvegarde automatique - Consultation historique détectée, utilisation du service unifié`);
                
                for (const message of messagesToSave) {
                  try {
                    console.log(`🔄 Sauvegarde automatique - Ajout du message ${message.sender} à la conversation unifiée ${currentConsultation.id}`);
                    
                    const savedMessage = await conversationUnifiedService.addMessageToConversation(
                      currentConsultation.id, 
                      {
                        content: message.content,
                        sender: message.sender,
                        recommendation: message.recommendation
                      }
                    );
                    
                    if (!savedMessage) {
                      throw new Error("Échec de la sauvegarde du message");
                    }
                    
                    console.log(`✅ Sauvegarde automatique - Message ${message.sender} sauvegardé dans conversation unifiée`);
                  } catch (error) {
                    console.error(`❌ Sauvegarde automatique - Erreur lors de la sauvegarde du message ${message.sender}:`, error);
                  }
                }
              } else {
                // CAS 2: Nouvelle consultation en cours (stockage intermédiaire)
                // Utiliser le service consultation traditionnel pour le stockage intermédiaire
                console.log(`🔄 Sauvegarde automatique - Nouvelle consultation détectée, utilisation du stockage intermédiaire`);
                
                for (const message of messagesToSave) {
                  try {
                    console.log(`🔄 Sauvegarde automatique - Ajout du message ${message.sender} au stockage intermédiaire`);
                    
                    // Utiliser consultationService pour sauvegarder dans les tables consultation/message
                    const savedMessage = await consultationService.addMessage(
                      currentConsultation.id, 
                      {
                        content: message.content,
                        sender: message.sender,
                        recommendation: message.recommendation
                      }
                    );
                    
                    if (!savedMessage) {
                      throw new Error("Échec de la sauvegarde du message");
                    }
                    
                    console.log(`✅ Sauvegarde automatique - Message ${message.sender} sauvegardé dans stockage intermédiaire`);
                  } catch (error) {
                    console.error(`❌ Sauvegarde automatique - Erreur lors de la sauvegarde du message ${message.sender}:`, error);
                  }
                }
              }
              
              console.log(`✅ Sauvegarde automatique terminée - ${messagesToSave.length} messages sauvegardés dans la consultation ${currentConsultation.id}`);
            } else {
              console.log("🔄 Sauvegarde automatique - Aucun nouveau message à sauvegarder");
            }
          } catch (error) {
            console.error("❌ Sauvegarde automatique - Erreur:", error);
          }
        } else {
          console.log("🔄 Sauvegarde automatique - En attente de la réponse du bot");
        }
      }
    };
    
    // Déclencher la sauvegarde avec un petit délai pour s'assurer que l'état est stabilisé
    const timeoutId = setTimeout(autoSaveNewMessages, 100);
    
    return () => clearTimeout(timeoutId);
  }, [
    messages.length, // Se déclenche quand le nombre de messages change
    isAuthenticated, 
    userChooseContinueWithoutLogin, 
    currentConsultation?.id
  ]);
  
  // Fonction spécifique pour sauvegarder la conversation juste avant déconnexion
  const saveConversationBeforeLogout = async () => {
    if (!isAuthenticated || messages.length < 4) {
      return false;
    }
    
    const hasUserMessage = messages.some(m => m.sender === "user");
    const hasBotMessage = messages.some(m => m.sender === "bot");
    
    if (!hasUserMessage || !hasBotMessage) {
      console.log("saveConversationBeforeLogout: Conversation incomplète, sauvegarde ignorée");
      return false;
    }
    
    try {
      console.log("saveConversationBeforeLogout: Tentative de sauvegarde d'urgence avant déconnexion");
      
      // Obtenir le token avant qu'il ne soit invalidé
      const token = authService.getToken();
      if (!token) {
        console.error("saveConversationBeforeLogout: Pas de token disponible");
        return false;
      }
      
      // Utiliser la fonction de sauvegarde unifiée pour sauvegarder la conversation
      const conversationId = await saveUnifiedConversation(messages, chatMode);
      
      if (conversationId) {
        console.log(`saveConversationBeforeLogout: Conversation sauvegardée avec succès dans la table unifiée, ID: ${conversationId}`);
        return true;
      }
      
      // En cas d'échec de la sauvegarde unifiée, continuer avec la sauvegarde traditionnelle
      console.log("saveConversationBeforeLogout: Échec de la sauvegarde unifiée, tentative avec l'ancienne méthode");
      
      // Générer un titre basé sur le premier message utilisateur
      const firstUserMessage = messages.find(m => m.sender === "user");
      const title = firstUserMessage 
        ? firstUserMessage.content.substring(0, 50) + (firstUserMessage.content.length > 50 ? "..." : "") 
        : "Nouvelle session";
      
      // Appel direct à l'API pour éviter les problèmes de promesses
      const messagesToSend = messages.map(m => {
        // S'assurer que les recommandations sont correctement formatées
        let processedRecommendation = m.recommendation;
        
        if (processedRecommendation) {
          if (typeof processedRecommendation === 'string') {
            try {
              processedRecommendation = JSON.parse(processedRecommendation);
            } catch (error) {
              console.warn("saveConversationBeforeLogout: Erreur lors du parsing de la recommandation", error);
            }
          }
          
          // Assurer que tous les champs requis sont présents
          if (typeof processedRecommendation === 'object' && processedRecommendation !== null) {
            if (!processedRecommendation.plant) processedRecommendation.plant = "Plante médicinale";
            if (!processedRecommendation.dosage) processedRecommendation.dosage = "Dosage à déterminer selon le cas";
            if (!processedRecommendation.prep) processedRecommendation.prep = "Préparation à adapter selon les besoins";
            if (!processedRecommendation.image_url) processedRecommendation.image_url = "";
            if (!processedRecommendation.explanation) processedRecommendation.explanation = "Pas de détails disponibles";
            if (!processedRecommendation.contre_indications) processedRecommendation.contre_indications = "Consultez un professionnel de santé avant utilisation";
            if (!processedRecommendation.partie_utilisee) processedRecommendation.partie_utilisee = "Diverses parties de la plante";
            if (!processedRecommendation.composants) processedRecommendation.composants = "Composants actifs à déterminer";
            if (!processedRecommendation.nom_local) processedRecommendation.nom_local = processedRecommendation.plant || "Nom local non disponible";
          }
        }
        
        return {
          content: m.content,
          sender: m.sender,
          recommendation: processedRecommendation
        };
      });
      
      // Si nous avons déjà une consultation, mettre à jour avec les nouveaux messages
      if (currentConsultation && currentConsultation.id) {
        console.log(`saveConversationBeforeLogout: Mise à jour de la consultation existante ${currentConsultation.id}`);
          // Appel direct à l'API pour la mise à jour
        const response = await fetch(`${API_URL}/api/consultations/${currentConsultation.id}`, {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`
          },
          body: JSON.stringify({
            title,
            type: chatMode,
            messages: messagesToSend
          }),
        });
        
        if (!response.ok) {
          console.error(`saveConversationBeforeLogout: Erreur lors de la mise à jour de la consultation ${currentConsultation.id}`);
          return false;
        }
        
        console.log(`saveConversationBeforeLogout: Consultation ${currentConsultation.id} mise à jour avec succès`);
        return true;
      } 
      // Sinon, créer une nouvelle consultation
      else {        console.log("saveConversationBeforeLogout: Création d'une nouvelle consultation d'urgence");
        // Appel direct à l'API pour la création
        console.log("saveConversationBeforeLogout: Envoi d'une requête de création de consultation avec", 
          messagesToSend.length, "messages et token:", token.substring(0, 15) + "...");
        const response = await fetch(`${API_URL}/api/consultations`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`
          },
          body: JSON.stringify({
            title,
            type: chatMode,
            messages: messagesToSend
          }),
        });
        
        if (!response.ok) {
          const errorText = await response.text();
          console.error("saveConversationBeforeLogout: Erreur lors de la création d'une nouvelle consultation:", 
            response.status, errorText);
          return false;
        }
        
        const newConsultation = await response.json();
        console.log("saveConversationBeforeLogout: Nouvelle consultation créée avec succès avant déconnexion, ID:", 
          newConsultation.id);
        return true;
      }
    } catch (error) {
      console.error("saveConversationBeforeLogout: Erreur lors de la sauvegarde d'urgence:", error);
      return false;
    }
  };
  
  // Créer une nouvelle entrée d'historique contenant toute la session
  const createNewConsultation = async () => {
    if (!isAuthenticated) {
      console.log("createNewConsultation: Non authentifié, impossible de créer une entrée d'historique");
      return null;
    }
    
    // Vérifier si la session est valide pour la sauvegarde
    // Accepter les sessions avec au moins 4 messages (deux échanges user-bot complets)
    const hasUserMessage = messages.some(m => m.sender === "user");
    const hasBotMessage = messages.some(m => m.sender === "bot");
    
    if (messages.length < 4 || !hasUserMessage || !hasBotMessage) {
      console.log(`createNewConsultation: Impossible de créer une entrée d'historique: session avec seulement ${messages.length} messages (minimum 4 requis) ou échange incomplet`);
      return null;
    }
    
    // Générer un titre basé sur le premier message de l'utilisateur
    const firstUserMessage = messages.find(m => m.sender === "user");
    const title = firstUserMessage 
      ? firstUserMessage.content.substring(0, 50) + (firstUserMessage.content.length > 50 ? "..." : "") 
      : "Nouvelle session";
    
    try {
      console.log("createNewConsultation: Tentative de création d'une nouvelle entrée d'historique pour la session complète:", {
        title,
        type: chatMode,
        messagesCount: messages.length,
        token: authService.getToken()?.substring(0, 10) + "..."
      });
      
      // Créer des copies des messages sans références problématiques et avec tous les champs nécessaires
      const messagesToSend = messages.map(m => {
        // Si le message contient une recommandation, vérifier qu'elle est correctement formatée
        let processedRecommendation = undefined;
        if (m.recommendation) {
          try {
            // Faire une copie profonde de la recommandation
            processedRecommendation = JSON.parse(JSON.stringify(m.recommendation));
            
            // Vérifier et compléter chaque champ individuellement pour éviter les erreurs TypeScript
            // et garantir une restauration fidèle de la session
            if (!processedRecommendation.plant) {
              processedRecommendation.plant = "Plante non spécifiée";
              console.log(`Recommandation: champ 'plant' manquant, valeur par défaut ajoutée`);
            }
            if (!processedRecommendation.dosage) {
              processedRecommendation.dosage = "Dosage non spécifié";
              console.log(`Recommandation: champ 'dosage' manquant, valeur par défaut ajoutée`);
            }
            if (!processedRecommendation.prep) {
              processedRecommendation.prep = "Préparation non spécifiée";
              console.log(`Recommandation: champ 'prep' manquant, valeur par défaut ajoutée`);
            }
            if (!processedRecommendation.image_url) {
              processedRecommendation.image_url = "";
            }
            if (!processedRecommendation.explanation) {
              processedRecommendation.explanation = "";
              console.log(`Recommandation: champ 'explanation' manquant, valeur par défaut ajoutée`);
            }
            if (!processedRecommendation.contre_indications) {
              processedRecommendation.contre_indications = "Aucune contre-indication connue";
            }
            if (!processedRecommendation.partie_utilisee) {
              processedRecommendation.partie_utilisee = "Non spécifié";
            }
            if (!processedRecommendation.composants) {
              processedRecommendation.composants = "Non spécifié";
            }
            if (!processedRecommendation.nom_local) {
              processedRecommendation.nom_local = "";
            }
            
            console.log(`Recommandation du message traitée et complétée pour la sauvegarde:`, 
              processedRecommendation.plant);
          } catch (error) {
            console.error("Erreur lors du traitement de la recommandation:", error);
          }
        }
        
        return {
          content: m.content,
          sender: m.sender,
          recommendation: processedRecommendation
        };
      });
      
      console.log("createNewConsultation: Envoi de la requête au service...");
      const newConsultation = await consultationService.createConsultation({
        title,
        type: chatMode,
        messages: messagesToSend
      });
      
      if (newConsultation) {
        console.log("createNewConsultation: Nouvelle entrée d'historique créée avec succès:", {
          id: newConsultation.id,
          title: newConsultation.title,
          type: newConsultation.type,
          messageCount: newConsultation.messages?.length || messagesToSend.length
        });
        setCurrentConsultation(newConsultation);
        return newConsultation;
      } else {
        console.error("createNewConsultation: Échec de création de la consultation, aucun objet retourné");
      }
    } catch (error) {
      console.error("createNewConsultation: Erreur lors de la création de l'entrée d'historique:", error);
    }
    
    return null;
  };
  
  // Fonction améliorée pour sauvegarder les sessions de conversation complètes
  const saveConversation = async () => {
    console.log("Tentative de sauvegarde de session complète, authentifié:", isAuthenticated);
    
    if (!isAuthenticated) {
      console.log("Non authentifié, sauvegarde impossible");
      return false;
    }
    
    // Vérifier si la conversation est valide pour la sauvegarde
    const hasUserMessage = messages.some(m => m.sender === "user");
    const hasBotMessage = messages.some(m => m.sender === "bot");
    
    // Ne sauvegarder que les sessions avec au moins 4 messages (deux échanges utilisateur-bot)
    if (messages.length < 4 || !hasUserMessage || !hasBotMessage) {
      console.log(`Session ignorée car moins de 4 messages (${messages.length}) ou pas d'échange user-bot`);
      return false;
    }
    
    try {
      setIsLoading(true);
      
      // Générer un titre basé sur le premier message de l'utilisateur
      const firstUserMessage = messages.find(m => m.sender === "user");
      const title = firstUserMessage 
        ? firstUserMessage.content.substring(0, 50) + (firstUserMessage.content.length > 50 ? "..." : "") 
        : "Nouvelle session";
      
      // Si nous avons déjà une consultation, mettre à jour avec tous les nouveaux messages
      if (currentConsultation && currentConsultation.id) {
        console.log(`Mise à jour de la session historique existante ${currentConsultation.id}`);
        
        // Trouver les nouveaux messages qui n'ont pas encore été sauvegardés
        const existingMessageIds = new Set(
          (currentConsultation.messages || [])
            .filter(m => m.id)
            .map(m => m.id)
        );
        
        // Nouveaux messages à ajouter à la session (ceux qui n'ont pas d'ID dans existingMessageIds)
        const newMessages = messages
          .filter(m => !m.id || !existingMessageIds.has(m.id))
          .map(m => {
            // S'assurer que toutes les recommandations ont les champs nécessaires pour une restauration fidèle
            let processedRecommendation = undefined;
            if (m.recommendation) {
              try {
                // Faire une copie profonde de la recommandation
                processedRecommendation = JSON.parse(JSON.stringify(m.recommendation));
                
                // Vérifier et compléter les champs individuellement pour éviter les erreurs TypeScript
                if (!processedRecommendation.plant) {
                  processedRecommendation.plant = "Plante non spécifiée";
                }
                if (!processedRecommendation.dosage) {
                  processedRecommendation.dosage = "Dosage non spécifié";
                }
                if (!processedRecommendation.prep) {
                  processedRecommendation.prep = "Préparation non spécifiée";
                }
                if (!processedRecommendation.image_url) {
                  processedRecommendation.image_url = "";
                }
                if (!processedRecommendation.explanation) {
                  processedRecommendation.explanation = "";
                }
                if (!processedRecommendation.contre_indications) {
                  processedRecommendation.contre_indications = "Aucune contre-indication connue";
                }
                if (!processedRecommendation.partie_utilisee) {
                  processedRecommendation.partie_utilisee = "Non spécifié";
                }
                if (!processedRecommendation.composants) {
                  processedRecommendation.composants = "Non spécifié";
                }
                if (!processedRecommendation.nom_local) {
                  processedRecommendation.nom_local = "";
                }
              } catch (error) {
                console.error("Erreur lors du traitement de la recommandation:", error);
              }
            }
            
            return {
              content: m.content,
              sender: m.sender,
              recommendation: processedRecommendation
            };
          });
        
        if (newMessages.length > 0) {
          console.log(`Ajout de ${newMessages.length} nouveaux messages à la session historique ${currentConsultation.id}`);
          
          // Ajouter chaque nouveau message à la session existante
          let success = true;
          for (const message of newMessages) {
            try {
              await consultationService.addMessage(currentConsultation.id, message);
            } catch (error) {
              console.error("Erreur lors de l'ajout d'un message à la session:", error);
              success = false;
              break;
            }
          }
          
          // Mettre à jour les autres champs de la session si nécessaire
          if (success) {
            await consultationService.updateConsultation(currentConsultation.id, {
              title,
              type: chatMode
            });
            
            console.log(`Session historique ${currentConsultation.id} mise à jour avec succès`);
            return true;
          }
        } else {
          console.log("Aucun nouveau message à ajouter à la session historique");
          return true;
        }
      } else {
        // Créer une nouvelle entrée d'historique contenant toute la session
        console.log("Création d'une nouvelle entrée d'historique pour toute la session");
        const result = await createNewConsultation();
        return !!result;
      }
    } catch (error) {
      console.error("Erreur lors de la sauvegarde de la session complète:", error);
      return false;
    } finally {
      setIsLoading(false);
    }
    
    return false;
  }
  
  const handleLogin = () => {
    // La fermeture de la modale d'authentification est désormais gérée par AlertDialog lui-même via onOpenChange=onClose
    // On ouvre simplement la modale de connexion - le setTimeout est géré dans AuthRequiredModal
    setIsLoginModalOpen(true)
  }
  
  const handleLoginSuccess = () => {
    console.log("Connexion réussie - Message en attente:", pendingMessage)
    
    // L'utilisateur est maintenant connecté - forcer la mise à jour
    setIsAuthenticated(prev => {
      console.log("Mise à jour de isAuthenticated à true (état précédent:", prev, ")")
      return true
    })
    setIsLoginModalOpen(false)
    
    // L'utilisateur n'est plus dans le mode "continuer sans connexion"
    setUserChooseContinueWithoutLogin(false)
    
    // Sauvegarder la conversation actuelle maintenant que l'utilisateur est connecté
    if (messages.length > 0) {
      // Attendre que la modale soit fermée avant de sauvegarder
      setTimeout(() => {
        saveConversation()
        console.log("Conversation sauvegardée après connexion")
      }, 500)
    }
    
    // S'il y a un message en attente, l'envoyer après la connexion
    if (pendingMessage) {
      const savedMessage = pendingMessage
      setPendingMessage("")
      
      // Créer et envoyer directement le message utilisateur et sa réponse
      // Nous utilisons un délai pour s'assurer que isAuthenticated est bien pris en compte partout
      setTimeout(() => {
        // Maintenant que isAuthenticated est à true, créer le message utilisateur
        const userMessage: Message = {
          id: Date.now().toString(),
          content: savedMessage,
          sender: "user",
          timestamp: new Date(),
        }
        
        // Ajouter le message
        setMessages(prev => [...prev, userMessage])
        
        // Puis traiter la réponse
        processMessageResponse(savedMessage)
        
        console.log("Message envoyé après connexion:", savedMessage)
      }, 300)
    }
  }
  
  const handleContinueWithoutLogin = () => {
    // La fermeture de la modale est désormais gérée par le composant AlertDialog lui-même via onOpenChange
    // Ne pas appeler setIsAuthModalOpen(false) ici pour éviter la boucle infinie
    
    // Indiquer qu'on ne veut pas sauvegarder
    setPendingSaveConversation(false)
    
    // Marquer que l'utilisateur a choisi de continuer sans connexion
    setUserChooseContinueWithoutLogin(true)
    console.log("Utilisateur a choisi de continuer sans connexion")
    
    // Traiter le message en attente s'il y en a un
    if (pendingMessage) {
      const savedMessage = pendingMessage
      
      // Réinitialiser l'état du message en attente
      setPendingMessage("")
      
      // Utiliser un setTimeout pour éviter les mises à jour d'état multiples dans le même cycle de rendu
      setTimeout(() => {
        // Ajouter manuellement le message utilisateur
        const userMessage: Message = {
          id: Date.now().toString(),
          content: savedMessage,
          sender: "user",
          timestamp: new Date(),
        }
        
        setInputValue("") // Effacer le champ de saisie
        setMessages(prev => [...prev, userMessage]) // Ajouter le message au chat
        
        // Appeler la fonction qui gère la réponse du bot sans sauvegarde
        processMessageResponse(savedMessage)
      }, 100)
    } else {
      console.log("Conversation continue sans sauvegarde")
    }
  }

  const handleSendMessage = async (e?: React.FormEvent) => {
    // Empêcher le comportement par défaut du formulaire si l'événement est fourni
    if (e) e.preventDefault();
    
    if (!inputValue.trim()) return
    
    // Éviter les actions si nous sommes déjà en train de charger
    if (isLoading) return;
    
    // Sauvegarder le message courant avant tout traitement
    const currentMessage = inputValue;
    
    // Effacer immédiatement le champ de saisie pour une meilleure réactivité de l'interface
    setInputValue("");
    
    // Si l'utilisateur n'est pas connecté et n'a pas déjà choisi de continuer sans connexion
    if (!isAuthenticated && !userChooseContinueWithoutLogin) {
      // Stocker le message avant d'afficher la modale
      setPendingMessage(currentMessage);
      
      // Utiliser un setTimeout pour s'assurer que pendingMessage est bien défini avant d'ouvrir la modale
      setTimeout(() => {
        setIsAuthModalOpen(true);
      }, 10);
      return;
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      content: currentMessage,
      sender: "user",
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])    // Traiter la réponse au message
    await processMessageResponse(currentMessage)
    
    // La sauvegarde automatique se fait maintenant via un effet qui surveille les changements de messages
    // Cela évite les problèmes de synchronisation avec les mises à jour d'état asynchrones
  }

  // Fonction pour traiter la réponse à un message sans la logique de sauvegarde
  const processMessageResponse = async (messageText: string) => {
    // Si c'est en mode consultation, appeler l'API backend
    if (chatMode === "consultation") {
      setIsLoading(true);
      
      try {
        console.log("Envoi de la requête au backend avec les symptômes:", messageText);
        
        // Vérifier si la requête est vide
        if (!messageText.trim()) {
          throw new Error("Veuillez décrire vos symptômes avant de demander une consultation");
        }        // Utiliser l'URL configurée pour le backend
        const response = await fetch(`${BASE_URL}/recommend`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ 
            symptoms: messageText,
            attempt_count: attemptCount 
          }),
          // Ajouter mode CORS pour s'assurer que les requêtes sont bien envoyées
          mode: "cors",
          cache: "no-cache",
        });
        
        if (!response.ok) {
          const errorText = await response.text();
          console.error("Réponse du serveur non valide:", response.status, errorText);
          throw new Error(`Erreur: ${response.status} - ${errorText}`);
        }
        
        const recommendation: PlantRecommendation = await response.json();
        console.log("Réponse reçue du backend:", recommendation);
        
        // Vérifier si la réponse est valide et contient les données nécessaires
        if (!recommendation) {
          throw new Error("Réponse vide du serveur");
        }
        
        if (!recommendation.plant) {
          console.warn("⚠️ Aucune plante spécifiée dans la réponse");
          recommendation.plant = "plante médicinale";
        }
        
        if (!recommendation.explanation) {
          console.warn("⚠️ L'explication est vide ou manquante dans la réponse");
          // Créer une explication minimale pour éviter les erreurs d'affichage
          recommendation.explanation = `
          Diagnostic possible
          
          D'après vos symptômes, un remède à base de ${recommendation.plant} pourrait vous aider.
          
          Résumé de traitement
          
          Veuillez suivre les instructions de préparation et dosage indiquées ci-dessous.
          `;
        }
        
        // S'assurer que tous les champs requis sont présents pour une restauration future identique
        // Des valeurs par défaut significatives garantissent un affichage cohérent dans l'historique
        if (!recommendation.dosage) recommendation.dosage = "Dosage à déterminer selon le cas";
        if (!recommendation.prep) recommendation.prep = "Préparation à adapter selon les besoins";
        if (!recommendation.image_url) recommendation.image_url = "";
        if (!recommendation.explanation) recommendation.explanation = "Pas de détails disponibles";
        if (!recommendation.contre_indications) recommendation.contre_indications = "Consultez un professionnel de santé avant utilisation";
        if (!recommendation.partie_utilisee) recommendation.partie_utilisee = "Diverses parties de la plante";
        if (!recommendation.composants) recommendation.composants = "Composants actifs à déterminer";
        if (!recommendation.nom_local) recommendation.nom_local = recommendation.plant || "Nom local non disponible";
          console.log("Tous les champs requis ont été ajoutés à la recommandation pour garantir une restauration identique dans l'historique");
        
        // Gérer les indicateurs de fallback et incrémenter/réinitialiser le compteur de tentatives
        if (recommendation.needs_more_details) {
          // Première tentative sans correspondance - incrémenter pour la prochaine fois
          setAttemptCount(prev => prev + 1);
          console.log("Première tentative sans correspondance détectée, compteur incrémenté à:", attemptCount + 1);
        } else if (recommendation.requires_consultation) {
          // Deuxième tentative sans correspondance - réinitialiser le compteur pour une nouvelle conversation
          setAttemptCount(1);
          console.log("Deuxième tentative sans correspondance détectée, compteur réinitialisé à 1");
        } else {
          // Recommandation trouvée - réinitialiser le compteur pour une nouvelle série de tentatives
          setAttemptCount(1);
          console.log("Recommandation trouvée, compteur réinitialisé à 1");
        }
        
        const botResponse: Message = {
          id: (Date.now() + 1).toString(),
          content: `J'ai analysé vos symptômes et je vous recommande le remède suivant à base de **${recommendation.plant}**. Retrouvez ci-dessus la fiche détaillée avec préparation et dosage recommandés.`,
          sender: "bot",
          timestamp: new Date(),
          recommendation,};
        
        setMessages((prev) => [...prev, botResponse]);
        
        // La sauvegarde automatique est gérée dans handleSendMessage pour éviter les doublons
        // Plus besoin d'appeler saveConversation ici - la logique de sauvegarde unifiée 
        // est dans handleSendMessage
      } catch (error) {
        console.error("Erreur lors de l'appel à l'API:", error);
        
        const errorMessage: Message = {
          id: (Date.now() + 1).toString(),
          content: "Je suis désolé, une erreur est survenue lors de la recherche d'un remède adapté. Veuillez vérifier que le serveur backend est bien démarré ou essayez une description différente de vos symptômes.",
          sender: "bot",
          timestamp: new Date(),
        };
        
        setMessages((prev) => [...prev, errorMessage]);
      } finally {
        setIsLoading(false);
      }
    } else {
      // Mode discussion - appel à l'API de chat
      setIsLoading(true);
      
      try {        console.log("Envoi de la requête au backend en mode Discussion pour:", messageText);        // Appel à l'API /chat pour le mode discussion
        const response = await fetch(`${BASE_URL}/chat`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ message: messageText }), // Utiliser 'message' comme attendu par le backend
          mode: "cors",
          cache: "no-cache",
        });
        
        if (!response.ok) {
          const errorText = await response.text();
          console.error("Réponse du serveur non valide:", response.status, errorText);
          throw new Error(`Erreur: ${response.status} - ${errorText}`);
        }
        
        const data = await response.json();
        console.log("Réponse du backend (mode discussion):", data);
        
        if (!data.response) {
          console.warn("⚠️ Aucune réponse dans la donnée reçue");
        }
          const botResponse: Message = {
          id: (Date.now() + 1).toString(),
          content: data.response || `Merci pour votre question sur : "${messageText}". Je suis là pour discuter de phytothérapie africaine avec vous.`,
          sender: "bot",
          timestamp: new Date(),
        }
        
        setMessages((prev) => [...prev, botResponse]);
        
        // La sauvegarde automatique est gérée dans handleSendMessage pour éviter les doublons
        // Plus besoin d'appeler saveConversation ici - la logique de sauvegarde unifiée 
        // est dans handleSendMessage
      } catch (error) {
        console.error("Erreur lors de l'appel à l'API chat:", error);
        
        // Fallback en cas d'erreur
        const errorResponse: Message = {
          id: (Date.now() + 1).toString(),
          content: `Désolé, je n'ai pas pu traiter votre question : "${messageText}". Le serveur est-il bien démarré ? Vous pouvez réessayer ou passer en mode Consultation.`,
          sender: "bot",
          timestamp: new Date(),
        }
        
        setMessages((prev) => [...prev, errorResponse]);
      } finally {
        setIsLoading(false);
      }
    }
  }

  const handleVoiceInput = () => {
    setIsListening(!isListening)
    // Ici, vous pourriez intégrer une API de reconnaissance vocale
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault() // Empêcher le saut de ligne dans le textarea
      handleSendMessage() // Appeler la fonction avec l'événement
    }
  }

  // Fonction pour mettre à jour l'état d'authentification de manière cohérente
  const setIsAuthenticated = (value: boolean | ((prev: boolean) => boolean)) => {
    // Si la valeur est une fonction, l'appliquer à l'état actuel
    const newValue = typeof value === 'function' ? value(isAuthenticated) : value
    
    // Si une fonction de changement d'état est fournie par les props, l'appeler
    if (onAuthChange) {
      onAuthChange(newValue)
    }
    
    // Mettre également à jour l'état local
    setLocalIsAuthenticated(newValue)
    
    console.log("setIsAuthenticated appelé avec", newValue, "props handler:", !!onAuthChange)
  }

  // Fonction pour aider au débogage - à supprimer en production
  // Utiliser useRef pour suivre la valeur précédente et éviter les logs redondants
  const prevAuthState = React.useRef(isAuthenticated);
  const prevPropAuthState = React.useRef(propIsAuthenticated);
  
  React.useEffect(() => {
    // Ne logger que si l'état a réellement changé
    if (prevAuthState.current !== isAuthenticated || prevPropAuthState.current !== propIsAuthenticated) {
      console.log("État d'authentification mis à jour:", isAuthenticated, 
        "source:", propIsAuthenticated !== undefined ? "props" : "local");
      
      // Mettre à jour les références pour le prochain render
      prevAuthState.current = isAuthenticated;
      prevPropAuthState.current = propIsAuthenticated;
    }
  }, [isAuthenticated, propIsAuthenticated])
  // Effet pour charger une consultation spécifique si consultationId est fourni
  useEffect(() => {
    let isMounted = true;
    const loadConsultation = async () => {
      if (consultationId && isAuthenticated) {
        console.log(`Chargement de la conversation: ${consultationId}`);
        setIsLoading(true);
          try {
          // Charger uniquement depuis la table conversations unifiées (historique sauvegardé)
          console.log("Chargement de la conversation historique depuis la table conversations unifiées...");
          const unifiedConversation = await conversationUnifiedService.getConversationWithMessages(consultationId);
          
          if (unifiedConversation && unifiedConversation.messages && isMounted) {
            console.log(`Conversation historique récupérée: Type=${unifiedConversation.type}, ${unifiedConversation.messages.length} messages`);
            
            // Convertir les messages de la conversation unifiée au format attendu
            const formattedMessages = unifiedConversation.messages.map((msg, index) => ({
              id: msg.id || `msg-${index}`,
              content: msg.content,
              sender: msg.sender,
              timestamp: msg.timestamp ? new Date(msg.timestamp) : new Date(),
              recommendation: msg.recommendation
            }));
              if (isMounted) {
              setMessages(formattedMessages);
              setChatMode(unifiedConversation.chat_mode || "discussion");
              
              // Définir currentConsultation avec les données de la conversation historique
              // Cela permet à la sauvegarde automatique de fonctionner correctement
              setCurrentConsultation({
                id: consultationId,
                title: unifiedConversation.title || "Conversation historique",
                type: unifiedConversation.chat_mode || "discussion",
                messages: formattedMessages,
                created_at: unifiedConversation.created_at,
                updated_at: unifiedConversation.updated_at
              });
              
              // Marquer comme conversation historique pour éviter la recréation
              setIsHistoricalConsultation(true);
              console.log(`✅ Conversation historique ${consultationId} chargée avec succès - currentConsultation défini`);
            }} else {
            // Si la conversation n'existe pas dans l'historique, afficher un message d'erreur
            console.log("Conversation historique non trouvée dans la table unifiée");
            if (isMounted) {
              console.error("La conversation demandée n'existe pas dans l'historique");
            }
          }
        } catch (error) {
          console.error("Erreur lors du chargement de la conversation historique:", error);
        } finally {
          if (isMounted) {
            setIsLoading(false);
          }
        }
      }
    };
    
    loadConsultation();
    
    // Nettoyer l'effet lors du démontage
    return () => {
      isMounted = false;
    };
  }, [consultationId, isAuthenticated]);

  // Effet pour charger la conversation depuis les props (uniquement au montage initial)
  useEffect(() => {
    let isMounted = true;
    
    // Fonction asynchrone pour traiter le chargement
    const loadConversation = async () => {
      // Uniquement au chargement initial et si on n'a pas de consultationId
      if (currentConversation && !consultationId && messages.length === 0) {
        console.log("Chargement de la conversation précédente depuis les props:", currentConversation);
        
        // Si la conversation existe et contient des messages, les charger
        if (currentConversation.messages && currentConversation.messages.length > 0) {
          try {
            // Créer des copies profondes pour éviter les problèmes de référence
            // Et convertir les timestamps en objets Date
            const messagesCopy = currentConversation.messages.map((m: any) => ({
              id: m.id || Date.now().toString(),
              content: m.content,
              sender: m.sender,
              timestamp: m.timestamp ? new Date(m.timestamp) : new Date(),
              recommendation: m.recommendation
            }));
            
            if (isMounted) {
              setMessages(messagesCopy);
              
              // Si un mode est défini, l'utiliser
              if (currentConversation.mode) {
                setChatMode(currentConversation.mode);
              }
              
              // Si une consultation est associée, la définir
              if (currentConversation.consultation) {
                const consultationCopy = JSON.parse(JSON.stringify(currentConversation.consultation));
                setCurrentConsultation(consultationCopy);
                
                // Vérifier si la consultation existe déjà dans la base de données
                if (consultationCopy.id) {
                  // Marquer comme historique pour éviter une recréation
                  setIsHistoricalConsultation(true);
                  console.log("Conversation restaurée depuis une consultation existante:", consultationCopy.id);
                }
              }
            }
          } catch (error) {
            console.error("Erreur lors de la restauration de la conversation:", error);
          }
        }
      }
    };
    
    loadConversation();
    
    return () => {
      isMounted = false;
    };
    // Exécuter ce code uniquement au montage initial du composant
  }, []);
    // Fonction pour créer une nouvelle conversation
  const handleNewConversation = async () => {
    // Pour les conversations historiques : ne pas créer de nouvelle consultation, 
    // juste réinitialiser l'interface pour une nouvelle discussion
    if (currentConsultation?.id) {
      console.log(`Fin de la modification de la consultation ${currentConsultation.id}, démarrage d'une nouvelle conversation`);
      
      // Les nouveaux messages ont déjà été sauvegardés automatiquement lors de la conversation
      // Il n'y a donc rien à sauvegarder ici, juste réinitialiser l'interface
      
      // Réinitialiser l'interface pour une nouvelle conversation
      setMessages([]);
      setInputValue("");
      setChatMode("discussion");
      setCurrentConsultation(null); // Libérer la consultation historique
      setIsHistoricalConsultation(false);
      
      // Réinitialiser les autres états
      setUserChooseContinueWithoutLogin(false);
      setPendingSaveConversation(false);
      setPendingMessage("");
      
      // Notifier le composant parent
      if (onConversationChange) {
        setTimeout(() => {
          onConversationChange({
            messages: [],
            mode: "discussion",
            consultation: null
          });
        }, 100);
      }
      
      console.log("Interface réinitialisée pour une nouvelle conversation");
      return;
    }
    
    // Pour les nouvelles conversations (non historiques) : sauvegarder si nécessaire avant de réinitialiser
    const hasUserMessage = messages.some(m => m.sender === "user");
    const hasBotMessage = messages.some(m => m.sender === "bot");
    const isValidConversation = isAuthenticated && messages.length >= 4 && hasUserMessage && hasBotMessage;
    
    if (isValidConversation) {
      try {
        console.log("Sauvegarde de la session complète avant d'en créer une nouvelle");
        
        // Sauvegarder la conversation dans la table unifiée
        const conversationId = await saveUnifiedConversation(messages, chatMode);
        if (conversationId) {
          console.log(`Conversation sauvegardée avec succès dans la table unifiée, ID: ${conversationId}`);
        } else {
          console.warn("Échec de la sauvegarde unifiée, utilisation de la méthode traditionnelle");
          // Créer une nouvelle consultation contenant toute la session
          await createNewConsultation();
          console.log("Nouvelle session complète sauvegardée avec succès");
        }
      } catch (error) {
        console.error("Erreur lors de la sauvegarde de la session:", error);
      }
    } else if (messages.length > 0) {
      console.log("Session ignorée pour la sauvegarde car incomplète ou utilisateur non connecté");
    }
    
    // Réinitialiser tous les états pour une nouvelle conversation
    setMessages([]);
    setInputValue("");
    setChatMode("discussion");
    setCurrentConsultation(null);
    setIsHistoricalConsultation(false);
    
    // Réinitialiser également l'état de choix de l'utilisateur
    setUserChooseContinueWithoutLogin(false);
    setPendingSaveConversation(false);
    setPendingMessage("");
    
    // Notifier le composant parent du changement de conversation
    // Utiliser setTimeout pour éviter les mises à jour en cascade
    if (onConversationChange) {
      setTimeout(() => {
        onConversationChange({
          messages: [],
          mode: "discussion",
          consultation: null
        });
      }, 100);
    }
    
    console.log("Nouvelle conversation initiée");
  };

  // Fonction utilitaire pour formater les timestamps des messages en toute sécurité
  const formatTimestamp = (timestamp: Date | string | undefined): string => {
    if (!timestamp) return '';
    
    try {
      // Si c'est déjà un objet Date, utiliser directement toLocaleTimeString
      if (timestamp instanceof Date) {
        return timestamp.toLocaleString('fr-FR', {
          hour: '2-digit',
          minute: '2-digit'
        });
      }
      
      // Si c'est une chaîne de caractères, essayer de la convertir en Date
      if (typeof timestamp === 'string') {
        return new Date(timestamp).toLocaleString('fr-FR', {
          hour: '2-digit',
          minute: '2-digit'
        });
      }
      
      // Cas par défaut: renvoyer une chaîne vide
      return '';
    } catch (error) {
      console.error("Erreur lors du formatage du timestamp:", error);
      return '';
    }
  };

  // Effet pour mettre à jour la conversation dans le composant parent
  useEffect(() => {
    // Éviter les mises à jour lorsqu'on charge une conversation existante
    if (isHistoricalConsultation) return;
    
    // Utiliser un effet à retardement pour réduire la fréquence des mises à jour
    // et éviter les boucles de mise à jour
    const conversationUpdateTimer = setTimeout(() => {
      if (onConversationChange && messages.length > 0) {
        console.log("Mise à jour de la conversation dans le composant parent");
        
        // Créer une copie des messages en préservant les objets Date
        const messagesCopy = messages.map(m => ({
          ...m,
          // Assurer que timestamp est bien un objet Date
          timestamp: m.timestamp instanceof Date ? m.timestamp : new Date(m.timestamp || Date.now()),
          // S'assurer que la recommandation est bien copiée et non référencée
          recommendation: m.recommendation ? JSON.parse(JSON.stringify(m.recommendation)) : undefined
        }));
        
        // Copie profonde de la consultation pour éviter les problèmes de référence
        const consultationCopy = currentConsultation ? JSON.parse(JSON.stringify(currentConsultation)) : null;
        
        onConversationChange({
          messages: messagesCopy,
          mode: chatMode,
          consultation: consultationCopy
        });
      }
    }, 300); // Ajouter un délai pour réduire la fréquence des mises à jour
    
    // Nettoyer le timer lors du démontage du composant ou d'une nouvelle mise à jour
    return () => clearTimeout(conversationUpdateTimer);
  }, [messages.length, chatMode, currentConsultation?.id, onConversationChange, isHistoricalConsultation]);

  // Références pour suivre les changements d'authentification
  const prevAuthenticated = React.useRef(isAuthenticated);
  const prevPropAuthenticated = React.useRef(propIsAuthenticated);

  // Effet pour surveiller les changements d'authentification et réinitialiser si déconnexion
  useEffect(() => {
    // Détecter une déconnexion : soit par props, soit par état local
    if ((prevPropAuthenticated.current === true && propIsAuthenticated === false) || 
        (prevAuthenticated.current === true && isAuthenticated === false)) {
      console.log("Déconnexion détectée dans ChatInterface - Sauvegarde de la session complète et réinitialisation du chat");
      
      // Sauvegarder la conversation en cours avant de réinitialiser si elle est valide
      const hasUserMessage = messages.some(m => m.sender === "user");
      const hasBotMessage = messages.some(m => m.sender === "bot");
      const isValidConversation = prevAuthenticated.current && messages.length > 0 && hasUserMessage && hasBotMessage;
      
      if (isValidConversation) {
        // Utiliser une fonction IIFE asynchrone pour permettre l'await
        (async () => {
          try {
            console.log("Déconnexion - Sauvegarde de la session complète avec", messages.length, "messages");
            
            // IMPORTANT: Forcer la sauvegarde AVANT que le token ne soit invalidé
            // Récupérer le token actuel qui est encore valide
            const token = authService.getToken();
            if (!token) {
              console.log("Déconnexion - Pas de token valide, impossible de sauvegarder");
              return;
            }            // Si nous avons une consultation existante (historique modifié), 
            // les nouveaux messages ont déjà été sauvegardés automatiquement pendant la conversation
            if (currentConsultation?.id) {
              console.log(`Déconnexion - Consultation existante ${currentConsultation.id} déjà mise à jour automatiquement - AUCUNE nouvelle sauvegarde`);
              // Rien à faire : la sauvegarde s'est faite en temps réel lors de l'ajout de chaque message
              return; // Important : sortir immédiatement pour éviter toute création de doublon
            } 
            // Seulement si nous n'avons aucune consultation existante, créer une nouvelle consultation
            else if (messages.length >= 2) {
              console.log("Déconnexion - Création d'une nouvelle entrée d'historique pour la session en cours (aucune consultation existante)");
              
              // Utiliser directement l'API pour éviter les problèmes avec le service
              try {
                // Préparer les données de la consultation
                const firstUserMessage = messages.find(m => m.sender === "user");
                const title = firstUserMessage 
                  ? firstUserMessage.content.substring(0, 50) + (firstUserMessage.content.length > 50 ? "..." : "") 
                  : "Session sauvegardée à la déconnexion";
                
                // Préparer les messages
                const messagesToSend = messages.map(m => ({
                  content: m.content,
                  sender: m.sender,
                  recommendation: m.recommendation ? JSON.parse(JSON.stringify(m.recommendation)) : undefined
                }));                  // Envoi direct à l'API
                const response = await fetch(`${API_URL}/api/consultations`, {
                  method: "POST",
                  headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                  },
                  body: JSON.stringify({
                    title,
                    type: chatMode,
                    messages: messagesToSend
                  }),
                });
                  if (response.ok) {
                  const newConsultation = await response.json();
                  console.log("Déconnexion - Nouvelle session sauvegardée avec succès:", newConsultation.id);
                } else {
                  console.error("Déconnexion - Échec de la création de la consultation:", await response.text());
                }
              } catch (error) {
                console.error("Déconnexion - Erreur lors de la création de la consultation:", error);
              }
            } else {
              console.log("Session ignorée pour la sauvegarde car aucune consultation existante et conversation incomplète ou utilisateur non connecté");
            }
          } catch (error) {
            console.error("Déconnexion - Erreur lors de la sauvegarde de la session complète:", error);
          }
        })();
      } else {
        console.log("Déconnexion - Pas de session valide à sauvegarder");
      }
      
      // Réinitialiser les messages immédiatement
      setMessages([]);
      
      // Réinitialiser l'input
      setInputValue("");
      
      // Réinitialiser le mode de discussion
      setChatMode("discussion");
      
      // Réinitialiser la consultation actuelle
      setCurrentConsultation(null);
      
      // Réinitialiser l'état de consultation historique
      setIsHistoricalConsultation(false);
      
      // Réinitialiser l'état du choix utilisateur
      setUserChooseContinueWithoutLogin(false);
      setPendingSaveConversation(false);
      setPendingMessage("");
      
      // Notifier le composant parent
      if (onConversationChange) {
        onConversationChange({
          messages: [],
          mode: "discussion",
          consultation: null
        });
      }
      
      // Forcer la mise à jour de l'état local d'authentification
      setLocalIsAuthenticated(false);
    }
    
    // Mettre à jour les références pour le prochain render
    prevAuthenticated.current = isAuthenticated;
    prevPropAuthenticated.current = propIsAuthenticated;
  }, [propIsAuthenticated, isAuthenticated, onConversationChange]);

  // Effet pour sauvegarder automatiquement lors de la navigation (démontage du composant)
  useEffect(() => {
    // Fonction de nettoyage appelée lors du démontage du composant (navigation)
    return () => {
      // Sauvegarder automatiquement si nous avons une consultation existante avec des nouveaux messages
      if (currentConsultation?.id && messages.length > 0 && isAuthenticated) {
        console.log("Navigation détectée - Sauvegarde automatique des derniers messages");
        
        // Sauvegarder de manière asynchrone les derniers messages non sauvegardés
        // Note: Ce sera exécuté de manière asynchrone, les messages seront sauvegardés
        (async () => {
          try {
            // Identifier les nouveaux messages qui pourraient ne pas être sauvegardés
            const existingMessageIds = new Set(
              (currentConsultation.messages || [])
                .filter(m => m.id)
                .map(m => m.id?.toString())
            );
            
            // Trouver les messages récents qui ne sont pas encore sauvegardés
            const recentMessages = messages.slice(-2).filter(m => !existingMessageIds.has(m.id?.toString()));
            
            if (recentMessages.length > 0) {
              console.log(`Navigation - Sauvegarde de ${recentMessages.length} messages récents`);
                // Sauvegarder chaque message récent
              for (const message of recentMessages) {
                try {
                  // Utiliser l'API conversations unifiées au lieu de l'API consultations                  console.log(`Navigation - Sauvegarde du message ${message.sender} dans la conversation unifiée ${currentConsultation.id}`);
                  
                  const response = await fetch(`${API_URL}/api/conversations/${currentConsultation.id}/messages`, {
                    method: "POST",
                    headers: {
                      "Content-Type": "application/json",
                      "Authorization": `Bearer ${authService.getToken()}`
                    },
                    body: JSON.stringify({
                      content: message.content,
                      sender: message.sender,
                      recommendation: message.recommendation
                    })
                  });
                  
                  if (!response.ok) {
                    throw new Error(`Erreur HTTP: ${response.status}`);
                  }
                } catch (error) {
                  console.error("Navigation - Erreur lors de la sauvegarde d'un message:", error);
                }
              }
              console.log("Navigation - Messages sauvegardés avec succès");
            }
          } catch (error) {
            console.error("Navigation - Erreur lors de la sauvegarde automatique:", error);
          }
        })();
      }
    };
  }, [currentConsultation?.id, messages, isAuthenticated]); // Dépendances pour capturer l'état actuel

  return (
    <div className="space-y-6">
      {onBack && (
        <div className="flex items-center justify-between gap-4 mb-6">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm" onClick={onBack} className="text-emerald-700 hover:text-emerald-800">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Retour
            </Button>
            <div>
              <h2 className="text-2xl font-bold text-emerald-800">Assistant aiBotanik</h2>
              {isHistoricalConsultation && currentConsultation && (
                <p className="text-sm text-emerald-600 mt-1">
                  Conversation reprise du {new Date(currentConsultation.date || Date.now()).toLocaleDateString('fr-FR')}
                </p>
              )}
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            {/* Bouton de connexion */}
            {!isAuthenticated && (
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => setIsLoginModalOpen(true)} 
                className="text-emerald-700 border-emerald-200 hover:bg-emerald-50"
              >
                <LogIn className="h-4 w-4 mr-2" />
                Se connecter
              </Button>
            )}
          </div>
        </div>
      )}

      <Card className="border-emerald-100">
        <CardContent className="p-6">
          {/* Zone de messages */}
          <div className="min-h-[300px] max-h-[500px] md:min-h-[400px] md:max-h-[600px] overflow-y-auto mb-6 space-y-4">
            {isLoading && (
              <div className="absolute inset-0 bg-white/50 flex items-center justify-center z-20">
                <div className="flex flex-col items-center gap-3 bg-white p-6 rounded-xl shadow-md">
                  <Loader2 className="h-8 w-8 text-emerald-600 animate-spin" />
                  <p className="text-emerald-800">Recherche de remèdes naturels...</p>
                </div>
              </div>
            )}
            
            {messages.length === 0 ? (
              <div className="space-y-6">
                <div className="text-center">
                  <div className="w-20 h-20 bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Bot className="h-10 w-10 text-white" />
                  </div>
                  <h3 className="text-xl font-semibold text-emerald-800 mb-2">Bienvenue sur aiBotanik</h3>
                </div>
                <div className="bg-gradient-to-r from-emerald-50 to-amber-50 rounded-xl p-6 border border-emerald-100">
                  <p className="text-emerald-800 leading-relaxed text-center">{welcomeText}</p>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div className="bg-white rounded-lg p-4 border border-emerald-100">
                    <h4 className="font-medium text-emerald-800 mb-2">💡 Exemples de questions</h4>
                    <ul className="text-sm text-gray-600 space-y-1">
                      <li>• "J'ai mal à la tête depuis 2 jours"</li>
                      <li>• "Quels remèdes pour la toux ?"</li>
                      <li>• "Plantes contre l'insomnie"</li>
                    </ul>
                  </div>
                  <div className="bg-white rounded-lg p-4 border border-amber-100">
                    <h4 className="font-medium text-amber-800 mb-2">🌿 Je peux vous aider avec</h4>
                    <ul className="text-sm text-gray-600 space-y-1">
                      <li>• Remèdes traditionnels</li>
                      <li>• Dosages et préparations</li>
                      <li>• Conseils de prévention</li>
                    </ul>
                  </div>
                </div>
              </div>
            ) : (
              <div className="space-y-8">
                {messages.map((message, index) => {
                  // Vérifier et debugger les messages avec recommandations
                  if (message.recommendation) {
                    console.log(`Affichage du message ${message.id} avec recommandation:`, 
                      typeof message.recommendation === 'object' ? message.recommendation.plant : typeof message.recommendation);
                  }
                  
                  // Valider que la recommendation est bien un objet avant affichage
                  const hasValidRecommendation = message.recommendation && 
                    typeof message.recommendation === 'object' &&
                    message.recommendation !== null;
                  
                  if (message.recommendation && !hasValidRecommendation) {
                    console.error(`Message ${message.id} contient une recommandation invalide:`, 
                      typeof message.recommendation);
                  }
                  
                  return (
                    <React.Fragment key={message.id}>
                      {/* Afficher la recommandation seulement pour les messages du bot qui ont une recommendation valide */}
                      {message.sender === "bot" && hasValidRecommendation && (
                        <div className="mb-8 mt-4">
                          <PlantRecommendationCard recommendation={message.recommendation as PlantRecommendation} />
                        </div>
                      )}
                      <div
                        className={`flex items-start gap-3 ${message.sender === "user" ? "flex-row-reverse" : ""}`}
                      >
                        <div
                          className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                            message.sender === "user" ? "bg-blue-100" : "bg-emerald-100"
                          }`}
                        >
                          {message.sender === "user" ? (
                            <User className="h-4 w-4 text-blue-600" />
                          ) : (
                            <Bot className="h-4 w-4 text-emerald-600" />
                          )}
                        </div>
                        <div
                          className={`rounded-lg p-4 max-w-[80%] ${
                            message.sender === "user" ? "bg-blue-50 text-blue-800" : "bg-emerald-50 text-emerald-800"
                          }`}
                        >
                          <p className="whitespace-pre-line">{message.content}</p>
                          <span className="text-xs opacity-60 mt-2 block">{formatTimestamp(message.timestamp)}</span>
                          
                          {/* Message d'erreur si la recommandation est invalide mais censée être affichée */}
                          {message.sender === "bot" && message.recommendation && !hasValidRecommendation && (
                            <div className="mt-2 p-2 bg-amber-50 border border-amber-200 rounded text-amber-700 text-sm">
                              ⚠️ Cette réponse contient une recommandation de plante qui ne peut pas être affichée correctement.
                            </div>
                          )}
                        </div>
                      </div>
                    </React.Fragment>
                  );
                })}
              </div>
            )}
          </div>

          {/* Zone de saisie */}
          <div className="flex justify-center">
            <div className="w-full max-w-4xl">
              {/* Utiliser un formulaire pour éviter les comportements de navigation par défaut */}
              <form onSubmit={handleSendMessage} className="flex gap-2 items-end">
                <div className="flex-1 relative">
                  <div className="relative">                    {/* Boutons de mode intégrés dans le textarea */}
                    <div className="absolute left-2 top-2 flex items-center gap-1 z-10">
                      <button
                        type="button" /* Ajouter type="button" pour éviter la soumission du formulaire */
                        onClick={() => setChatMode("discussion")}
                        className={`flex items-center gap-1 px-1.5 py-0.5 rounded-md text-xs font-medium transition-all ${
                          chatMode === "discussion"
                            ? "bg-emerald-500 text-white shadow-sm"
                            : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                        }`}
                      >
                        <MessageCircle className="h-3 w-3" />
                        Discussion
                      </button>
                      <button
                        type="button" /* Ajouter type="button" pour éviter la soumission du formulaire */
                        onClick={() => setChatMode("consultation")}
                        className={`flex items-center gap-1 px-1.5 py-0.5 rounded-md text-xs font-medium transition-all ${
                          chatMode === "consultation"
                            ? "bg-blue-500 text-white shadow-sm"
                            : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                        }`}
                      >
                        <Stethoscope className="h-3 w-3" />
                        Consultation
                      </button>
                    </div><Textarea
                      value={inputValue}
                      onChange={(e) => setInputValue(e.target.value)}
                      onKeyPress={handleKeyPress}
                      placeholder={
                        chatMode === "discussion"
                          ? "Posez votre question sur la phytothérapie..."
                          : "Décrivez vos symptômes pour une consultation..."
                      }
                      className="w-full min-h-[75px] pl-4 pr-9 pt-9 pb-3 resize-none border-emerald-200 focus:border-emerald-400 rounded-2xl"
                    />                    <Button
                      type="button" /* Ajouter type="button" pour éviter la soumission du formulaire */
                      size="sm"
                      variant="ghost"
                      className={`absolute right-2 bottom-1 ${isListening ? "text-red-500" : "text-emerald-600"}`}
                      onClick={handleVoiceInput}
                    >
                      <Mic className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
                <Button
                  type="submit" /* Spécifier qu'il s'agit d'un bouton de soumission */
                  disabled={!inputValue.trim() || isLoading}
                  className="bg-emerald-600 hover:bg-emerald-700 px-4 rounded-2xl h-[40px]"
                >
                  {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                </Button>
                
                {/* Bouton pour nouvelle conversation - toujours visible à côté du bouton d'envoi */}
                <Button
                  type="button"
                  onClick={handleNewConversation}
                  title="Nouvelle conversation"
                  className="bg-amber-500 hover:bg-amber-600 px-3 rounded-2xl h-[40px]"
                >
                  <PlusCircle className="h-4 w-4" />
                </Button>
              </form>
            </div>
          </div>
        </CardContent>
      </Card>
      
      {/* Modal d'authentification requise */}
      <AuthRequiredModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        onLogin={handleLogin}
        onContinueWithoutLogin={handleContinueWithoutLogin}
      />
      
      {/* Modal de connexion */}
      <LoginModal
        open={isLoginModalOpen}
        onOpenChange={setIsLoginModalOpen}
        onLoginSuccess={handleLoginSuccess}
      />
    </div>
  )
}
