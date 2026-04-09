// backend/controllers/lawyerController.js
import Lawyer from "../models/Lawyer.js";
import multer from "multer";

// -------------------------
// MULTER STORAGE FOR PHOTO
// -------------------------
const storage = multer.diskStorage({
  destination: "uploads/lawyers/",
  filename: (req, file, cb) => {
    cb(null, Date.now() + "-" + file.originalname);
  }
});

export const upload = multer({ storage });

// -------------------------
// GET PROFILE
// -------------------------
export const getProfile = async (req, res) => {
  try {
    const { id } = req.params;
    let profile = null;

    // Support both lawyer document id and linked user id.
    if (id) {
      profile = await Lawyer.findById(id);
      if (!profile) {
        profile = await Lawyer.findOne({ userId: id });
      }
    }

    if (!profile) return res.json({ success: true, profile: null });
    res.json({ success: true, profile });

  } catch (err) {
    console.error("PROFILE FETCH ERROR:", err);
    res.status(500).json({ success: false, error: "Server error" });
  }
};

// -------------------------
// UPSERT PROFILE
// -------------------------
export const upsertProfile = async (req, res) => {
  try {
    const { userId } = req.params;

    const {
      name,
      email,
      phone,
      specialization,
      experienceYears,
      qualifications,
      
      about,
      city,
      country,
      experienceDetails,
      degree,
      university,
      startYear,
      endYear,
    } = req.body;

    // Validate
    if (!name || !email || !phone) {
      return res.status(400).json({
        success: false,
        error: "Name, email and phone are required"
      });
    }

    const updateFields = {
      userId,
      name,
      email,
      phone,
      specialization: String(specialization || "")
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean),
      experienceYears: Number(experienceYears) || 0,
      qualifications: qualifications || "",
      
      about: about || "",
      city: city || "",
      country: country || "",
      experienceDetails: experienceDetails || "",
      degree: degree || "",
      university: university || "",
      
      startYear: startYear ||"",
      endYear: endYear ||",",
      updatedAt: Date.now()
    };

    // Add photo if uploaded
    if (req.file) {
      updateFields.photo = req.file.filename;
    }

    const profile = await Lawyer.findOneAndUpdate(
      { userId },
      { $set: updateFields },
      { new: true, upsert: true, setDefaultsOnInsert: true }
    );

    res.json({ success: true, profile });

  } catch (err) {
    console.error("PROFILE UPDATE ERROR:", err);
    res.status(500).json({ success: false, error: "Server error" });
  }
};
// Add to backend/controllers/lawyerController.js

export const listLawyers = async (req, res) => {
  try {
    // Return fields required by Contact Lawyer cards.
    const lawyers = await Lawyer.find(
      {},
      "userId name specialization experienceYears city country photo"
    );
    return res.json({ success: true, lawyers });
  } catch (err) {
    console.error("LIST LAWYERS ERROR:", err);
    return res.status(500).json({ success: false, error: "Server error" });
  }
};
