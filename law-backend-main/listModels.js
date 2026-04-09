import dotenv from "dotenv";
dotenv.config();

const key = process.env.GEMINI_API_KEY;

const url = "https://generativelanguage.googleapis.com/v1/models?key=" + key;

const res = await fetch(url);
const data = await res.json();

console.log(JSON.stringify(data, null, 2));
