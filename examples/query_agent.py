"""Send a question to a running Pramanix server.

Usage:
    uvicorn app.main:app --reload
    python examples/query_agent.py "search github for pramanix"
"""

import json
import sys
import urllib.request

URL = "http://localhost:8000/chat"


def main() -> None:
    message = sys.argv[1] if len(sys.argv) > 1 else "Hello!"
    payload = json.dumps({"message": message}).encode()
    request = urllib.request.Request(
        URL, data=payload, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(request) as response:
        print(json.dumps(json.load(response), indent=2))


if __name__ == "__main__":
    main()
