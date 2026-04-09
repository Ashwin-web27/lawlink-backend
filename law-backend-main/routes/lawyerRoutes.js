// backend/routes/lawyerRoutes.js
import express from "express";
import { getProfile, upsertProfile, upload } from "../controllers/lawyerController.js";
import { listLawyers } from "../controllers/lawyerController.js";

const router = express.Router();

// GET profile by lawyer id (or linked user id fallback)
router.get("/profile/:id", getProfile);

// PUT update/create profile
router.put("/profile/:userId", upload.single("photo"), upsertProfile);

router.get("/list", listLawyers);

export default router;
