import express from "express";
import {
  createAppointment,
  getAppointmentsForLawyer,
  getAppointmentsForUser,
  updateAppointmentStatus
} from "../controllers/appointmentController.js";

const router = express.Router();

// ⭐ IMPORTANT — this MUST match frontend
router.post("/book", createAppointment);

router.get("/lawyer/:lawyerId", getAppointmentsForLawyer);
router.get("/user/:userId", getAppointmentsForUser);
router.put("/update/:id", updateAppointmentStatus);

export default router;
