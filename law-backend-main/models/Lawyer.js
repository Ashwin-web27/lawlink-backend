import mongoose from "mongoose";

const LawyerSchema = new mongoose.Schema({
  userId: { type: mongoose.Schema.Types.ObjectId, required: true, unique: true },

  name: String,
  email: String,
  phone: String,
  city: { type: String },
  country: { type: String },
  experienceDetails: { type: String },
  degree: { type: String },
  university: { type: String },
  
  startYear: { type: String,default: "" },
  endYear: { type: String ,default: ""},


  specialization: { type: [String], default: [] },
  experienceYears: { type: Number, default: 0 },
  qualifications: { type: String, default: "" },
  

  about: { type: String, default: "" },
  photo: { type: String, default: "" }
}, { timestamps: true });

export default mongoose.models.Lawyer || mongoose.model("Lawyer", LawyerSchema);
