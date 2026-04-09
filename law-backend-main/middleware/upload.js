import multer from "multer";
import fs from "fs";
import path from "path";

const userUploadDir = path.join(process.cwd(), "uploads", "user");

if (!fs.existsSync(userUploadDir)) {
  fs.mkdirSync(userUploadDir, { recursive: true });
}

const storage = multer.diskStorage({
  destination: userUploadDir,
  filename: (req, file, cb) => {
    cb(null, Date.now() + "-" + file.originalname);
  }
});

const upload = multer({ storage });

export default upload;