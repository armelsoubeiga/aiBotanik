export default function Recommendation({ data }) {
  if (!data) return null;
  
  // Formater l'explication pour un meilleur affichage
  const formattedExplanation = data.explanation
    .split('\n')
    .filter(line => line.trim() !== '')
    .map((line, i) => <p key={i}>{line}</p>);
  
  return (
    <div className="recommendation">
      <h2>{data.plant}</h2>
      <div className="recommendation-content">
        <div className="plant-image-container">
          <img 
            src={data.image_url || "/plant-placeholder.jpg"} 
            alt={data.plant} 
            className="plant-image"
          />
          {data.nom_local && (
            <div className="plant-local-name">
              {data.nom_local}
            </div>
          )}
        </div>
        
        <div className="plant-info">
          <div className="info-section">
            <h3>Informations de traitement</h3>
            <p><strong>Dosage:</strong> {data.dosage}</p>
            <p><strong>Préparation:</strong> {data.prep}</p>
            {data.partie_utilisee && (
              <p><strong>Partie utilisée:</strong> {data.partie_utilisee}</p>
            )}
          </div>
          
          {data.composants && (
            <div className="info-section">
              <h3>Composants actifs</h3>
              <p>{data.composants}</p>
            </div>
          )}
          
          {data.contre_indications && (
            <div className="info-section warning">
              <h3>Contre-indications et précautions</h3>
              <p>{data.contre_indications}</p>
            </div>
          )}
          
          <div className="explanation-section">
            <h3>Recommandation personnalisée</h3>
            <div className="explanation">
              {formattedExplanation}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
