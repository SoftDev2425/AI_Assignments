"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = __importDefault(require("express"));
const multer_1 = __importDefault(require("multer"));
const body_parser_1 = __importDefault(require("body-parser"));
const child_process_1 = require("child_process");
const path_1 = __importDefault(require("path"));
const fs_1 = __importDefault(require("fs"));
const app = (0, express_1.default)();
const upload = (0, multer_1.default)({ dest: "uploads/" });
app.use(body_parser_1.default.json());
app.use(body_parser_1.default.urlencoded({ extended: true }));
// Serve static files from the "public" directory
app.use(express_1.default.static(path_1.default.join(__dirname, "../public")));
app.get("/", (req, res) => {
    res.sendFile(path_1.default.join(__dirname, "../public/index.html"));
});
app.post("/ask", upload.array("files"), (req, res) => __awaiter(void 0, void 0, void 0, function* () {
    const files = req.files;
    const question = req.body.question;
    if (!question) {
        return res.status(400).json({ error: "No question provided" });
    }
    try {
        // Save the uploaded files and question to a temporary directory
        const tempDir = path_1.default.join(__dirname, "../temp");
        if (!fs_1.default.existsSync(tempDir)) {
            fs_1.default.mkdirSync(tempDir);
        }
        const fileNames = [];
        for (const file of files) {
            const tempFilePath = path_1.default.join(tempDir, file.originalname);
            fs_1.default.renameSync(file.path, tempFilePath);
            fileNames.push(tempFilePath);
        }
        // Call the Python script
        const pythonProcess = (0, child_process_1.exec)(`python3 ./src/process.py ${fileNames.join(" ")} "${question}"`, (error, stdout, stderr) => {
            if (error) {
                console.error(`exec error: ${error}`);
                return res.status(500).json({ error: "Error processing the request" });
            }
            // check for duplicated sentences in the answer and filter out
            // Split the stdout into sentences
            const sentences = stdout.trim().split(/(?<=[.!?])\s+/);
            // Remove duplicate sentences
            const uniqueSentences = [...new Set(sentences)];
            // Join the unique sentences back into a single string
            const uniqueAnswer = uniqueSentences.join(" ");
            res.json({ answer: uniqueAnswer });
        });
    }
    catch (error) {
        res.status(500).json({ error: "Error processing the files" });
    }
}));
const PORT = process.env.PORT || 5001;
app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});
