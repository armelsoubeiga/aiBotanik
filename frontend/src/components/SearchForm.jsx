import { useState } from "react";
import { getRecommendation } from "../api";

export default function SearchForm({ onResult }) {
  const [symptoms, setSymptoms] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    try {
      const data = await getRecommendation(symptoms);
      onResult(data);
    } catch (err) {
      console.error("Error getting recommendation:", err);
      setError("Une erreur est survenue lors de la recherche. Veuillez réessayer.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ marginTop: "20px", marginBottom: "30px" }}>
      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "15px" }}>
        <div style={{ display: "flex", gap: "10px" }}>
          <input
            type="text"
            placeholder="Décrivez vos symptômes..."
            value={symptoms}
            onChange={(e) => setSymptoms(e.target.value)}
            required
            style={{ flex: 1 }}
          />
          <button type="submit" disabled={loading}>
            {loading ? "Recherche en cours..." : "Obtenir une recommandation"}
          </button>
        </div>
        
        {error && (
          <div style={{ color: "red", marginTop: "10px" }}>
            {error}
          </div>
        )}
      </form>
    </div>
  );
}
