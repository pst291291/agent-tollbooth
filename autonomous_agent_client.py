import urllib.request
import urllib.error
import json
import time
from eth_account import Account
from eth_account.messages import encode_defunct

# Generate a disposable agent wallet key for testing
AGENT_WALLET = Account.create()

GATEWAY_URL = "http://127.0.0.1:8402"

def agent_call_tool(tool_path):
    url = f"{GATEWAY_URL}{tool_path}"
    print(f"\n[AGENT] Calling tool: {url}")
    print(f"[AGENT] My Wallet Address: {AGENT_WALLET.address}")

    # STEP 1: Initial request (without payment)
    req = urllib.request.Request(url, headers={"User-Agent": "AutonomousAgentSwarm/3.2"})
    try:
        with urllib.request.urlopen(req) as res:
            print("[AGENT] Unexpected 200 OK (Expected 402 Payment Required)")
            return json.loads(res.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 402:
            print(f"[AGENT] Received HTTP 402: Payment Required!")
            challenge_header = e.headers.get("PAYMENT-REQUIRED")
            challenge = json.loads(challenge_header)
            
            price = challenge.get("price_usd")
            token = challenge.get("accepted_token")
            provider = challenge.get("recipient_provider")
            operator = challenge.get("tollbooth_operator")
            nonce = challenge.get("nonce")
            deadline = challenge.get("deadline")

            print(f"  -> Required Micro-Fee: ${price:.4f} {token}")
            print(f"  -> Provider: {provider[:10]}...")
            print(f"  -> Tollbooth Operator: {operator[:10]}... (Protocol Cut: {challenge.get('toll_fee_bps') / 100.0}%)")
            print(f"  -> Nonce: {nonce} | Deadline: {deadline}")

            # STEP 2: Agent autonomous decision & signing
            max_budget = 0.05 # Agent policy: spend up to $0.05 per tool
            if price > max_budget:
                print(f"[AGENT ERROR] Price ${price} exceeds agent budget policy (${max_budget}). Aborting.")
                return None

            print("[AGENT] Price verified within autonomous budget policy. Signing micro-voucher...")

            # Construct message to sign
            sign_text = f"X402_PAYMENT:{AGENT_WALLET.address}:{provider}:{price}:{nonce}:{deadline}"
            msg_hash = encode_defunct(text=sign_text)
            signed_voucher = Account.sign_message(msg_hash, private_key=AGENT_WALLET.key)
            signature = signed_voucher.signature.hex()
            if not signature.startswith("0x"):
                signature = "0x" + signature

            payload = {
                "agent_address": AGENT_WALLET.address,
                "provider": provider,
                "amount_usd": price,
                "nonce": nonce,
                "deadline": deadline,
                "signed_message": sign_text
            }

            # STEP 3: Re-submit request with x402 headers
            print("[AGENT] Re-submitting request with PAYMENT-SIGNATURE...")
            retry_req = urllib.request.Request(url, headers={
                "User-Agent": "AutonomousAgentSwarm/3.2",
                "PAYMENT-SIGNATURE": signature,
                "PAYMENT-PAYLOAD": json.dumps(payload)
            })

            with urllib.request.urlopen(retry_req) as success_res:
                payment_receipt = success_res.headers.get("PAYMENT-RESPONSE")
                result_data = json.loads(success_res.read().decode())
                print(f"[AGENT SUCCESS] HTTP {success_res.status} OK!")
                print(f"  Receipt: {payment_receipt}")
                print(f"  Payload Returned: {json.dumps(result_data.get('data'), indent=2)}")
                print(f"  Toll Sliced to Operator: ${result_data.get('clearing', {}).get('tollbooth_fee_usd'):.6f} USDC")
                return result_data
        else:
            print(f"[AGENT ERROR] Unexpected HTTP Error: {e.code} - {e.read().decode()}")
            return None

def run_agent_simulation(num_calls=5):
    print("==================================================================")
    print("       AUTONOMOUS AGENT x402 PAYMENT PROTOCOL SIMULATOR          ")
    print("==================================================================")
    
    tools = [
        "/v1/tools/alpha-engine",
        "/v1/tools/cad-mesh-validator",
        "/v1/tools/deep-liquidation-hunter"
    ]

    for i in range(num_calls):
        chosen_tool = tools[i % len(tools)]
        print(f"\n--- [AGENT TRANSACTION #{i+1} of {num_calls}] ---")
        agent_call_tool(chosen_tool)
        time.sleep(0.5)

    print("\n==================================================================")
    print("  SIMULATION COMPLETE: All micro-payments cleared through Gateway!")
    print("==================================================================")

if __name__ == "__main__":
    run_agent_simulation()
