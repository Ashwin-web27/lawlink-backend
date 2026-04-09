import User from "../models/User.js";
import Lawyer from "../models/Lawyer.js";
import jwt from "jsonwebtoken";
import crypto from "crypto";
import { OAuth2Client } from "google-auth-library";

const googleClient = new OAuth2Client(process.env.GOOGLE_CLIENT_ID);

// REGISTER
export const register = async (req, res) => {
  try {
    const {
      name,
      email,
      phone,
      password,
      role,
      specialization,
      experienceYears,
      qualifications,
      barAssociation
    } = req.body;

    // Required validation
    if (!name || !email || !phone || !password || !role) {
      return res.status(400).json({
        success: false,
        error: "All required fields must be filled."
      });
    }

    // Check if user already exists
    const existingUser = await User.findOne({ email });
    if (existingUser) {
      return res.status(400).json({
        success: false,
        error: "Email already registered"
      });
    }

    // 1️⃣ CREATE USER ACCOUNT
    const newUser = await User.create({
      name,
      email,
      phone,
      password,
      role
    });

    // 2️⃣ IF LAWYER → CREATE PROFILE
    if (role === "lawyer") {
      await Lawyer.create({
        userId: newUser._id,
        name,
        email,
        phone,
        specialization: specialization
          ? specialization.split(",").map(s => s.trim())
          : [],
        experienceYears: experienceYears ? Number(experienceYears) : 0,
        qualifications: qualifications || "",
        barAssociation: barAssociation || "",
        about: "",
        photo: ""  // default blank
      });
    }

    return res.json({
      success: true,
      message: "Registered successfully",
      userId: newUser._id,
      role
    });

  } catch (err) {
    console.error("REGISTER ERROR:", err);
    return res.status(500).json({
      success: false,
      error: "Server error"
    });
  }
};

// LOGIN
export const login = async (req, res) => {
  try {
    const { email, password, role } = req.body;

    if (!email || !password || !role) {
      return res.status(400).json({
        success: false,
        error: "Email, password and role are required"
      });
    }

    const user = await User.findOne({ email, role });

    if (!user) {
      return res.status(404).json({
        success: false,
        error: "Account not found"
      });
    }

    if (user.password !== password) {
      return res.status(400).json({
        success: false,
        error: "Incorrect password"
      });
    }

    let lawyerProfile = null;

    if (role === "lawyer") {
      lawyerProfile = await Lawyer.findOne({ userId: user._id });

      if (!lawyerProfile) {
        return res.status(400).json({
          success: false,
          error: "Lawyer profile missing. Contact support."
        });
      }
    }

    const token = jwt.sign(
      { id: user._id, role: user.role },
      process.env.JWT_SECRET,
      { expiresIn: "7d" }
    );

    return res.json({
      success: true,
      message: "Login successful",
      role: user.role,
      token,
      userId: user._id,
      lawyerProfile
    });

  } catch (err) {
    console.error("LOGIN ERROR:", err);
    return res.status(500).json({
      success: false,
      error: "Server error"
    });
  }
};

