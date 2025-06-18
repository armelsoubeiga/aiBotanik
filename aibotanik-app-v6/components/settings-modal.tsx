"use client"

import { useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Separator } from "@/components/ui/separator"
import { Settings, User, Bell, Shield, Globe } from "lucide-react"

interface SettingsModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function SettingsModal({ open, onOpenChange }: SettingsModalProps) {
  const [settings, setSettings] = useState({
    name: "Utilisateur aiBotanik",
    email: "user@example.com",
    notifications: true,
    emailNotifications: false,
    language: "fr",
    darkMode: false,
  })

  const [isLoading, setIsLoading] = useState(false)

  const handleSave = async () => {
    setIsLoading(true)
    // Simulation de sauvegarde
    setTimeout(() => {
      setIsLoading(false)
      onOpenChange(false)
    }, 1000)
  }

  const handleSettingChange = (key: string, value: any) => {
    setSettings((prev) => ({ ...prev, [key]: value }))
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <Settings className="h-5 w-5 text-emerald-600" />
            <DialogTitle className="text-xl font-bold text-emerald-800">Paramètres</DialogTitle>
          </div>
        </DialogHeader>

        <div className="space-y-6 mt-6">
          {/* Profil */}
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <User className="h-4 w-4 text-gray-600" />
              <h3 className="font-medium text-gray-800">Profil</h3>
            </div>

            <div className="space-y-3 ml-6">
              <div className="space-y-2">
                <Label htmlFor="settings-name" className="text-gray-700">
                  Nom
                </Label>
                <Input
                  id="settings-name"
                  value={settings.name}
                  onChange={(e) => handleSettingChange("name", e.target.value)}
                  className="border-emerald-200 focus:border-emerald-400"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="settings-email" className="text-gray-700">
                  Email
                </Label>
                <Input
                  id="settings-email"
                  type="email"
                  value={settings.email}
                  onChange={(e) => handleSettingChange("email", e.target.value)}
                  className="border-emerald-200 focus:border-emerald-400"
                />
              </div>
            </div>
          </div>

          <Separator />

          {/* Notifications */}
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Bell className="h-4 w-4 text-gray-600" />
              <h3 className="font-medium text-gray-800">Notifications</h3>
            </div>

            <div className="space-y-3 ml-6">
              <div className="flex items-center justify-between">
                <div>
                  <Label className="text-gray-700">Notifications push</Label>
                  <p className="text-xs text-gray-500">Recevoir des notifications dans l'application</p>
                </div>
                <Switch
                  checked={settings.notifications}
                  onCheckedChange={(checked) => handleSettingChange("notifications", checked)}
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <Label className="text-gray-700">Notifications par email</Label>
                  <p className="text-xs text-gray-500">Recevoir des emails de rappel</p>
                </div>
                <Switch
                  checked={settings.emailNotifications}
                  onCheckedChange={(checked) => handleSettingChange("emailNotifications", checked)}
                />
              </div>
            </div>
          </div>

          <Separator />

          {/* Préférences */}
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Globe className="h-4 w-4 text-gray-600" />
              <h3 className="font-medium text-gray-800">Préférences</h3>
            </div>

            <div className="space-y-3 ml-6">
              <div className="space-y-2">
                <Label className="text-gray-700">Langue</Label>
                <select
                  value={settings.language}
                  onChange={(e) => handleSettingChange("language", e.target.value)}
                  className="w-full px-3 py-2 border border-emerald-200 rounded-md focus:border-emerald-400 focus:outline-none"
                >
                  <option value="fr">Français</option>
                  <option value="en">English</option>
                  <option value="moore">Mooré</option>
                </select>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <Label className="text-gray-700">Mode sombre</Label>
                  <p className="text-xs text-gray-500">Activer le thème sombre</p>
                </div>
                <Switch
                  checked={settings.darkMode}
                  onCheckedChange={(checked) => handleSettingChange("darkMode", checked)}
                />
              </div>
            </div>
          </div>

          <Separator />

          {/* Sécurité */}
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Shield className="h-4 w-4 text-gray-600" />
              <h3 className="font-medium text-gray-800">Sécurité</h3>
            </div>

            <div className="ml-6">
              <Button variant="outline" className="w-full">
                Changer le mot de passe
              </Button>
            </div>
          </div>
        </div>

        <div className="flex gap-3 mt-8">
          <Button variant="outline" onClick={() => onOpenChange(false)} className="flex-1">
            Annuler
          </Button>
          <Button onClick={handleSave} disabled={isLoading} className="flex-1 bg-emerald-600 hover:bg-emerald-700">
            {isLoading ? "Sauvegarde..." : "Sauvegarder"}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
