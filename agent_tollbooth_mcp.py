#!/usr/bin/env python3
"""
Model Context Protocol (MCP) Server for the Agent Tollbooth Gateway.
Enables Claude Desktop, Cursor, Windsurf, and autonomous agent swarms to seamlessly
discover and invoke our proprietary financial oracle and CAD fabrication tools.
"""

import os
import sys
import json
import urllib.request
import urllib.error

# Connects directly to the live VPS gateway, or local instance if offline
GATEWAY_URL = os.environ.get("TOLLBOOTH_GATEWAY_URL", "http://217.154.51.0")

TOOLS_SCHEMA = [
    {
        "name": "get_market_microstructure_alpha",
        "description": "Returns institutional market microstructure metrics for crypto assets: 2:1 orderbook depth absorption, derivatives funding rate squeeze skew, and unfilled CME weekend gap magnet targets.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "asset": {
                    "type": "string",
                    "description": "Trading pair asset symbol, e.g. 'BTC' or 'ETH'",
                    "default": "BTC"
                }
            },
            "required": ["asset"]
        }
    },
    {
        "name": "get_stink_bid_cascade_levels",
        "description": "Calculates high-convexity resting limit order depths ('stink bids') sitting below market liquidation clusters (-15% to -35%) to capture violent flash-crash V-reversals.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "asset": {
                    "type": "string",
                    "description": "Asset to calculate cascade levels for (BTC, ETH, SOL)",
                    "default": "BTC"
                }
            },
            "required": ["asset"]
        }
    },
    {
        "name": "validate_cad_laser_mesh",
        "description": "Validates 3D CAD mesh files (STL/OBJ) and 2D vector laser sheets (SVG) for watertight manifold edges, kerf beam offset compensation (0.15mm), and laser toolpath cutting parameters.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "mesh_name": {
                    "type": "string",
                    "description": "Name or path of the 3D model or laser sheet",
                    "default": "gothic_cathedral_master.stl"
                }
            },
            "required": ["mesh_name"]
        }
    }
]

def call_gateway(path):
    url = f"{GATEWAY_URL}{path}"
    req = urllib.request.Request(url, headers={"User-Agent": "MCP-Agent-Connector/1.1"})
    try:
        with urllib.request.urlopen(req, timeout=5) as res:
            return json.loads(res.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 402:
            challenge = json.loads(e.headers.get("PAYMENT-REQUIRED", "{}"))
            return {
                "error": "Payment Required (x402)",
                "price_usd": challenge.get("price_usd"),
                "instructions": challenge.get("instructions"),
                "tollbooth_contract": challenge.get("contract")
            }
        return {"error": f"HTTP {e.code}: {e.reason}"}
    except Exception as ex:
        return {"error": str(ex)}

def handle_rpc_request(req):
    req_id = req.get("id")
    method = req.get("method")
    params = req.get("params", {})

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": TOOLS_SCHEMA
            }
        }
    
    elif method == "tools/call":
        name = params.get("name")
        args = params.get("arguments", {})

        if name == "get_market_microstructure_alpha":
            data = call_gateway("/v1/tools/alpha-engine")
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {"type": "text", "text": json.dumps(data, indent=2)}
                    ]
                }
            }
        elif name == "get_stink_bid_cascade_levels":
            data = call_gateway("/v1/tools/deep-liquidation-hunter")
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {"type": "text", "text": json.dumps(data, indent=2)}
                    ]
                }
            }
        elif name == "validate_cad_laser_mesh":
            data = call_gateway("/v1/tools/cad-mesh-validator")
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {"type": "text", "text": json.dumps(data, indent=2)}
                    ]
                }
            }
        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Method {name} not found"}
            }

    elif method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "agent-tollbooth-mcp",
                    "version": "1.1.0"
                }
            }
        }

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"Unknown method {method}"}
    }

def run_mcp_server():
    sys.stdout.reconfigure(line_buffering=True)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            res = handle_rpc_request(req)
            sys.stdout.write(json.dumps(res) + "\n")
            sys.stdout.flush()
        except Exception as e:
            sys.stderr.write(f"Error handling MCP request: {e}\n")

if __name__ == "__main__":
    run_mcp_server()