// GOOGLE AUTH (Login/Register via Google ID token)
export const googleAuth = async (req, res) => {
  try {
    const { credential, role } = req.body || {};

    if (!credential) {
      return res.status(400).json({ success: false, error: "Google credential is required" });
    }
    if (!role || !["user", "lawyer"].includes(role)) {
      return res.status(400).json({ success: false, error: "Valid role is required" });
    }
    if (!process.env.GOOGLE_CLIENT_ID) {
      return res.status(500).json({ success: false, error: "Google client is not configured" });
    }

    const ticket = await googleClient.verifyIdToken({
      idToken: credential,
      audience: process.env.GOOGLE_CLIENT_ID,
    });

    const payload = ticket.getPayload();
    const email = payload?.email;
    const name = payload?.name || "Google User";
    const picture = payload?.picture || "";

    if (!email) {
      return res.status(400).json({ success: false, error: "Google account email not available" });
    }

    let user = await User.findOne({ email });

    // If email exists but role mismatches, block (email is unique)
    if (user && user.role !== role) {
      return res.status(400).json({
        success: false,
        error: `This email is already registered as ${user.role}. Please continue as ${user.role}.`,
      });
    }

    // Create account if missing
    if (!user) {
      const randomPass = crypto.randomBytes(18).toString("hex");
      user = await User.create({
        name,
        email,
        phone: "NA",
        password: randomPass,
        role,
        photo: picture,
      });

      if (role === "lawyer") {
        await Lawyer.create({
          userId: user._id,
          name,
          email,
          phone: "NA",
          specialization: [],
          experienceYears: 0,
          qualifications: "",
          barAssociation: "",
          about: "",
          photo: "",
        });
      }
    } else {
      // Keep profile info fresh (non-destructive)
      const updates = {};
      if (!user.name && name) updates.name = name;
      if (!user.photo && picture) updates.photo = picture;
      if (Object.keys(updates).length > 0) {
        user = await User.findByIdAndUpdate(user._id, updates, { new: true });
      }
    }

    let lawyerProfile = null;
    if (role === "lawyer") {
      lawyerProfile = await Lawyer.findOne({ userId: user._id });
      if (!lawyerProfile) {
        lawyerProfile = await Lawyer.create({
          userId: user._id,
          name: user.name,
          email: user.email,
          phone: user.phone || "NA",
          specialization: [],
          experienceYears: 0,
          qualifications: "",
          barAssociation: "",
          about: "",
          photo: "",
        });
      }
    }

    const token = jwt.sign(
      { id: user._id, role: user.role },
      process.env.JWT_SECRET,
      { expiresIn: "7d" }
    );

    return res.json({
      success: true,
      message: "Google login successful",
      role: user.role,
      token,
      userId: user._id,
      lawyerProfile,
    });
  } catch (err) {
    console.error("GOOGLE AUTH ERROR:", err);
    return res.status(500).json({ success: false, error: "Server error" });
  }
};
// ================= USER PROFILE =================

// GET PROFILE
export const getProfile = async (req, res) => {
  try {
    const user = await User.findById(req.user.id).select("-password");

    if (!user) {
      return res.status(404).json({
        success: false,
        error: "User not found"
      });
    }

    return res.json({
      success: true,
      user
    });

  } catch (err) {
    console.error("GET PROFILE ERROR:", err);
    return res.status(500).json({
      success: false,
      error: "Server error"
    });
  }
};


// UPDATE PROFILE
export const updateProfile = async (req, res) => {
  try {
    const { name, email, phone, address, bio } = req.body;
    const updates = { name, email, phone, address, bio };

    const user = await User.findByIdAndUpdate(
      req.user.id,
      updates,
      { new: true }
    ).select("-password");

    return res.json({
      success: true,
      message: "Profile updated",
      user
    });

  } catch (err) {
    console.error("UPDATE PROFILE ERROR:", err);
    return res.status(500).json({
      success: false,
      error: "Server error"
    });
  }
};

// UPLOAD PROFILE PHOTO (NEW API)
export const uploadProfilePhoto = async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({
        success: false,
        error: "Photo file is required"
      });
    }

    const user = await User.findByIdAndUpdate(
      req.user.id,
      { photo: req.file.filename },
      { new: true }
    ).select("-password");

    return res.json({
      success: true,
      message: "Profile photo uploaded",
      user
    });
  } catch (err) {
    console.error("UPLOAD PROFILE PHOTO ERROR:", err);
    return res.status(500).json({
      success: false,
      error: "Server error"
    });
  }
};

// Forgot password — generic response (does not reveal whether email exists)
export const forgotPassword = async (req, res) => {
  try {
    const { email } = req.body || {};
    if (!email || !String(email).trim()) {
      return res.status(400).json({ success: false, error: "Email is required" });
    }
    await User.findOne({ email: String(email).trim() });
    return res.json({
      success: true,
      message:
        "If an account exists for this email, you will receive password reset instructions shortly.",
    });
  } catch (err) {
    console.error("FORGOT PASSWORD ERROR:", err);
    return res.status(500).json({ success: false, error: "Server error" });
  }
};