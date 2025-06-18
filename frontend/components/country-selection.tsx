"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { ArrowLeft } from "lucide-react"

interface Country {
  code: string
  name: string
  flag: string
}

interface CountrySelectionProps {
  countries: Country[]
  onCountrySelect: (countryCode: string) => void
  onBack: () => void
}

export function CountrySelection({ countries, onCountrySelect, onBack }: CountrySelectionProps) {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4 mb-6">
        <Button variant="ghost" size="sm" onClick={onBack} className="text-emerald-700 hover:text-emerald-800">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Retour
        </Button>
        <h2 className="text-2xl font-bold text-emerald-800">Choisissez votre pays</h2>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {countries.map((country) => (
          <Card
            key={country.code}
            className="cursor-pointer transition-all duration-200 hover:shadow-lg hover:scale-105 border-emerald-100 hover:border-emerald-200"
            onClick={() => onCountrySelect(country.code)}
          >
            <CardContent className="p-6 text-center">
              <div className="text-4xl mb-3">{country.flag}</div>
              <h3 className="font-medium text-emerald-800 text-sm">{country.name}</h3>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="bg-emerald-50 rounded-lg p-4 border border-emerald-100">
        <p className="text-emerald-800 text-center">
          <strong>Sélectionnez votre pays</strong> pour découvrir les tradipraticiens disponibles dans votre région.
        </p>
      </div>
    </div>
  )
}
