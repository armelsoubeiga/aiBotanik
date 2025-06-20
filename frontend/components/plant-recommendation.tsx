import React from "react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Leaf, Info, Pill, AlertTriangle, FlaskConical, BookOpenText, FlowerIcon, GlobeIcon } from "lucide-react";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";

export interface PlantRecommendation {
  plant: string;
  dosage: string;
  prep: string;
  image_url: string;
  explanation: string;
  contre_indications: string;
  partie_utilisee: string;
  composants: string;
  nom_local: string;
}

interface PlantRecommendationCardProps {
  recommendation: PlantRecommendation;
}

export function PlantRecommendationCard({ recommendation }: PlantRecommendationCardProps) {
  // Vérifier si la recommandation est valide
  if (!recommendation) {
    console.error("Recommendation invalide ou manquante");
    return renderErrorCard("Les détails de cette recommandation ne sont pas disponibles.");
  }

  // Vérifier le type de la recommandation
  if (typeof recommendation !== 'object') {
    console.error(`Recommendation dans un format invalide: ${typeof recommendation}`);
    return renderErrorCard(`Format de recommandation non valide: ${typeof recommendation}`);
  }

  // Vérifier les champs obligatoires minimaux
  if (!recommendation.plant) {
    console.error("Recommendation sans nom de plante");
    return renderErrorCard("Cette recommandation est incomplète (nom de plante manquant).");
  }
  
  // Débogage pour voir exactement ce qui est reçu
  console.log(`Recommendation reçue pour la plante: ${recommendation.plant}`);
  
  // Essayer de traiter la recommandation comme une chaîne JSON si nécessaire
  let processedRecommendation = recommendation;
  
  if (typeof recommendation === 'string') {
    try {
      processedRecommendation = JSON.parse(recommendation);
      console.log("Recommandation convertie de chaîne en objet avec succès");
    } catch(e) {
      console.error("Impossible de parser la recommandation depuis la chaîne:", e);
      return renderErrorCard("Impossible de traiter les détails de cette recommandation.");
    }
  }
  
  // Assurer que tous les champs requis sont présents
  const requiredFields: Record<keyof PlantRecommendation, string> = {
    plant: "Plante non spécifiée",
    dosage: "Dosage non spécifié",
    prep: "Préparation non spécifiée",
    image_url: "",
    explanation: "",
    contre_indications: "Aucune contre-indication connue",
    partie_utilisee: "Non spécifié",
    composants: "Non spécifié",
    nom_local: ""
  };
  
  // Compléter les champs manquants pour garantir l'affichage complet
  for (const field of Object.keys(requiredFields) as Array<keyof PlantRecommendation>) {
    if (!processedRecommendation[field]) {
      processedRecommendation[field] = requiredFields[field];
      console.warn(`Champ '${field}' manquant dans la recommandation, valeur par défaut ajoutée`);
    }
  }
  
  // Valider que l'explication existe et normaliser si nécessaire
  const safeExplanation = processedRecommendation.explanation || "";
  
  // Fonction utilitaire pour afficher une carte d'erreur
  function renderErrorCard(message: string) {
    return (
      <Card className="border-amber-200 mb-4">
        <CardHeader>
          <h3 className="text-lg font-semibold text-amber-700">
            Erreur d'affichage de la recommandation
          </h3>
        </CardHeader>
        <CardContent>
          <p className="text-amber-600">{message}</p>
        </CardContent>
      </Card>
    );
  }
  console.log("Explication complète (longueur):", safeExplanation.length);
  
  // Ajouter des informations de débogage supplémentaires
  if (!safeExplanation) {
    console.warn("⚠️ L'explication est vide ou manquante");
  } else if (safeExplanation.length < 100) {
    console.warn(`⚠️ L'explication semble très courte (${safeExplanation.length} caractères):`);
    console.log(safeExplanation);
  }
  // Extraction des sections de l'explication (basées sur la structure du prompt dans le backend)
  const extractSections = (text: string) => {
    const sections = [
      "Diagnostic possible",
      "Symptômes associés",
      "Présentation de",
      "Mode d'action",
      "Informations de traitement",
      "Précautions et contre-indications",
      "Composants actifs",
      "Résumé de traitement"
    ];
    
    const result: Record<string, string> = {};
    
    // Si l'explication est vide ou indéfinie, retourner un objet avec des valeurs par défaut
    if (!text) {
      console.log("ERREUR: Texte d'explication vide ou non défini");
      result["Diagnostic possible"] = "Les informations de diagnostic ne sont pas disponibles pour le moment.";
      result["Résumé de traitement"] = "Consultez les détails de préparation et de dosage ci-dessous pour ce remède.";
      return result;
    }
    
    console.log("Extraction des sections depuis l'explication:", text.substring(0, 100) + "...");
    
    // Détection du format du texte (présence de sections ou texte brut)
    const containsMarkers = sections.some(section => text.includes(section));
    
    // Si le texte contient des marqueurs de sections, procéder à l'extraction normale
    if (containsMarkers) {
      let currentSection = "";
      let currentContent: string[] = [];
      
      // Normaliser le texte pour éviter les problèmes de formatage
      const normalizedText = text.replace(/\r\n/g, "\n").trim();
      const lines = normalizedText.split("\n");
      
      for (const line of lines) {
        const trimmedLine = line.trim();
        
        // Vérifier si la ligne correspond à un en-tête de section
        const foundSection = sections.find(section => 
          trimmedLine === section || 
          trimmedLine.startsWith(section + " ")
        );
        
        if (foundSection) {
          console.log("Section trouvée:", foundSection);
          
          // Si on a déjà une section en cours, on l'enregistre
          if (currentSection && currentContent.length > 0) {
            result[currentSection] = currentContent.join("\n");
            currentContent = [];
          }
          
          currentSection = foundSection;
        } else if (currentSection) {
          // Ajouter à la section en cours
          currentContent.push(line);
        }
      }
      
      // Enregistrer la dernière section
      if (currentSection && currentContent.length > 0) {
        result[currentSection] = currentContent.join("\n");
      }
    }
    
    // Si aucune section n'a été correctement extraite, essayer une approche différente
    if (Object.keys(result).length === 0) {
      console.log("Méthode alternative d'extraction de sections");
      
      // Normaliser le texte et le diviser en blocs
      const normalizedText = text.replace(/\r\n/g, "\n").trim();
      
      // Essayer de diviser par double saut de ligne
      const blocks = normalizedText.split(/\n\s*\n/).filter(block => block.trim());
      
      console.log(`Nombre de blocs de texte identifiés: ${blocks.length}`);
      
      // Si nous avons suffisamment de blocs, essayer de les associer aux sections
      if (blocks.length >= 3) {
        // Analyser chaque bloc pour trouver des indices sur son contenu
        blocks.forEach((block, index) => {
          const lowerBlock = block.toLowerCase();
          
          // Catégoriser les blocs
          if (index === 0 || lowerBlock.includes("diagnostic") || lowerBlock.includes("symptôme")) {
            result["Diagnostic possible"] = block;
          } else if (lowerBlock.includes("préparation") || lowerBlock.includes("dosage") || lowerBlock.includes("traitement") && !result["Informations de traitement"]) {
            result["Informations de traitement"] = block;
          } else if (lowerBlock.includes("action") || lowerBlock.includes("effet")) {
            result["Mode d'action"] = block;
          } else if (lowerBlock.includes("composant") || lowerBlock.includes("actif")) {
            result["Composants actifs"] = block;
          } else if (lowerBlock.includes("précaution") || lowerBlock.includes("contre-indication") || lowerBlock.includes("risque")) {
            result["Précautions et contre-indications"] = block;
          } else if (index === blocks.length - 1 || lowerBlock.includes("résumé")) {
            result["Résumé de traitement"] = block;
          } else if (lowerBlock.includes("présentation") || lowerBlock.includes("plante")) {
            result["Présentation de"] = block;
          }
        });
        
        // Assurer au minimum un diagnostic et un résumé
        if (!result["Diagnostic possible"] && blocks.length > 0) {
          result["Diagnostic possible"] = blocks[0];
        }
        
        if (!result["Résumé de traitement"] && blocks.length > 1) {
          result["Résumé de traitement"] = blocks[blocks.length - 1];
        }
      } 
      // Si nous n'avons pas assez de blocs ou aucune section n'a été identifiée
      else {
        console.log("Création de sections par défaut à partir du texte brut");
        
        // Utiliser tout le texte comme diagnostic
        result["Diagnostic possible"] = normalizedText;
        
        // Si le texte est assez long, créer un résumé à partir de la fin
        if (normalizedText.length > 200) {
          const lastSentences = normalizedText.split(/[.!?]/).slice(-3).join(". ") + ".";
          result["Résumé de traitement"] = lastSentences;
        }
      }
    }
    
    console.log("Sections extraites:", Object.keys(result));
    return result;
  };

  // S'assurer que l'explication existe et n'est pas undefined avant d'extraire les sections
  const sections = extractSections(recommendation?.explanation || "");

  return (
    <Card className="border-emerald-100 hover:shadow-md transition-all duration-300 bg-gradient-to-br from-white to-emerald-50 overflow-hidden">
      <div className="relative">
        {recommendation.image_url && (
          <div className="w-full h-64 relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-b from-transparent to-emerald-900/60 z-10" />
            <div 
              className="w-full h-full bg-cover bg-center" 
              style={{backgroundImage: `url(${recommendation.image_url})`}}
            />
          </div>
        )}
        
        <CardHeader className="relative bg-emerald-700 px-6 py-5">
          <div className="flex flex-col text-white">
            <div className="flex items-center gap-2 mb-1">
              <Leaf className="h-5 w-5" />
              <h2 className="text-xl md:text-2xl font-bold">{recommendation.plant}</h2>
            </div>
            {recommendation.nom_local && (
              <div className="flex items-center gap-1 text-emerald-100 text-sm">
                <GlobeIcon className="h-3.5 w-3.5" />
                <span>{recommendation.nom_local}</span>
              </div>
            )}
          </div>
        </CardHeader>
      </div>

      <CardContent className="px-6 pt-5 pb-6 space-y-6">
        {/* Diagnostic et information principale */}
        {sections["Diagnostic possible"] && (
          <div className="bg-white rounded-xl p-5 shadow-sm border border-emerald-100">
            <h3 className="text-lg font-medium text-emerald-800 mb-3 flex items-center gap-2">
              <Info className="h-5 w-5" />
              Diagnostic
            </h3>
            <div className="text-gray-700 leading-relaxed">
              {sections["Diagnostic possible"]}
            </div>
          </div>
        )}

        {/* Résumé du traitement */}
        {sections["Résumé de traitement"] && (
          <div className="bg-emerald-50 rounded-xl p-5 border border-emerald-200">
            <h3 className="text-lg font-medium text-emerald-800 mb-2 flex items-center gap-2">
              <BookOpenText className="h-5 w-5" />
              Résumé du traitement
            </h3>
            <div className="text-emerald-700 leading-relaxed">
              {sections["Résumé de traitement"]}
            </div>
          </div>
        )}

        {/* D�tails pliables */}
        <Accordion type="single" collapsible className="w-full">
          {/* Symptômes associés */}
          {sections["Symptômes associés"] && (
            <AccordionItem value="symptoms" className="border-emerald-200">
              <AccordionTrigger className="text-emerald-700 hover:text-emerald-800">
                <div className="flex items-center gap-2">
                  <Pill className="h-4 w-4" />
                  Symptômes associés
                </div>
              </AccordionTrigger>
              <AccordionContent className="text-gray-700 px-2">
                {sections["Symptômes associés"]}
              </AccordionContent>
            </AccordionItem>
          )}

          {/* Présentation de la plante */}
          {sections["Présentation de"] && (
            <AccordionItem value="presentation" className="border-emerald-200">
              <AccordionTrigger className="text-emerald-700 hover:text-emerald-800">
                <div className="flex items-center gap-2">
                  <FlowerIcon className="h-4 w-4" />
                  Présentation de {recommendation.plant}
                </div>
              </AccordionTrigger>
              <AccordionContent className="text-gray-700 px-2">
                {sections["Présentation de"]}
              </AccordionContent>
            </AccordionItem>
          )}

          {/* Mode d'action */}
          {sections["Mode d'action"] && (
            <AccordionItem value="mode" className="border-emerald-200">
              <AccordionTrigger className="text-emerald-700 hover:text-emerald-800">
                <div className="flex items-center gap-2">
                  <FlaskConical className="h-4 w-4" />
                  Mode d'action
                </div>
              </AccordionTrigger>
              <AccordionContent className="text-gray-700 px-2">
                {sections["Mode d'action"]}
              </AccordionContent>
            </AccordionItem>
          )}

          {/* Informations de traitement */}
          {sections["Informations de traitement"] && (
            <AccordionItem value="treatment" className="border-emerald-200">
              <AccordionTrigger className="text-emerald-700 hover:text-emerald-800">
                <div className="flex items-center gap-2">
                  <Leaf className="h-4 w-4" />
                  Informations de traitement
                </div>
              </AccordionTrigger>
              <AccordionContent className="text-gray-700 px-2">
                {sections["Informations de traitement"]}                  <div className="mt-4 p-3 bg-amber-50 rounded-lg border border-amber-100">
                  <div className="mb-3">
                    <h4 className="font-medium text-amber-800">Préparation</h4>
                    <p className="text-amber-700">{recommendation.prep}</p>
                  </div>
                  
                  <div className="mb-3">
                    <h4 className="font-medium text-amber-800">Dosage</h4>
                    <p className="text-amber-700 whitespace-pre-line">{recommendation.dosage}</p>
                  </div>
                  
                  <div>
                    <h4 className="font-medium text-amber-800">Parties utilisées</h4>
                    <p className="text-amber-700 whitespace-pre-line">{recommendation.partie_utilisee}</p>
                  </div>
                </div>
              </AccordionContent>
            </AccordionItem>
          )}

          {/* Précautions */}
          {(sections["Précautions et contre-indications"] || recommendation.contre_indications) && (
            <AccordionItem value="warnings" className="border-emerald-200">
              <AccordionTrigger className="text-emerald-700 hover:text-emerald-800">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4" />
                  Précautions et contre-indications
                </div>
              </AccordionTrigger>
              <AccordionContent className="text-gray-700 px-2">
                {sections["Précautions et contre-indications"] || (
                  <div className="p-3 bg-red-50 rounded-lg border border-red-100 text-red-700">
                    {recommendation.contre_indications || "Aucune contre-indication spécifiée"}
                  </div>
                )}
              </AccordionContent>
            </AccordionItem>
          )}

          {/* Composants actifs */}
          {(sections["Composants actifs"] || recommendation.composants) && (
            <AccordionItem value="components" className="border-emerald-200">
              <AccordionTrigger className="text-emerald-700 hover:text-emerald-800">
                <div className="flex items-center gap-2">
                  <FlaskConical className="h-4 w-4" />
                  Composants actifs
                </div>
              </AccordionTrigger>
              <AccordionContent className="text-gray-700 px-2">
                {sections["Composants actifs"] || (
                  <div className="whitespace-pre-line">{recommendation.composants}</div>
                )}
              </AccordionContent>
            </AccordionItem>
          )}
        </Accordion>
      </CardContent>
    </Card>
  );
}
