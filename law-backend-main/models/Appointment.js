// backend/models/Appointment.js
import mongoose from "mongoose";

const AppointmentSchema = new mongoose.Schema({
  userId: { type: mongoose.Schema.Types.ObjectId, required: true, ref: "User" },
  lawyerId: { type: mongoose.Schema.Types.ObjectId, required: true, ref: "Lawyer" },

  date: { type: String, required: true },   // keep as ISO date string / human readable date
  time: { type: String, required: true },   // e.g. "14:30" or "2:30 PM"

  message: { type: String, default: "" },
  status: { type: String, enum: ["pending","accepted","rejected","completed"], default: "pending" },

  createdAt: { type: Date, default: Date.now }
});

export default mongoose.models.Appointment || mongoose.model("Appointment", AppointmentSchema);
