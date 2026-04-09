import mongoose from "mongoose";
import Message from "../models/Message.js";
import Conversation from "../models/Conversation.js";

export const sendMessage = async (req, res) => {
  try {
    const { conversationId, senderId, text } = req.body || {};
    if (!conversationId || !senderId || !text?.trim()) {
      return res.status(400).json({
        success: false,
        error: "conversationId, senderId and non-empty text are required",
      });
    }

    const message = await Message.create({
      conversationId,
      senderId,
      text: text.trim(),
    });

    const conversation = await Conversation.findById(conversationId);
    if (!conversation) {
      return res.status(404).json({ success: false, error: "Conversation not found" });
    }

    const normalizedSenderId = String(senderId);
    const isSenderUser = String(conversation.userId) === normalizedSenderId;

    conversation.lastMessage = {
      text: message.text,
      senderId: message.senderId,
      createdAt: message.createdAt,
    };
    if (isSenderUser) {
      conversation.unreadByLawyer = Number(conversation.unreadByLawyer || 0) + 1;
    } else {
      conversation.unreadByUser = Number(conversation.unreadByUser || 0) + 1;
    }
    conversation.updatedAt = new Date();
    await conversation.save();

    return res.status(201).json({ success: true, message });
  } catch (error) {
    console.error("sendMessage error:", error);
    return res.status(500).json({ success: false, error: "Failed to send message" });
  }
};

export const getMessagesByConversationId = async (req, res) => {
  try {
    const { conversationId } = req.params;
    if (!conversationId || !mongoose.Types.ObjectId.isValid(conversationId)) {
      return res.status(400).json({ success: false, error: "Invalid conversationId" });
    }

    const messages = await Message.find({ conversationId }).sort({ createdAt: 1 });
    return res.status(200).json({ success: true, messages });
  } catch (error) {
    console.error("getMessagesByConversationId error:", error);
    return res.status(500).json({ success: false, error: "Failed to fetch messages" });
  }
};

