import dotenv from "dotenv";
dotenv.config();

const key = process.env.GEMINI_API_KEY;

console.log("Key starts with:", key?.substring(0, 6));
console.log("Key length:", key?.length);