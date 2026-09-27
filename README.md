# Lumen

[![CI](https://github.com/shreyansh-asopa/blog-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/shreyansh-asopa/blog-platform/actions/workflows/ci.yml)

A multi-user blog platform where writers share ideas: posts, likes, comments and moderation.

How it fits together (layers, data model, auth, key decisions): [docs/architecture.md](docs/architecture.md).

## AI writing help

The editor's **AI assistant** checks grammar, polishes wording, suggests ideas and gives
recommendations. By default it uses **Claude** through Anthropic's API:

1. Create an API key at [console.anthropic.com](https://console.anthropic.com/settings/keys).
2. Add it to `.env` as `ANTHROPIC_API_KEY=...` and restart the API
   (`docker compose up -d api`).
3. Open the editor and click **AI assistant**.

Posts are sent to Anthropic to get suggestions, and usage is billed to the key. Set
`AI_MODEL` to pick another Claude model (`claude-haiku-4-5` costs less).

For a free option that keeps posts on your machine, set `AI_PROVIDER=ollama`, install
[Ollama](https://ollama.com/download) and run `ollama pull llama3.1:8b` (about 5 GB).
`AI_PROVIDER=off` hides the feature. See `.env.example`.
