export default function Recommendation({ data }) {
  if (!data) return null;
  // Analyser l'explication pour extraire les sections structurées
  const parseExplanation = (text) => {
    const sections = {
      diagnostic: "",
      symptomes: "",
      presentation: "",
      action: "",
      dosage: "",
      parties: "",
      precautions: "",
      resume: ""
    };
    
    try {
      const lines = text.split('\n').filter(line => line.trim());
      let currentSection = null;
      let contentBuffer = "";
      
      for (const line of lines) {
        const cleanLine = line.trim();
        
        // Identifier le début des sections avec une approche plus flexible pour capturer les variantes
        if (cleanLine.match(/^(?:\d+\.?)?\s*(?:\*\*)?diagnostic(?:\s+possible)?(?:\*\*)?/i)) {
          currentSection = "diagnostic";
          contentBuffer = "";  // Réinitialiser le buffer pour la nouvelle section
        } else if (cleanLine.match(/^(?:\d+\.?)?\s*(?:\*\*)?symptômes(?:\s+associés)?(?:\*\*)?/i)) {
          if (currentSection === "diagnostic" && contentBuffer) {
            sections.diagnostic += contentBuffer.trim();
          }
          currentSection = "symptomes";
          contentBuffer = "";
        } else if (cleanLine.match(/^(?:\d+\.?)?\s*(?:\*\*)?présentation(?:\s+de\s+.*)?(?:\*\*)?/i)) {
          if (currentSection === "symptomes" && contentBuffer) {
            sections.symptomes += contentBuffer.trim();
          }
          currentSection = "presentation";
          contentBuffer = "";
        } else if (cleanLine.match(/^(?:\d+\.?)?\s*(?:\*\*)?(?:comment|mode\s+d['']action|cette\s+plante\s+agit)(?:\*\*)?/i)) {
          if (currentSection === "presentation" && contentBuffer) {
            sections.presentation += contentBuffer.trim();
          }
          currentSection = "action";
          contentBuffer = "";
        } else if (cleanLine.match(/^(?:\d+\.?)?\s*(?:\*\*)?(?:guide\s+de\s+dosage|posologie|dosage)(?:\*\*)?/i)) {
          if (currentSection === "action" && contentBuffer) {
            sections.action += contentBuffer.trim();
          }
          currentSection = "dosage";
          contentBuffer = "";
        } else if (cleanLine.match(/^(?:\d+\.?)?\s*(?:\*\*)?parties(?:\s+de\s+la\s+plante)?(?:\s+à\s+utiliser)?(?:\*\*)?/i)) {
          if (currentSection === "dosage" && contentBuffer) {
            sections.dosage += contentBuffer.trim();
          }
          currentSection = "parties";
          contentBuffer = "";
        } else if (cleanLine.match(/^(?:\d+\.?)?\s*(?:\*\*)?précautions(?:\s+et\s+contre-indications)?(?:\*\*)?/i)) {
          if (currentSection === "parties" && contentBuffer) {
            sections.parties += contentBuffer.trim();
          }
          currentSection = "precautions";
          contentBuffer = "";
        } else if (cleanLine.match(/^(?:\d+\.?)?\s*(?:\*\*)?(?:résumé|synthèse|traitement\s+recommandé)(?:\s+de\s+traitement)?(?:\s+en\s+mode\s+moore)?(?:\*\*)?/i)) {
          if (currentSection === "precautions" && contentBuffer) {
            sections.precautions += contentBuffer.trim();
          }
          currentSection = "resume";
          contentBuffer = "";
        } else if (currentSection) {
          // Ne pas ajouter les titres de sections au contenu
          if (!cleanLine.match(/^(?:\d+\.?)?\s*(?:\*\*)?[a-zéèêàçôîûë\s]+(?:\*\*)?$/i)) {
            contentBuffer += (contentBuffer ? " " : "") + cleanLine;
          }
        }
      }
      
      // Ajouter le dernier buffer à la dernière section
      if (currentSection && contentBuffer) {
        sections[currentSection] += contentBuffer.trim();
      }
      
      // Nettoyer les sections de tout formatage markdown ou HTML restant
      Object.keys(sections).forEach(key => {
        // Supprimer les marqueurs markdown
        let cleanedText = sections[key].replace(/\*\*([^*]+)\*\*/g, "$1");
        // Supprimer les puces et numérotations
        cleanedText = cleanedText.replace(/^[-*•]\s+/gm, "");
        // Supprimer les numéros de liste
        cleanedText = cleanedText.replace(/^\d+\.\s+/gm, "");
        sections[key] = cleanedText;
      });
      
      // Si aucune section n'a été identifiée, utiliser tout le texte comme présentation
      if (Object.values(sections).every(section => section === "")) {
        sections.presentation = text.replace(/\*\*([^*]+)\*\*/g, "$1");
      }
      
      return sections;
    } catch (e) {
      console.error("Erreur lors de l'analyse de l'explication:", e);
      return { presentation: text };
    }
  };
  
  // Traiter l'explication
  const sections = parseExplanation(data.explanation);
  
  return (
    <div className="recommendation">
      <h2>{data.plant}</h2>
      <div className="recommendation-content">
        <div className="plant-image-container">
          <img 
            src={data.image_url || "/plant-placeholder.jpg"} 
            alt={data.plant} 
            className="plant-image"
          />          {data.nom_local && (
            <div className="plant-local-name">
              <h4>Noms locaux</h4>
              {data.nom_local.startsWith("Noms locaux:") || data.nom_local.startsWith("Nom local:") ? (
                <div className="local-names-list">
                  {data.nom_local.split('. ').map((item, index) => (
                    <p key={index}>{item.trim()}</p>
                  ))}
                </div>
              ) : (
                <p>{data.nom_local}</p>
              )}
            </div>
          )}
        </div>          <div className="plant-info">          {/* Section diagnostic - Placé en premier */}
          {sections.diagnostic && sections.diagnostic.trim() !== "" && (
            <div className="info-section diagnostic">
              <h3>Diagnostic possible</h3>
              <p dangerouslySetInnerHTML={{ __html: sections.diagnostic.replace(/([A-Z]{2,})/g, '<span class="highlight-pathology">$1</span>') }}></p>
            </div>
          )}            {/* Section symptômes */}
          {sections.symptomes && sections.symptomes.trim() !== "" && (
            <div className="info-section symptomes">
              <h3>Symptômes associés</h3>
              <p>{sections.symptomes}</p>
            </div>
          )}          {/* Section résumé - Placé en troisième position */}
          {sections.resume && sections.resume.trim() !== "" && (
            <div className="info-section resume">
              <h3>Résumé de traitement</h3>
              <p className="resume-content">{sections.resume}</p>
            </div>
          )}

          {/* Section présentation - Placée avant le traitement pour mieux comprendre la plante */}
          <div className="info-section presentation">
            <h3>Présentation de la plante</h3>
            <p>{sections.presentation || "Cette plante médicinale est recommandée pour les symptômes décrits."}</p>
          </div>
            {/* Section action */}
          {sections.action && sections.action.trim() !== "" && (
            <div className="info-section action">
              <h3>Mode d'action</h3>
              <p>{sections.action}</p>
            </div>
          )}          {/* Section information de traitement */}
          <div className="info-section treatment">
            <h3>Informations de traitement</h3>
            
            <div className="treatment-intro">
              <p>Pour préparer et utiliser efficacement ce remède traditionnel à base de {data.plant}, suivez ces instructions :</p>
            </div>
            
            <div className="treatment-details">
              {/* Section préparation */}
              <div className="treatment-item">
                <div className="treatment-icon preparation-icon">🍵</div>
                <h4>Préparation</h4>
                <p className="treatment-description">{data.prep}</p>
              </div>
              
              {/* Section dosage */}
              <div className="treatment-item">
                <div className="treatment-icon dosage-icon">⚖️</div>
                <h4>Dosage</h4>
                {(sections.dosage || data.dosage).includes('\n') ? (
                  <div className="dosage-list treatment-description">
                    {(sections.dosage || data.dosage).split('\n').map((line, index) => (
                      line.trim() && <p key={index}>{line}</p>
                    ))}
                  </div>
                ) : (
                  <p className="treatment-description">{sections.dosage || data.dosage}</p>
                )}
              </div>
              
              {/* Section parties utilisées */}
              <div className="treatment-item">
                <div className="treatment-icon parts-icon">🌿</div>
                <h4>Parties de la plante</h4>
                {(sections.parties || data.partie_utilisee).includes('\n') ? (
                  <div className="parties-list treatment-description">
                    {(sections.parties || data.partie_utilisee).split('\n').map((line, index) => (
                      line.trim() && <p key={index}>{line}</p>
                    ))}
                  </div>
                ) : (
                  <p className="treatment-description">{sections.parties || data.partie_utilisee}</p>
                )}
              </div>
            </div>
            
            <div className="treatment-footer">
              <p>Pour un résultat optimal, suivez scrupuleusement ces instructions et respectez les dosages indiqués.</p>
            </div>
          </div>
            {/* Section précautions - Placée après le traitement pour souligner l'importance de la sécurité */}
          <div className="info-section warning">
            <h3>Précautions et contre-indications</h3>
            {sections.precautions && sections.precautions.trim() !== "" ? (
              <p>{sections.precautions}</p>
            ) : data.contre_indications && data.contre_indications.trim() !== "" ? (
              <div className="precautions-container">
                <p className="precautions-intro">
                  <strong>Attention !</strong> Ce traitement à base de plantes nécessite quelques précautions importantes :
                </p>
                <ul className="precautions-list">
                  {data.contre_indications
                    .replace(/;/g, '.')
                    .split('.')
                    .filter(item => item.trim())
                    .map((item, idx) => (
                      <li key={idx}>
                        {item.trim().startsWith('pregnancy') || item.trim().toLowerCase().includes('grossesse') ? 
                          'Déconseillé aux femmes enceintes ou qui souhaitent le devenir.' :
                        item.trim().includes('breastfeeding') || item.trim().toLowerCase().includes('allaitement') ?
                          'Ne pas utiliser pendant l\'allaitement.' :
                        item.trim().includes('child') || item.trim().toLowerCase().includes('enfant') ?
                          'Ne pas administrer aux enfants sans avis médical spécialisé.' :
                        item.trim().includes('ulceration') || item.trim().toLowerCase().includes('ulcère') ?
                          'Contre-indiqué en cas d\'ulcère gastrique ou de problèmes digestifs chroniques.' :
                        item.trim()}
                      </li>
                    ))
                  }
                </ul>
                <p className="precautions-conclusion">
                  En cas de doute ou de traitement médical en cours, consultez un professionnel de santé avant d'utiliser ce remède.
                </p>
              </div>
            ) : (
              <p>Aucune contre-indication majeure n'est connue, mais comme pour tout traitement à base de plantes, 
              consultez un professionnel de santé avant utilisation, particulièrement si vous êtes enceinte, 
              allaitante, ou sous traitement médical.</p>
            )}
          </div>
            {/* Section composants */}
          {data.composants && data.composants.trim() !== "" && (
            <div className="info-section composants">
              <h3>Composants actifs</h3>
              <div className="composants-intro">
                <p>Les principaux composés actifs de cette plante médicinale sont responsables de ses effets thérapeutiques :</p>
              </div>
              {data.composants.includes('\n') ? (
                <div className="composants-list">
                  {data.composants.split('\n').map((line, index) => {
                    // Détecter si c'est une ligne avec plante: composants
                    const match = line.match(/^([^:]+):\s*(.+)$/);
                    if (match) {
                      const [_, plantName, components] = match;
                      return (
                        <div key={index} className="composant-item">
                          <h4>{plantName.trim()}</h4>
                          <div className="composant-details">
                            {components.split(',').map((component, idx) => (
                              <span key={idx} className="component-tag">{component.trim()}</span>
                            ))}
                          </div>
                        </div>
                      );
                    }
                    return <p key={index}>{line}</p>;
                  })}
                </div>
              ) : (
                <div className="composants-simple">
                  {data.composants.split(';').map((group, index) => {
                    const match = group.match(/^([^:]+):\s*(.+)$/);
                    if (match) {
                      const [_, plantName, components] = match;
                      return (
                        <div key={index} className="composant-item">
                          <h4>{plantName.trim()}</h4>
                          <div className="composant-details">
                            {components.split(',').map((component, idx) => (
                              <span key={idx} className="component-tag">{component.trim()}</span>
                            ))}
                          </div>
                        </div>
                      );
                    }
                    return <p key={index} className="composant-simple">{group.trim()}</p>;
                  })}
                </div>
              )}
              <p className="composants-footer">Ces substances naturelles agissent en synergie pour produire les effets thérapeutiques recherchés.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
