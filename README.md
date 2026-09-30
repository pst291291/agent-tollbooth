# ⚡ Agent Tollbooth: Autonomous x402 Micro-Payment Gateway & MCP Tools

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Polygon Mainnet](https://img.shields.io/badge/Polygon-0x8b41...4D55-blueviolet)](https://polygonscan.com/address/0x8b415416f026a168aACD4bd4c8391c194e704D55)
[![x402 Protocol](https://img.shields.io/badge/Protocol-x402_HTTP_402-green)](http://217.154.51.0/v1/catalog)
[![MCP Compliant](https://img.shields.io/badge/MCP-JSON--RPC_2.0-orange)](http://217.154.51.0/.well-known/mcp.json)

An open-source, production-ready micro-payment tollbooth and Model Context Protocol (MCP) server designed for the emerging autonomous machine-to-machine (A2A) economy. 

Enables AI agent swarms (Claude, AutoGPT, CrewAI, LangChain, Cursor) to discover, test, and pay for high-value financial market oracles and physical CAD fabrication tools using gasless off-chain EIP-712 payment vouchers with Polygon on-chain settlement.

---

## 🎯 Features

1. **3-Call Freemium Conversion Hook**: Every agent gets 3 free queries every 24 hours to inspect sample data before hitting the paywall.
2. **RFC-7231 x402 Protocol**: Intercepts queries when quotas expire and returns HTTP 402 with structured cryptographic payment challenge headers.
3. **Polygon Smart Contract Settlement**: Immutable fee-split logic deployed live on Polygon Mainnet ([`0x8b415416f026a168aACD4bd4c8391c194e704D55`](https://polygonscan.com/address/0x8b415416f026a168aACD4bd4c8391c194e704D55)).
4. **Native MCP Server**: Ready to drop into Claude Desktop, Cursor, and Windsurf.

---

## 🛠 Available Tools

| Tool Endpoint | Tool Name | Price (USDC) | Purpose |
| :--- | :--- | :--- | :--- |
| `/v1/tools/alpha-engine` | **Alpha Lab Microstructure Oracle** | $0.0025 | Composite score, 2:1 orderbook depth ratio, funding rate skew, CME gap target |
| `/v1/tools/cad-mesh-validator` | **CAD Mesh & Laser Geometry Validator** | $0.0050 | Non-manifold edges, kerf beam offset compensation, CNC/laser cutting parameters |
| `/v1/tools/deep-liquidation-hunter` | **Deep Liquidation Stink-Bid Levels** | $0.0010 | Extreme limit-order cascades (-15% to -35%) to catch liquidation wicks |

---

## 🚀 Quickstart

### 1. Direct HTTP Calling (Autonomous Agent)
```python
import urllib.request
import json

req = urllib.request.Request("http://217.154.51.0/v1/tools/alpha-engine", headers={
    "User-Agent": "AutonomousAgent/1.0",
    "X-AGENT-ADDRESS": "0xYourAgentWalletAddress"
})

with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode())
    print("Received Oracle Data:", data)
```

### 2. Using with Claude Desktop (MCP)
Add this to your `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "agent-tollbooth": {
      "command": "python",
      "args": ["path/to/agent_tollbooth_mcp.py"],
      "env": {
        "TOLLBOOTH_GATEWAY_URL": "http://217.154.51.0"
      }
    }
  }
}
```

---

## 🔗 Discovery & Standards Compliance
- **Catalog**: `http://217.154.51.0/v1/catalog`
- **Agent Discovery**: `http://217.154.51.0/.well-known/agent.json`
- **MCP Manifest**: `http://217.154.51.0/.well-known/mcp.json`
- **LLM Context**: `http://217.154.51.0/llms.txt`
- **OpenAPI 3.1 Spec**: `http://217.154.51.0/openapi.json`

---

## 📜 On-Chain Verification
- **Network**: Polygon PoS (Chain ID: 137)
- **Contract**: [`0x8b415416f026a168aACD4bd4c8391c194e704D55`](https://polygonscan.com/address/0x8b415416f026a168aACD4bd4c8391c194e704D55)
- **Deployment Block**: #94729837
- **Operator Royalty Cut**: 2.5% (250 BPS)
- **License**: MIT
