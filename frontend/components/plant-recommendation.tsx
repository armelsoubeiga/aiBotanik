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
  // Nouveaux champs structurés venant directement du backend
  diagnostic?: string;
  symptomes?: string;
  presentation?: string;
  mode_action?: string;
  traitement_info?: string;
  precautions_info?: string;
  composants_info?: string;
  resume_traitement?: string;
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
    nom_local: "",
    // Nouveaux champs structurés (optionnels)
    diagnostic: "",
    symptomes: "",
    presentation: "",
    mode_action: "",
    traitement_info: "",
    precautions_info: "",
    composants_info: "",
    resume_traitement: ""
  };
    // Compléter les champs manquants obligatoires seulement (les champs structurés sont optionnels)
  const obligatoryFields = ["plant", "dosage", "prep", "image_url", "explanation", "contre_indications", "partie_utilisee", "composants", "nom_local"];
  
  for (const field of obligatoryFields) {
    if (!processedRecommendation[field as keyof PlantRecommendation]) {
      processedRecommendation[field as keyof PlantRecommendation] = requiredFields[field as keyof PlantRecommendation];
      console.warn(`Champ obligatoire '${field}' manquant dans la recommandation, valeur par défaut ajoutée`);
    }
  }
    // S'assurer que l'explication existe et normaliser si nécessaire
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

  // NOUVEAU: Prioriser les champs structurés s'ils sont disponibles (backend OpenAI)
  // Sinon, extraire depuis l'explication (fallback pour autres backends)
  const getSectionContent = (structuredField: string | undefined, sectionTitle: string, fallbackText: string = "") => {
    // D'abord vérifier si le champ structuré existe et n'est pas vide
    if (structuredField && structuredField.trim()) {
      console.log(`✅ Utilisation du champ structuré pour: ${sectionTitle}`);
      return structuredField.trim();
    }
    
    // Sinon, essayer d'extraire depuis l'explication
    if (safeExplanation) {
      const extracted = extractSectionFromExplanation(safeExplanation, sectionTitle);
      if (extracted) {
        console.log(`📄 Extraction depuis l'explication pour: ${sectionTitle}`);
        return extracted;
      }
    }
    
    // En dernier recours, utiliser le texte de fallback
    console.log(`⚠️ Utilisation du fallback pour: ${sectionTitle}`);
    return fallbackText;
  };

  // Fonction utilitaire pour extraire une section spécifique de l'explication
  const extractSectionFromExplanation = (text: string, sectionTitle: string): string => {
    const lines = text.split('\n');
    let currentSection = "";
    let currentContent: string[] = [];
    let foundSection = false;
    
    for (const line of lines) {
      const trimmedLine = line.trim();
      
      // Vérifier si la ligne correspond à notre section
      if (trimmedLine === sectionTitle || trimmedLine.startsWith(sectionTitle)) {
        foundSection = true;
        continue;
      }
      
      // Si on a trouvé notre section et qu'on arrive à une nouvelle section
      if (foundSection && (
        trimmedLine.startsWith("Diagnostic possible") ||
        trimmedLine.startsWith("Symptômes associés") ||
        trimmedLine.startsWith("Présentation de") ||
        trimmedLine.startsWith("Mode d'action") ||
        trimmedLine.startsWith("Informations de traitement") ||
        trimmedLine.startsWith("Précautions et contre-indications") ||
        trimmedLine.startsWith("Composants actifs") ||
        trimmedLine.startsWith("Résumé de traitement")
      )) {
        break;
      }
      
      // Ajouter le contenu si on est dans la bonne section
      if (foundSection && trimmedLine) {
        currentContent.push(line);
      }
    }
    
    return currentContent.join('\n').trim();
  };

  // Créer un objet sections unifié utilisant les champs structurés en priorité
  const sections = {
    "Diagnostic possible": getSectionContent(
      processedRecommendation.diagnostic,
      "Diagnostic possible",
      "Les informations de diagnostic ne sont pas disponibles pour le moment."
    ),
    "Symptômes associés": getSectionContent(
      processedRecommendation.symptomes,
      "Symptômes associés",
      "Les symptômes associés ne sont pas détaillés."
    ),
    "Présentation de": getSectionContent(
      processedRecommendation.presentation,
      "Présentation de",
      `La plante ${processedRecommendation.plant} est utilisée en phytothérapie traditionnelle.`
    ),
    "Mode d'action": getSectionContent(
      processedRecommendation.mode_action,
      "Mode d'action",
      "Le mode d'action de cette plante n'est pas détaillé."
    ),
    "Informations de traitement": getSectionContent(
      processedRecommendation.traitement_info,
      "Informations de traitement",
      `Préparation: ${processedRecommendation.prep}\nDosage: ${processedRecommendation.dosage}`
    ),
    "Précautions et contre-indications": getSectionContent(
      processedRecommendation.precautions_info,
      "Précautions et contre-indications",
      processedRecommendation.contre_indications || "Aucune contre-indication spécifique mentionnée."
    ),
    "Composants actifs": getSectionContent(
      processedRecommendation.composants_info,
      "Composants actifs",
      processedRecommendation.composants || "Les composants actifs ne sont pas détaillés."
    ),
    "Résumé de traitement": getSectionContent(
      processedRecommendation.resume_traitement,
      "Résumé de traitement",
      "Consultez les détails de préparation et de dosage pour ce remède."
    )
  };

  console.log("Sections finales créées:", Object.keys(sections));
  console.log("Utilisation des champs structurés:", {
    diagnostic: !!processedRecommendation.diagnostic,
    symptomes: !!processedRecommendation.symptomes,
    presentation: !!processedRecommendation.presentation,
    mode_action: !!processedRecommendation.mode_action,
    traitement_info: !!processedRecommendation.traitement_info,
    precautions_info: !!processedRecommendation.precautions_info,
    composants_info: !!processedRecommendation.composants_info,
    resume_traitement: !!processedRecommendation.resume_traitement
  });

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
