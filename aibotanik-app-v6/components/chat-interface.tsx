"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { Mic, Send, ArrowLeft, Bot, User, MessageCircle, Stethoscope } from "lucide-react"

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
}

export function ChatInterface({ onBack, onStartChat, isWelcome = false }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState("")
  const [isListening, setIsListening] = useState(false)
  const [chatMode, setChatMode] = useState<"discussion" | "consultation">("discussion")

  const welcomeText = `Bonjour ! Je suis aiBotanik, votre assistant spécialisé en phytothérapie africaine.

Décrivez vos symptômes et je vous aiderai à trouver des remèdes naturels adaptés.

Comment puis-je vous aider ?`

  const handleSendMessage = () => {
    if (!inputValue.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputValue,
      sender: "user",
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])

    // Simulation d'une réponse du bot
    setTimeout(() => {
      const botResponse: Message = {
        id: (Date.now() + 1).toString(),
        content:
          chatMode === "consultation"
            ? `Merci pour cette consultation. Symptômes rapportés : "${inputValue}". Je vais analyser vos symptômes et vous proposer des solutions naturelles adaptées. Pouvez-vous me préciser depuis quand vous ressentez ces symptômes et leur intensité ?`
            : `Merci pour votre question : "${inputValue}". Je suis là pour discuter de phytothérapie africaine avec vous. Comment puis-je vous aider davantage ?`,
        sender: "bot",
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, botResponse])
    }, 1000)

    setInputValue("")

    if (isWelcome && onStartChat) {
      onStartChat()
    }
  }

  const handleVoiceInput = () => {
    setIsListening(!isListening)
    // Ici, vous pourriez intégrer une API de reconnaissance vocale
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
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
          <div className="min-h-[300px] max-h-[400px] md:min-h-[400px] md:max-h-[500px] overflow-y-auto mb-6 space-y-4">
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
              messages.map((message) => (
                <div
                  key={message.id}
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
              ))
            )}
          </div>

          {/* Zone de saisie */}
          <div className="flex justify-center">
            <div className="w-full max-w-4xl">
              <div className="flex gap-2 items-end">
                <div className="flex-1 relative">
                  <div className="relative">
                    {/* Boutons de mode intégrés dans le textarea */}
                    <div className="absolute left-3 top-3 flex items-center gap-2 z-10">
                      <button
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
                  onClick={handleSendMessage}
                  disabled={!inputValue.trim()}
                  className="bg-emerald-600 hover:bg-emerald-700 px-4 rounded-2xl h-[60px]"
                >
                  <Send className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
