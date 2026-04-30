# Meridian Electronics Customer Support Chatbot

AI-powered customer support chatbot for **Meridian Electronics**, a computer products retailer. Built with the OpenAI Agents SDK and MCP (Model Context Protocol) for real-time integration with the order management system.

## Architecture

```
User (Gradio Chat UI)
        ↓
   Agent Layer (OpenAI Agents SDK, gpt-4o-mini)
        ↓  tool calls via MCP
   MCP Server (Streamable HTTP)
        ↓
   Meridian Order Management System
```

### Key Design Decisions

- **OpenAI Agents SDK + MCP** — The agent discovers and calls tools dynamically via MCP, so the chatbot automatically adapts if the backend adds new capabilities.
- **gpt-4o-mini** — Cost-effective model that handles tool calling reliably. Per-conversation cost stays well under $0.01.
- **Streaming responses** — Users see the response as it generates, improving perceived latency.
- **Stateful conversations** — Full chat history is passed to the agent each turn, so authentication persists and context is maintained.
- **Graceful error handling** — Network failures, auth errors, and inventory issues are caught and presented as friendly messages.

### Capabilities

| Feature | Auth Required? |
|---|---|
| Browse products (list, search, details) | No |
| Authenticate (email + 4-digit PIN) | — |
| View order history | Yes |
| View order details | Yes |
| Place new orders | Yes |

## Setup

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- OpenAI API key

### Install & Run

```bash
# Clone the repo
git clone <repo-url>
cd meridian-chatbot

# Create environment
uv venv && uv pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Run
uv run app.py
```

Open **http://localhost:7860** in your browser.

### Environment Variables

| Variable | Description | Default |
|---|---|---|
| `OPENAI_API_KEY` | Your OpenAI API key | (required) |
| `MCP_SERVER_URL` | MCP server endpoint | `https://order-mcp-74afyau24q-uc.a.run.app/mcp` |

## Testing Scenarios

Use these test accounts (email + PIN):

| Email | PIN |
|---|---|
| `donaldgarcia@example.net` | 7912 |
| `michellejames@example.com` | 1520 |
| `glee@example.net` | 4582 |

### Demo Flows

1. **Product browsing** — "What monitors do you have?" → browse without auth
2. **Authentication** — "I want to check my orders" → prompted for email + PIN
3. **Order history** — After auth, view past orders and details
4. **Place order** — "I'd like to order a 24-inch monitor" → confirm and create
5. **Error handling** — Wrong PIN, out-of-stock item, invalid SKU

## Limitations & Future Improvements

- **Session-scoped auth** — authentication resets on page reload; production would use persistent sessions (e.g. JWT or server-side session store)
- **Single shared MCP connection** — all concurrent users share one connection; production needs per-session isolation to prevent state leakage
- **No payment integration** — orders are created as "submitted/pending"; a real system would integrate Stripe or similar before committing
- **Unbounded context window** — full chat history is passed every turn; long conversations will eventually hit the model's context limit and should be summarised or truncated

## Tech Stack

- **LLM**: GPT-4o-mini (OpenAI)
- **Agent Framework**: OpenAI Agents SDK
- **Tool Integration**: MCP (Model Context Protocol) via Streamable HTTP
- **UI**: Gradio 6
- **Language**: Python 3.11+
