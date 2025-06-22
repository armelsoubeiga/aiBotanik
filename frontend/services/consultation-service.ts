"use client";

import { authService } from "./auth-service";
import { API_URL } from '@/lib/config';

export interface Message {
  id?: string;
  content: string;
  sender: "user" | "bot";
  timestamp?: Date;
  recommendation?: any;
}

export interface Consultation {
  id?: string;
  title: string;
  type: "discussion" | "consultation";
  date?: string;
  created_at?: string;  // Ajout de created_at
  updated_at?: string;  // Ajout de updated_at
  summary?: string;
  messages?: Message[];
  messages_count?: number;  user_id?: string;     // Ajout de user_id
}

export class ConsultationService {
  private static instance: ConsultationService;

  public static getInstance(): ConsultationService {
    if (!ConsultationService.instance) {
      ConsultationService.instance = new ConsultationService();
    }
    return ConsultationService.instance;
  }

  // Créer une nouvelle consultation
  public async createConsultation(consultation: Consultation): Promise<Consultation | null> {
    if (!authService.isAuthenticated()) {
      console.error("Utilisateur non authentifié");
      return null;
    }

    try {
      const token = authService.getToken();      console.log("Token utilisé pour l'API:", token);
      
      const response = await fetch(`${API_URL}/api/consultations`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify(consultation),
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error("Erreur lors de la création de la consultation:", response.status, errorText);
        throw new Error(`Erreur ${response.status}: ${errorText}`);
      }

      const data = await response.json();
      console.log("Consultation créée avec succès:", data);
      return data;
    } catch (error) {
      console.error("Erreur lors de la création de la consultation:", error);
      return null;
    }
  }  // Récupérer toutes les consultations
  public async getConsultations(): Promise<Consultation[]> {
    if (!authService.isAuthenticated()) {
      console.log("getConsultations: Utilisateur non authentifié");
      return [];
    }

    try {
      const token = authService.getToken();      console.log("getConsultations: Récupération des consultations avec token", token?.substring(0, 15) + "...");
      
      const response = await fetch(`${API_URL}/api/consultations`, {
        method: "GET",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json",
          "Accept": "application/json"
        },
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error("getConsultations: Réponse non valide:", response.status, errorText);
        throw new Error(`Erreur ${response.status}: ${errorText}`);
      }

      const data = await response.json();
      console.log(`getConsultations: ${data.length} consultations récupérées avec succès`);
      
      // Vérifier les consultations reçues pour le débogage
      if (data.length > 0) {
        console.log("Exemple de consultation reçue:", {
          id: data[0].id,
          title: data[0].title,
          messages_count: data[0].messages_count,
          date: data[0].created_at || data[0].date
        });
      } else {
        console.warn("getConsultations: Aucune consultation trouvée dans la base de données");
      }
      
      return data;
    } catch (error) {
      console.error("getConsultations: Erreur lors de la récupération des consultations:", error);
      return [];
    }
  }
  // Récupérer une consultation par son ID
  public async getConsultation(id: string): Promise<Consultation | null> {
    if (!authService.isAuthenticated()) {
      console.error("Tentative de récupérer une consultation sans être authentifié");
      return null;
    }

    try {
      const token = authService.getToken();
      
      if (!token) {
        console.error("Pas de token disponible pour récupérer la consultation");
        return null;
      }
        console.log(`Récupération de la consultation ${id} avec token ${token.substring(0, 10)}...`);
        const response = await fetch(`${API_URL}/api/consultations/${id}`, {
        headers: {
          "Authorization": `Bearer ${token}`
        },
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error(`Erreur ${response.status} lors de la récupération de la consultation:`, errorText);
        throw new Error(`Erreur ${response.status}: ${errorText}`);
      }      const consultation = await response.json();
      console.log(`Consultation ${id} récupérée avec succès:`, consultation);
        // Vérification et traitement des messages pour s'assurer que les recommandations sont correctement formatées
      if (consultation.messages && Array.isArray(consultation.messages)) {
        consultation.messages = consultation.messages.map((message: any) => {
          if (message.recommendation) {
            try {              // Vérifier si la recommandation a besoin d'être désérialisée
              if (typeof message.recommendation === 'string') {
                console.log(`Message ${message.id}: désérialisation de la recommendation (string → object)`);
                try {
                  message.recommendation = JSON.parse(message.recommendation);
                } catch (parseError) {
                  console.error(`Erreur de parsing JSON pour la recommendation du message ${message.id}:`, parseError);
                  // Laisser la recommandation telle quelle si elle ne peut pas être parsée
                }
              }
              
              // Vérifier la validité de l'objet recommendation et compléter les champs manquants
              if (message.recommendation && typeof message.recommendation === 'object') {
                // Assurer que tous les champs requis par PlantRecommendation sont présents
                const requiredFields = {
                  plant: "Plante non spécifiée",
                  dosage: "Dosage non spécifié",
                  prep: "Préparation non spécifiée",
                  image_url: "",
                  explanation: "",
                  contre_indications: "Aucune contre-indication connue",
                  partie_utilisee: "Non spécifié",
                  composants: "Non spécifié",
                  nom_local: ""
                };
                
                // Remplir les champs manquants avec des valeurs par défaut
                for (const [field, defaultValue] of Object.entries(requiredFields)) {
                  if (!message.recommendation[field]) {
                    message.recommendation[field] = defaultValue;
                    console.warn(`Message ${message.id}: champ '${field}' manquant dans recommendation, valeur par défaut ajoutée`);
                  }
                }
                
                console.log(`Message ${message.id}: recommendation traitée correctement:`, 
                  message.recommendation.plant || "nom de plante inconnu");
              } else {
                console.warn(`Message ${message.id}: recommendation dans un format incorrect:`, 
                  typeof message.recommendation);
              }
            } catch (error) {
              console.error(`Erreur lors du traitement de la recommendation du message ${message.id}:`, error);
            }
          }
          return message;
        });
      }
      
      return consultation;
    } catch (error) {
      console.error(`Erreur lors de la récupération de la consultation ${id}:`, error);
      return null;
    }
  }
  // Ajouter un message à une consultation
  public async addMessage(consultationId: string, message: Message): Promise<boolean> {
    if (!authService.isAuthenticated()) {
      return false;
    }

    try {
      const token = authService.getToken();
        // Traiter la recommandation si elle existe
      let processedMessage = {...message};      if (processedMessage.recommendation) {
        try {
          // S'assurer que la recommandation est bien sérialisée pour le transport
          console.log("Message avec recommandation détecté:", 
            typeof processedMessage.recommendation === 'object' ? 
            processedMessage.recommendation.plant : typeof processedMessage.recommendation);
          
          // Cas où la recommandation est déjà une chaîne
          if (typeof processedMessage.recommendation === 'string') {
            try {
              // Tenter de vérifier si c'est du JSON valide et le transformer en objet
              const parsed = JSON.parse(processedMessage.recommendation);
              processedMessage.recommendation = parsed;
              console.log("Recommandation désérialisée de chaîne JSON à objet");
            } catch(e) {
              console.warn("La recommandation est une chaîne mais pas au format JSON valide:", e);
              // On laisse sous forme de chaîne et on s'attend à ce que le backend gère l'erreur
            }
          } 
          
          // Cas où la recommandation est un objet (le cas normal ou après désérialisation)
          if (typeof processedMessage.recommendation === 'object' && processedMessage.recommendation !== null) {
            // Faire une copie profonde pour éviter de modifier l'original
            const recommendationCopy = JSON.parse(JSON.stringify(processedMessage.recommendation));
            
            // Assurer que tous les champs requis par PlantRecommendation sont présents
            const requiredFields = {
              plant: "Plante non spécifiée",
              dosage: "Dosage non spécifié",
              prep: "Préparation non spécifiée",
              image_url: "",
              explanation: "",
              contre_indications: "Aucune contre-indication connue", 
              partie_utilisee: "Non spécifié",
              composants: "Non spécifié",
              nom_local: ""
            };
            
            // Remplir les champs manquants avec des valeurs par défaut
            for (const [field, defaultValue] of Object.entries(requiredFields)) {
              if (!recommendationCopy[field]) {
                recommendationCopy[field] = defaultValue;
                console.warn(`Champ '${field}' manquant dans la recommandation, valeur par défaut ajoutée`);
              }
            }
            
            processedMessage.recommendation = recommendationCopy;
            console.log("Recommandation complétée avec succès pour la plante:", recommendationCopy.plant);
          }
          // Cas où la recommandation n'est pas un format valide après traitement
          else if (typeof processedMessage.recommendation !== 'string') {
            console.error("Format de recommandation non géré:", typeof processedMessage.recommendation);
            // Créer un objet complet pour éviter les erreurs
            processedMessage.recommendation = {
              plant: "Plante non spécifiée",
              explanation: "Détails non disponibles",
              dosage: "Non spécifié",
              prep: "Non spécifié",
              image_url: "",
              contre_indications: "Aucune contre-indication connue",
              partie_utilisee: "Non spécifié",
              composants: "Non spécifié",
              nom_local: ""
            };
          }
        } catch (error) {
          console.error("Erreur lors du traitement de la recommandation:", error);
          // Au lieu de supprimer, créer un objet minimal pour garantir l'affichage
          processedMessage.recommendation = {
            plant: "Plante non spécifiée",
            explanation: "Une erreur est survenue lors du traitement des détails",
            dosage: "Non spécifié",
            prep: "Non spécifié",
            image_url: "",
            contre_indications: "Consulter un professionnel de santé",
            partie_utilisee: "Non spécifié", 
            composants: "Non spécifié",
            nom_local: ""
          };
        }
      }
        // Préparation du message avec consultation_id, nécessaire pour le backend
      // S'assurer que la recommendation est correctement sérialisée si présente
      const messageToSend = {
        ...processedMessage,
        consultation_id: consultationId,  // Ajout du consultation_id requis par l'API
        // Convertir explicitement l'objet recommendation en JSON string si présent
        recommendation: processedMessage.recommendation ? 
          typeof processedMessage.recommendation === 'string' ? 
            processedMessage.recommendation : 
            JSON.stringify(processedMessage.recommendation) 
          : undefined
      };
        console.log(`Envoi d'un message à la consultation ${consultationId}:`, messageToSend);
      
      const response = await fetch(`${API_URL}/api/consultations/${consultationId}/messages`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify(messageToSend),
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error(`Erreur ${response.status} lors de l'ajout du message:`, errorText);
        throw new Error(`Erreur ${response.status}: ${errorText}`);
      }

      return true;
    } catch (error) {
      console.error(`Erreur lors de l'ajout du message à la consultation ${consultationId}:`, error);
      return false;
    }
  }
  // Supprimer une consultation
  public async deleteConsultation(consultationId: string): Promise<boolean> {
    if (!authService.isAuthenticated()) {
      return false;
    }    try {
      const token = authService.getToken();
      
      const response = await fetch(`${API_URL}/api/consultations/${consultationId}`, {
        method: "DELETE",
        headers: {
          "Authorization": `Bearer ${token}`
        },
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error(`Erreur lors de la suppression de la consultation ${consultationId}:`, response.status, errorText);
        throw new Error(`Erreur ${response.status}: ${errorText}`);
      }

      return true;
    } catch (error) {
      console.error(`Erreur lors de la suppression de la consultation ${consultationId}:`, error);
      return false;
    }
  }

  // Mettre à jour une consultation existante
  public async updateConsultation(consultationId: string, data: Partial<Consultation>): Promise<boolean> {
    if (!authService.isAuthenticated()) {
      return false;
    }

    try {
      const token = authService.getToken();
        const response = await fetch(`${API_URL}/api/consultations/${consultationId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error(`Erreur ${response.status}`);
      }

      return true;
    } catch (error) {
      console.error(`Erreur lors de la mise à jour de la consultation ${consultationId}:`, error);
      return false;
    }
  }
}

// Exporter une instance par défaut du service
export const consultationService = ConsultationService.getInstance();
