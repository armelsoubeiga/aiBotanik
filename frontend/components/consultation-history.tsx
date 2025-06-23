"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ArrowLeft, MessageCircle, Calendar, ChevronLeft, ChevronRight } from "lucide-react"
import { Pagination } from "@/components/ui/pagination"

interface Consultation {
  id: string | number  // Accepter à la fois string et number pour la compatibilité
  title: string
  date?: string  // Rendre optionnel pour éviter les erreurs TypeScript
  created_at?: string
  summary?: string  // Rendre optionnel
  messagesCount?: number  // Rendre optionnel
  messages_count?: number // Support pour le champ backend
}

interface ConsultationHistoryProps {
  consultations: Consultation[]
  onConsultationSelect: (id: string) => void
  onBack: () => void
  isLoading?: boolean
}

export function ConsultationHistory({ consultations, onConsultationSelect, onBack, isLoading = false }: ConsultationHistoryProps) {
  // État pour la pagination
  const [currentPage, setCurrentPage] = useState(1)
  const itemsPerPage = 5 // 5 consultations par page
  
  // Effet pour réinitialiser la pagination quand les consultations changent
  useEffect(() => {
    // Si les consultations changent, vérifier que la page courante est toujours valide
    const maxPageForItems = Math.max(1, Math.ceil(consultations.length / itemsPerPage));
    if (currentPage > maxPageForItems) {
      setCurrentPage(maxPageForItems);
    }
  }, [consultations.length, currentPage]);
  
  // Calcul pour la pagination
  const totalItems = consultations.length
  const totalPages = Math.max(1, Math.ceil(totalItems / itemsPerPage))
  const startIndex = (currentPage - 1) * itemsPerPage
  const endIndex = Math.min(startIndex + itemsPerPage, totalItems)
  const currentItems = consultations.slice(startIndex, endIndex)
  
  // Handlers pour la navigation de page
  const goToNextPage = () => {
    setCurrentPage(prev => Math.min(prev + 1, totalPages))
  }
  
  const goToPrevPage = () => {
    setCurrentPage(prev => Math.max(prev - 1, 1))
  }
  
  const formatDate = (dateString: string) => {
    try {
      // Inclure à la fois la date et l'heure avec un format clair et lisible
      return new Date(dateString).toLocaleString("fr-FR", {
        day: "numeric",
        month: "long",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit"
      })
    } catch (error) {
      console.error("Erreur lors du formatage de la date:", error, "pour la valeur:", dateString)
      return "Date inconnue"
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4 mb-6">
        <Button variant="ghost" size="sm" onClick={onBack} className="text-emerald-700 hover:text-emerald-800">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Retour
        </Button>
        <h2 className="text-2xl font-bold text-emerald-800">Historique de consultations</h2>
      </div>

      {isLoading ? (
        <Card className="border-emerald-100">
          <CardContent className="p-8 text-center">
            <div className="animate-spin h-16 w-16 text-emerald-600 mx-auto mb-4">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 12a9 9 0 1 1-6.219-8.56"></path>
              </svg>
            </div>
            <p className="text-emerald-800 mb-2">Chargement de vos consultations...</p>
          </CardContent>
        </Card>
      ) : consultations.length === 0 ? (
        <Card className="border-amber-100">
          <CardContent className="p-8 text-center">
            <MessageCircle className="h-16 w-16 text-gray-400 mx-auto mb-4" />
            <p className="text-amber-800 mb-2">Aucune consultation précédente</p>
            <p className="text-sm text-gray-600">
              Vos conversations avec aiBotanik apparaîtront ici après votre première consultation.
            </p>
            <p className="text-xs text-gray-500 mt-4">
              Les conversations sont sauvegardées automatiquement quand vous avez au moins quatre messages (deux échanges complets).
            </p>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="space-y-4">
            {currentItems.map((consultation) => (
              <Card
                key={consultation.id}
                className="cursor-pointer transition-all duration-200 hover:shadow-lg hover:border-emerald-200 border-emerald-100"
                onClick={() => onConsultationSelect(consultation.id.toString())}
              >
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-emerald-800 text-lg">
                      {/* Afficher la date à la place du titre */}
                      {formatDate(consultation.date || consultation.created_at || new Date().toISOString())}
                    </CardTitle>
                    <div className="flex items-center gap-2 text-sm text-gray-500">
                      <MessageCircle className="h-4 w-4" />
                      <span>
                        {/* Utiliser messagesCount si disponible, sinon utiliser messages_count */}
                        {consultation.messagesCount || consultation.messages_count || 0} messages
                      </span>
                    </div>
                  </div>
                </CardHeader>

                <CardContent className="space-y-3">
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <Calendar className="h-4 w-4" />
                    <span>{formatDate(consultation.date || consultation.created_at || new Date().toISOString())}</span>
                  </div>

                  <p className="text-gray-700 text-sm leading-relaxed">
                    {consultation.summary || "Résumé non disponible"}
                  </p>

                  <div className="pt-2">
                    <Button variant="outline" size="sm" className="text-emerald-700 border-emerald-200">
                      Reprendre la conversation
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
          
          {/* Pagination component */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center mt-6">
              <div className="flex items-center gap-2">
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={goToPrevPage}
                  disabled={currentPage <= 1}
                  className="h-8 w-8 p-0"
                >
                  <span className="sr-only">Page précédente</span>
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                
                <div className="flex items-center gap-1 mx-2">
                  <span className="text-sm font-medium text-emerald-700">{currentPage}</span>
                  <span className="text-sm text-gray-500"> / {totalPages}</span>
                </div>
                
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={goToNextPage}
                  disabled={currentPage >= totalPages}
                  className="h-8 w-8 p-0"
                >
                  <span className="sr-only">Page suivante</span>
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
