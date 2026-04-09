import express from "express";
import { register, login, googleAuth, forgotPassword } from "../controllers/authController.js";
import { getProfile, updateProfile, uploadProfilePhoto } from "../controllers/authController.js";
import { protect } from "../middleware/protect.js";
import upload from "../middleware/upload.js";

const router = express.Router();

router.post("/register", register);
router.post("/login", login);
router.post("/google", googleAuth);
router.post("/forgot-password", forgotPassword);
router.get("/profile", protect, getProfile);
router.put("/profile", protect, updateProfile);
router.put("/profile/photo", protect, upload.single("photo"), uploadProfilePhoto);

export default router;
