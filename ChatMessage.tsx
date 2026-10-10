// frontend/src/components/ChatMessage.tsx
import type { Message } from "../App";
import RepositoryCard from "./RepositoryCard";

export default function ChatMessage({ message }: { message: Message }) {
  const kind = message.error ? "error" : message.role;
  return (
    <div className={`msg ${kind}`}>
      <div className="bubble">{message.content}</div>
      {message.repositories?.map((repo) => (
        <RepositoryCard key={repo.url} repo={repo} />
      ))}
    </div>
  );
}
