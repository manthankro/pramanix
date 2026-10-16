import { useEffect, useState } from "react";
import { fetchSuggestions, type SuggestionItem } from "../api";

type Props = {
  onSelectPrompt: (promptText: string) => void;
};

export default function WelcomeHero({ onSelectPrompt }: Props) {
  const [suggestions, setSuggestions] = useState<SuggestionItem[]>([]);

  useEffect(() => {
    fetchSuggestions().then(setSuggestions);
  }, []);

  return (
    <div className="welcome-hero">
      <div className="brand-stage">
        <img
          src="/pramanix-lockup.svg"
          alt="Pramanix Logo"
          className="welcome-logo"
        />
        <div className="status-kicker">
          <span className="live-dot" />
          <span>AUTONOMOUS AGENT · LANGGRAPH & GEMINI</span>
        </div>
      </div>

      <h1 className="welcome-title">
        Explore Ideas. <br />
        <span className="gradient-text">Build Great Software.</span>
      </h1>

      <p className="welcome-subtitle">
        Your intelligent AI companion for students and developers. Ask questions, explore code
        architectures, and discover quality open-source GitHub repositories.
      </p>

      <div className="suggestions-grid">
        {suggestions.map((item, idx) => (
          <button
            key={idx}
            type="button"
            className="suggestion-card"
            onClick={() => onSelectPrompt(item.prompt)}
          >
            <div className="suggestion-top">
              <span className="suggestion-icon">{item.icon}</span>
              <span className="suggestion-category">{item.category}</span>
              <span className="suggestion-arrow">↗</span>
            </div>
            <strong className="suggestion-title">{item.title}</strong>
            <p className="suggestion-prompt">{item.prompt}</p>
          </button>
        ))}
      </div>
    </div>
  );
}
