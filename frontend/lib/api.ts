export const FASTAPI_BASE_URL = process.env.NEXT_PUBLIC_FASTAPI_BASE_URL || "http://localhost:8000";

export async function sendMessage(message: string, history: string[][] = [], conversation_id: string = "") {
  const response = await fetch(`${FASTAPI_BASE_URL}/chat/message`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      message,
      history,
      conversation_id,
      reasoning_type: "simple", // Default for now
      llm_type: "", // Default
      use_mind_map: false,
      use_citation: "off",
      language: "English",
      user_id: "default",
      selected_file_ids: [],
    }),
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  // Return a ReadableStream directly
  return response.body;
}

export async function getChatSuggestions() {
  const response = await fetch(`${FASTAPI_BASE_URL}/chat/suggestions`);
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  const data = await response.json();
  return data.suggestions;
}

export async function uploadFile(file: File) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${FASTAPI_BASE_URL}/files/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  const data = await response.json();
  return data;
}

export async function getFiles() {
  const response = await fetch(`${FASTAPI_BASE_URL}/files`);
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  const data = await response.json();
  return data.files;
}
