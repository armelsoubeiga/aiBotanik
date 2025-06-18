import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Leaf, MapPin, Pill } from "lucide-react"

interface LocalName {
  country: string
  dialect: string
  name: string
}

interface Plant {
  id: number
  name: string
  localNames: LocalName[]
  symptoms: string[]
  dosage: string
  mooreSummary: string
}

interface PlantCardProps {
  plant: Plant
}

export function PlantCard({ plant }: PlantCardProps) {
  return (
    <Card className="border-emerald-100 hover:shadow-lg transition-shadow duration-200">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2 mb-2">
          <Leaf className="h-5 w-5 text-emerald-600" />
          <CardTitle className="text-emerald-800">{plant.name}</CardTitle>
        </div>

        {/* Noms locaux */}
        <div className="space-y-1">
          {plant.localNames.map((localName, index) => (
            <div key={index} className="flex items-center gap-2 text-sm text-gray-600">
              <MapPin className="h-3 w-3" />
              <span>
                {localName.country} • {localName.dialect} • <strong>{localName.name}</strong>
              </span>
            </div>
          ))}
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Symptômes */}
        <div>
          <h4 className="font-medium text-gray-800 mb-2 flex items-center gap-2">
            <Pill className="h-4 w-4" />
            Symptômes traités
          </h4>
          <div className="flex flex-wrap gap-1">
            {plant.symptoms.map((symptom, index) => (
              <Badge key={index} variant="secondary" className="bg-amber-100 text-amber-800">
                {symptom}
              </Badge>
            ))}
          </div>
        </div>

        {/* Dosage */}
        <div>
          <h4 className="font-medium text-gray-800 mb-2">Utilisation</h4>
          <p className="text-sm text-gray-600 leading-relaxed">{plant.dosage}</p>
        </div>

        {/* Résumé en mooré */}
        <div className="bg-emerald-50 p-3 rounded-lg">
          <h4 className="font-medium text-emerald-800 mb-1 text-sm">En mooré</h4>
          <p className="text-sm text-emerald-700 italic">{plant.mooreSummary}</p>
        </div>
      </CardContent>
    </Card>
  )
}
