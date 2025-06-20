"use client"

import type React from "react"

import { useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Leaf, Eye, EyeOff } from "lucide-react"
import { ForgotPasswordModal } from "@/components/forgot-password-modal"
import { authService } from "@/services/auth-service"

interface LoginModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onLoginSuccess: () => void
}

export function LoginModal({ open, onOpenChange, onLoginSuccess }: LoginModalProps) {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [showForgotPassword, setShowForgotPassword] = useState(false)
  const [loginError, setLoginError] = useState<string | null>(null)
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoginError(null)
    setIsLoading(true)

    // Validation des champs localement
    if (!email.trim() || !password.trim()) {
      setLoginError("Veuillez remplir tous les champs")
      setIsLoading(false)
      return
    }

    try {
      // Utiliser le service d'authentification pour se connecter
      const result = await authService.login({
        email,
        password
      });
      
      if (result.success) {
        console.log("Connexion réussie");
        onLoginSuccess();
        setEmail("");
        setPassword("");
      } else {
        console.error("Échec de la connexion:", result.errorMessage);
        setLoginError(result.errorMessage || "Identifiants incorrects. Veuillez réessayer.");
      }
    } catch (error) {
      console.error("Erreur lors de la connexion:", error);
      setLoginError("Une erreur est survenue lors de la connexion. Veuillez réessayer.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader className="text-center">
          <div className="w-16 h-16 bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-full flex items-center justify-center mx-auto mb-4">
            <Leaf className="h-8 w-8 text-white" />
          </div>
          <DialogTitle className="text-2xl font-bold text-emerald-800">Connexion à aiBotanik</DialogTitle>
          <p className="text-gray-600">Accédez à votre assistant phytothérapie</p>
        </DialogHeader>        <form onSubmit={handleSubmit} className="space-y-4 mt-6">
          {loginError && (
            <div className="bg-red-50 p-3 rounded-md border border-red-200 text-red-800 text-sm">
              <p>{loginError}</p>
            </div>
          )}
          <div className="space-y-2">
            <Label htmlFor="email" className="text-gray-700">
              Email
            </Label>
            <Input
              id="email"
              type="email"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value)
                setLoginError(null)
              }}
              placeholder="votre@email.com"
              required
              className="border-emerald-200 focus:border-emerald-400"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="password" className="text-gray-700">
              Mot de passe
            </Label>
            <div className="relative">              <Input
                id="password"
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value)
                  setLoginError(null)
                }}
                placeholder="••••••••"
                required
                className="border-emerald-200 focus:border-emerald-400 pr-10"
              />
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="absolute right-0 top-0 h-full px-3 hover:bg-transparent"
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? (
                  <EyeOff className="h-4 w-4 text-gray-400" />
                ) : (
                  <Eye className="h-4 w-4 text-gray-400" />
                )}
              </Button>
            </div>
          </div>

          <Button type="submit" className="w-full bg-emerald-600 hover:bg-emerald-700" disabled={isLoading}>
            {isLoading ? "Connexion..." : "Se connecter"}
          </Button>

          <div className="text-center">
            <Button
              type="button"
              variant="link"
              className="text-emerald-600 hover:text-emerald-700"
              onClick={() => setShowForgotPassword(true)}
            >
              Mot de passe oublié ?
            </Button>
          </div>
        </form>
      </DialogContent>
      <ForgotPasswordModal open={showForgotPassword} onOpenChange={setShowForgotPassword} />
    </Dialog>
  )
}
