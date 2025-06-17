import axios from "axios";
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/recommend";

export const getRecommendation = async (symptoms) => {
  const res = await axios.post(API_URL, { symptoms });
  return res.data;
};
