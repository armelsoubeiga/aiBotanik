"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"
import { Menu, User, LogOut, Settings, Leaf } from "lucide-react"
import { LoginModal } from "@/components/login-modal"
import { SignupModal } from "@/components/signup-modal"
import { SettingsModal } from "@/components/settings-modal"
import { authService } from "@/services/auth-service"

interface HeaderProps {
  isAuthenticated: boolean
  onAuthChange: (authenticated: boolean) => void
  onSettingsChanged?: () => void  // Nouveau callback pour les changements de paramètres
}

export function Header({ isAuthenticated, onAuthChange, onSettingsChanged }: HeaderProps) {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const [showLoginModal, setShowLoginModal] = useState(false)
  const [showSignupModal, setShowSignupModal] = useState(false)
  const [showSettingsModal, setShowSettingsModal] = useState(false)

  const handleLogin = () => {
    setShowLoginModal(true)
  }

  const handleSignup = () => {
    setShowSignupModal(true)
  }

  const handleLoginSuccess = () => {
    onAuthChange(true)
    setShowLoginModal(false)
  }

  const handleSignupSuccess = () => {
    onAuthChange(true)
    setShowSignupModal(false)
  }

  const handleLogout = () => {
    console.log("Déconnexion demandée depuis l'en-tête");
    
    // Utiliser le service d'authentification pour se déconnecter
    // La méthode logout() va émettre un événement aiBotanikLogout
    // qui sera capturé par ChatInterface pour sauvegarder les données
    authService.logout();
    
    // Après un court délai pour laisser le temps de sauvegarder,
    // informer le composant parent que l'utilisateur s'est déconnecté
    setTimeout(() => {
      console.log("Notification de déconnexion envoyée aux composants parents");
      onAuthChange(false);
      
      // Fermer la modale mobile si ouverte
      setIsMobileMenuOpen(false);
    }, 500);
    
    // Réinitialiser l'état des modales au cas où
    setShowLoginModal(false);
    setShowSignupModal(false);
    setShowSettingsModal(false);
  }

  return (
    <>
      <header className="bg-white/80 backdrop-blur-sm border-b border-emerald-100 sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          {/* Logo et titre */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-lg flex items-center justify-center">
              <Leaf className="h-6 w-6 text-white" />
            </div>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-emerald-700 to-emerald-600 bg-clip-text text-transparent">
              aiBotanik
            </h1>
          </div>

          {/* Navigation desktop */}
          <div className="hidden md:flex items-center gap-4">
            {isAuthenticated ? (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="flex items-center gap-2 hover:bg-emerald-50">
                    <div className="w-8 h-8 bg-emerald-100 rounded-full flex items-center justify-center">
                      <User className="h-4 w-4 text-emerald-600" />
                    </div>
                    <span className="text-emerald-800">Mon compte</span>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-48 bg-white border border-gray-200 shadow-lg">
                  <DropdownMenuItem 
                    onClick={() => setShowSettingsModal(true)}
                    className="flex items-center gap-3 px-3 py-2 hover:bg-gray-50 cursor-pointer"
                  >
                    <Settings className="h-4 w-4 text-gray-600" />
                    <span className="text-gray-700">Paramètres</span>
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    onClick={handleLogout}
                    className="flex items-center gap-3 px-3 py-2 hover:bg-gray-50 cursor-pointer"
                  >
                    <LogOut className="h-4 w-4 text-gray-600" />
                    <span className="text-gray-700">Se déconnecter</span>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            ) : (
              <div className="flex gap-2">
                <Button
                  variant="ghost"
                  onClick={handleLogin}
                  className="text-emerald-700 hover:text-emerald-800 hover:bg-emerald-50"
                >
                  Se connecter
                </Button>
                <Button onClick={handleSignup} className="bg-emerald-600 hover:bg-emerald-700 text-white">
                  S'inscrire
                </Button>
              </div>
            )}
          </div>

          {/* Menu mobile */}
          <div className="md:hidden">
            <Sheet open={isMobileMenuOpen} onOpenChange={setIsMobileMenuOpen}>
              <SheetTrigger asChild>
                <Button variant="ghost" size="sm">
                  <Menu className="h-5 w-5" />
                </Button>
              </SheetTrigger>
              <SheetContent side="right" className="w-64">
                <div className="flex flex-col gap-4 mt-8">
                  {isAuthenticated ? (
                    <>
                      <Button 
                        variant="ghost" 
                        className="justify-start"
                        onClick={() => {
                          setIsMobileMenuOpen(false); 
                          setShowSettingsModal(true);
                        }}
                      >
                        <Settings className="h-4 w-4 mr-2" />
                        Paramètres
                      </Button>
                      <Button variant="ghost" className="justify-start" onClick={handleLogout}>
                        <LogOut className="h-4 w-4 mr-2" />
                        Se déconnecter
                      </Button>
                    </>
                  ) : (
                    <>
                      <Button variant="ghost" onClick={handleLogin}>
                        Se connecter
                      </Button>
                      <Button className="bg-emerald-600 hover:bg-emerald-700" onClick={handleSignup}>
                        S'inscrire
                      </Button>
                    </>
                  )}
                </div>
              </SheetContent>
            </Sheet>
          </div>
        </div>
      </header>

      {/* Modales */}
      <LoginModal open={showLoginModal} onOpenChange={setShowLoginModal} onLoginSuccess={handleLoginSuccess} />
      <SignupModal open={showSignupModal} onOpenChange={setShowSignupModal} onSignupSuccess={handleSignupSuccess} />      <SettingsModal 
        open={showSettingsModal} 
        onOpenChange={setShowSettingsModal} 
        onSettingsChanged={() => {
          // Notifier le composant parent des changements de paramètres
          console.log("Paramètres modifiés - notification du composant parent");
          if (onSettingsChanged) {
            onSettingsChanged();
          }
        }} 
      />
    </>
  )
}
