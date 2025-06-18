"use client"
import { Card, CardContent } from "@/components/ui/card"
import { Leaf, History, Plus } from "lucide-react"

interface MainActionsProps {
  onActionClick: (view: "tradipraticiens" | "consultations" | "diagnostic") => void
}

export function MainActions({ onActionClick }: MainActionsProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
      <Card
        className="cursor-pointer transition-all duration-200 hover:shadow-lg hover:scale-105 border-emerald-100 hover:border-emerald-200"
        onClick={() => onActionClick("tradipraticiens")}
      >
        <CardContent className="p-6 text-center">
          <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Leaf className="h-8 w-8 text-emerald-600" />
          </div>
          <h3 className="font-semibold text-emerald-800 mb-2">Consulter un tradipraticien</h3>
          <p className="text-sm text-gray-600">Trouvez des praticiens traditionnels près de chez vous</p>
        </CardContent>
      </Card>

      <Card
        className="cursor-pointer transition-all duration-200 hover:shadow-lg hover:scale-105 border-amber-100 hover:border-amber-200"
        onClick={() => onActionClick("consultations")}
      >
        <CardContent className="p-6 text-center">
          <div className="w-16 h-16 bg-amber-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <History className="h-8 w-8 text-amber-600" />
          </div>
          <h3 className="font-semibold text-amber-800 mb-2">Historique de consultations</h3>
          <p className="text-sm text-gray-600">Consultez vos conversations précédentes</p>
        </CardContent>
      </Card>

      <Card
        className="cursor-pointer transition-all duration-200 hover:shadow-lg hover:scale-105 border-blue-100 hover:border-blue-200"
        onClick={() => onActionClick("diagnostic")}
      >
        <CardContent className="p-6 text-center">
          <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Plus className="h-8 w-8 text-blue-600" />
          </div>
          <h3 className="font-semibold text-blue-800 mb-2">Pré-diagnostic guidé</h3>
          <p className="text-sm text-gray-600">Questionnaire pour orienter vos symptômes</p>
        </CardContent>
      </Card>
    </div>
  )
}
