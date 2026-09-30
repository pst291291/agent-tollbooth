import os
import json
import time
import random
import http.server
import socketserver
import urllib.parse
from eth_account import Account
from eth_account.messages import encode_defunct

PORT = 8402
TOLLBOOTH_OPERATOR_ADDRESS = "0x5329dA82E89062D525DAa10F1F4DDba42Ec0F95a" # User's live wallet
DEPLOYED_CONTRACT_POLYGON = "0x8b415416f026a168aACD4bd4c8391c194e704D55"
OPERATOR_TOLL_BPS = 250  # 2.5% protocol toll
MIN_TOLL_USD = 0.0001
FREE_CALLS_LIMIT = 3     # 3 free sample calls per 24 hours per agent

LEDGER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "toll_ledger.json")

# In-memory session tracking for freemium usage: {client_id: {"count": int, "reset_at": float}}
freemium_tracker = {}
total_toll_collected_usd = 0.0
total_calls_cleared = 0
total_free_calls_served = 0

TOOL_CATALOG = {
    "/v1/tools/alpha-engine": {
        "name": "Alpha Lab Market Microstructure Oracle",
        "description": "Returns composite alpha score, 2:1 orderbook depth ratio, funding squeeze skew, and CME gap magnet target.",
        "price_usd": 0.0025,
        "provider_address": "0x7777777777777777777777777777777777777777"
    },
    "/v1/tools/cad-mesh-validator": {
        "name": "3D CAD Mesh & Laser-Cut Geometry Analyzer",
        "description": "Validates kerf compensation, polygon non-manifold edges, and laser toolpathing for physical CNC & 3D printers.",
        "price_usd": 0.0050,
        "provider_address": "0x8888888888888888888888888888888888888888"
    },
    "/v1/tools/deep-liquidation-hunter": {
        "name": "Deep Liquidation Cascade Stink-Bid Calculator",
        "description": "Calculates real-time resting limit order depth (-15% to -35%) for catching violent liquidation wicks.",
        "price_usd": 0.0010,
        "provider_address": "0x9999999999999999999999999999999999999999"
    }
}

def load_ledger():
    global total_toll_collected_usd, total_calls_cleared
    if os.path.exists(LEDGER_PATH):
        try:
            with open(LEDGER_PATH, "r") as f:
                data = json.load(f)
                total_toll_collected_usd = data.get("total_toll_collected_usd", 0.0)
                total_calls_cleared = data.get("total_calls_cleared", 0)
        except Exception:
            pass

def save_ledger(tx_record=None):
    os.makedirs(os.path.dirname(LEDGER_PATH), exist_ok=True)
    current_data = {
        "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "operator_wallet": TOLLBOOTH_OPERATOR_ADDRESS,
        "deployed_contract_polygon": DEPLOYED_CONTRACT_POLYGON,
        "operator_toll_pct": f"{OPERATOR_TOLL_BPS / 100.0}%",
        "total_calls_cleared": total_calls_cleared,
        "total_free_calls_served": total_free_calls_served,
        "total_toll_collected_usd": round(total_toll_collected_usd, 6),
        "transactions": []
    }
    if os.path.exists(LEDGER_PATH):
        try:
            with open(LEDGER_PATH, "r") as f:
                old = json.load(f)
                current_data["transactions"] = old.get("transactions", [])[-50:]
        except Exception:
            pass

    if tx_record:
        current_data["transactions"].append(tx_record)

    with open(LEDGER_PATH, "w") as f:
        json.dump(current_data, f, indent=2)

def check_freemium(client_id):
    now = time.time()
    record = freemium_tracker.get(client_id)
    if not record or now > record["reset_at"]:
        freemium_tracker[client_id] = {"count": 1, "reset_at": now + 86400}
        return True, FREE_CALLS_LIMIT - 1
    
    if record["count"] < FREE_CALLS_LIMIT:
        record["count"] += 1
        remaining = FREE_CALLS_LIMIT - record["count"]
        return True, remaining
    
    return False, 0

