import express from "express";
import {
  getMessagesByConversationId,
  sendMessage,
} from "../controllers/messageController.js";

const router = express.Router();

router.post("/", sendMessage);
router.get("/:conversationId", getMessagesByConversationId);

export default router;

