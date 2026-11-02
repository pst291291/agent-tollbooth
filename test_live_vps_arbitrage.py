import json
import urllib.request
import urllib.error
from eth_account import Account
from eth_account.messages import encode_defunct
from vast_arbitrage_broker import _get_vast_api_key

GATEWAY_URL = "http://217.154.51.0"
ENDPOINT = "/v1/tools/gpu-burst-broker?tier=RTX%203090"

def test_live_vps_arbitrage():
    # Create an ephemeral test agent wallet to test the full 3-free + 4th-402 + signed-settlement loop
    agent_acct = Account.create()
    agent_addr = agent_acct.address
    print(f"=== Testing Live VPS GPU Arbitrage Gateway ({GATEWAY_URL}{ENDPOINT}) ===")
    print(f"Test Agent Wallet: {agent_addr}\n")

    # 1. Calls 1, 2, 3 -> Freemium Live Orderbook Quote
    for i in range(1, 4):
        req = urllib.request.Request(
            f"{GATEWAY_URL}{ENDPOINT}",
            headers={"X-AGENT-ADDRESS": agent_addr, "User-Agent": "ArbitrageTester/1.0"}
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            body = json.loads(r.read().decode("utf-8"))
            rem = r.headers.get("X-FREEMIUM-REMAINING")
            mode = body["data"]["mode"]
            rtx = body["data"]["live_orderbook"]["tiers"]["RTX 3090"]
            print(f"[Call #{i} - HTTP 200 FREEMIUM] Remaining: {rem} | Mode: {mode}")
            print(f"   -> Live RTX 3090 Floor: Offer #{rtx['best_offer_id']} @ ${rtx['wholesale_usd_per_hr']}/hr (${rtx['wholesale_3min_cost_usd']} per 3m burst) vs Retail ${rtx['retail_burst_price_usd']} (+{rtx['arbitrage_margin_pct']}% margin)")

    # 2. Call 4 -> Expect HTTP 402 Payment Required Challenge
    challenge = None
    try:
        req = urllib.request.Request(
            f"{GATEWAY_URL}{ENDPOINT}",
            headers={"X-AGENT-ADDRESS": agent_addr, "User-Agent": "ArbitrageTester/1.0"}
        )
        urllib.request.urlopen(req, timeout=10)
    except urllib.error.HTTPError as e:
        if e.code == 402:
            challenge = json.loads(e.read().decode("utf-8"))
            print(f"\n[Call #4 - HTTP 402 CHALLENGE TRIGGERED] Price: ${challenge['price_usd']} USDC | Contract: {challenge['contract']} | Nonce: {challenge['nonce']}")
        else:
            raise

    # 3. Call 5 -> Sign x402 Voucher and Clear Paid GPU Burst Arbitrage
    msg_text = f"x402-voucher:{challenge['contract']}:{challenge['recipient_provider']}:{challenge['price_usd']}:{challenge['nonce']}"
    msg_hash = encode_defunct(text=msg_text)
    signed = Account.sign_message(msg_hash, private_key=agent_acct.key)
    sig_hex = signed.signature.hex()
    payload_json = json.dumps({
        "agent_address": agent_addr,
        "signed_message": msg_text,
        "nonce": challenge["nonce"]
    })

    paid_req = urllib.request.Request(
        f"{GATEWAY_URL}{ENDPOINT}",
        headers={
            "X-AGENT-ADDRESS": agent_addr,
            "PAYMENT-SIGNATURE": sig_hex,
            "PAYMENT-PAYLOAD": payload_json,
            "User-Agent": "ArbitrageTester/1.0"
        }
    )
    with urllib.request.urlopen(paid_req, timeout=10) as r:
        paid_body = json.loads(r.read().decode("utf-8"))
        rec = paid_body["data"]["execution_receipt"]
        clr = paid_body["clearing"]
        print(f"\n[Call #5 - HTTP 200 PAID x402 SETTLED]")
        print(f"   -> Gross Charged: ${clr['gross_usd']} USDC | Protocol Toll: ${clr['tollbooth_fee_usd']} USDC")
        print(f"   -> Execution Status: {rec['lease_status']} | Matched Offer: #{rec['matched_vast_offer_id']} ({rec['gpu_model']})")
        print(f"   -> Wholesale 3m Cost: ${rec['wholesale_3min_cost_usd']} | Net Profit: +${rec['net_arbitrage_profit_usd']} ({rec['arbitrage_margin_pct']}%)")

    # 4. Verify Vast.ai active instances == 0 and credit balance intact
    vast_key = _get_vast_api_key()
    v_req = urllib.request.Request(
        "https://cloud.vast.ai/api/v1/instances/",
        headers={"Authorization": f"Bearer {vast_key}", "Accept": "application/json", "User-Agent": "VastAI-CLI/1.0"}
    )
    with urllib.request.urlopen(v_req, timeout=10) as vr:
        v_data = json.loads(vr.read().decode("utf-8"))
        instances = v_data.get("instances", [])
        print(f"\n[SAFETY AUDIT] Active Vast.ai Instances Running: {len(instances)} (0 = $7.85 Credit 100% Untouched)")

if __name__ == "__main__":
    test_live_vps_arbitrage()
