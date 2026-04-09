import mongoose from "mongoose";

const QuerySchema = new mongoose.Schema({
  userQuery: { type: String, required: true },
  botReply: { type: String, required: true },
  date: { type: Date, default: Date.now }
});

export default mongoose.model("UserQuery", QuerySchema);
