// frontend/src/components/RepositoryCard.tsx
import type { Repository } from "../api";

export default function RepositoryCard({ repo }: { repo: Repository }) {
  return (
    <article className="repo">
      <h4>{repo.name}</h4>
      <p>{repo.description ?? "No description provided."}</p>
      <div className="meta">
        <span>{repo.language ?? "Unknown language"}</span>
        <span>{repo.stars.toLocaleString()} stars</span>
        <a href={repo.url} target="_blank" rel="noopener noreferrer">
          Open on GitHub
        </a>
      </div>
    </article>
  );
}
