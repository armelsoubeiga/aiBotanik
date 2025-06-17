import { useState } from 'react';
import SearchForm from '../src/components/SearchForm';
import Recommendation from '../src/components/Recommendation';

export default function Home() {
  const [result, setResult] = useState(null);
  
  return (
    <>
      <h1>aiBotanik</h1>
      <p>Votre conseiller en phytothérapie basé sur l'intelligence artificielle</p>
      
      <SearchForm onResult={setResult} />
      <Recommendation data={result} />
    </>
  );
}
