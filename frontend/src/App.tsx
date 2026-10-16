import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from "react";
import { ChatResult, ChatTurn, Repository, sendMessage } from "./api";

type Message = ChatTurn & { id: number; repositories?: Repository[] };

const starterPrompts = [
  "Find beginner Python projects for a library system",
  "Explain how an AI agent chooses a tool",
  "Compare React and Vue for a student project",
];

function RepositoryCard({ repository }: { repository: Repository }) {
  return (
    <article className="repo-card">
      <div className="repo-topline">
        <span className="repo-mark" aria-hidden="true">⌘</span>
        <a href={repository.url} target="_blank" rel="noreferrer">{repository.name}</a>
        <span className="stars" aria-label={`${repository.stars} stars`}>★ {repository.stars.toLocaleString()}</span>
      </div>
      <p>{repository.description || "No description provided."}</p>
      <div className="repo-bottomline">
        <span>{repository.language || "Language not specified"}</span>
        {repository.updated_at && <span>Updated {new Date(repository.updated_at).toLocaleDateString()}</span>}
      </div>
    </article>
  );
}

export default function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pendingMessage, setPendingMessage] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  async function submit(text: string, retry = false) {
    const value = text.trim();
    if (!value || loading) return;
    const retryingLastTurn = retry && messages[messages.length - 1]?.role === "user";
    const priorMessages = messages
      .slice(0, retryingLastTurn ? -1 : undefined)
      .map(({ role, content }) => ({ role, content }));
    if (!retryingLastTurn) {
      setMessages((current) => [...current, { id: Date.now(), role: "user", content: value }]);
    }
    setDraft("");
    setLoading(true);
    setError(null);
    setPendingMessage(value);
    try {
      const result: ChatResult = await sendMessage(value, priorMessages);
      setMessages((current) => [
        ...current,
        {
          id: Date.now() + 1,
          role: "assistant",
          content: result.response,
          repositories: result.repositories,
        },
      ]);
      setPendingMessage(null);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Something went wrong. Please try again.");
      setDraft(value);
    } finally {
      setLoading(false);
    }
  }

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void submit(draft);
  }

  function onKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void submit(draft);
    }
  }

  function newChat() {
    setMessages([]);
    setDraft("");
    setError(null);
    setPendingMessage(null);
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand"><span className="brand-icon">P</span><span>pramanix</span></div>
        <button className="new-chat" onClick={newChat}><span>＋</span> New chat</button>
        <p className="side-label">YOUR SPACE</p>
        <button className="side-link active"><span>◉</span> AI Assistant</button>
        <div className="sidebar-spacer" />
        <div className="privacy-note"><span>✦</span><p>Your ideas stay yours.<br />API keys remain on the server.</p></div>
        <div className="profile"><div className="avatar">P</div><div><strong>Pramanix AI</strong><small>Student assistant</small></div></div>
      </aside>

      <section className="workspace">
        <header className="topbar"><div className="mobile-brand"><span className="brand-icon">P</span> pramanix</div><span className="model-pill"><i /> AI assistant</span><button className="top-new" onClick={newChat}>＋ <span>New chat</span></button></header>

        <div className="conversation" ref={scrollRef}>
          {messages.length === 0 ? (
            <div className="welcome">
              <div className="welcome-orb"><span>✳</span></div>
              <p className="eyebrow">YOUR AI STUDY PARTNER</p>
              <h1>Ideas start<br /><em>somewhere.</em></h1>
              <p className="welcome-copy">Ask a question, explore a topic, or find real open-source projects on GitHub.</p>
              <div className="suggestions" aria-label="Suggested questions">
                {starterPrompts.map((prompt, index) => (
                  <button key={prompt} onClick={() => void submit(prompt)}><span>{["⌘", "✳", "↗"][index]}</span>{prompt}<b>↗</b></button>
                ))}
              </div>
            </div>
          ) : (
            <div className="message-list">
              {messages.map((message) => (
                <article key={message.id} className={`message ${message.role}`}>
                  {message.role === "assistant" && <div className="assistant-avatar">✳</div>}
                  <div className="message-body">
                    {message.role === "assistant" && <span className="message-name">Pramanix</span>}
                    <div className="message-text">{message.content}</div>
                    {message.repositories && message.repositories.length > 0 && (
                      <div className="repo-list">{message.repositories.map((repo) => <RepositoryCard key={repo.url} repository={repo} />)}</div>
                    )}
                  </div>
                </article>
              ))}
              {loading && <article className="message assistant"><div className="assistant-avatar">✳</div><div className="message-body"><span className="message-name">Pramanix</span><div className="typing"><i /><i /><i /></div></div></article>}
            </div>
          )}
        </div>

        <div className="composer-wrap">
          {error && <div className="error-banner" role="alert"><span>{error}</span><button onClick={() => pendingMessage && void submit(pendingMessage, true)}>Retry ↻</button></div>}
          <form className="composer" onSubmit={onSubmit}>
            <textarea value={draft} onChange={(event) => setDraft(event.target.value)} onKeyDown={onKeyDown} placeholder="Ask anything, or find a GitHub project..." rows={1} maxLength={2000} aria-label="Message Pramanix" />
            <div className="composer-footer"><span>AI can make mistakes. Check important information.</span><button type="submit" disabled={!draft.trim() || loading} aria-label="Send message">↑</button></div>
          </form>
          <p className="shortcut">Enter to send <span>·</span> Shift + Enter for a new line</p>
        </div>
      </section>
    </main>
  );
}
