"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ArrowLeft, Phone, MapPin, User, Award } from "lucide-react"

interface Tradipraticien {
  id: number
  name: string
  localName: string
  country: string
  city: string
  province: string
  village: string
  phone: string
  specialties: string[]
  experience: string
}

interface TradipraticiensListProps {
  country: string
  tradipraticiens: Tradipraticien[]
  onBack: () => void
}

export function TradipraticiensList({ country, tradipraticiens, onBack }: TradipraticiensListProps) {
  const countryNames: { [key: string]: string } = {
    BF: "Burkina Faso",
    ML: "Mali",
    SN: "Sénégal",
    CI: "Côte d'Ivoire",
    GH: "Ghana",
    NG: "Nigeria",
    BJ: "Bénin",
    TG: "Togo",
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4 mb-6">
        <Button variant="ghost" size="sm" onClick={onBack} className="text-emerald-700 hover:text-emerald-800">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Retour
        </Button>
        <h2 className="text-2xl font-bold text-emerald-800">Tradipraticiens - {countryNames[country]}</h2>
      </div>

      {tradipraticiens.length === 0 ? (
        <Card className="border-amber-100">
          <CardContent className="p-8 text-center">
            <p className="text-amber-800 mb-2">Aucun tradipraticien disponible pour le moment</p>
            <p className="text-sm text-gray-600">
              Nous travaillons à enrichir notre réseau de praticiens dans cette région.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {tradipraticiens.map((praticien) => (
            <Card key={praticien.id} className="border-emerald-100 hover:shadow-lg transition-shadow duration-200">
              <CardHeader className="pb-3">
                <div className="flex items-center gap-2 mb-2">
                  <User className="h-5 w-5 text-emerald-600" />
                  <CardTitle className="text-emerald-800 text-lg">{praticien.name}</CardTitle>
                </div>
                <p className="text-sm text-gray-600 italic">"{praticien.localName}"</p>
              </CardHeader>

              <CardContent className="space-y-4">
                {/* Localisation */}
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <MapPin className="h-4 w-4" />
                    <span>
                      {praticien.village}, {praticien.city}
                    </span>
                  </div>
                  <div className="text-xs text-gray-500 ml-6">
                    {praticien.province}, {praticien.country}
                  </div>
                </div>

                {/* Contact */}
                <div className="flex items-center gap-2 text-sm">
                  <Phone className="h-4 w-4 text-emerald-600" />
                  <a href={`tel:${praticien.phone}`} className="text-emerald-700 hover:text-emerald-800">
                    {praticien.phone}
                  </a>
                </div>

                {/* Expérience */}
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <Award className="h-4 w-4" />
                  <span>{praticien.experience}</span>
                </div>

                {/* Spécialités */}
                <div>
                  <h4 className="font-medium text-gray-800 mb-2 text-sm">Spécialités</h4>
                  <div className="flex flex-wrap gap-1">
                    {praticien.specialties.map((specialty, index) => (
                      <Badge key={index} variant="secondary" className="bg-emerald-100 text-emerald-800 text-xs">
                        {specialty}
                      </Badge>
                    ))}
                  </div>
                </div>

                {/* Bouton de contact */}
                <Button className="w-full bg-emerald-600 hover:bg-emerald-700 mt-4">Contacter</Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
