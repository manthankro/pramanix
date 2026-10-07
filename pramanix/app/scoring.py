"""Deterministic project-fit scoring. No LLM calls here.

The LLM supplies *judgments with evidence* (requirement match, difficulty,
demo, setup risk). Everything verifiable (license, activity, docs, tests,
dependency files, technology overlap) is computed from fetched data.
"""
import re

WEIGHTS = {
    "requirement_match": 30,
    "technology_match": 15,
    "difficulty_fit": 15,
    "documentation": 10,
    "completeness": 10,
    "health": 8,
    "license": 7,
    "setup_risk": 5,
}
LEVELS = {"beginner": 0, "medium": 1, "advanced": 2}
PERMISSIVE = {"mit", "apache-2.0", "bsd-2-clause", "bsd-3-clause", "isc", "unlicense", "cc0-1.0", "0bsd"}
COPYLEFT = {"gpl-2.0", "gpl-3.0", "agpl-3.0", "lgpl-2.1", "lgpl-3.0", "mpl-2.0"}
DEP_FILES = {"requirements.txt", "pyproject.toml", "package.json", "pom.xml", "build.gradle",
             "pipfile", "go.mod", "cargo.toml", "composer.json", "gemfile"}


def clamp(x, lo=0.0, hi=1.0):
    try:
        return max(lo, min(hi, float(x)))
    except (TypeError, ValueError):
        return lo


def license_score(spdx):
    if not spdx:
        return 0.0
    s = spdx.lower()
    if s in PERMISSIVE:
        return 1.0
    if s in COPYLEFT:
        return 0.6
    return 0.3


def health_score(days_since_push, archived, commits_90d):
    if archived:
        return 0.0
    if days_since_push is None:
        return 0.0
    recency = 1.0 if days_since_push <= 90 else 0.6 if days_since_push <= 365 else 0.3 if days_since_push <= 730 else 0.1
    return 0.7 * recency + 0.3 * min((commits_90d or 0) / 10, 1.0)


def documentation_score(readme):
    if not readme:
        return 0.0
    low = readme.lower()
    s = min(len(readme) / 2000, 1.0) * 0.4
    if re.search(r"install|setup|getting started|quick ?start", low):
        s += 0.3
    if re.search(r"usage|example|how to run|run the", low):
        s += 0.2
    if re.search(r"!\[|screenshot|demo", low):
        s += 0.1
    return min(s, 1.0)


def technology_score(required, languages, topics, readme):
    if not required:
        return 0.5
    hay = " ".join(list(languages or []) + list(topics or []) + [(readme or "")[:20000]]).lower()
    hits = sum(1 for t in required if str(t).lower() in hay)
    return hits / len(required)


def difficulty_score(requested, repo_level):
    if requested not in LEVELS or repo_level not in LEVELS:
        return None
    diff = LEVELS[repo_level] - LEVELS[requested]
    if diff == 0:
        return 1.0
    if abs(diff) == 2:
        return 0.0
    return 0.6 if diff < 0 else 0.4  # slightly easier is better than harder


def completeness_score(has_demo, tree):
    demo = 0.5 if has_demo else 0.0
    if tree is None:
        return demo, False
    has_tests = any(re.search(r"(^|/)(tests?|__tests__)/|\.github/workflows/", p) for p in tree)
    has_deps = any(p.rsplit("/", 1)[-1].lower() in DEP_FILES for p in tree)
    return demo + 0.25 * has_tests + 0.25 * has_deps, True


def score_repository(overview, readme, tree, requirements, judgments):
    warnings, unverified, parts = [], [], {}

    rm = clamp(judgments.get("requirement_match"))
    if not judgments.get("evidence"):
        rm = min(rm, 0.3)
        unverified.append("Requirement match had no supporting evidence, so it was capped.")
    parts["requirement_match"] = rm

    parts["technology_match"] = technology_score(
        requirements.get("technologies"), overview.get("languages"), overview.get("topics"), readme)

    d = difficulty_score(requirements.get("difficulty"), judgments.get("repo_difficulty"))
    if d is None:
        d = 0.5
        unverified.append("Difficulty fit could not be verified.")
    parts["difficulty_fit"] = d

    parts["documentation"] = documentation_score(readme)
    if not readme:
        warnings.append("No README found.")

    comp, tree_seen = completeness_score(judgments.get("has_demo"), tree)
    if not tree_seen:
        unverified.append("File tree was not inspected (tests and dependency files unverified).")
    parts["completeness"] = comp

    parts["health"] = health_score(overview.get("days_since_push"), overview.get("archived"), overview.get("commits_90d"))
    if overview.get("archived"):
        warnings.append("Repository is archived (read-only, no longer maintained).")
    elif (overview.get("days_since_push") or 0) > 365:
        warnings.append("No pushes in over a year; may be abandoned.")

    spdx = overview.get("license_spdx")
    parts["license"] = license_score(spdx)
    if not spdx:
        warnings.append("No license: by default all rights are reserved, so reuse is not permitted without the author's permission.")
    elif spdx.lower() in COPYLEFT:
        warnings.append(f"{spdx} is copyleft: derivative work must follow the same license terms.")

    risk = judgments.get("setup_risk")
    if risk is None:
        risk = 0.5
        unverified.append("Setup risk could not be verified.")
    parts["setup_risk"] = 1.0 - clamp(risk)

    breakdown = {k: round(WEIGHTS[k] * clamp(v), 1) for k, v in parts.items()}
    return {
        "total": round(sum(breakdown.values())),
        "breakdown": breakdown,
        "max_per_factor": WEIGHTS,
        "warnings": warnings,
        "unverified": unverified,
        "evidence": judgments.get("evidence", []),
    }
