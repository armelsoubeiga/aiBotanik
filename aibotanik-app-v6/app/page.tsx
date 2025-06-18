"use client"

import { useState } from "react"
import { Header } from "@/components/header"
import { MainActions } from "@/components/main-actions"
import { ChatInterface } from "@/components/chat-interface"
import { PlantCard } from "@/components/plant-card"
import { Button } from "@/components/ui/button"
import { ArrowLeft } from "lucide-react"
import { CountrySelection } from "@/components/country-selection"
import { TradipraticiensList } from "@/components/tradipraticiens-list"
import { ConsultationHistory } from "@/components/consultation-history"
import { PreDiagnostic } from "@/components/pre-diagnostic"
import { samplePlants } from "@/data/samplePlants" // Import samplePlants

type View = "home" | "tradipraticiens" | "country" | "consultations" | "chat" | "diagnostic"

const westAfricanCountries = [
  { code: "BF", name: "Burkina Faso", flag: "🇧🇫" },
  { code: "ML", name: "Mali", flag: "🇲🇱" },
  { code: "SN", name: "Sénégal", flag: "🇸🇳" },
  { code: "CI", name: "Côte d'Ivoire", flag: "🇨🇮" },
  { code: "GH", name: "Ghana", flag: "🇬🇭" },
  { code: "NG", name: "Nigeria", flag: "🇳🇬" },
  { code: "BJ", name: "Bénin", flag: "🇧🇯" },
  { code: "TG", name: "Togo", flag: "🇹🇬" },
]

const sampleTradipraticiens = {
  BF: [
    {
      id: 1,
      name: "Amadou Ouédraogo",
      localName: "Tibo Amadou",
      country: "Burkina Faso",
      city: "Ouagadougou",
      province: "Kadiogo",
      village: "Tanghin",
      phone: "+226 70 12 34 56",
      specialties: ["Paludisme", "Troubles digestifs", "Douleurs articulaires"],
      experience: "25 ans d'expérience",
    },
    {
      id: 2,
      name: "Fatimata Sawadogo",
      localName: "Poko Fatimata",
      country: "Burkina Faso",
      city: "Bobo-Dioulasso",
      province: "Houet",
      village: "Sarfalao",
      phone: "+226 76 98 76 54",
      specialties: ["Santé féminine", "Pédiatrie traditionnelle", "Hypertension"],
      experience: "30 ans d'expérience",
    },
  ],
  ML: [
    {
      id: 3,
      name: "Ibrahim Traoré",
      localName: "Baba Ibrahim",
      country: "Mali",
      city: "Bamako",
      province: "District de Bamako",
      village: "Kalaban Coro",
      phone: "+223 76 12 34 56",
      specialties: ["Diabète", "Rhumatismes", "Troubles respiratoires"],
      experience: "20 ans d'expérience",
    },
  ],
}

const sampleConsultations = [
  {
    id: 1,
    title: "Consultation du 15 Décembre 2024",
    date: "2024-12-15",
    summary: "Discussion sur les remèdes contre la toux persistante",
    messagesCount: 8,
  },
  {
    id: 2,
    title: "Consultation du 10 Décembre 2024",
    date: "2024-12-10",
    summary: "Conseils pour troubles digestifs et ballonnements",
    messagesCount: 12,
  },
]

export default function Home() {
  const [currentView, setCurrentView] = useState<View>("home")
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [selectedCountry, setSelectedCountry] = useState<string | null>(null)
  const [selectedConsultation, setSelectedConsultation] = useState<string | null>(null)

  const renderContent = () => {
    switch (currentView) {
      case "tradipraticiens":
        return (
          <CountrySelection
            countries={westAfricanCountries}
            onCountrySelect={(code) => {
              setSelectedCountry(code)
              setCurrentView("country")
            }}
            onBack={() => setCurrentView("home")}
          />
        )
      case "country":
        return selectedCountry ? (
          <TradipraticiensList
            country={selectedCountry}
            tradipraticiens={sampleTradipraticiens[selectedCountry] || []}
            onBack={() => setCurrentView("tradipraticiens")}
          />
        ) : null
      case "consultations":
        return (
          <ConsultationHistory
            consultations={sampleConsultations}
            onConsultationSelect={(id) => {
              setSelectedConsultation(id)
              setCurrentView("chat")
            }}
            onBack={() => setCurrentView("home")}
          />
        )
      case "diagnostic":
        return <PreDiagnostic onBack={() => setCurrentView("home")} />
      case "solutions":
        return (
          <div className="space-y-6">
            <div className="flex items-center gap-4 mb-6">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setCurrentView("home")}
                className="text-emerald-700 hover:text-emerald-800"
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Retour
              </Button>
              <h2 className="text-2xl font-bold text-emerald-800">Solutions disponibles</h2>
            </div>
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {samplePlants.map((plant) => (
                <PlantCard key={plant.id} plant={plant} />
              ))}
            </div>
          </div>
        )
      case "history":
        return (
          <div className="space-y-6">
            <div className="flex items-center gap-4 mb-6">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setCurrentView("home")}
                className="text-emerald-700 hover:text-emerald-800"
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Retour
              </Button>
              <h2 className="text-2xl font-bold text-emerald-800">Historique des consultations</h2>
            </div>
            <div className="bg-white rounded-lg border border-emerald-100 p-6 text-center">
              <p className="text-gray-600">Aucune consultation précédente trouvée.</p>
              <p className="text-sm text-gray-500 mt-2">Vos conversations avec aiBotanik apparaîtront ici.</p>
            </div>
          </div>
        )
      case "chat":
        return <ChatInterface onBack={() => setCurrentView("home")} />
      default:
        return (
          <>
            <MainActions onActionClick={setCurrentView} />
            <ChatInterface onStartChat={() => setCurrentView("chat")} isWelcome />
          </>
        )
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-white to-amber-50">
      <Header isAuthenticated={isAuthenticated} onAuthChange={setIsAuthenticated} />

      <main className="container mx-auto px-4 py-8 max-w-6xl">{renderContent()}</main>
    </div>
  )
}
