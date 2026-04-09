import mongoose from "mongoose";
import Conversation from "../models/Conversation.js";
import Lawyer from "../models/Lawyer.js";
import User from "../models/User.js";
import Message from "../models/Message.js";

export const createOrGetConversation = async (req, res) => {
  try {
    const { userId, lawyerId } = req.body || {};
    if (!userId || !lawyerId) {
      return res.status(400).json({ success: false, error: "userId and lawyerId are required" });
    }

    let conversation = await Conversation.findOne({ userId, lawyerId });
    if (!conversation) {
      conversation = await Conversation.create({ userId, lawyerId });
    }

    return res.status(200).json({
      success: true,
      conversationId: conversation._id,
      conversation,
    });
  } catch (error) {
    console.error("createOrGetConversation error:", error);
    return res.status(500).json({ success: false, error: "Failed to create/get conversation" });
  }
};

export const getConversationsByUserId = async (req, res) => {
  try {
    const { userId } = req.params;
    if (!userId || !mongoose.Types.ObjectId.isValid(userId)) {
      return res.status(400).json({ success: false, error: "Invalid userId" });
    }

    const viewer = await User.findById(userId).select("role");
    if (!viewer) {
      return res.status(404).json({ success: false, error: "User not found" });
    }

    const query = viewer.role === "lawyer" ? { lawyerId: userId } : { userId };

    const conversations = await Conversation.find(query)
      .populate("userId", "name photo email role")
      .populate("lawyerId", "name photo email role")
      .sort({ updatedAt: -1 });

    const normalized = await Promise.all(conversations.map(async (c) => {
      const isLawyerViewer = String(c.lawyerId?._id || c.lawyerId) === String(userId);
      const other = isLawyerViewer ? c.userId : c.lawyerId;
      let photoFile = other?.photo || "";

      // For lawyers, prefer profile photo from Lawyer collection (mapped by userId).
      if (other?.role === "lawyer" && other?._id) {
        const lawyerProfile = await Lawyer.findOne({ userId: other._id }).select("photo");
        if (lawyerProfile?.photo) {
          photoFile = lawyerProfile.photo;
        }
      }

      const photoFolder = other?.role === "lawyer" ? "lawyers" : "user";
      let resolvedLastMessage = c.lastMessage || null;
      if (!resolvedLastMessage?.text) {
        const latestMessage = await Message.findOne({ conversationId: c._id })
          .sort({ createdAt: -1 })
          .select("text senderId createdAt");
        if (latestMessage) {
          resolvedLastMessage = {
            text: latestMessage.text,
            senderId: latestMessage.senderId,
            createdAt: latestMessage.createdAt,
          };
        }
      }

      const unreadCount = isLawyerViewer
        ? Number(c.unreadByLawyer || 0)
        : Number(c.unreadByUser || 0);
      return {
        ...c.toObject(),
        conversationId: c._id,
        unreadCount,
        lastMessage: resolvedLastMessage,
        user: other
          ? {
              _id: other._id,
              name: other.name,
              photo: photoFile ? `https://law-api.skyzin.com/uploads/${photoFolder}/${photoFile}` : "",
              email: other.email,
              role: other.role,
            }
          : null,
      };
    }));

    return res.status(200).json({ success: true, conversations: normalized });
  } catch (error) {
    console.error("getConversationsByUserId error:", error);
    return res.status(500).json({ success: false, error: "Failed to fetch conversations" });
  }
};

export const markConversationRead = async (req, res) => {
  try {
    const { conversationId, viewerId } = req.params;
    if (!conversationId || !mongoose.Types.ObjectId.isValid(conversationId)) {
      return res.status(400).json({ success: false, error: "Invalid conversationId" });
    }
    if (!viewerId || !mongoose.Types.ObjectId.isValid(viewerId)) {
      return res.status(400).json({ success: false, error: "Invalid viewerId" });
    }

    const conversation = await Conversation.findById(conversationId);
    if (!conversation) {
      return res.status(404).json({ success: false, error: "Conversation not found" });
    }

    const normalizedViewerId = String(viewerId);
    if (String(conversation.userId) === normalizedViewerId) {
      conversation.unreadByUser = 0;
      conversation.lastSeenByUserAt = new Date();
    } else if (String(conversation.lawyerId) === normalizedViewerId) {
      conversation.unreadByLawyer = 0;
      conversation.lastSeenByLawyerAt = new Date();
    } else {
      return res.status(403).json({ success: false, error: "Viewer is not part of conversation" });
    }

    await conversation.save();
    const seenAt =
      String(conversation.userId) === normalizedViewerId
        ? conversation.lastSeenByUserAt
        : conversation.lastSeenByLawyerAt;
    return res.status(200).json({ success: true, seenAt });
  } catch (error) {
    console.error("markConversationRead error:", error);
    return res.status(500).json({ success: false, error: "Failed to mark as read" });
  }
};

