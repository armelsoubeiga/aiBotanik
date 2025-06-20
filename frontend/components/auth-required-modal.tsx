"use client"

import React from "react"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { LogIn } from "lucide-react"

interface AuthRequiredModalProps {
  isOpen: boolean
  onClose: () => void
  onLogin: () => void
  onContinueWithoutLogin: () => void
}

export function AuthRequiredModal({
  isOpen,
  onClose,
  onLogin,
  onContinueWithoutLogin,
}: AuthRequiredModalProps) {
  // Ces fonctions ne sont plus utilisées car elles sont remplacées par des fonctions en ligne
  // avec setTimeout pour éviter les erreurs de mise à jour

  return (
    <AlertDialog open={isOpen} onOpenChange={onClose}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Connexion requise</AlertDialogTitle>
          <AlertDialogDescription>
            Pour sauvegarder votre consultation et accéder à votre historique, vous devez vous connecter ou
            créer un compte.
            <br />
            <br />
            Si vous continuez sans vous connecter, votre conversation ne sera pas sauvegardée.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter className="flex-col space-y-2 sm:space-y-0 sm:flex-row">
          <AlertDialogCancel
            className="w-full"
            onClick={() => setTimeout(onContinueWithoutLogin, 100)}
          >
            Continuer sans connexion
          </AlertDialogCancel>
          <AlertDialogAction
            className="w-full bg-emerald-600 hover:bg-emerald-700"
          >
            <LogIn className="mr-2 h-4 w-4" />
            <span onClick={() => setTimeout(onLogin, 100)}>Se connecter</span>
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
