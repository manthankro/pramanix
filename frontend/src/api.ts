// frontend/src/api.ts

export type Repository = {
  name: string;
  url: string;
  full_name?: string | null;
  description: string | null;
  language: string | null;
  stars: number;
  forks?: number;
  topics?: string[];
  license?: string | null;
  updated_at: string | null;
};

export type ChatTurn = {
  role: "user" | "assistant";
  content: string;
};

export type ChatResult = {
  response: string;
  tool_used: string | null;
  repositories: Repository[];
  model?: string | null;
};

export type SuggestionItem = {
  category: string;
  title: string;
  prompt: string;
  icon: string;
};

export type HealthStatus = {
  status: string;
  version: string;
  model: string;
  tools: string[];
};

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

export async function sendMessage(
  message: string,
  history: ChatTurn[] = []
): Promise<ChatResult> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, history }),
    });
  } catch {
    throw new Error("Unable to connect to Pramanix server. Please verify the backend is running.");
  }

  if (!response.ok) {
    let detail = `Server responded with status ${response.status}.`;
    try {
      const body = await response.json();
      if (typeof body.detail === "string") {
        detail = body.detail;
      }
    } catch {
      // Keep generic message
    }
    throw new Error(detail);
  }

  return (await response.json()) as ChatResult;
}

export async function checkHealth(): Promise<HealthStatus | null> {
  try {
    const res = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(4000) });
    if (res.ok) {
      return (await res.json()) as HealthStatus;
    }
  } catch {
    // Health check failed
  }
  return null;
}

export async function fetchSuggestions(): Promise<SuggestionItem[]> {
  try {
    const res = await fetch(`${API_BASE}/api/suggestions`, { signal: AbortSignal.timeout(4000) });
    if (res.ok) {
      return (await res.json()) as SuggestionItem[];
    }
  } catch {
    // Fall back to default suggestions
  }
  return [
    {
      category: "🎓 Student Projects",
      title: "Python Starter Kits",
      prompt: "Find beginner-friendly Python repositories for a library management system with good documentation.",
      icon: "📚",
    },
    {
      category: "🤖 AI & Agents",
      title: "LangGraph & LLMs",
      prompt: "Find top open-source repositories demonstrating AI agents built with LangGraph and FastAPI.",
      icon: "🧠",
    },
    {
      category: "⚡ Full Stack",
      title: "React + FastAPI Starters",
      prompt: "Compare React and Next.js templates for building full-stack web applications with FastAPI.",
      icon: "🚀",
    },
    {
      category: "🔧 Developer Tools",
      title: "Top CLI & Utilities",
      prompt: "Recommend popular open-source developer CLI tools written in Python or Rust.",
      icon: "⚙️",
    },
  ];
}
