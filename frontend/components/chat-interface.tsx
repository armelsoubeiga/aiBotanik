"use client"

import React, { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { Mic, Send, ArrowLeft, Bot, User, MessageCircle, Stethoscope, Loader2 } from "lucide-react"
import { PlantRecommendationCard, PlantRecommendation } from "./plant-recommendation"

interface ChatInterfaceProps {
  onBack?: () => void
  onStartChat?: () => void
  isWelcome?: boolean
}

interface Message {
  id: string
  content: string
  sender: "user" | "bot"
  timestamp: Date
  recommendation?: PlantRecommendation
}

export function ChatInterface({ onBack, onStartChat, isWelcome = false }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState("")
  const [isListening, setIsListening] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  // Définir le mode discussion comme mode par défaut
  const [chatMode, setChatMode] = useState<"discussion" | "consultation">("discussion")

  const welcomeText = `Bonjour ! Je suis aiBotanik, votre assistant spécialisé en phytothérapie africaine.

Décrivez vos symptômes et je vous aiderai à trouver des remèdes naturels adaptés.

Comment puis-je vous aider ?`

  const handleSendMessage = async (e?: React.FormEvent) => {
    // Empêcher le comportement par défaut du formulaire si l'événement est fourni
    if (e) e.preventDefault();
    
    if (!inputValue.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputValue,
      sender: "user",
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInputValue("")

    // Désactivation complète de la redirection pour tous les modes
    // Nous préférons traiter les messages directement dans cette page
    // Commenté pour éviter la redirection vers une nouvelle page
    // if (isWelcome && onStartChat) {
    //   onStartChat()
    // }

    // Si c'est en mode consultation, appeler l'API backend
    if (chatMode === "consultation") {
      setIsLoading(true);
      
      try {
        console.log("Envoi de la requête au backend avec les symptômes:", inputValue);
        
        // Vérifier si la requête est vide
        if (!inputValue.trim()) {
          throw new Error("Veuillez décrire vos symptômes avant de demander une consultation");
        }
        
        // Utiliser une URL absolue pour le backend
        const response = await fetch("http://localhost:8000/recommend", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ symptoms: inputValue }),
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
        
        const botResponse: Message = {
          id: (Date.now() + 1).toString(),
          content: `J'ai analysé vos symptômes et je vous recommande le remède suivant à base de **${recommendation.plant}**. Retrouvez ci-dessus la fiche détaillée avec préparation et dosage recommandés.`,
          sender: "bot",
          timestamp: new Date(),
          recommendation,
        };
        
        setMessages((prev) => [...prev, botResponse]);
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
      
      try {
        console.log("Envoi de la requête au backend en mode Discussion pour:", inputValue);
        
        // Appel à l'API /chat pour le mode discussion
        const response = await fetch("http://localhost:8000/chat", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ symptoms: inputValue }), // Réutilise la même structure de requête pour simplifier
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
          content: data.response || `Merci pour votre question sur : "${inputValue}". Je suis là pour discuter de phytothérapie africaine avec vous.`,
          sender: "bot",
          timestamp: new Date(),
        }
        
        setMessages((prev) => [...prev, botResponse]);
      } catch (error) {
        console.error("Erreur lors de l'appel à l'API chat:", error);
        
        // Fallback en cas d'erreur
        const errorResponse: Message = {
          id: (Date.now() + 1).toString(),
          content: `Désolé, je n'ai pas pu traiter votre question : "${inputValue}". Le serveur est-il bien démarré ? Vous pouvez réessayer ou passer en mode Consultation.`,
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

  return (
    <div className="space-y-6">
      {onBack && (
        <div className="flex items-center gap-4 mb-6">
          <Button variant="ghost" size="sm" onClick={onBack} className="text-emerald-700 hover:text-emerald-800">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Retour
          </Button>
          <h2 className="text-2xl font-bold text-emerald-800">Assistant aiBotanik</h2>
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
                {messages.map((message, index) => (
                  <React.Fragment key={message.id}>
                    {message.recommendation && (
                      <div className="mb-8 mt-4">
                        <PlantRecommendationCard recommendation={message.recommendation} />
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
                        <span className="text-xs opacity-60 mt-2 block">{message.timestamp.toLocaleTimeString()}</span>
                      </div>
                    </div>
                  </React.Fragment>
                ))}
              </div>
            )}
          </div>

          {/* Zone de saisie */}
          <div className="flex justify-center">
            <div className="w-full max-w-4xl">
              {/* Utiliser un formulaire pour éviter les comportements de navigation par défaut */}
              <form onSubmit={handleSendMessage} className="flex gap-2 items-end">
                <div className="flex-1 relative">
                  <div className="relative">
                    {/* Boutons de mode intégrés dans le textarea */}
                    <div className="absolute left-3 top-3 flex items-center gap-2 z-10">
                      <button
                        type="button" /* Ajouter type="button" pour éviter la soumission du formulaire */
                        onClick={() => setChatMode("discussion")}
                        className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium transition-all ${
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
                        className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium transition-all ${
                          chatMode === "consultation"
                            ? "bg-blue-500 text-white shadow-sm"
                            : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                        }`}
                      >
                        <Stethoscope className="h-3 w-3" />
                        Consultation
                      </button>
                    </div>

                    <Textarea
                      value={inputValue}
                      onChange={(e) => setInputValue(e.target.value)}
                      onKeyPress={handleKeyPress}
                      placeholder={
                        chatMode === "discussion"
                          ? "Posez votre question sur la phytothérapie..."
                          : "Décrivez vos symptômes pour une consultation..."
                      }
                      className="min-h-[60px] pl-56 pr-12 pt-12 pb-3 resize-none border-emerald-200 focus:border-emerald-400 rounded-2xl"
                    />

                    <Button
                      type="button" /* Ajouter type="button" pour éviter la soumission du formulaire */
                      size="sm"
                      variant="ghost"
                      className={`absolute right-12 bottom-2 ${isListening ? "text-red-500" : "text-emerald-600"}`}
                      onClick={handleVoiceInput}
                    >
                      <Mic className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
                <Button
                  type="submit" /* Spécifier qu'il s'agit d'un bouton de soumission */
                  disabled={!inputValue.trim() || isLoading}
                  className="bg-emerald-600 hover:bg-emerald-700 px-4 rounded-2xl h-[60px]"
                >
                  {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                </Button>
              </form>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
