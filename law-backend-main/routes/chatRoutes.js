import express from "express";
import { orchestratedChat } from "../controllers/chatController.js";

const router = express.Router();

router.get("/", (req, res) => {
  res.send("Chat API is running ✔");
});

router.post("/", orchestratedChat);
router.post("/ask", orchestratedChat);

export default router;
