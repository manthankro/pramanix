// frontend/src/components/ChatInput.tsx
import type { KeyboardEvent } from "react";

type Props = {
  value: string;
  disabled: boolean;
  onChange: (value: string) => void;
  onSend: () => void;
};

export default function ChatInput({ value, disabled, onChange, onSend }: Props) {
  function onKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!disabled) onSend();
    }
  }
  return (
    <div className="composer">
      <textarea
        aria-label="Message"
        placeholder="Ask anything, or describe a project to find repositories"
        value={value}
        rows={2}
        maxLength={2000}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={onKeyDown}
      />
      <button onClick={onSend} disabled={disabled || !value.trim()}>
        {disabled ? "Thinking..." : "Send"}
      </button>
    </div>
  );
}
