"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ArrowLeft, MessageCircle, Calendar } from "lucide-react"

interface Consultation {
  id: number
  title: string
  date: string
  summary: string
  messagesCount: number
}

interface ConsultationHistoryProps {
  consultations: Consultation[]
  onConsultationSelect: (id: string) => void
  onBack: () => void
}

export function ConsultationHistory({ consultations, onConsultationSelect, onBack }: ConsultationHistoryProps) {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("fr-FR", {
      day: "numeric",
      month: "long",
      year: "numeric",
    })
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

      {consultations.length === 0 ? (
        <Card className="border-amber-100">
          <CardContent className="p-8 text-center">
            <MessageCircle className="h-16 w-16 text-gray-400 mx-auto mb-4" />
            <p className="text-amber-800 mb-2">Aucune consultation précédente</p>
            <p className="text-sm text-gray-600">
              Vos conversations avec aiBotanik apparaîtront ici après votre première consultation.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {consultations.map((consultation) => (
            <Card
              key={consultation.id}
              className="cursor-pointer transition-all duration-200 hover:shadow-lg hover:border-emerald-200 border-emerald-100"
              onClick={() => onConsultationSelect(consultation.id.toString())}
            >
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-emerald-800 text-lg">{consultation.title}</CardTitle>
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <MessageCircle className="h-4 w-4" />
                    <span>{consultation.messagesCount} messages</span>
                  </div>
                </div>
              </CardHeader>

              <CardContent className="space-y-3">
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <Calendar className="h-4 w-4" />
                  <span>{formatDate(consultation.date)}</span>
                </div>

                <p className="text-gray-700 text-sm leading-relaxed">{consultation.summary}</p>

                <div className="pt-2">
                  <Button variant="outline" size="sm" className="text-emerald-700 border-emerald-200">
                    Reprendre la conversation
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
