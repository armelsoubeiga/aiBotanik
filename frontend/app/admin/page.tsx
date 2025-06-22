"use client";

import React, { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { toast } from "@/components/ui/use-toast";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Separator } from "@/components/ui/separator";
import { AlertCircle, Check, Info, Settings, Terminal, TerminalSquare } from "lucide-react";
// Configuration des URLs backend
import { API_URL, BASE_URL } from "@/lib/config";

export default function AdminPage() {
  const [loading, setLoading] = useState(false);
  const [config, setConfig] = useState({
    llm_backend: "huggingface",
    hasOpenAIKey: false,
    hasHFKey: false,
  });
  const [openAIKey, setOpenAIKey] = useState("");
  const [rebuilding, setRebuilding] = useState(false);
  const [testingConnection, setTestingConnection] = useState(false);
  const [testResponse, setTestResponse] = useState("");

  useEffect(() => {
    // Charger la configuration actuelle
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    try {
      const response = await fetch(`${BASE_URL}/admin/config/llm`);
      
      if (response.ok) {
        const data = await response.json();
        setConfig({
          llm_backend: data.llm_backend,
          hasOpenAIKey: data.has_openai_key,
          hasHFKey: data.has_hf_key,
        });
      } else {
        toast({
          title: "Erreur",
          description: "Impossible de récupérer la configuration",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error("Erreur lors de la récupération de la configuration:", error);
      toast({
        title: "Erreur de connexion",
        description: "Assurez-vous que le backend est démarré et accessible.",
        variant: "destructive",
      });
    }
  };

  const saveConfig = async () => {
    setLoading(true);    try {
      const payload: any = {
        llm_backend: config.llm_backend,
      };

      // Ajouter la clé API si OpenAI est sélectionné et qu'une clé est fournie
      if (config.llm_backend === "openai" && openAIKey) {
        payload.api_key = openAIKey;
      }

      const response = await fetch(`${BASE_URL}/admin/config/llm`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      const data = await response.json();      if (data.status === "success") {
        const backendName = config.llm_backend === "openai" ? "OpenAI" : "HuggingFace";
        toast({
          title: "✅ Configuration sauvegardée",
          description: `Backend LLM changé vers ${backendName}. ${data.message}`,
        });
        // Mettre à jour l'état local
        fetchConfig();
        // Réinitialiser le champ de la clé API
        setOpenAIKey("");
      } else {
        toast({
          title: "Erreur",
          description: data.message,
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error("Erreur lors de la sauvegarde de la configuration:", error);
      toast({
        title: "Erreur de connexion",
        description: "Impossible de sauvegarder la configuration.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const rebuildIndex = async () => {
    setRebuilding(true);

    try {
      const response = await fetch(`${BASE_URL}/admin/rebuild-index`, {
        method: "POST",
      });

      const data = await response.json();

      if (response.ok) {
        toast({
          title: "Index reconstruit",
          description: "L'index vectoriel a été reconstruit avec succès.",
        });
      } else {
        toast({
          title: "Erreur",
          description: data.detail || "Impossible de reconstruire l'index",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error("Erreur lors de la reconstruction de l'index:", error);
      toast({
        title: "Erreur de connexion",
        description: "Impossible de reconstruire l'index.",
        variant: "destructive",
      });
    } finally {
      setRebuilding(false);
    }
  };

  const testLLM = async () => {
    setTestingConnection(true);
    setTestResponse("");

    try {
      const response = await fetch(`${BASE_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ symptoms: "Bonjour, dis-moi comment tu vas?" }),
      });

      const data = await response.json();

      if (response.ok) {
        setTestResponse(data.response);
        toast({
          title: "Test réussi",
          description: `LLM (${data.backend}) a répondu en ${Math.round(data.processing_time * 100) / 100}s`,
        });
      } else {
        setTestResponse("ERREUR: " + (data.error_details || "Réponse invalide"));
        toast({
          title: "Erreur",
          description: "Le test a échoué",
          variant: "destructive",
        });
      }    } catch (error) {
      console.error("Erreur lors du test du LLM:", error);
      setTestResponse("ERREUR DE CONNEXION: " + (error as Error).message);
      toast({
        title: "Erreur de connexion",
        description: "Impossible de tester le LLM.",
        variant: "destructive",
      });
    } finally {
      setTestingConnection(false);
    }
  };

  return (
    <div className="container py-10">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold mb-2">Administration aiBotanik</h1>
          <p className="text-gray-500">Configurez le comportement du backend</p>
        </div>
        <Button variant="outline" onClick={() => window.location.href = "/"}>
          Retour à l'accueil
        </Button>
      </div>

      <Tabs defaultValue="llm">
        <TabsList className="mb-6">
          <TabsTrigger value="llm">Configuration LLM</TabsTrigger>
          <TabsTrigger value="tools">Outils</TabsTrigger>
        </TabsList>
        
        <TabsContent value="llm">
          <div className="grid gap-6 md:grid-cols-2">
            <Card>              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Settings className="w-5 h-5" />
                  Configuration du backend LLM
                </CardTitle>
                <CardDescription>
                  Choisissez le backend LLM à utiliser pour les réponses en mode Discussion et Consultation
                </CardDescription>
                
                {/* Affichage du backend actuellement actif */}
                <Alert className="mt-4">
                  <Info className="h-4 w-4" />
                  <AlertTitle>Backend actuellement actif</AlertTitle>
                  <AlertDescription>
                    <strong>
                      {config.llm_backend === "openai" ? "OpenAI (GPT-3.5-Turbo)" : "HuggingFace"}
                    </strong>
                    {config.llm_backend === "openai" && config.hasOpenAIKey && " - Clé API OpenAI validée"}
                    {config.llm_backend === "huggingface" && config.hasHFKey && " - Clé API HuggingFace validée"}
                  </AlertDescription>
                </Alert>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <RadioGroup 
                    value={config.llm_backend} 
                    onValueChange={(value) => setConfig({...config, llm_backend: value})}
                  >
                    <div className="flex items-start space-x-3 space-y-0">
                      <RadioGroupItem value="huggingface" id="huggingface" />
                      <div className="grid gap-1.5">
                        <Label htmlFor="huggingface" className="font-medium">HuggingFace (gratuit)</Label>
                        <p className="text-sm text-gray-500">
                          Utilise des modèles légers via l'API HuggingFace. Peut être limité en qualité et performances.
                          {config.hasHFKey ? (
                            <span className="text-green-600 ml-2 flex items-center gap-1 mt-1">
                              <Check className="w-3 h-3" /> Clé API configurée
                            </span>
                          ) : (
                            <span className="text-amber-600 ml-2 flex items-center gap-1 mt-1">
                              <AlertCircle className="w-3 h-3" /> Clé API non configurée
                            </span>
                          )}
                        </p>
                      </div>
                    </div>
                    <Separator className="my-4" />
                    <div className="flex items-start space-x-3 space-y-0">
                      <RadioGroupItem value="openai" id="openai" />
                      <div className="grid gap-1.5">
                        <Label htmlFor="openai" className="font-medium">OpenAI (payant)</Label>
                        <p className="text-sm text-gray-500">
                          Utilise GPT-3.5-Turbo. Meilleures réponses mais nécessite une clé API OpenAI valide.
                          {config.hasOpenAIKey ? (
                            <span className="text-green-600 ml-2 flex items-center gap-1 mt-1">
                              <Check className="w-3 h-3" /> Clé API configurée
                            </span>
                          ) : (
                            <span className="text-amber-600 ml-2 flex items-center gap-1 mt-1">
                              <AlertCircle className="w-3 h-3" /> Clé API non configurée
                            </span>
                          )}
                        </p>
                      </div>
                    </div>
                  </RadioGroup>

                  {config.llm_backend === "openai" && !config.hasOpenAIKey && (
                    <div className="mt-6">
                      <Label htmlFor="openai-key">Clé API OpenAI</Label>
                      <Input 
                        id="openai-key"
                        type="password"
                        placeholder="sk-..."
                        value={openAIKey}
                        onChange={(e) => setOpenAIKey(e.target.value)}
                        className="mt-2"
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        La clé sera stockée dans le fichier .env du backend.
                      </p>
                    </div>
                  )}

                  {config.llm_backend === "openai" && (
                    <Alert className="bg-amber-50 border-amber-200">
                      <AlertCircle className="h-4 w-4 text-amber-600" />
                      <AlertTitle>Important</AlertTitle>
                      <AlertDescription>
                        L'utilisation d'OpenAI API est payante. Des frais seront facturés sur votre compte OpenAI.
                      </AlertDescription>
                    </Alert>
                  )}
                </div>
              </CardContent>
              <CardFooter>
                <Button 
                  onClick={saveConfig} 
                  disabled={loading || (config.llm_backend === "openai" && !config.hasOpenAIKey && !openAIKey)}
                  className="w-full"
                >
                  {loading ? "Enregistrement..." : "Enregistrer la configuration"}
                </Button>
              </CardFooter>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Terminal className="w-5 h-5" />
                  Test de connexion
                </CardTitle>
                <CardDescription>
                  Testez la connexion et la qualité des réponses du LLM configuré
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Button 
                  onClick={testLLM} 
                  disabled={testingConnection}
                  className="w-full mb-4"
                >
                  {testingConnection ? "Test en cours..." : "Tester le LLM"}
                </Button>

                {testResponse && (
                  <div className="mt-4 p-4 bg-gray-50 rounded-lg border">
                    <div className="text-sm mb-2 font-medium text-gray-500">Réponse:</div>
                    <div className="text-sm whitespace-pre-wrap">{testResponse}</div>
                  </div>
                )}

                <Alert className="mt-6 bg-blue-50 border-blue-200">
                  <Info className="h-4 w-4 text-blue-600" />
                  <AlertTitle>Astuce</AlertTitle>
                  <AlertDescription>
                    Si le test échoue, vérifiez que le backend est bien démarré et que les clés API sont correctement configurées.
                  </AlertDescription>
                </Alert>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
        
        <TabsContent value="tools">
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TerminalSquare className="w-5 h-5" />
                  Outils d'administration
                </CardTitle>
                <CardDescription>
                  Outils pour la maintenance du système
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <h3 className="text-lg font-medium mb-2">Reconstruire l'index vectoriel</h3>
                    <p className="text-sm text-gray-500 mb-4">
                      Force la reconstruction de l'index FAISS utilisé pour la recherche sémantique.
                      Utile après des mises à jour manuelles de la base de données de plantes.
                    </p>
                    <Button 
                      onClick={rebuildIndex} 
                      disabled={rebuilding}
                      variant="outline"
                      className="w-full"
                    >
                      {rebuilding ? "Reconstruction en cours..." : "Reconstruire l'index"}
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
