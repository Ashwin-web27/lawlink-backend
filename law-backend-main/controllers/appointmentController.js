// backend/controllers/appointmentController.js
import Appointment from "../models/Appointment.js";
import Lawyer from "../models/Lawyer.js";
import User from "../models/User.js";

// Create appointment (user booking a lawyer)
export const createAppointment = async (req, res) => {
  try {
    const { userId, lawyerId, date, time, message } = req.body;
    if (!userId || !lawyerId || !date || !time) {
      return res.status(400).json({ success: false, error: "userId, lawyerId, date and time are required" });
    }

    // optional: make sure lawyer exists
    const lawyer = await Lawyer.findOne({ userId: lawyerId }) || await Lawyer.findById(lawyerId);
    // If you store lawyer references in Lawyer.userId, above finds it; if you used User collection, adjust accordingly
    // It's OK if lawyer is null — you can decide to enforce it:
    if (!lawyer) {
      // try checking User model for lawyer role
      const maybe = await User.findOne({ _id: lawyerId, role: "lawyer" });
      if (!maybe) {
        return res.status(404).json({ success: false, error: "Lawyer not found" });
      }
    }

    const appointment = await Appointment.create({
      userId,
      lawyerId,
      date,
      time,
      message,
      status: "pending"
    });

    return res.json({ success: true, appointment });
  } catch (err) {
    console.error("CREATE APPT ERROR:", err);
    return res.status(500).json({ success: false, error: "Server error" });
  }
};

// Get appointments for a lawyer
export const getAppointmentsForLawyer = async (req, res) => {
  try {
    const { lawyerId } = req.params;
    // Populate client details so the lawyer UI can show client avatar/name.
    const appointments = await Appointment.find({ lawyerId })
      .populate("userId", "name photo")
      .sort({ createdAt: -1 });
    return res.json({ success: true, appointments });
  } catch (err) {
    console.error("GET APPTS LAWYER ERROR:", err);
    return res.status(500).json({ success: false, error: "Server error" });
  }
};

// Get appointments for a user
export const getAppointmentsForUser = async (req, res) => {
  try {
    const { userId } = req.params;
    const appointments = await Appointment.find({ userId })
      .sort({ createdAt: -1 })
      .lean();

    const lawyerRefIds = Array.from(
      new Set(
        appointments
          .map((appt) => {
            if (!appt?.lawyerId) return null;
            if (typeof appt.lawyerId === "object" && appt.lawyerId._id) {
              return String(appt.lawyerId._id);
            }
            return String(appt.lawyerId);
          })
          .filter(Boolean)
      )
    );

    const lawyers = await Lawyer.find({
      $or: [
        { _id: { $in: lawyerRefIds } },
        { userId: { $in: lawyerRefIds } },
      ],
    })
      .select("userId name specialization photo")
      .lean();

    const lawyerMap = new Map();
    for (const lawyer of lawyers) {
      lawyerMap.set(String(lawyer._id), lawyer);
      if (lawyer.userId) {
        lawyerMap.set(String(lawyer.userId), lawyer);
      }
    }

    const enrichedAppointments = appointments.map((appt) => {
      const key =
        typeof appt.lawyerId === "object" && appt.lawyerId?._id
          ? String(appt.lawyerId._id)
          : String(appt.lawyerId || "");
      const lawyer = lawyerMap.get(key) || null;

      return {
        ...appt,
        lawyer: lawyer
          ? {
              _id: lawyer._id,
              userId: lawyer.userId,
              name: lawyer.name || "Lawyer",
              photo: lawyer.photo || "",
              specialization: lawyer.specialization || [],
            }
          : null,
      };
    });

    return res.json({ success: true, appointments: enrichedAppointments });
  } catch (err) {
    console.error("GET APPTS USER ERROR:", err);
    return res.status(500).json({ success: false, error: "Server error" });
  }
};

// Update status (accept/reject/complete)
export const updateAppointmentStatus = async (req, res) => {
  try {
    const { id } = req.params;
    const { status } = req.body;
    if (!["pending","accepted","rejected","completed"].includes(status)) {
      return res.status(400).json({ success: false, error: "Invalid status" });
    }

    const appt = await Appointment.findByIdAndUpdate(id, { $set: { status } }, { new: true });
    if (!appt) return res.status(404).json({ success: false, error: "Appointment not found" });

    return res.json({ success: true, appointment: appt });
  } catch (err) {
    console.error("UPDATE APPT ERROR:", err);
    return res.status(500).json({ success: false, error: "Server error" });
  }
};
