from app.scoring import score_repository

REQ = {"technologies": ["Python", "Flask"], "difficulty": "medium"}
README = "# App\n## Installation\npip install -r requirements.txt\n## Usage\nRun it. ![screenshot](a.png)\n" + "text " * 500
TREE = ["app.py", "requirements.txt", "tests/test_app.py", ".github/workflows/ci.yml"]


def good():
    return dict(
        overview={"languages": {"Python": 1}, "topics": ["flask"], "days_since_push": 20,
                  "commits_90d": 12, "archived": False, "license_spdx": "MIT"},
        readme=README, tree=TREE, requirements=REQ,
        judgments={"requirement_match": 0.9, "evidence": ["README: student portal"],
                   "repo_difficulty": "medium", "has_demo": True, "setup_risk": 0.1})


def test_strong_repo_scores_high():
    assert score_repository(**good())["total"] >= 85


def test_no_license_and_abandoned_is_penalised_and_warned():
    g = good()
    g["overview"].update(license_spdx=None, days_since_push=900, commits_90d=0)
    r = score_repository(**g)
    assert r["total"] < score_repository(**good())["total"] - 10
    assert any("No license" in w for w in r["warnings"])


def test_requirement_match_without_evidence_is_capped():
    g = good()
    g["judgments"]["evidence"] = []
    r = score_repository(**g)
    assert r["breakdown"]["requirement_match"] <= 9.0
    assert r["unverified"]


def test_scores_are_deterministic_and_bounded():
    assert score_repository(**good()) == score_repository(**good())
    assert 0 <= score_repository(**good())["total"] <= 100


def test_missing_tree_is_flagged_unverified():
    g = good()
    g["tree"] = None
    assert any("tree" in u for u in score_repository(**g)["unverified"])
