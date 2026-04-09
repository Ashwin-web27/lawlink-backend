import UserQuery from "../models/UserQuery.js";
import { askGemini } from "../services/askGemini.js";
import dotenv from "dotenv";

dotenv.config();

const FASTAPI_CHAT_URL =
  process.env.FASTAPI_CHAT_URL || "https://llm.skyzin.com/chat";
function isInformationalQuery(query) {
  const q = query.toLowerCase().trim();

  return (
    q.startsWith("what is") ||
    q.startsWith("what are") ||
    q.startsWith("define") ||
    q.startsWith("explain") ||
    q.includes("article") ||
    q.includes("section") ||
    q.includes("act")
  );
}

async function fetchDatasetAnswer(question) {
  const q = typeof question === "string" ? question.trim() : "";
  try {
    const ragRes = await fetch(FASTAPI_CHAT_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: q }),
    });

    if (!ragRes.ok) return { answer: "", sources: [] };
    const ragData = await ragRes.json();
    return {
      answer: ragData?.answer || "",
      sources: Array.isArray(ragData?.sources) ? ragData.sources : [],
    };
  } catch (err) {
    console.error("FastAPI dataset unreachable:", err.message);
    return { answer: "", sources: [] };
  }
}

export const orchestratedChat = async (req, res) => {
  try {
    const { question } = req.body;
    const q = typeof question === "string" ? question.trim() : "";
    if (!q) {
      return res.status(400).json({ error: "question is required" });
    }

    // CASE 1: informational query -> dataset first
    if (isInformationalQuery(q)) {
      const ragData = await fetchDatasetAnswer(q);
      const datasetAnswer = String(ragData.answer || "").trim();
      const isValid = datasetAnswer !== "" && datasetAnswer.length > 30;

      if (isValid) {
        try {
          await UserQuery.create({ userQuery: q, botReply: datasetAnswer });
        } catch (e) {
          console.error("UserQuery save failed:", e);
        }

        return res.json({
          answer: datasetAnswer,
          answer_source: "dataset",
          sources: ragData.sources || [],
        });
      }

      let geminiAnswer = "";
      try {
        geminiAnswer = await askGemini(q);
      } catch (err) {
        console.error("GEMINI CHAT ERROR (informational fallback):", err);
      }

      const finalAnswer =
        String(geminiAnswer || "").trim() ||
        "Unable to generate an answer at this time. Please try again later.";

      try {
        await UserQuery.create({ userQuery: q, botReply: finalAnswer });
      } catch (e) {
        console.error("UserQuery save failed:", e);
      }

      return res.json({
        answer: finalAnswer,
        answer_source: "gemini",
      });
    }

    // CASE 2: non-informational query -> Gemini (optional dataset context)
    const ragData = await fetchDatasetAnswer(q);
    const context = String(ragData.answer || "").trim();
    let geminiAnswer = "";
    try {
      geminiAnswer = await askGemini(q, context);
    } catch (err) {
      console.error("GEMINI CHAT ERROR (non-informational):", err);
    }

    const finalAnswer =
      String(geminiAnswer || "").trim() ||
      "Unable to generate an answer at this time. Please try again later.";

    try {
      await UserQuery.create({ userQuery: q, botReply: finalAnswer });
    } catch (e) {
      console.error("UserQuery save failed:", e);
    }

    return res.json({
      answer: finalAnswer,
      answer_source: "gemini",
    });
  } catch (error) {
    console.error("ORCHESTRATED CHAT ERROR:", error);
    return res.status(500).json({
      error: "Chat failed",
      details: error.message,
    });
  }
};
