import axios from "axios";
const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://<your-space>.hf.space/recommend";

export const getRecommendation = async (symptoms) => {
  const res = await axios.post(API_URL, { symptoms });
  return res.data;
};
