import type { Repository } from "../api";

type Props = {
  repo: Repository;
  onAskAbout?: (repoName: string) => void;
};

const LANGUAGE_COLORS: Record<string, string> = {
  Python: "#3572A5",
  TypeScript: "#3178C6",
  JavaScript: "#F7DF1E",
  HTML: "#E34F26",
  CSS: "#563D7C",
  Rust: "#DEA584",
  Go: "#00ADD8",
  Java: "#B07219",
  "C++": "#F34B7D",
  C: "#555555",
  Ruby: "#701516",
  PHP: "#4F5D95",
};

export default function RepositoryCard({ repo, onAskAbout }: Props) {
  const displayName = repo.full_name || repo.name;
  const langColor = repo.language ? LANGUAGE_COLORS[repo.language] || "#4fd8e0" : "#9a9a9f";

  return (
    <article className="repo-card" aria-label={`Repository ${displayName}`}>
      <div className="repo-header">
        <div className="repo-title-wrap">
          <svg className="repo-icon" viewBox="0 0 16 16" width="16" height="16" fill="currentColor">
            <path d="M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-.75.75h-2.5a.75.75 0 0 1 0-1.5h1.75v-2h-8a1 1 0 0 0-.714 1.7.75.75 0 1 1-1.072 1.05A2.495 2.495 0 0 1 2 11.5Zm10.5-1h-8a1 1 0 0 0-1 1v6.708A2.486 2.486 0 0 1 4.5 9h8ZM5 12.25a.25.25 0 0 1 .25-.25h3.5a.25.25 0 0 1 .25.25v3.25a.25.25 0 0 1-.4.2l-1.6-1.2-1.6 1.2a.25.25 0 0 1-.4-.2Z" />
          </svg>
          <a
            href={repo.url}
            target="_blank"
            rel="noopener noreferrer"
            className="repo-link"
            title={`View ${displayName} on GitHub`}
          >
            {displayName}
            <span className="external-mark" aria-hidden="true">↗</span>
          </a>
        </div>
        <div className="repo-stats">
          <span className="stat-badge stars" title={`${repo.stars} stargazers`}>
            ★ {repo.stars.toLocaleString()}
          </span>
          {Boolean(repo.forks && repo.forks > 0) && (
            <span className="stat-badge forks" title={`${repo.forks} forks`}>
              ⑂ {repo.forks?.toLocaleString()}
            </span>
          )}
        </div>
      </div>

      <p className="repo-desc">{repo.description || "No description provided."}</p>

      {repo.topics && repo.topics.length > 0 && (
        <div className="repo-topics">
          {repo.topics.slice(0, 4).map((topic) => (
            <span key={topic} className="topic-pill">
              {topic}
            </span>
          ))}
        </div>
      )}

      <div className="repo-footer">
        <div className="repo-meta-left">
          {repo.language && (
            <span className="lang-indicator">
              <span className="lang-dot" style={{ backgroundColor: langColor }} />
              {repo.language}
            </span>
          )}
          {repo.license && (
            <span className="license-badge" title={`License: ${repo.license}`}>
              ⚖️ {repo.license}
            </span>
          )}
        </div>
        {onAskAbout && (
          <button
            type="button"
            className="ask-repo-btn"
            onClick={() => onAskAbout(displayName)}
            title={`Ask Pramanix to explain ${displayName}`}
          >
            Explain repo 💬
          </button>
        )}
      </div>
    </article>
  );
}
