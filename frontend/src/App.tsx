// frontend/src/App.tsx
import React, { useEffect, useRef, useState } from "react";
import {
  checkHealth,
  sendMessage,
  type ChatTurn,
  type HealthStatus,
} from "./api";
import ChatInput from "./components/ChatInput";
import ChatMessage, { type MessageItem } from "./components/ChatMessage";
import Sidebar, { type Conversation } from "./components/Sidebar";
import WelcomeHero from "./components/WelcomeHero";

const STORAGE_KEY = "pramanix.conversations.v2";

function createBlankChat(): Conversation {
  return {
    id: crypto.randomUUID(),
    title: "New Exploration",
    messages: [],
    createdAt: Date.now(),
  };
}

function loadInitialChats(): Conversation[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw) as Conversation[];
      if (Array.isArray(parsed) && parsed.length > 0) {
        return parsed;
      }
    }
  } catch {
    // Fall back to blank
  }
  return [createBlankChat()];
}

export default function App() {
  const [conversations, setConversations] = useState<Conversation[]>(loadInitialChats);
  const [activeId, setActiveId] = useState<string>(() => conversations[0]?.id || "");
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const activeChat = conversations.find((c) => c.id === activeId) || conversations[0] || createBlankChat();

  // Save conversations to localStorage
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations.slice(0, 30)));
    } catch {
      // Ignore storage errors
    }
  }, [conversations]);

  // Periodic health check
  useEffect(() => {
    checkHealth().then(setHealth);
    const interval = setInterval(() => {
      checkHealth().then(setHealth);
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  // Auto-scroll to bottom of conversation
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [activeChat.messages, busy]);

  const updateChat = (id: string, updater: (chat: Conversation) => Conversation) => {
    setConversations((all) => all.map((c) => (c.id === id ? updater(c) : c)));
  };

  async function handleSend(customText?: string) {
    const textToSend = (customText || draft).trim();
    if (!textToSend || busy) return;

    const currentChatId = activeChat.id;
    const history: ChatTurn[] = activeChat.messages
      .filter((m) => !m.error)
      .slice(-12)
      .map((m) => ({ role: m.role, content: m.content }));

    const userMessage: MessageItem = {
      id: crypto.randomUUID(),
      role: "user",
      content: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    // Append user message & update chat title if it's the first message
    updateChat(currentChatId, (chat) => ({
      ...chat,
      title: chat.messages.length === 0 ? textToSend.slice(0, 36) : chat.title,
      messages: [...chat.messages, userMessage],
    }));

    if (!customText) {
      setDraft("");
    }
    setBusy(true);

    try {
      const result = await sendMessage(textToSend, history);
      const assistantMessage: MessageItem = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: result.response,
        toolUsed: result.tool_used,
        repositories: result.repositories,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      updateChat(currentChatId, (chat) => ({
        ...chat,
        messages: [...chat.messages, assistantMessage],
      }));
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "An unexpected error occurred.";
      const failureMessage: MessageItem = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: errorMessage,
        error: true,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      updateChat(currentChatId, (chat) => ({
        ...chat,
        messages: [...chat.messages, failureMessage],
      }));
    } finally {
      setBusy(false);
    }
  }

  function handleNewChat() {
    const newChat = createBlankChat();
    setConversations((all) => [newChat, ...all]);
    setActiveId(newChat.id);
  }

  function handleDeleteChat(id: string, e: React.MouseEvent) {
    e.stopPropagation();
    if (conversations.length <= 1) return;
    const remaining = conversations.filter((c) => c.id !== id);
    setConversations(remaining);
    if (activeId === id) {
      setActiveId(remaining[0].id);
    }
  }

  function handleClearAll() {
    if (window.confirm("Are you sure you want to clear all chat history?")) {
      const fresh = createBlankChat();
      setConversations([fresh]);
      setActiveId(fresh.id);
    }
  }

  function handleAskAboutRepo(repoName: string) {
    const prompt = `Can you inspect and explain the GitHub repository '${repoName}'? What is its architecture, primary use-case, and how can a student get started with it?`;
    handleSend(prompt);
  }

  function handleRetryLast() {
    const lastUserMessage = [...activeChat.messages].reverse().find((m) => m.role === "user");
    if (lastUserMessage) {
      handleSend(lastUserMessage.content);
    }
  }

  return (
    <div className="app-container">
      <Sidebar
        conversations={conversations}
        activeId={activeChat.id}
        onSelectChat={setActiveId}
        onNewChat={handleNewChat}
        onDeleteChat={handleDeleteChat}
        onClearAll={handleClearAll}
        health={health}
        isOpenMobile={mobileSidebarOpen}
        onCloseMobile={() => setMobileSidebarOpen(false)}
      />

      <main className="main-workspace">
        <header className="workspace-topbar">
          <button
            type="button"
            className="hamburger-btn"
            onClick={() => setMobileSidebarOpen(true)}
            aria-label="Open sidebar menu"
          >
            ☰
          </button>

          <div className="topbar-brand">
            <img src="/pramanix-mark.svg" alt="Pramanix" className="topbar-logo" />
            <span className="topbar-name">PRAMANIX</span>
          </div>

          <div className="topbar-right">
            <span className={`connection-pill ${health ? "connected" : "connecting"}`}>
              <span className="pill-dot" />
              <span>{health ? `${health.model}` : "Connecting to server"}</span>
            </span>
            <button
              type="button"
              className="topbar-new-btn"
              onClick={handleNewChat}
              title="Start a new chat"
            >
              ＋ New
            </button>
          </div>
        </header>

        <section className="chat-viewport">
          {activeChat.messages.length === 0 ? (
            <WelcomeHero onSelectPrompt={(prompt) => handleSend(prompt)} />
          ) : (
            <div className="messages-stream">
              {activeChat.messages.map((message) => (
                <ChatMessage
                  key={message.id}
                  message={message}
                  onAskAboutRepo={handleAskAboutRepo}
                  onRetry={handleRetryLast}
                />
              ))}

              {busy && (
                <div className="message-row assistant thinking-row">
                  <div className="avatar-wrap">
                    <img src="/pramanix-mark.svg" alt="Pramanix" className="avatar-img pulsing" />
                  </div>
                  <div className="message-content-wrap">
                    <div className="assistant-meta">
                      <span className="brand-badge">Pramanix AI</span>
                    </div>
                    <div className="message-bubble assistant-bubble thinking-bubble">
                      <div className="typing-dots">
                        <span className="t-dot" />
                        <span className="t-dot" />
                        <span className="t-dot" />
                      </div>
                      <span className="thinking-text">Exploring repositories and reasoning...</span>
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} className="scroll-anchor" />
            </div>
          )}
        </section>

        <footer className="workspace-composer-footer">
          <ChatInput
            value={draft}
            disabled={busy}
            onChange={setDraft}
            onSend={() => handleSend()}
          />
        </footer>
      </main>
    </div>
  );
}
