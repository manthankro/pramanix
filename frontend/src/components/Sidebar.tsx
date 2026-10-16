// frontend/src/components/Sidebar.tsx
import React from "react";
import type { HealthStatus } from "../api";

export type Conversation = {
  id: string;
  title: string;
  messages: any[];
  createdAt: number;
};

type Props = {
  conversations: Conversation[];
  activeId: string;
  onSelectChat: (id: string) => void;
  onNewChat: () => void;
  onDeleteChat: (id: string, e: React.MouseEvent) => void;
  onClearAll: () => void;
  health: HealthStatus | null;
  isOpenMobile: boolean;
  onCloseMobile: () => void;
};

export default function Sidebar({
  conversations,
  activeId,
  onSelectChat,
  onNewChat,
  onDeleteChat,
  onClearAll,
  health,
  isOpenMobile,
  onCloseMobile,
}: Props) {
  return (
    <>
      {isOpenMobile && <div className="sidebar-backdrop" onClick={onCloseMobile} />}
      <aside className={`app-sidebar ${isOpenMobile ? "open" : ""}`}>
        <div className="sidebar-header">
          <div className="sidebar-brand">
            <img src="/pramanix-mark.svg" alt="Pramanix Mark" className="brand-mark-img" />
            <span className="brand-name">PRAMANIX</span>
          </div>
          <button
            type="button"
            className="mobile-close-btn"
            onClick={onCloseMobile}
            aria-label="Close sidebar"
          >
            ✕
          </button>
        </div>

        <button
          type="button"
          className="new-chat-btn"
          onClick={() => {
            onNewChat();
            onCloseMobile();
          }}
        >
          <span className="plus-icon">＋</span>
          <span>New Chat</span>
        </button>

        <div className="sidebar-nav-section">
          <div className="nav-section-title">
            <span>RECENT CHATS</span>
            {conversations.length > 1 && (
              <button
                type="button"
                className="clear-all-btn"
                onClick={onClearAll}
                title="Clear all conversations"
              >
                Clear all
              </button>
            )}
          </div>
          <nav className="chat-history-list" aria-label="Recent chats">
            {conversations.map((chat) => (
              <div
                key={chat.id}
                className={`chat-item-row ${chat.id === activeId ? "active" : ""}`}
                onClick={() => {
                  onSelectChat(chat.id);
                  onCloseMobile();
                }}
              >
                <span className="chat-item-icon">💬</span>
                <span className="chat-item-title" title={chat.title}>
                  {chat.title}
                </span>
                {conversations.length > 1 && (
                  <button
                    type="button"
                    className="delete-chat-btn"
                    onClick={(e) => onDeleteChat(chat.id, e)}
                    title="Delete conversation"
                  >
                    ✕
                  </button>
                )}
              </div>
            ))}
          </nav>
        </div>

        <div className="sidebar-footer">
          <div className="server-status-card">
            <div className="status-indicator-row">
              <span className={`status-dot ${health ? "online" : "offline"}`} />
              <span className="status-label">
                {health ? "Backend Connected" : "Connecting..."}
              </span>
            </div>
            {health && (
              <div className="status-meta">
                <span>Model: {health.model}</span>
                <span>Version: v{health.version}</span>
              </div>
            )}
          </div>

          <div className="privacy-pill">
            <span className="privacy-icon">🔒</span>
            <span>API keys & tokens remain server-side.</span>
          </div>
        </div>
      </aside>
    </>
  );
}
