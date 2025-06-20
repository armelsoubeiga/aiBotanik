"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ArrowLeft, MessageCircle, Calendar, ChevronLeft, ChevronRight, Bot, User, Stethoscope } from "lucide-react"
import { conversationUnifiedService, ConversationHistoryItem } from "@/services/conversation-unified-service"

interface UnifiedConversationHistoryProps {
  onConversationSelect: (id: string) => void
  onBack: () => void
  isAuthenticated: boolean
}

export function UnifiedConversationHistory({ onConversationSelect, onBack, isAuthenticated }: UnifiedConversationHistoryProps) {
  const [conversations, setConversations] = useState<ConversationHistoryItem[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const itemsPerPage = 6 // 6 conversations par page

  // Charger les conversations à l'initialisation et quand l'utilisateur est authentifié
  useEffect(() => {
    if (isAuthenticated) {
      loadConversations()
    } else {
      setConversations([])
    }
  }, [isAuthenticated])

  // Fonction pour charger les conversations
  const loadConversations = async () => {
    if (!isAuthenticated) {
      console.log("loadConversations: Utilisateur non authentifié")
      return
    }

    try {
      setIsLoading(true)
      console.log("Chargement de l'historique des conversations unifiées...")
      
      const history = await conversationUnifiedService.getConversationHistory()
      
      console.log(`${history.length} conversations chargées depuis la table unifiée`)
      setConversations(history)
      
      // Réinitialiser la pagination si nécessaire
      const maxPage = Math.max(1, Math.ceil(history.length / itemsPerPage))
      if (currentPage > maxPage) {
        setCurrentPage(1)
      }
    } catch (error) {
      console.error("Erreur lors du chargement des conversations:", error)
      setConversations([])
    } finally {
      setIsLoading(false)
    }
  }

  // Calculs pour la pagination
  const totalItems = conversations.length
  const totalPages = Math.max(1, Math.ceil(totalItems / itemsPerPage))
  const startIndex = (currentPage - 1) * itemsPerPage
  const endIndex = Math.min(startIndex + itemsPerPage, totalItems)
  const currentItems = conversations.slice(startIndex, endIndex)

  // Handlers pour la navigation de page
  const goToNextPage = () => {
    setCurrentPage(prev => Math.min(prev + 1, totalPages))
  }

  const goToPrevPage = () => {
    setCurrentPage(prev => Math.max(prev - 1, 1))
  }

  // Fonction pour formater la date
  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleString("fr-FR", {
        day: "numeric",
        month: "long", 
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit"
      })
    } catch (error) {
      console.error("Erreur lors du formatage de la date:", error)
      return "Date inconnue"
    }
  }

  // Fonction pour obtenir l'icône et la couleur selon le type
  const getTypeDisplay = (type: string, chatMode: string) => {
    switch (type) {
      case "consultation":
        return {
          icon: <Stethoscope className="h-4 w-4" />,
          label: "Consultation",
          color: "bg-red-100 text-red-800"
        }
      case "discussion":
        return {
          icon: <MessageCircle className="h-4 w-4" />,
          label: "Discussion",
          color: "bg-blue-100 text-blue-800"
        }
      case "mixed":
        return {
          icon: <Bot className="h-4 w-4" />,
          label: "Mixte",
          color: "bg-purple-100 text-purple-800"
        }
      default:
        return {
          icon: <MessageCircle className="h-4 w-4" />,
          label: chatMode === "consultation" ? "Consultation" : "Discussion",
          color: chatMode === "consultation" ? "bg-red-100 text-red-800" : "bg-blue-100 text-blue-800"
        }
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4 mb-6">
        <Button variant="ghost" size="sm" onClick={onBack} className="text-emerald-700 hover:text-emerald-800">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Retour
        </Button>
        <h2 className="text-2xl font-bold text-emerald-800">Historique des conversations</h2>
        {!isLoading && (
          <Button
            variant="outline"
            size="sm"
            onClick={loadConversations}
            className="ml-auto"
          >
            Actualiser
          </Button>
        )}
      </div>

      {isLoading ? (
        <Card className="border-emerald-100">
          <CardContent className="p-8 text-center">
            <div className="animate-spin h-16 w-16 text-emerald-600 mx-auto mb-4">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 12a9 9 0 1 1-6.219-8.56"></path>
              </svg>
            </div>
            <p className="text-emerald-800 mb-2">Chargement de vos conversations...</p>
          </CardContent>
        </Card>
      ) : conversations.length === 0 ? (
        <Card className="border-amber-100">
          <CardContent className="p-8 text-center">
            <MessageCircle className="h-16 w-16 text-gray-400 mx-auto mb-4" />
            <p className="text-amber-800 mb-2">Aucune conversation sauvegardée</p>
            <p className="text-sm text-gray-600">
              Vos conversations avec aiBotanik apparaîtront ici après avoir créé des discussions ou consultations.
            </p>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="grid gap-4">
            {currentItems.map((conversation) => {
              const typeDisplay = getTypeDisplay(conversation.type, conversation.chat_mode)
              
              return (
                <Card 
                  key={conversation.id} 
                  className="border-emerald-100 hover:border-emerald-200 transition-colors cursor-pointer"
                  onClick={() => onConversationSelect(conversation.id)}
                >
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <CardTitle className="text-lg font-semibold text-emerald-800 line-clamp-2">
                        {conversation.title}
                      </CardTitle>
                      <Badge variant="secondary" className={`${typeDisplay.color} flex items-center gap-1`}>
                        {typeDisplay.icon}
                        {typeDisplay.label}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="pt-0">
                    <div className="space-y-3">
                      <p className="text-sm text-gray-600 line-clamp-2">
                        {conversation.summary}
                      </p>
                      
                      <div className="flex items-center justify-between text-xs text-gray-500">
                        <div className="flex items-center gap-4">
                          <span className="flex items-center gap-1">
                            <Calendar className="h-3 w-3" />
                            {formatDate(conversation.created_at)}
                          </span>
                          <span className="flex items-center gap-1">
                            <MessageCircle className="h-3 w-3" />
                            {conversation.messages_count} messages
                          </span>
                        </div>
                        
                        {conversation.last_recommendation && (
                          <span className="flex items-center gap-1 text-green-600">
                            <Bot className="h-3 w-3" />
                            Recommandation
                          </span>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between">
              <p className="text-sm text-gray-600">
                Page {currentPage} sur {totalPages} ({totalItems} conversation{totalItems > 1 ? 's' : ''})
              </p>
              
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={goToPrevPage}
                  disabled={currentPage === 1}
                >
                  <ChevronLeft className="h-4 w-4 mr-1" />
                  Précédent
                </Button>
                
                <Button
                  variant="outline"
                  size="sm"
                  onClick={goToNextPage}
                  disabled={currentPage === totalPages}
                >
                  Suivant
                  <ChevronRight className="h-4 w-4 ml-1" />
                </Button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
