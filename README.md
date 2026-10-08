# Pramanix Agent 🤖

An autonomous AI agent built with **LangGraph**, **FastAPI**, and **Pydantic**.

## Features
- **LangGraph State Machine:** Reasoning loop for multi-step tool execution.
- **FastAPI Endpoints:** Production-ready API integration.
- **Automated CI/CD:** Code formatting, linting, and type checking via GitHub Actions.

## Getting Started

### Local Setup
```bash
pip install -e ".[dev]"
ruff check .
mypy app/
pytest
```
