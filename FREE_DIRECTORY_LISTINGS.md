# 🌐 Free Public Directory Submissions & Registry Manifests

All endpoints below are active and responding on **`http://217.154.51.0`** (Port 80) and Polygon Mainnet.

---

## 1. Live Discovery Standards (Already Deployed & Active)

| Standard / Crawler | Live URL | Purpose |
| :--- | :--- | :--- |
| **Agent Reference Homepage** | [`http://217.154.51.0/`](http://217.154.51.0/) | Public homepage with featured Tollbooth banner & tool links |
| **A2A Protocol Discovery** | [`http://217.154.51.0/.well-known/agent.json`](http://217.154.51.0/.well-known/agent.json) | Auto-discovered by autonomous agent spiders & swarms |
| **Model Context Protocol** | [`http://217.154.51.0/.well-known/mcp.json`](http://217.154.51.0/.well-known/mcp.json) | Indexed by MCP ecosystem crawlers (Glama, PulseMCP) |
| **LLMs.txt Standard** | [`http://217.154.51.0/llms.txt`](http://217.154.51.0/llms.txt) | Ingested by Anthropic, Cursor, OpenAI & Perplexity agents |
| **OpenAPI 3.1 Specification** | [`http://217.154.51.0/openapi.json`](http://217.154.51.0/openapi.json) | Auto-generates tools for LangChain, AutoGPT, CrewAI |
| **Live Tool Catalog** | [`http://217.154.51.0/v1/catalog`](http://217.154.51.0/v1/catalog) | Full pricing, contract addresses & freemium rules |

---

## 2. Free 1-Click External Directory Submissions

### A. Smithery.ai (Largest Public MCP Registry)
- **Link**: [https://smithery.ai/new](https://smithery.ai/new)
- **Cost**: 100% Free
- **How to Submit**:
  1. Push the local Git repository in `C:\Users\Admin\.gemini\antigravity\scratch\agent_tollbooth` to a free GitHub repo (e.g. `your-username/agent-tollbooth`).
  2. Paste the GitHub URL into [smithery.ai/new](https://smithery.ai/new).
  3. Smithery automatically detects [`smithery.yaml`](file:///C:/Users/Admin/.gemini/antigravity/scratch/agent_tollbooth/smithery.yaml) and indexes the server instantly.

### B. Glama.ai MCP Directory
- **Link**: [https://glama.ai/mcp/servers](https://glama.ai/mcp/servers)
- **Cost**: 100% Free
- **How to Submit**: Click "Add Server" and submit:
  - **Name**: `agent-tollbooth`
  - **Manifest URL**: `http://217.154.51.0/.well-known/mcp.json`
  - **Category**: Finance / Web3 / Tools

### C. Awesome-MCP-Servers (GitHub Community List)
- **Link**: [https://github.com/punkpeye/awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers)
- **Cost**: 100% Free
- **Submission Line to add under `Financial / Crypto` or `Utilities`**:
  ```markdown
  - [Agent Tollbooth](http://217.154.51.0) - Autonomous x402 micro-payment gateway providing institutional crypto microstructure alpha, stink-bid cascades, and 3D CAD fabrication validation with Polygon on-chain settlement and 3-call freemium tier.
  ```

### D. Coinbase AgentKit Tool Catalog
- **Specification**: Ingests our [`openapi.json`](file:///C:/Users/Admin/.gemini/antigravity/scratch/agent_tollbooth/openapi.json).
- **Target URL**: `http://217.154.51.0/openapi.json`
- **Supported Network**: Polygon PoS (Chain ID 137), Smart Contract [`0x8b415416f026a168aACD4bd4c8391c194e704D55`](https://polygonscan.com/address/0x8b415416f026a168aACD4bd4c8391c194e704D55).
