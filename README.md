# ⚡ Cloud GPU Rental & Parametric CAD MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![MCP Standard](https://img.shields.io/badge/MCP-JSON--RPC_2.0-orange)](https://modelcontextprotocol.io)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)

A production-ready **Model Context Protocol (MCP)** server providing direct local tool execution for Claude Desktop, Cursor, Windsurf, and autonomous AI swarms:

1. **Autonomous Cloud GPU Spot Arbitrage (`rent_gpu_burst_arbitrage`)**: Scans real-time wholesale spot floors (RTX 3090, RTX 4090, A100, H100) and executes on-demand compute bursts with automatic 180-second idle deadman destruction protection.
2. **Parametric 3D CAD & Laser-Cut Compiler (`compile_parametric_cad_stl_svg`)**: Compiles watertight binary 3D `.STL` stepped flush-face structural joinery and kerf-compensated `.SVG` laser cut sheets on the fly across any pair of mismatched material thicknesses.
3. **24/7 Polymarket & Stink-Bid Intelligence (`get_polymarket_and_stinkbid_radar`)**: Scans Polymarket orderbooks for YES+NO pricing anomalies and calculates resting flash-crash limit order tiers (-12% to -25%).
4. **Market Microstructure & CAD Validation Oracles**: Provides orderbook depth ratios, funding skew, and watertight 3D mesh verification.

---

## 📦 Installation & Setup

### Option 1: Direct Python Execution (Claude Desktop & Cursor)

Clone the repository:
```bash
git clone https://github.com/pst291291/agent-tollbooth.git
cd agent-tollbooth
pip install -e .
```

### Option 2: Claude Desktop Configuration

Add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "gpu-rental-mcp": {
      "command": "python",
      "args": ["-m", "agent_tollbooth_mcp"],
      "env": {
        "VAST_API_KEY": "optional_your_vast_key"
      }
    }
  }
}
```

### Option 3: Cursor / Windsurf Configuration

In Cursor Settings -> Features -> MCP Servers -> Add New MCP Server:
- **Name**: `gpu-rental-mcp`
- **Type**: `command`
- **Command**: `python -m agent_tollbooth_mcp`

---

## 🛠 Available MCP Tools

| Tool Name | Parameters | What It Does |
| :--- | :--- | :--- |
| `rent_gpu_burst_arbitrage` | `tier` (e.g. `'RTX 3090'`, `'RTX 4090'`, `'A100'`, `'H100'`) | Queries live wholesale spot orderbooks and provisions 3-minute compute bursts with 180s auto-destroy protection. |
| `compile_parametric_cad_stl_svg` | `board_a_mm`, `board_b_mm`, `kerf_mm` | Compiles watertight binary 3D `.STL` stepped joint models and kerf-compensated `.SVG` laser cut sheets. |
| `get_polymarket_and_stinkbid_radar` | *none* | Streams real-time Polymarket orderbook anomalies and crypto flash-crash cascade stink-bid levels. |
| `get_market_microstructure_alpha` | `asset` (`'BTC'`, `'ETH'`) | Returns 2:1 depth absorption ratios, funding rate skew, and CME gap targets. |
| `get_stink_bid_cascade_levels` | `asset` (`'BTC'`, `'ETH'`, `'SOL'`) | Calculates high-convexity resting limit order depths (-12% to -25%). |
| `validate_cad_laser_mesh` | `mesh_name` | Validates manifold edges, kerf beam offset compensation, and CNC cutting parameters. |

---

## 🏗 Repository Structure & Source Code

* **`agent_tollbooth_mcp.py`**: Core Model Context Protocol (MCP) server handling stdio JSON-RPC 2.0 communication (`tools/list` and `tools/call`).
* **`vast_arbitrage_broker.py`**: Pure Python connector interfacing wholesale cloud GPU providers, warm-pool reuse, and background deadman thread monitors.
* **`pyproject.toml`**: Standard Python packaging specification and entry point configuration.
* **`AgentTollbooth.sol`**: (Optional) Smart contract deployed on Polygon Mainnet (`0x8b415416f026a168aACD4bd4c8391c194e704D55`) for on-chain EIP-712 micro-settlements.
* **`x402_gateway.py`**: (Optional) Hosted HTTP tollbooth gateway proxying HTTP 402 challenges to external agent swarms.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
