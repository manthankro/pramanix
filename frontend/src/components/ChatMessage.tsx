// frontend/src/components/ChatMessage.tsx
import React, { useState } from "react";
import type { Repository } from "../api";
import RepositoryCard from "./RepositoryCard";

export type MessageItem = {
  id: string;
  role: "user" | "assistant";
  content: string;
  toolUsed?: string | null;
  repositories?: Repository[];
  error?: boolean;
  timestamp?: string;
};

type Props = {
  message: MessageItem;
  onAskAboutRepo?: (repoName: string) => void;
  onRetry?: () => void;
};

function FormattedContent({ text }: { text: string }) {
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const copyCode = (code: string, index: number) => {
    navigator.clipboard.writeText(code);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  // Split content by code blocks ```lang ... ```
  const codeBlockRegex = /```(\w*)\n([\s\S]*?)```/g;
  const parts: React.ReactNode[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;
  let blockIndex = 0;

  while ((match = codeBlockRegex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(
        <FormattedText key={`text-${lastIndex}`} text={text.slice(lastIndex, match.index)} />
      );
    }
    const lang = match[1] || "text";
    const code = match[2].trimEnd();
    const currentBlock = blockIndex++;
    parts.push(
      <div key={`code-${match.index}`} className="code-block-wrapper">
        <div className="code-block-header">
          <span className="code-lang">{lang}</span>
          <button
            type="button"
            className="copy-code-btn"
            onClick={() => copyCode(code, currentBlock)}
          >
            {copiedIndex === currentBlock ? "✓ Copied" : "Copy"}
          </button>
        </div>
        <pre className="code-pre">
          <code>{code}</code>
        </pre>
      </div>
    );
    lastIndex = match.index + match[0].length;
  }

  if (lastIndex < text.length) {
    parts.push(<FormattedText key={`text-${lastIndex}`} text={text.slice(lastIndex)} />);
  }

  return <div className="formatted-body">{parts}</div>;
}

function FormattedText({ text }: { text: string }) {
  const lines = text.split("\n");
  const renderedLines = lines.map((line, idx) => {
    if (line.trim().startsWith("- ") || line.trim().startsWith("* ")) {
      return (
        <li key={idx} className="list-item">
          {renderInlineFormatting(line.trim().slice(2))}
        </li>
      );
    }
    if (line.startsWith("### ")) {
      return <h4 key={idx} className="heading-3">{renderInlineFormatting(line.slice(4))}</h4>;
    }
    if (line.startsWith("## ")) {
      return <h3 key={idx} className="heading-2">{renderInlineFormatting(line.slice(3))}</h3>;
    }
    if (line.startsWith("# ")) {
      return <h2 key={idx} className="heading-1">{renderInlineFormatting(line.slice(2))}</h2>;
    }
    if (line.trim() === "") {
      return <div key={idx} className="paragraph-spacer" />;
    }
    return (
      <p key={idx} className="paragraph">
        {renderInlineFormatting(line)}
      </p>
    );
  });

  return <>{renderedLines}</>;
}

function renderInlineFormatting(line: string): React.ReactNode {
  // Bold **text**
  const boldRegex = /\*\*(.*?)\*\*/g;
  const parts: React.ReactNode[] = [];
  let lastIdx = 0;
  let match: RegExpExecArray | null;

  while ((match = boldRegex.exec(line)) !== null) {
    if (match.index > lastIdx) {
      parts.push(renderLinksAndCode(line.slice(lastIdx, match.index)));
    }
    parts.push(<strong key={match.index}>{renderLinksAndCode(match[1])}</strong>);
    lastIdx = match.index + match[0].length;
  }

  if (lastIdx < line.length) {
    parts.push(renderLinksAndCode(line.slice(lastIdx)));
  }

  return parts;
}

function renderLinksAndCode(text: string): React.ReactNode {
  // Inline code `code` and links [title](url)
  const tokens = text.split(/(`[^`]+`|\[[^\]]+\]\([^)]+\))/g);
  return tokens.map((token, i) => {
    if (token.startsWith("`") && token.endsWith("`")) {
      return <code key={i} className="inline-code">{token.slice(1, -1)}</code>;
    }
    const linkMatch = token.match(/\[([^\]]+)\]\(([^)]+)\)/);
    if (linkMatch) {
      return (
        <a key={i} href={linkMatch[2]} target="_blank" rel="noopener noreferrer" className="inline-link">
          {linkMatch[1]}
        </a>
      );
    }
    return token;
  });
}

export default function ChatMessage({ message, onAskAboutRepo, onRetry }: Props) {
  const isUser = message.role === "user";
  const [copied, setCopied] = useState(false);

  const copyMessage = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <article className={`message-row ${isUser ? "user" : "assistant"} ${message.error ? "error" : ""}`}>
      {!isUser && (
        <div className="avatar-wrap">
          <img src="/pramanix-mark.svg" alt="Pramanix Mark" className="avatar-img" />
        </div>
      )}

      <div className="message-content-wrap">
        {!isUser && (
          <div className="assistant-meta">
            <span className="brand-badge">Pramanix AI</span>
            {message.toolUsed && (
              <span className="tool-pill" title={`Executed tool: ${message.toolUsed}`}>
                🛠️ {message.toolUsed}
              </span>
            )}
            <button
              type="button"
              className="copy-msg-btn"
              onClick={copyMessage}
              title="Copy message to clipboard"
            >
              {copied ? "✓ Copied" : "Copy"}
            </button>
          </div>
        )}

        <div className={`message-bubble ${isUser ? "user-bubble" : "assistant-bubble"}`}>
          <FormattedContent text={message.content} />
        </div>

        {message.error && onRetry && (
          <div className="error-actions">
            <button type="button" className="retry-btn" onClick={onRetry}>
              ↻ Retry Request
            </button>
          </div>
        )}

        {message.repositories && message.repositories.length > 0 && (
          <div className="repositories-grid">
            <div className="repos-heading">
              <span>Discovered Repositories ({message.repositories.length})</span>
            </div>
            {message.repositories.map((repo) => (
              <RepositoryCard
                key={repo.url}
                repo={repo}
                onAskAbout={onAskAboutRepo}
              />
            ))}
          </div>
        )}
      </div>
    </article>
  );
}
