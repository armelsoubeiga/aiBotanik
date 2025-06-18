"use client"

import type React from "react"

import { useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Leaf, Mail, ArrowLeft, CheckCircle } from "lucide-react"

interface ForgotPasswordModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function ForgotPasswordModal({ open, onOpenChange }: ForgotPasswordModalProps) {
  const [email, setEmail] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [isEmailSent, setIsEmailSent] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)

    // Simulation d'envoi d'email
    setTimeout(() => {
      setIsLoading(false)
      setIsEmailSent(true)
    }, 2000)
  }

  const handleClose = () => {
    onOpenChange(false)
    // Reset après fermeture
    setTimeout(() => {
      setIsEmailSent(false)
      setEmail("")
    }, 300)
  }

  const handleBackToLogin = () => {
    handleClose()
  }

  if (isEmailSent) {
    return (
      <Dialog open={open} onOpenChange={handleClose}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader className="text-center">
            <div className="w-16 h-16 bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-full flex items-center justify-center mx-auto mb-4">
              <CheckCircle className="h-8 w-8 text-white" />
            </div>
            <DialogTitle className="text-2xl font-bold text-emerald-800">Email envoyé !</DialogTitle>
            <p className="text-gray-600">Vérifiez votre boîte de réception</p>
          </DialogHeader>

          <div className="space-y-4 mt-6">
            <div className="bg-emerald-50 rounded-lg p-4 border border-emerald-100">
              <div className="flex items-start gap-3">
                <Mail className="h-5 w-5 text-emerald-600 mt-0.5" />
                <div>
                  <p className="text-emerald-800 font-medium mb-1">Instructions envoyées</p>
                  <p className="text-emerald-700 text-sm">
                    Nous avons envoyé un lien de réinitialisation à <strong>{email}</strong>
                  </p>
                </div>
              </div>
            </div>

            <div className="text-center space-y-2">
              <p className="text-gray-600 text-sm">Vous n'avez pas reçu l'email ?</p>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={() => setIsEmailSent(false)} className="flex-1">
                  Renvoyer
                </Button>
                <Button variant="outline" size="sm" onClick={handleBackToLogin} className="flex-1">
                  Retour à la connexion
                </Button>
              </div>
            </div>

            <div className="bg-amber-50 rounded-lg p-3 border border-amber-100">
              <p className="text-amber-800 text-xs text-center">
                <strong>Conseil :</strong> Vérifiez aussi vos spams et courriers indésirables
              </p>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    )
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader className="text-center">
          <div className="w-16 h-16 bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-full flex items-center justify-center mx-auto mb-4">
            <Leaf className="h-8 w-8 text-white" />
          </div>
          <DialogTitle className="text-2xl font-bold text-emerald-800">Mot de passe oublié</DialogTitle>
          <p className="text-gray-600">Récupérez l'accès à votre compte</p>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4 mt-6">
          <div className="space-y-2">
            <Label htmlFor="forgot-email" className="text-gray-700">
              Adresse email
            </Label>
            <Input
              id="forgot-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="votre@email.com"
              required
              className="border-emerald-200 focus:border-emerald-400"
            />
            <p className="text-xs text-gray-500">Entrez l'email associé à votre compte aiBotanik</p>
          </div>

          <Button type="submit" className="w-full bg-emerald-600 hover:bg-emerald-700" disabled={isLoading}>
            {isLoading ? (
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Envoi en cours...
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Mail className="h-4 w-4" />
                Envoyer le lien de récupération
              </div>
            )}
          </Button>

          <div className="text-center">
            <Button
              type="button"
              variant="link"
              className="text-gray-600 hover:text-gray-800 flex items-center gap-1 mx-auto"
              onClick={handleClose}
            >
              <ArrowLeft className="h-3 w-3" />
              Retour à la connexion
            </Button>
          </div>
        </form>

        <div className="bg-blue-50 rounded-lg p-3 border border-blue-100 mt-4">
          <p className="text-blue-800 text-xs text-center">
            <strong>Sécurisé :</strong> Le lien de récupération expire dans 24h pour votre sécurité
          </p>
        </div>
      </DialogContent>
    </Dialog>
  )
}
