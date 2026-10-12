// frontend/src/api.ts
const API_BASE = import.meta.env.VITE_API_BASE_URL as string;

export type Repository = {
  name: string;
  url: string;
  description: string | null;
  language: string | null;
  stars: number;
  updated_at: string | null;
};

export type ChatResult = {
  response: string;
  tool_used: string | null;
  repositories: Repository[];
};

export type Turn = { role: "user" | "assistant"; content: string };

export async function sendMessage(message: string, history: Turn[]): Promise<ChatResult> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, history }),
    });
  } catch {
    throw new Error("Cannot reach the server. Check your connection and try again.");
  }
  if (!res.ok) {
    let detail = `Request failed (${res.status}).`;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") detail = body.detail;
    } catch {
      /* keep the generic message */
    }
    throw new Error(detail);
  }
  return (await res.json()) as ChatResult;
}
