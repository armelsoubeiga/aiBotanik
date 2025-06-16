export default function Recommendation({ data }) {
  if (!data) return null;
  return (
    <div>
      <h2>{data.plant}</h2>
      <img src={data.image_url} alt={data.plant} style={{ maxWidth: 200 }} />
      <p><strong>Dosage:</strong> {data.dosage}</p>
      <p><strong>Preparation:</strong> {data.prep}</p>
      <p>{data.explanation}</p>
    </div>
  );
}
