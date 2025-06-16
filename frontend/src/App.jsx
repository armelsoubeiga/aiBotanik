import { useState } from "react";
import SearchForm from "./components/SearchForm";
import Recommendation from "./components/Recommendation";

export default function App() {
  const [result, setResult] = useState(null);
  return (
    <div style={{ padding: 20, fontFamily: "Poppins, sans-serif" }}>
      <h1>BotanikAI</h1>
      <SearchForm onResult={setResult} />
      <Recommendation data={result} />
    </div>
  );
}
