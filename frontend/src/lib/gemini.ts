import { GoogleGenerativeAI } from "@google/generative-ai";

const API_KEY = import.meta.env.VITE_GEMINI_API_KEY;

let genAI: GoogleGenerativeAI | null = null;

if (API_KEY) {
  genAI = new GoogleGenerativeAI(API_KEY);
}

export async function generateTitle(firstPrompt: string): Promise<string> {
  if (!genAI) {
    console.warn("Gemini API key not configured, using default title");
    return `Pane ${Date.now().toString().slice(-4)}`;
  }

  try {
    const model = genAI.getGenerativeModel({ model: "gemini-pro" });

    const prompt = `Given this user request for code changes: "${firstPrompt}"

Generate a short, concise title (3-5 words maximum) that describes what the user wants to do. Only return the title, nothing else.

Examples:
- "Add login button" -> "Add Login"
- "Fix the navbar styling" -> "Fix Navbar Styling"
- "Create a new dashboard component" -> "Create Dashboard"
- "Refactor API calls" -> "Refactor API"

Title:`;

    const result = await model.generateContent(prompt);
    const response = await result.response;
    const text = response.text().trim();

    // Limit to 50 characters
    return text.length > 50 ? text.substring(0, 47) + "..." : text;
  } catch (error) {
    console.error("Error generating title:", error);
    // Fallback to a simple title
    const words = firstPrompt.split(" ").slice(0, 3).join(" ");
    return words.length > 30 ? words.substring(0, 27) + "..." : words;
  }
}

