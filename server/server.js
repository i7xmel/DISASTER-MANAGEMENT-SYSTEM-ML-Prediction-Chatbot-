require("dotenv").config();
require("./models/user");
require("./models/event");
require("./models/request");

const express = require("express");
const bodyParser = require("body-parser");
const axios = require("axios");
const middlewares = require("./middlewares");
const api = require("./routes");

const app = express();
app.use(bodyParser.urlencoded({ extended: true }));
app.use(bodyParser.json());

// ✅ API Home Route
app.get("/", (req, res) => {
    res.json({ status: "API Running" });
});

// ✅ Chatbot Route
app.post("/api/chatbot", async (req, res) => {
    const userMessage = req.body.message;

    try {
        const response = await axios.post("https://api.groq.com/openai/v1/chat/completions", {
            model: "llama3-8b-8192",
            messages: [{ role: "user", content: userMessage }],
        }, {
            headers: {
                "Authorization": ``,
                "Content-Type": "application/json"
            }
        });

        res.json({ reply: response.data.choices[0].message.content });
    } catch (error) {
        console.error("Chatbot Error:", error.response ? error.response.data : error.message);
        res.status(500).json({ error: "Failed to get response from chatbot" });
    }
});

// ✅ Existing API Routes
app.use("/api/v1", api);
app.use(middlewares.notFound);
app.use(middlewares.errorHandler);

module.exports = app;





