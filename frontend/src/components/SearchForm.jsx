import { useState } from "react";
import { getRecommendation } from "../api";

export default function SearchForm({ onResult }) {
  const [symptoms, setSymptoms] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    const data = await getRecommendation(symptoms);
    setLoading(false);
    onResult(data);
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="text"
        placeholder="Describe your symptoms..."
        value={symptoms}
        onChange={(e) => setSymptoms(e.target.value)}
        required
      />
      <button type="submit" disabled={loading}>
        {loading ? "Loading..." : "Get Recommendation"}
      </button>
    </form>
  );
}
