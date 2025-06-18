"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"
import { Menu, User, LogOut, Settings, Leaf } from "lucide-react"

interface HeaderProps {
  isAuthenticated: boolean
  onAuthChange: (authenticated: boolean) => void
}

export function Header({ isAuthenticated, onAuthChange }: HeaderProps) {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)

  const handleLogin = () => {
    onAuthChange(true)
  }

  const handleLogout = () => {
    onAuthChange(false)
  }

  return (
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
                <Button variant="ghost" className="flex items-center gap-2">
                  <User className="h-4 w-4" />
                  Mon compte
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-48">
                <DropdownMenuItem>
                  <Settings className="h-4 w-4 mr-2" />
                  Paramètres
                </DropdownMenuItem>
                <DropdownMenuItem onClick={handleLogout}>
                  <LogOut className="h-4 w-4 mr-2" />
                  Se déconnecter
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          ) : (
            <div className="flex gap-2">
              <Button variant="ghost" onClick={handleLogin}>
                Se connecter
              </Button>
              <Button className="bg-emerald-600 hover:bg-emerald-700">S'inscrire</Button>
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
                    <Button variant="ghost" className="justify-start">
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
                    <Button className="bg-emerald-600 hover:bg-emerald-700">S'inscrire</Button>
                  </>
                )}
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </header>
  )
}
