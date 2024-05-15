import express, { Request, Response } from "express";
import multer from "multer";
import bodyParser from "body-parser";
import { exec } from "child_process";
import path from "path";
import fs from "fs";

const app = express();
const upload = multer({ dest: "uploads/" });

app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// Serve static files from the "public" directory
app.use(express.static(path.join(__dirname, "../public")));

app.get("/", (req: Request, res: Response) => {
  res.sendFile(path.join(__dirname, "../public/index.html"));
});

app.post("/ask", upload.array("files"), async (req: Request, res: Response) => {
  const files = req.files as Express.Multer.File[];
  const question = req.body.question;

  if (!question) {
    return res.status(400).json({ error: "No question provided" });
  }

  try {
    // Save the uploaded files and question to a temporary directory
    const tempDir = path.join(__dirname, "../temp");
    if (!fs.existsSync(tempDir)) {
      fs.mkdirSync(tempDir);
    }

    const fileNames: string[] = [];
    for (const file of files) {
      const tempFilePath = path.join(tempDir, file.originalname);
      fs.renameSync(file.path, tempFilePath);
      fileNames.push(tempFilePath);
    }

    // Call the Python script
    const pythonProcess = exec(
      `python3 ./src/process.py ${fileNames.join(" ")} "${question}"`,
      (error, stdout, stderr) => {
        if (error) {
          console.error(`exec error: ${error}`);
          return res.status(500).json({ error: "Error processing the request" });
        }
        res.json({ answer: stdout.trim() });
      }
    );
  } catch (error) {
    res.status(500).json({ error: "Error processing the files" });
  }
});

const PORT = process.env.PORT || 5001;
app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});
