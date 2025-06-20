"use client"

import React, { useState, useEffect } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Loader2, Settings, Key, History, Trash2, CheckCircle2, AlertCircle } from "lucide-react"
import { authService } from "@/services/auth-service"
import { consultationService } from "@/services/consultation-service"
import { conversationUnifiedService } from "@/services/conversation-unified-service"
import { 
  Alert,
  AlertTitle,
  AlertDescription
} from "@/components/ui/alert"
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardFooter, 
  CardHeader, 
  CardTitle 
} from "@/components/ui/card"

interface SettingsModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSettingsChanged?: () => void
}

interface Consultation {
  id: string;
  title: string;
  date: string;
  messagesCount: number;
  summary: string;
}

export function SettingsModal({ open, onOpenChange, onSettingsChanged }: SettingsModalProps) {
  // États pour le changement de mot de passe
  const [email, setEmail] = useState("")
  const [currentPassword, setCurrentPassword] = useState("")
  const [newPassword, setNewPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [isChangingPassword, setIsChangingPassword] = useState(false)
  const [passwordChangeError, setPasswordChangeError] = useState<string | null>(null)
  const [passwordChangeSuccess, setPasswordChangeSuccess] = useState(false)
  
  // États pour l'historique des consultations
  const [consultations, setConsultations] = useState<Consultation[]>([])
  const [isLoadingConsultations, setIsLoadingConsultations] = useState(false)
  const [isDeletingConsultation, setIsDeletingConsultation] = useState<string | null>(null)
  const [consultationDeleteError, setConsultationDeleteError] = useState<string | null>(null)
  const [consultationDeleteSuccess, setConsultationDeleteSuccess] = useState(false)

  // Charger les informations utilisateur et les consultations au chargement
  useEffect(() => {
    if (open) {
      loadUserInfo();
      loadConsultations();
    } else {
      // Réinitialiser les états quand la modal se ferme
      resetStates();
    }
  }, [open]);

  // Charger les informations utilisateur
  const loadUserInfo = async () => {
    if (!authService.isAuthenticated()) return;
    
    try {
      const user = await authService.getCurrentUser();
      if (user) {
        setEmail(user.email);
      }
    } catch (error) {
      console.error("Erreur lors du chargement des informations utilisateur:", error);
    }
  };
  // Charger les consultations (conversations unifiées)
  const loadConsultations = async () => {
    if (!authService.isAuthenticated()) return;
    
    setIsLoadingConsultations(true);
    try {
      console.log("Chargement des conversations unifiées pour les paramètres...");
      
      // Utiliser le service unifié pour charger les conversations
      const data = await conversationUnifiedService.getConversationHistory();
      
      if (data && Array.isArray(data)) {
        const formattedConsultations = data.map(c => ({
          id: c.id || "",
          title: c.title || "Sans titre",
          date: c.created_at || new Date().toISOString(),
          messagesCount: c.messages_count || 0,
          summary: c.summary || "Pas de résumé"
        }));
        
        console.log(`${formattedConsultations.length} conversations chargées dans les paramètres`);
        setConsultations(formattedConsultations);
      } else {
        setConsultations([]);
      }
    } catch (error) {
      console.error("Erreur lors du chargement des conversations:", error);
      setConsultations([]);
    } finally {
      setIsLoadingConsultations(false);
    }
  };
  // Supprimer une consultation (conversation unifiée)
  const deleteConsultation = async (id: string) => {
    if (!authService.isAuthenticated()) return;
    
    setIsDeletingConsultation(id);
    setConsultationDeleteError(null);
    setConsultationDeleteSuccess(false);
    
    try {
      console.log(`Suppression de la conversation unifiée ${id}`);
      
      // Utiliser le service unifié pour supprimer la conversation
      const success = await conversationUnifiedService.deleteConversation(id);
      
      if (success) {
        setConsultations(prev => prev.filter(c => c.id !== id));
        setConsultationDeleteSuccess(true);
        
        console.log(`Conversation ${id} supprimée avec succès`);
        
        if (onSettingsChanged) {
          onSettingsChanged();
        }
        
        // Masquer le message de succès après quelques secondes
        setTimeout(() => {
          setConsultationDeleteSuccess(false);
        }, 3000);
      } else {
        setConsultationDeleteError("Impossible de supprimer cette conversation.");
      }
    } catch (error) {
      console.error("Erreur lors de la suppression de la conversation:", error);
      setConsultationDeleteError("Une erreur est survenue lors de la suppression.");
    } finally {
      setIsDeletingConsultation(null);
    }
  };
  // Changer le mot de passe
  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    
    setPasswordChangeError(null);
    setPasswordChangeSuccess(false);
    
    // Validation des champs simplifiée (ne demande plus l'ancien mot de passe)
    if (!newPassword || !confirmPassword) {
      setPasswordChangeError("Veuillez remplir tous les champs.");
      return;
    }
    
    if (newPassword !== confirmPassword) {
      setPasswordChangeError("Les mots de passe ne correspondent pas.");
      return;
    }
    
    // Vérification de la force du mot de passe
    if (newPassword.length < 8) {
      setPasswordChangeError("Le mot de passe doit contenir au moins 8 caractères.");
      return;
    }
    
    setIsChangingPassword(true);
    
    try {
      // Appeler le service d'authentification pour changer le mot de passe (sans demander l'ancien)
      const success = await authService.changePassword({
        email,
        new_password: newPassword
      });
      
      if (success) {
        setPasswordChangeSuccess(true);
        setCurrentPassword("");
        setNewPassword("");
        setConfirmPassword("");
        
        // Masquer le message de succès après quelques secondes
        setTimeout(() => {
          setPasswordChangeSuccess(false);
        }, 3000);
      } else {
        setPasswordChangeError("Impossible de changer le mot de passe. Veuillez vérifier vos informations.");
      }
    } catch (error) {
      console.error("Erreur lors du changement de mot de passe:", error);
      setPasswordChangeError("Une erreur est survenue. Veuillez réessayer plus tard.");
    } finally {
      setIsChangingPassword(false);
    }
  };

  // Réinitialiser tous les états
  const resetStates = () => {
    setCurrentPassword("");
    setNewPassword("");
    setConfirmPassword("");
    setPasswordChangeError(null);
    setPasswordChangeSuccess(false);
    setConsultationDeleteError(null);
    setConsultationDeleteSuccess(false);
  };

  // Formater la date
  const formatDate = (dateStr: string) => {
    try {
      return new Date(dateStr).toLocaleDateString('fr-FR', {
        day: "numeric",
        month: "long",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit"
      });
    } catch (e) {
      return "Date inconnue";
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-3xl">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold text-emerald-800 flex items-center gap-2">
            <Settings className="h-6 w-6" />
            Paramètres
          </DialogTitle>
        </DialogHeader>

        <Tabs defaultValue="password" className="mt-4">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="password">
              <Key className="h-4 w-4 mr-2" />
              Mot de passe
            </TabsTrigger>
            <TabsTrigger value="history">
              <History className="h-4 w-4 mr-2" />
              Historique
            </TabsTrigger>
          </TabsList>
          
          {/* Onglet de changement de mot de passe */}
          <TabsContent value="password" className="mt-4">
            <Card>
              <CardHeader>
                <CardTitle>Changer de mot de passe</CardTitle>
                <CardDescription>
                  Modifiez votre mot de passe pour sécuriser votre compte.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleChangePassword} className="space-y-4">
                  {passwordChangeError && (
                    <Alert variant="destructive" className="bg-red-50 text-red-800 border-red-200">
                      <AlertCircle className="h-4 w-4" />
                      <AlertTitle>Erreur</AlertTitle>
                      <AlertDescription>{passwordChangeError}</AlertDescription>
                    </Alert>
                  )}

                  {passwordChangeSuccess && (
                    <Alert className="bg-green-50 text-green-800 border-green-200">
                      <CheckCircle2 className="h-4 w-4" />
                      <AlertTitle>Succès</AlertTitle>
                      <AlertDescription>Votre mot de passe a été modifié avec succès.</AlertDescription>
                    </Alert>
                  )}

                  <div className="space-y-2">
                    <Label htmlFor="email">Email</Label>
                    <Input
                      id="email"
                      type="email"
                      value={email}
                      readOnly
                      className="bg-gray-50"
                    />
                  </div>                  {/* Le champ de mot de passe actuel a été supprimé pour simplifier le processus */}

                  <div className="space-y-2">
                    <Label htmlFor="new-password">Nouveau mot de passe</Label>
                    <Input
                      id="new-password"
                      type="password"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="confirm-password">Confirmer le nouveau mot de passe</Label>
                    <Input
                      id="confirm-password"
                      type="password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      required
                    />
                  </div>
                
                  <Button 
                    type="submit" 
                    className="w-full bg-emerald-600 hover:bg-emerald-700" 
                    disabled={isChangingPassword}
                  >
                    {isChangingPassword ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Modification en cours...
                      </>
                    ) : "Changer mon mot de passe"}
                  </Button>
                </form>
              </CardContent>
            </Card>
          </TabsContent>
          
          {/* Onglet de gestion de l'historique */}
          <TabsContent value="history" className="mt-4">
            <Card>
              <CardHeader>
                <CardTitle>Historique des consultations</CardTitle>
                <CardDescription>
                  Gérez vos consultations précédentes.
                </CardDescription>
              </CardHeader>
              <CardContent>
                {consultationDeleteSuccess && (
                  <Alert className="mb-4 bg-green-50 text-green-800 border-green-200">
                    <CheckCircle2 className="h-4 w-4" />
                    <AlertTitle>Succès</AlertTitle>
                    <AlertDescription>La consultation a été supprimée avec succès.</AlertDescription>
                  </Alert>
                )}

                {consultationDeleteError && (
                  <Alert variant="destructive" className="mb-4 bg-red-50 text-red-800 border-red-200">
                    <AlertCircle className="h-4 w-4" />
                    <AlertTitle>Erreur</AlertTitle>
                    <AlertDescription>{consultationDeleteError}</AlertDescription>
                  </Alert>
                )}                {isLoadingConsultations ? (
                  <div className="flex items-center justify-center h-32">
                    <Loader2 className="h-8 w-8 text-emerald-600 animate-spin" />
                    <span className="ml-2 text-emerald-600">Chargement des consultations...</span>
                  </div>
                ) : consultations.length === 0 ? (
                  <div className="text-center py-8">
                    <p className="text-gray-500">Vous n'avez pas encore de consultations.</p>
                  </div>
                ) : (
                  <div className="space-y-3 max-h-[350px] overflow-y-auto pr-2 custom-scrollbar">
                    {consultations.map((consultation) => (
                      <div 
                        key={consultation.id} 
                        className="border rounded-lg p-4 flex justify-between items-center"
                      >
                        <div>
                          <h3 className="font-medium text-gray-800">{consultation.title}</h3>
                          <p className="text-sm text-gray-500">
                            {formatDate(consultation.date)} • {consultation.messagesCount} messages
                          </p>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => deleteConsultation(consultation.id)}
                          disabled={isDeletingConsultation === consultation.id}
                          className="text-red-600 hover:text-red-700 hover:bg-red-50"
                        >
                          {isDeletingConsultation === consultation.id ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <Trash2 className="h-4 w-4" />
                          )}
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  )
}
