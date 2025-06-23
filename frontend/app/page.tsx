"use client"

import { useState, useEffect } from "react"
import { Header } from "@/components/header"
import { MainActions } from "@/components/main-actions"
import { ChatInterface } from "@/components/chat-interface"
import { PlantCard } from "@/components/plant-card"
import { Button } from "@/components/ui/button"
import { ArrowLeft, AlertCircle } from "lucide-react"
import { CountrySelection } from "@/components/country-selection"
import { TradipraticiensList } from "@/components/tradipraticiens-list"
import { ConsultationHistory } from "@/components/consultation-history"
import { UnifiedConversationHistory } from "@/components/unified-conversation-history"
import { PreDiagnostic } from "@/components/pre-diagnostic"
import { samplePlants } from "@/data/samplePlants" // Import samplePlants
import { authService } from "@/services/auth-service"
import { consultationService } from "@/services/consultation-service"
import { Card, CardContent } from "@/components/ui/card"

type View = "home" | "tradipraticiens" | "country" | "consultations" | "chat" | "diagnostic" | "solutions" | "history"

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

const sampleTradipraticiens: Record<string, Tradipraticien[]> = {
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

// Type pour le traditionpraticien
interface Tradipraticien {
  id: number;
  name: string;
  localName: string;
  country: string;
  city: string;
  province: string;
  village: string;
  phone: string;
  specialties: string[];
  experience: string;
}

// Type pour les consultations
interface UserConsultation {
  id: string | number;
  title: string;
  date?: string;
  created_at?: string;
  summary?: string;
  messages_count?: number;
  messagesCount?: number; // Pour compatibilité avec le composant ConsultationHistory
  messages?: any[];
}

// Type pour la conversation en cours
interface CurrentConversation {
  messages: any[];
  mode: string;
  consultation?: any;
}

export default function Home() {
  const [currentView, setCurrentView] = useState<View>("home")
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [selectedCountry, setSelectedCountry] = useState<string | null>(null)
  const [selectedConsultation, setSelectedConsultation] = useState<string | null>(null)
  // État pour stocker les consultations de l'utilisateur
  const [userConsultations, setUserConsultations] = useState<UserConsultation[]>([])
  const [isLoadingConsultations, setIsLoadingConsultations] = useState(false)
  // État pour stocker la conversation en cours entre les navigations
  const [currentConversation, setCurrentConversation] = useState<CurrentConversation | null>(null)
  
  // Vérifier l'authentification au chargement de la page
  useEffect(() => {
    // Vérifier si l'utilisateur est authentifié
    const isUserAuthenticated = authService.isAuthenticated();
    console.log("État d'authentification au chargement:", isUserAuthenticated);
    setIsAuthenticated(isUserAuthenticated);
    
    // Si l'utilisateur est authentifié, charger ses données
    if (isUserAuthenticated) {
      console.log("Utilisateur authentifié automatiquement, chargement de l'historique des consultations");
      // Délai court pour s'assurer que le token est bien validé et disponible
      setTimeout(() => {
        loadUserConsultations();
      }, 300);
    }
  }, []);
  
  // Fonction pour charger les consultations de l'utilisateur
  const loadUserConsultations = async () => {
    if (!authService.isAuthenticated()) {
      console.log("loadUserConsultations: Tentative de charger les consultations sans être authentifié");
      setUserConsultations([]);
      return;
    }
    
    try {
      console.log("loadUserConsultations: Démarrage du chargement des consultations...");
      setIsLoadingConsultations(true);
      
      // Vérifier la validité du token avant de tenter de charger les consultations
      console.log("loadUserConsultations: Validation du token...");
      const isValid = await authService.validateToken();
      if (!isValid) {
        console.log("loadUserConsultations: Token invalide, impossible de charger les consultations");
        setUserConsultations([]);
        setIsLoadingConsultations(false);
        return;
      }
      
      console.log("loadUserConsultations: Token valide, appel du service pour récupérer les consultations");
      const consultations = await consultationService.getConsultations();
      console.log(`loadUserConsultations: Consultations chargées: ${consultations.length} consultations trouvées`);
      
      // Vérifier les détails de chaque consultation pour le débogage
      consultations.forEach((c, index) => {
        const messageCount = c.messages_count || (c.messages?.length || 0);
        console.log(`Consultation #${index+1} - ID: ${c.id}, Titre: ${c.title}, Messages: ${messageCount}, Date: ${c.created_at || c.date}`);
      });
      
      if (!consultations || consultations.length === 0) {
        setUserConsultations([]);
        return;
      }
      
      // Convertir le format pour correspondre à l'interface du composant ConsultationHistory
      const formattedConsultations = consultations
        .filter(c => {
          // Filtrer pour ne conserver que les conversations avec au moins 4 messages (deux échanges complets)
          const messageCount = c.messages_count || (c.messages?.length || 0);
          console.log(`Consultation ${c.id}, nombre de messages: ${messageCount}`);
          // Critère de filtrage: au moins 4 messages pour une conversation valide
          const isValidConversation = messageCount >= 4;
          if (!isValidConversation) {
            console.log(`Consultation ${c.id} ignorée: seulement ${messageCount} messages (minimum 4 requis)`);
          }
          return isValidConversation;
        })
        .map(c => {
          // Utiliser une chaîne vide par défaut pour l'ID pour éviter undefined
          const consultationId = c.id || "";
          const date = c.created_at || c.date || new Date().toISOString();
          const summary = c.summary || 
            (c.messages && c.messages.length > 0 ? c.messages[0].content.substring(0, 100) + "..." : "Pas de résumé disponible");
          const count = c.messages_count || (c.messages?.length || 0);
          
          return {
            id: consultationId,
            title: c.title || "Consultation sans titre",
            date: date,
            summary: summary,
            messagesCount: count,
          };
        })
        // Trier les consultations par date, les plus récentes en premier
        .sort((a, b) => {
          const dateA = new Date(a.date || "").getTime() || 0;
          const dateB = new Date(b.date || "").getTime() || 0;
          return dateB - dateA;
        });
      
      setUserConsultations(formattedConsultations);
      console.log(`${formattedConsultations.length} consultations chargées, filtrées et triées avec succès`);
      
      // Vérifier qu'il y a bien des consultations à afficher
      if (formattedConsultations.length === 0) {
        console.log("⚠️ Aucune consultation à afficher après filtrage. Vérifiez les critères de filtrage ou la sauvegarde des sessions.");
      } else {
        console.log("Consultations disponibles pour l'affichage:", formattedConsultations.map(c => 
          `${c.id} (${c.title?.substring(0, 20) || 'Sans titre'}... - ${c.messagesCount || '?'} messages)`
        ).join(', '));
      }
    } catch (error) {
      console.error("Erreur lors du chargement des consultations:", error);
      setUserConsultations([]);
    } finally {
      setIsLoadingConsultations(false);
    }
  };

  // Effet pour recharger l'historique quand l'utilisateur visite la page des consultations
  useEffect(() => {
    if (currentView === "consultations" && isAuthenticated) {
      console.log("Accès à la page des consultations, chargement de l'historique");
      loadUserConsultations();
    }
  }, [currentView, isAuthenticated]);
  
  const handleViewChange = (view: View) => {
    // Si on navigue vers l'historique ou les consultations et qu'on est connecté, recharger les consultations
    if ((view === "history" || view === "consultations") && isAuthenticated) {
      console.log(`Navigation vers ${view}: rechargement des consultations`);
      loadUserConsultations();
    }
    
    setCurrentView(view);
  };

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
        // Si l'utilisateur n'est pas authentifié, afficher un message
        if (!isAuthenticated) {
          return (
            <div className="space-y-6">
              <div className="flex items-center gap-4 mb-6">
                <Button 
                  variant="ghost" 
                  size="sm" 
                  onClick={() => handleViewChange("home")}
                  className="text-emerald-700 hover:text-emerald-800"
                >
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Retour
                </Button>
                <h2 className="text-2xl font-bold text-emerald-800">Historique des consultations</h2>
              </div>
              
              <Card className="border-amber-100">
                <CardContent className="p-8 text-center">
                  <AlertCircle className="h-16 w-16 text-amber-500 mx-auto mb-4" />
                  <p className="text-amber-800 text-lg mb-2">Vous devez être connecté pour accéder à cette fonctionnalité</p>
                  <p className="text-sm text-gray-600 mb-4">
                    Connectez-vous pour voir et gérer votre historique de consultations.
                  </p>
                  <Button 
                    onClick={() => {
                      // Retourner à l'accueil où l'utilisateur pourra se connecter
                      handleViewChange("home")
                    }}
                    variant="outline" 
                    className="bg-amber-50 border-amber-200 text-amber-800 hover:bg-amber-100"
                  >
                    Retour à l'accueil
                  </Button>
                </CardContent>
              </Card>
            </div>
          );
        }
          // Sinon, afficher l'historique des conversations unifiées
        return (
          <UnifiedConversationHistory
            isAuthenticated={isAuthenticated}
            onConversationSelect={(id) => {
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
          <ConsultationHistory 
            consultations={userConsultations} 
            onConsultationSelect={(id) => {
              setSelectedConsultation(id);
              handleViewChange("chat");
            }} 
            onBack={() => handleViewChange("home")}
            isLoading={isLoadingConsultations}
          />
        )
      case "chat":
        return <ChatInterface 
          onBack={() => handleViewChange("home")}
          isAuthenticated={isAuthenticated}
          onAuthChange={setIsAuthenticated}
          consultationId={selectedConsultation || undefined}
          currentConversation={currentConversation}
          onConversationChange={(conversation) => {
            console.log("Mise à jour de la conversation courante:", conversation);
            setCurrentConversation(conversation);
          }}
        />
      default:
        return (
          <>
            <MainActions onActionClick={handleViewChange} />
            <ChatInterface 
              onStartChat={() => handleViewChange("chat")}
              isWelcome
              isAuthenticated={isAuthenticated}
              onAuthChange={setIsAuthenticated}
              currentConversation={currentConversation}
              onConversationChange={(conversation) => {
                console.log("Mise à jour de la conversation courante (accueil):", conversation);
                setCurrentConversation(conversation);
              }}
            />
          </>
        )
    }
  }
  // Fonction pour gérer la déconnexion depuis l'en-tête
  const handleAuthChange = (authStatus: boolean) => {
    setIsAuthenticated(authStatus);
    
    // Si l'utilisateur s'est déconnecté
    if (!authStatus) {
      console.log("Déconnexion détectée : réinitialisation de l'état de l'application");
      
      // Réinitialiser la liste des consultations
      setUserConsultations([]);
      
      // Réinitialiser la consultation sélectionnée
      setSelectedConsultation(null);
      
      // Réinitialiser la conversation actuelle
      setCurrentConversation(null);
      
      // Revenir à l'écran d'accueil
      setCurrentView("home");
    } else {
      // L'utilisateur vient de se connecter, charger ses consultations
      loadUserConsultations();
    }
  };

  // Fonction pour gérer les changements de paramètres (ex: suppression de consultation)
  const handleSettingsChanged = () => {
    console.log("Changements de paramètres détectés - rechargement des consultations");
    // Recharger les consultations pour refléter les changements (suppressions, etc.)
    if (isAuthenticated) {
      loadUserConsultations();
    }
  };
    return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-white to-amber-50">
      <Header 
        isAuthenticated={isAuthenticated} 
        onAuthChange={handleAuthChange}
        onSettingsChanged={handleSettingsChanged}
        onLogoClick={() => {
          setCurrentView("home");
          setSelectedConsultation(null);
          setCurrentConversation(null);
        }}
      />

      <main className="container mx-auto px-4 py-8 max-w-6xl">{renderContent()}</main>
    </div>
  )
}
