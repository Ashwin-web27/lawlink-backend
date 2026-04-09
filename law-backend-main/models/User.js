import mongoose from "mongoose";

const UserSchema = new mongoose.Schema({
  name: { type: String, required: true },
  email: { type: String, required: true, unique: true },
  phone: { type: String, required: true },
  password: { type: String, required: true },
  role: { type: String, enum: ["user", "lawyer"], required: true },
  address: { type: String, default: "" },
  bio: { type: String, default: "" },
  photo: { type: String, default: "" },
}, { timestamps: true });

export default mongoose.models.User || mongoose.model("User", UserSchema);