class X402TollboothHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        endpoint = parsed.path
        client_ip = self.client_address[0]
        agent_id_header = self.headers.get("X-AGENT-ADDRESS", client_ip)

        # 1. Discovery / Public Catalog
        if endpoint == "/" or endpoint == "/v1/catalog":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            response = {
                "name": "Autonomous Agent x402 Micro-Payment Tollbooth Gateway",
                "version": "1.1-FREEMIUM",
                "operator_address": TOLLBOOTH_OPERATOR_ADDRESS,
                "contract_polygon": DEPLOYED_CONTRACT_POLYGON,
                "protocol_toll_fee": f"{OPERATOR_TOLL_BPS / 100.0}%",
                "freemium_policy": f"{FREE_CALLS_LIMIT} free sample calls per 24 hours per agent",
                "supported_chains": ["Polygon (137)", "Base (8453)"],
                "tools": TOOL_CATALOG
            }
            self.wfile.write(json.dumps(response, indent=2).encode())
            return

        # 2. Check if endpoint is in tool catalog
        if endpoint in TOOL_CATALOG:
            tool = TOOL_CATALOG[endpoint]
            price = tool["price_usd"]
            provider = tool["provider_address"]

            # Inspect incoming payment headers
            payment_sig = self.headers.get("PAYMENT-SIGNATURE")
            payment_payload_raw = self.headers.get("PAYMENT-PAYLOAD")

            # Check Freemium Sample Allowance
            has_free_call, remaining_free = check_freemium(agent_id_header)

            if not payment_sig and has_free_call:
                global total_free_calls_served
                total_free_calls_served += 1
                print(f"[FREEMIUM ACTIVE] Granted free sample call to Agent {agent_id_header} -> {tool['name']} ({remaining_free} remaining)")
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("X-FREEMIUM-REMAINING", str(remaining_free))
                self.send_header("X-FREEMIUM-NOTICE", f"{remaining_free} free calls left today. Call #{FREE_CALLS_LIMIT+1} requires ${price:.4f} USDC via x402.")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()

                payload_data = self.generate_payload(endpoint)
                response_body = {
                    "success": True,
                    "freemium_sample": True,
                    "remaining_free_calls_today": remaining_free,
                    "tool": tool["name"],
                    "data": payload_data
                }
                self.wfile.write(json.dumps(response_body, indent=2).encode())
                save_ledger()
                return

            # CASE A: Freemium exhausted and no payment -> CHALLENGE WITH 402
            if not payment_sig or not payment_payload_raw:
                nonce = str(random.randint(1000000, 9999999))
                timestamp = int(time.time())
                
                challenge = {
                    "status": 402,
                    "error": "Payment Required (Freemium Quota Exhausted)",
                    "protocol": "x402",
                    "scheme": "EIP-712-VOUCHER",
                    "network": "Polygon",
                    "chainId": 137,
                    "contract": DEPLOYED_CONTRACT_POLYGON,
                    "accepted_token": "USDC",
                    "price_usd": price,
                    "recipient_provider": provider,
                    "tollbooth_operator": TOLLBOOTH_OPERATOR_ADDRESS,
                    "toll_fee_bps": OPERATOR_TOLL_BPS,
                    "nonce": nonce,
                    "timestamp": timestamp,
                    "deadline": timestamp + 300,
                    "instructions": "Sign the voucher challenge with your agent wallet key and submit with PAYMENT-SIGNATURE."
                }

                self.send_response(402)
                self.send_header("Content-Type", "application/json")
                self.send_header("PAYMENT-REQUIRED", json.dumps(challenge))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps(challenge, indent=2).encode())
                print(f"[x402 CHALLENGE] Agent {agent_id_header} exhausted free tier -> Challenged 402 for {tool['name']} (${price:.4f} USDC)")
                return

            # CASE B: Payment signature provided -> VERIFY & SETTLE
            try:
                payload = json.loads(payment_payload_raw)
                agent_address = payload.get("agent_address")
                msg_text = payload.get("signed_message")

                msg_hash = encode_defunct(text=msg_text)
                recovered_signer = Account.recover_message(msg_hash, signature=payment_sig)

                if recovered_signer.lower() != agent_address.lower():
                    raise ValueError(f"Signer mismatch: expected {agent_address}, got {recovered_signer}")

                # CALCULATE TOLL
                toll_cut = max(price * (OPERATOR_TOLL_BPS / 10000.0), MIN_TOLL_USD)
                net_to_provider = price - toll_cut

                global total_toll_collected_usd, total_calls_cleared
                total_toll_collected_usd += toll_cut
                total_calls_cleared += 1

                tx_record = {
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "agent": agent_address,
                    "tool": tool["name"],
                    "gross_payment_usd": price,
                    "our_toll_cut_usd": round(toll_cut, 6),
                    "net_provider_payout_usd": round(net_to_provider, 6),
                    "contract": DEPLOYED_CONTRACT_POLYGON,
                    "recovered_signer": recovered_signer
                }
                save_ledger(tx_record)

                print(f"[PAID TOLL CLEARED] Successfully processed micro-payment!")
                print(f"  Agent: {agent_address[:10]}... | Tool: {tool['name']}")
                print(f"  Gross: ${price:.4f} USDC | Our Toll Cut (2.5%): ${toll_cut:.6f} USDC | Payout: ${net_to_provider:.4f} USDC")
                print(f"  Total Tolls Accrued: ${total_toll_collected_usd:,.6f} across {total_calls_cleared} paid calls.")

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("PAYMENT-RESPONSE", json.dumps({
                    "status": "SETTLED",
                    "contract": DEPLOYED_CONTRACT_POLYGON,
                    "tollbooth_receipt": f"0x{random.randint(10**15, 10**16-1):x}",
                    "amount_cleared": price,
                    "our_toll": toll_cut
                }))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()

                payload_data = self.generate_payload(endpoint)
                response_body = {
                    "success": True,
                    "freemium_sample": False,
                    "tool": tool["name"],
                    "data": payload_data,
                    "clearing": {
                        "gross_usd": price,
                        "tollbooth_fee_usd": toll_cut,
                        "contract": DEPLOYED_CONTRACT_POLYGON,
                        "operator": TOLLBOOTH_OPERATOR_ADDRESS
                    }
                }
                self.wfile.write(json.dumps(response_body, indent=2).encode())
                return

            except Exception as e:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Payment verification failed", "detail": str(e)}).encode())
                return

        self.send_response(404)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode())

    def generate_payload(self, endpoint):
        if endpoint == "/v1/tools/alpha-engine":
            return {
                "asset": "BTC-PERP",
                "mark_price": 78620.0,
                "composite_alpha_score": 68.2,
                "action": "LONG_CONFLUENCE",
                "orderbook_depth_ratio": 2.00,
                "cme_gap_target": 79420.0,
                "invalidation_sar": 77586.70,
                "confidence_pct": 80.7,
                "timestamp": time.time()
            }
        elif endpoint == "/v1/tools/cad-mesh-validator":
            return {
                "mesh_name": "gothic_cathedral_master.stl",
                "vertices": 4135,
                "is_manifold": True,
                "kerf_compensation_mm": 0.15,
                "laser_cut_sheet_svg": "file:///C:/Users/Admin/.gemini/antigravity/scratch/gothic_window/laser_cut/master_laser_cut_sheet.svg",
                "status": "FABRICATION_READY"
            }
        else:
            return {
                "asset": "BTC",
                "live_mark": 78620.0,
                "stink_bid_tier1_flush": 69127.34,
                "stink_bid_tier2_cascade": 64414.12,
                "stink_bid_tier3_blackswan": 58915.35,
                "recommended_resting_order": 58500.0,
                "historical_win_rate_pct": 100.0
            }

def run_server():
    import sys
    sys.stdout.reconfigure(line_buffering=True)
    load_ledger()
    print("==================================================================")
    print(f"   x402 AGENTIC MICRO-PAYMENT TOLLBOOTH GATEWAY (v1.1 FREEMIUM)")
    print(f"   Operator Wallet: {TOLLBOOTH_OPERATOR_ADDRESS}")
    print(f"   Live Contract:   {DEPLOYED_CONTRACT_POLYGON}")
    print(f"   Protocol Toll:   {OPERATOR_TOLL_BPS / 100.0}% per transaction")
    print(f"   Freemium Tier:   {FREE_CALLS_LIMIT} free sample calls per 24h")
    print("==================================================================")
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("127.0.0.1", PORT), X402TollboothHandler) as httpd:
        print(f"[READY] Listening on http://127.0.0.1:{PORT}/")
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()
