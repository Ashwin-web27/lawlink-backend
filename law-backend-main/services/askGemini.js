import { GoogleGenerativeAI } from "@google/generative-ai";
import dotenv from "dotenv";

dotenv.config();

const genAI = process.env.GEMINI_API_KEY
  ? new GoogleGenerativeAI(process.env.GEMINI_API_KEY)
  : null;

function cleanReply(userMessage, aiReply) {
  if (!aiReply) return "";

  const lowerUser = userMessage.toLowerCase().trim();
  let cleaned = aiReply.trim();

  if (cleaned.toLowerCase().startsWith(lowerUser)) {
    cleaned = cleaned.slice(userMessage.length).trim();
  }

  cleaned = cleaned.replace(new RegExp(userMessage, "gi"), "").trim();

  return cleaned;
}

export async function askGemini(query, context = "") {
  if (!genAI) {
    return "AI assistant is not configured (missing GEMINI_API_KEY). Please contact the administrator.";
  }

  const model = genAI.getGenerativeModel({
    model: "models/gemini-2.5-flash",
  });

  const prompt = `
You are a legal assistant.

Context (if available):
${context || ""}

User Question:
${query}

If context exists, use it to provide better suggestions or advice.
If no context, answer using general legal knowledge.

Provide a clear and helpful response.
`;

  const result = await model.generateContent([{ text: prompt }]);
  const rawReply = result.response.text();
  return cleanReply(query, rawReply);
}
