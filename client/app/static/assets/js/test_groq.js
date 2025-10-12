const API_KEY = "";
const API_URL = "https://api.groq.com/openai/v1/chat/completions";

async function testGroq() {
    try {
        const response = await fetch(API_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${API_KEY}`,
            },
            body: JSON.stringify({
                model: "llama3-8b-8192",  // ✅ Use a supported model
                messages: [{ role: "user", content: "Hello, how are you?" }],
                max_tokens: 50,
            }),
        });

        const data = await response.json();
        console.log("Groq API Response:", JSON.stringify(data, null, 2));
    } catch (error) {
        console.error("Error calling Groq API:", error);
    }
}

// Run the test
testGroq();
