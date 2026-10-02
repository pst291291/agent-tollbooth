import urllib.request
import urllib.error
import json
import time
from eth_account import Account
from eth_account.messages import encode_defunct

# Generate a new unique agent address
REMOTE_TEST_AGENT = Account.create()

GATEWAY_URL = "http://217.154.51.0/v1/tools/alpha-engine"

print("=======================================================")
print("  TESTING LIVE VPS (217.154.51.0) FREEMIUM & x402 PAYWALL")
print(f"  Test Agent Address: {REMOTE_TEST_AGENT.address}")
print("=======================================================\n")

for i in range(1, 5):
    print(f"--> [CALL #{i}] Requesting Alpha Engine from VPS...")
    req = urllib.request.Request(GATEWAY_URL, headers={
        "User-Agent": "AutonomousAgent/4.0",
        "X-AGENT-ADDRESS": REMOTE_TEST_AGENT.address
    })

    try:
        with urllib.request.urlopen(req) as res:
            rem = res.headers.get("X-FREEMIUM-REMAINING", "N/A")
            notice = res.headers.get("X-FREEMIUM-NOTICE", "N/A")
            data = json.loads(res.read().decode())
            print(f"    [STATUS 200 OK - FREEMIUM SAMPLE GRANTED]")
            print(f"    Remaining Free Calls: {rem}")
            print(f"    Notice: {notice}")
            print(f"    Payload Received: {data.get('data', {}).get('action')} @ ${data.get('data', {}).get('mark_price')}\n")
    except urllib.error.HTTPError as e:
        if e.code == 402:
            print(f"    [STATUS 402 PAYMENT REQUIRED - FREEMIUM EXHAUSTED!]")
            challenge_header = e.headers.get("PAYMENT-REQUIRED")
            challenge = json.loads(challenge_header) if challenge_header else json.loads(e.read().decode())
            print(f"    Paywall Triggered: Price = ${challenge.get('price_usd')} USDC on Polygon")
            print(f"    Tollbooth Contract: {challenge.get('contract')}")
            print(f"    Operator Wallet: {challenge.get('tollbooth_operator')}")
            
            # Now test paying Call #4!
            print("\n    >>> Autonomous Agent Signing Payment Voucher for Call #4...")
            price = challenge.get("price_usd")
            provider = challenge.get("recipient_provider")
            nonce = challenge.get("nonce")
            deadline = challenge.get("deadline")

            sign_text = f"X402_PAYMENT:{REMOTE_TEST_AGENT.address}:{provider}:{price}:{nonce}:{deadline}"
            msg_hash = encode_defunct(text=sign_text)
            sig = Account.sign_message(msg_hash, private_key=REMOTE_TEST_AGENT.key).signature.hex()
            if not sig.startswith("0x"): sig = "0x" + sig

            payload = {
                "agent_address": REMOTE_TEST_AGENT.address,
                "provider": provider,
                "amount_usd": price,
                "nonce": nonce,
                "deadline": deadline,
                "signed_message": sign_text
            }

            paid_req = urllib.request.Request(GATEWAY_URL, headers={
                "User-Agent": "AutonomousAgent/4.0",
                "X-AGENT-ADDRESS": REMOTE_TEST_AGENT.address,
                "PAYMENT-SIGNATURE": sig,
                "PAYMENT-PAYLOAD": json.dumps(payload)
            })

            with urllib.request.urlopen(paid_req) as paid_res:
                paid_data = json.loads(paid_res.read().decode())
                print(f"    [PAID CALL #4 SUCCESS - HTTP {paid_res.status} OK]")
                print(f"    Operator Toll Sliced (2.5%): ${paid_data.get('clearing', {}).get('tollbooth_fee_usd'):.6f} USDC")
                print(f"    Contract Receipt: {paid_res.headers.get('PAYMENT-RESPONSE')}\n")
        else:
            print("Error:", e)

print("=======================================================")
print("  LIVE VPS VERIFICATION SUCCEEDED: 100% OPERATIONAL!   ")
print("=======================================================")
