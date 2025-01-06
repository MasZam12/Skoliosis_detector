const express = require("express");
const multer = require("multer");
const cors = require("cors");
const axios = require("axios");
const FormData = require("form-data");
const fs = require("fs");
const path = require("path");

const app = express();

app.use(express.urlencoded({ extended: true }));
app.use(express.json());
app.use(cors());
app.use(express.static("../../results"));

const uploadFolder = path.join(__dirname, "uploads");

if (!fs.existsSync(uploadFolder)) {
  fs.mkdirSync(uploadFolder);
}

const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, uploadFolder);
  },
  filename: (req, file, cb) => {
    const safeName = file.originalname.replace(/[^a-zA-Z0-9.]/g, "_");
    cb(null, `${Date.now()}-${safeName}`);
  },
});

const upload = multer({ storage });

app.post("/api/upload", upload.single("file"), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).send({ error: "No file uploaded" });
    }

    const filePath = path.join(uploadFolder, req.file.filename);

    const formData = new FormData();
    formData.append("file", fs.createReadStream(filePath), req.file.filename);

    const response = await axios.post(
      "http://127.0.0.1:8000/upload/",
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
          ...formData.getHeaders(),
        },
      }
    );

    res.status(200).send(response.data);
  } catch (error) {
    console.error("Error uploading file to FastAPI backend:", error.message);
    res.status(500).send({ error: "Error uploading file to FastAPI backend" });
  }
});

app.listen(3000, () => {
  console.log("Express server running on PORT 3000");
});
