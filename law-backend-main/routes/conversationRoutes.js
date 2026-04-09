import express from "express";
import {
  createOrGetConversation,
  getConversationsByUserId,
  markConversationRead,
} from "../controllers/conversationController.js";

const router = express.Router();

router.post("/", createOrGetConversation);
router.get("/:userId", getConversationsByUserId);
router.patch("/:conversationId/read/:viewerId", markConversationRead);

export default router;

