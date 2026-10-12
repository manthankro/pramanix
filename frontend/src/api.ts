export type Repository = {
  name: string;
  url: string;
  description: string | null;
  language: string | null;
  stars: number;
  updated_at: string | null;
};

export type ChatTurn = { role: "user" | "assistant"; content: string };
export type ChatResult = {
  response: string;
  tool_used: string | null;
  repositories: Repository[];
};

const apiBase = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export async function sendMessage(message: string, history: ChatTurn[]): Promise<ChatResult> {
  const response = await fetch(`${apiBase}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, history }),
  });
  if (!response.ok) {
    const payload: { detail?: string } = await response.json().catch(() => ({}));
    throw new Error(payload.detail || `Chat request failed (${response.status})`);
  }
  return (await response.json()) as ChatResult;
}
