import express from "express";
import cors from "cors";
import dotenv from "dotenv";
import { createServer } from "http";
import { Server } from "socket.io";
import connectDB from "./config/db.js";
import Conversation from "./models/Conversation.js";

import chatRoutes from "./routes/chatRoutes.js";
import authRoutes from "./routes/authRoutes.js";
import appointmentRoutes from "./routes/appointmentRoutes.js";
import lawyerRoutes from "./routes/lawyerRoutes.js";
import conversationRoutes from "./routes/conversationRoutes.js";
import messageRoutes from "./routes/messageRoutes.js";



dotenv.config();
const app = express();
const httpServer = createServer(app);

const io = new Server(httpServer, {
  cors: {
    origin: "https://law.skyzin.com",
    methods: ["GET", "POST"],
    credentials: true,
  },
});

let onlineUsers = [];

function addUser(userId, socketId) {
  if (!userId) return;
  const normalizedUserId = String(userId);
  const existing = onlineUsers.find((u) => u.userId === normalizedUserId);
  if (existing) {
    existing.socketId = socketId;
    return;
  }
  onlineUsers.push({ userId: normalizedUserId, socketId });
}

function removeUser(socketId) {
  onlineUsers = onlineUsers.filter((u) => u.socketId !== socketId);
}

function getUser(userId) {
  return onlineUsers.find((u) => u.userId === String(userId));
}

io.on("connection", (socket) => {
  socket.on("addUser", (userId) => {
    addUser(userId, socket.id);
    io.emit("getOnlineUsers", onlineUsers);
  });

  socket.on("sendMessage", async ({ senderId, receiverId, text, conversationId }) => {
    const receiver = getUser(receiverId);
    if (!receiver) return;
    let unreadCount = 0;
    try {
      const conversation = await Conversation.findById(conversationId).select(
        "userId lawyerId unreadByUser unreadByLawyer"
      );
      if (conversation) {
        const normalizedReceiverId = String(receiverId);
        if (String(conversation.userId) === normalizedReceiverId) {
          unreadCount = Number(conversation.unreadByUser || 0);
        } else if (String(conversation.lawyerId) === normalizedReceiverId) {
          unreadCount = Number(conversation.unreadByLawyer || 0);
        }
      }
    } catch (error) {
      console.error("socket sendMessage unread lookup error:", error);
    }
    io.to(receiver.socketId).emit("receiveMessage", {
      senderId,
      receiverId,
      text,
      conversationId,
      unreadCount,
      createdAt: new Date().toISOString(),
    });
  });

  socket.on("markSeen", ({ conversationId, receiverId, seenAt }) => {
    const receiver = getUser(receiverId);
    if (!receiver) return;
    io.to(receiver.socketId).emit("conversationSeen", {
      conversationId,
      seenAt: seenAt || new Date().toISOString(),
    });
  });

  socket.on("disconnect", () => {
    removeUser(socket.id);
    io.emit("getOnlineUsers", onlineUsers);
  });
});

// --------------------
// MUST BE FIRST
// --------------------
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// --------------------
// CORS FIX
// --------------------
app.use(cors({
  origin: "https://law.skyzin.com",
  methods: ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
  allowedHeaders: ["Content-Type", "Authorization"],
  credentials: true
}));

// --------------------
// DB CONNECT
// --------------------
connectDB();

// --------------------
// DEBUG LOGGER
// --------------------
app.use((req, res, next) => {
  console.log("---- NEW REQUEST ----");
  console.log("URL:", req.url);
  console.log("Method:", req.method);
  console.log("Body:", req.body);
  next();
});

// --------------------
// ROUTES (JSON FIRST)
// --------------------
app.use("/api/auth", authRoutes);
app.use("/api/chat", chatRoutes);
app.use("/api/appointments", appointmentRoutes);
app.use("/api/conversations", conversationRoutes);
app.use("/api/messages", messageRoutes);

// --------------------
// MULTER ROUTES LAST
// --------------------
app.use("/api/lawyer", lawyerRoutes);

// --------------------
// STATIC FILES
// --------------------
app.use("/uploads", express.static("uploads"));


// --------------------
// DEFAULT
// --------------------
app.get("/", (req, res) => res.send("Backend running"));

const PORT = process.env.PORT || 8000;
httpServer.listen(PORT, () => console.log(`Backend running on port ${PORT}`));
