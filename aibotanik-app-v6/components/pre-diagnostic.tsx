"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ArrowLeft, CheckCircle, AlertCircle } from "lucide-react"

interface PreDiagnosticProps {
  onBack: () => void
}

interface Question {
  id: string
  text: string
  options: string[]
}

interface Symptom {
  id: string
  name: string
  category: string
}

const questions: Question[] = [
  {
    id: "zone",
    text: "Dans quelle zone ressentez-vous des symptômes ?",
    options: ["Tête", "Gorge/Cou", "Poitrine", "Ventre", "Membres", "Peau", "Général"],
  },
  {
    id: "type",
    text: "Quel type de symptôme décrit le mieux votre situation ?",
    options: ["Douleur", "Inflammation", "Troubles digestifs", "Fatigue", "Fièvre", "Troubles du sommeil"],
  },
  {
    id: "duree",
    text: "Depuis combien de temps ressentez-vous ces symptômes ?",
    options: ["Moins d'1 jour", "1-3 jours", "1 semaine", "Plus d'1 semaine", "Chronique"],
  },
]

const recommendations = {
  "Tête-Douleur": {
    plants: ["Eucalyptus", "Menthe"],
    advice: "Appliquez des feuilles d'eucalyptus en cataplasme sur le front",
  },
  "Ventre-Troubles digestifs": {
    plants: ["Gingembre", "Citronnelle"],
    advice: "Préparez une tisane avec du gingembre frais",
  },
  "Général-Fatigue": {
    plants: ["Moringa", "Baobab"],
    advice: "Consommez de la poudre de moringa dans vos repas",
  },
}

export function PreDiagnostic({ onBack }: PreDiagnosticProps) {
  const [currentStep, setCurrentStep] = useState(0)
  const [answers, setAnswers] = useState<{ [key: string]: string }>({})
  const [showResults, setShowResults] = useState(false)

  const handleAnswer = (answer: string) => {
    const newAnswers = { ...answers, [questions[currentStep].id]: answer }
    setAnswers(newAnswers)

    if (currentStep < questions.length - 1) {
      setCurrentStep(currentStep + 1)
    } else {
      setShowResults(true)
    }
  }

  const getRecommendation = () => {
    const key = `${answers.zone}-${answers.type}`
    return (
      recommendations[key as keyof typeof recommendations] || {
        plants: ["Consultation recommandée"],
        advice: "Consultez un tradipraticien pour un diagnostic personnalisé",
      }
    )
  }

  const resetDiagnostic = () => {
    setCurrentStep(0)
    setAnswers({})
    setShowResults(false)
  }

  if (showResults) {
    const recommendation = getRecommendation()
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4 mb-6">
          <Button variant="ghost" size="sm" onClick={onBack} className="text-emerald-700 hover:text-emerald-800">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Retour
          </Button>
          <h2 className="text-2xl font-bold text-emerald-800">Résultats du pré-diagnostic</h2>
        </div>

        <Card className="border-emerald-100">
          <CardHeader>
            <div className="flex items-center gap-2">
              <CheckCircle className="h-6 w-6 text-emerald-600" />
              <CardTitle className="text-emerald-800">Recommandations personnalisées</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <h3 className="font-medium text-gray-800 mb-3">Vos réponses :</h3>
              <div className="flex flex-wrap gap-2">
                {Object.entries(answers).map(([key, value]) => (
                  <Badge key={key} variant="outline" className="bg-emerald-50 text-emerald-700">
                    {value}
                  </Badge>
                ))}
              </div>
            </div>

            <div>
              <h3 className="font-medium text-gray-800 mb-3">Plantes recommandées :</h3>
              <div className="flex flex-wrap gap-2">
                {recommendation.plants.map((plant, index) => (
                  <Badge key={index} className="bg-emerald-100 text-emerald-800">
                    🌿 {plant}
                  </Badge>
                ))}
              </div>
            </div>

            <div className="bg-amber-50 rounded-lg p-4 border border-amber-100">
              <div className="flex items-start gap-2">
                <AlertCircle className="h-5 w-5 text-amber-600 mt-0.5" />
                <div>
                  <h4 className="font-medium text-amber-800 mb-1">Conseil d'utilisation</h4>
                  <p className="text-amber-700 text-sm">{recommendation.advice}</p>
                </div>
              </div>
            </div>

            <div className="flex gap-3">
              <Button onClick={resetDiagnostic} variant="outline" className="flex-1">
                Nouveau diagnostic
              </Button>
              <Button className="flex-1 bg-emerald-600 hover:bg-emerald-700">Consulter aiBotanik</Button>
            </div>
          </CardContent>
        </Card>

        <Card className="border-blue-100">
          <CardContent className="p-4">
            <p className="text-blue-800 text-sm text-center">
              <strong>Important :</strong> Ce pré-diagnostic est indicatif. Consultez toujours un professionnel de santé
              pour un diagnostic précis.
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4 mb-6">
        <Button variant="ghost" size="sm" onClick={onBack} className="text-emerald-700 hover:text-emerald-800">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Retour
        </Button>
        <h2 className="text-2xl font-bold text-emerald-800">Pré-diagnostic guidé</h2>
      </div>

      <Card className="border-emerald-100">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-emerald-800">
              Question {currentStep + 1} sur {questions.length}
            </CardTitle>
            <div className="text-sm text-gray-500">{Math.round(((currentStep + 1) / questions.length) * 100)}%</div>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-emerald-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${((currentStep + 1) / questions.length) * 100}%` }}
            />
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          <h3 className="text-lg font-medium text-gray-800">{questions[currentStep].text}</h3>

          <div className="grid gap-3">
            {questions[currentStep].options.map((option, index) => (
              <Button
                key={index}
                variant="outline"
                className="justify-start h-auto p-4 text-left hover:bg-emerald-50 hover:border-emerald-200"
                onClick={() => handleAnswer(option)}
              >
                {option}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card className="border-blue-100">
        <CardContent className="p-4">
          <p className="text-blue-800 text-sm text-center">
            Répondez aux questions pour recevoir des recommandations personnalisées basées sur vos symptômes.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
