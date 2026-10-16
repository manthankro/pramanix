"""Send a question or health check to a running Pramanix server.

Usage:
    # Run the server:
    uvicorn app.main:app --reload

    # Query the agent:
    python examples/query_agent.py "find beginner python repositories for quiz apps"

    # Check server health:
    python examples/query_agent.py --health
"""

import json
import sys
import urllib.request

BASE_URL = "http://localhost:8000"


def check_health() -> None:
    req = urllib.request.Request(f"{BASE_URL}/health")
    with urllib.request.urlopen(req) as res:
        print(json.dumps(json.load(res), indent=2))


def query_chat(message: str) -> None:
    payload = json.dumps({"message": message}).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as res:
            data = json.load(res)
            print("\n🤖 Pramanix Response:")
            print("-" * 60)
            print(data.get("response", ""))
            print("-" * 60)
            tool = data.get("tool_used")
            if tool:
                print(f"Tool used: {tool}")
            repos = data.get("repositories", [])
            if repos:
                print(f"\nDiscovered {len(repos)} repositories:")
                for r in repos:
                    print(
                        f"  • {r.get('full_name') or r.get('name')} (★ {r.get('stars', 0)}) -> {r.get('url')}"
                    )
    except urllib.error.HTTPError as exc:
        print(f"Server error {exc.code}: {exc.read().decode('utf-8')}", file=sys.stderr)


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "--health":
        check_health()
    else:
        message = (
            sys.argv[1]
            if len(sys.argv) > 1
            else "Find beginner Python projects for a library system"
        )
        query_chat(message)


if __name__ == "__main__":
    main()
