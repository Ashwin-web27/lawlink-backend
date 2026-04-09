import mongoose from "mongoose";

const ConversationSchema = new mongoose.Schema(
  {
    userId: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "User",
      required: true,
      index: true,
    },
    lawyerId: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "User",
      required: true,
      index: true,
    },
    lastMessage: {
      text: { type: String, default: "" },
      senderId: {
        type: mongoose.Schema.Types.ObjectId,
        ref: "User",
      },
      createdAt: { type: Date },
    },
    unreadByUser: {
      type: Number,
      default: 0,
      min: 0,
    },
    unreadByLawyer: {
      type: Number,
      default: 0,
      min: 0,
    },
    lastSeenByUserAt: {
      type: Date,
      default: null,
    },
    lastSeenByLawyerAt: {
      type: Date,
      default: null,
    },
  },
  { timestamps: true }
);

ConversationSchema.index({ userId: 1, lawyerId: 1 }, { unique: true });

export default mongoose.models.Conversation || mongoose.model("Conversation", ConversationSchema);

