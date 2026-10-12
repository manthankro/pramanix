// frontend/src/App.tsx
import { useEffect, useRef, useState } from "react";
import { sendMessage, type Repository } from "./api";
import ChatInput from "./components/ChatInput";
import ChatMessage from "./components/ChatMessage";

export type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  repositories?: Repository[];
  error?: boolean;
};
type Conversation = { id: string; title: string; messages: Message[] };

const KEY = "pramanix.conversations";
const blank = (): Conversation => ({ id: crypto.randomUUID(), title: "New chat", messages: [] });

function load(): Conversation[] {
  try {
    const saved = JSON.parse(localStorage.getItem(KEY) ?? "[]") as Conversation[];
    return saved.length ? saved : [blank()];
  } catch {
    return [blank()];
  }
}

export default function App() {
  const [chats, setChats] = useState<Conversation[]>(load);
  const [activeId, setActiveId] = useState(chats[0].id);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);
  const active = chats.find((c) => c.id === activeId) ?? chats[0];

  useEffect(() => {
    localStorage.setItem(KEY, JSON.stringify(chats.slice(0, 20)));
  }, [chats]);
  useEffect(() => endRef.current?.scrollIntoView({ behavior: "smooth" }), [active.messages]);

  const patch = (id: string, fn: (c: Conversation) => Conversation) =>
    setChats((all) => all.map((c) => (c.id === id ? fn(c) : c)));

  async function send() {
    const text = draft.trim();
    if (!text || busy) return;
    const chatId = active.id;
    const history = active.messages
      .filter((m) => !m.error)
      .slice(-10)
      .map((m) => ({ role: m.role, content: m.content }));
    const user: Message = { id: crypto.randomUUID(), role: "user", content: text };
    patch(chatId, (c) => ({
      ...c,
      title: c.messages.length ? c.title : text.slice(0, 40),
      messages: [...c.messages, user],
    }));
    setDraft("");
    setBusy(true);
    try {
      const result = await sendMessage(text, history);
      const reply: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: result.response,
        repositories: result.repositories,
      };
      patch(chatId, (c) => ({ ...c, messages: [...c.messages, reply] }));
    } catch (err) {
      const message = err instanceof Error ? err.message : "Something went wrong.";
      const failure: Message = {
        id: crypto.randomUUID(), role: "assistant", content: message, error: true,
      };
      patch(chatId, (c) => ({ ...c, messages: [...c.messages, failure] }));
      setDraft(text); // keep the user's text so they can retry
    } finally {
      setBusy(false);
    }
  }

  function newChat() {
    const chat = blank();
    setChats((all) => [chat, ...all]);
    setActiveId(chat.id);
  }

  return (
    <div className="layout">
      <aside className="sidebar">
        <h1>Pramanix</h1>
        <button className="new" onClick={newChat}>New chat</button>
        <nav aria-label="Recent conversations">
          {chats.map((c) => (
            <button
              key={c.id}
              className={c.id === active.id ? "item active" : "item"}
              onClick={() => setActiveId(c.id)}
            >
              {c.title}
            </button>
          ))}
        </nav>
      </aside>
      <main className="chat">
        <div className="messages" aria-live="polite">
          {active.messages.length === 0 && (
            <p className="empty">Try: Find beginner Python repositories for a library system.</p>
          )}
          {active.messages.map((m) => <ChatMessage key={m.id} message={m} />)}
          <div ref={endRef} />
        </div>
        <ChatInput value={draft} disabled={busy} onChange={setDraft} onSend={send} />
      </main>
    </div>
  );
}
