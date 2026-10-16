import { useRef, useEffect, type KeyboardEvent } from "react";

type Props = {
  value: string;
  disabled: boolean;
  onChange: (value: string) => void;
  onSend: () => void;
  placeholder?: string;
};

export default function ChatInput({
  value,
  disabled,
  onChange,
  onSend,
  placeholder = "Ask anything, explore project ideas, or search GitHub repositories...",
}: Props) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea based on content
  useEffect(() => {
    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto";
      const newHeight = Math.min(el.scrollHeight, 180);
      el.style.height = `${Math.max(newHeight, 52)}px`;
    }
  }, [value]);

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!disabled && value.trim()) {
        onSend();
      }
    }
  }

  const charCount = value.length;
  const isNearLimit = charCount > 1800;

  return (
    <div className="composer-container">
      <div className="composer-card">
        <textarea
          ref={textareaRef}
          aria-label="Message Pramanix"
          placeholder={placeholder}
          value={value}
          rows={1}
          maxLength={2000}
          disabled={disabled}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          className="composer-textarea"
        />
        <div className="composer-bar">
          <div className="composer-hints">
            <span className="key-hint">Enter to send · Shift+Enter for new line</span>
            {charCount > 0 && (
              <span className={`char-counter ${isNearLimit ? "warning" : ""}`}>
                {charCount} / 2000
              </span>
            )}
          </div>
          <div className="composer-actions">
            {value.trim() && !disabled && (
              <button
                type="button"
                className="clear-btn"
                onClick={() => onChange("")}
                title="Clear input"
              >
                Clear
              </button>
            )}
            <button
              type="button"
              className="send-btn"
              onClick={onSend}
              disabled={disabled || !value.trim()}
              title="Send message (Enter)"
            >
              {disabled ? (
                <span className="btn-loading">
                  <span className="dot" />
                  <span className="dot" />
                  <span className="dot" />
                </span>
              ) : (
                <span className="send-icon">↑</span>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
