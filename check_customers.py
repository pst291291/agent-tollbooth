import json
import urllib.request
import paramiko
from web3 import Web3

CONTRACT_ADDRESS = "0x8b415416f026a168aACD4bd4c8391c194e704D55"
OPERATOR_WALLET = "0x5329dA82E89062D525DAa10F1F4DDba42Ec0F95a"
VPS_HOST = "217.154.51.0"
VPS_USER = "root"
VPS_PASS = "MsB1EzI1nvANR"
POLYGON_RPC = "https://polygon-bor-rpc.publicnode.com"

def check_traffic():
    print("==================================================================")
    print("        TOLLBOOTH DAILY CHECK-IN: AUDITING CUSTOMER TRAFFIC       ")
    print("==================================================================")

    # 1. Check On-Chain Polygon State
    try:
        w3 = Web3(Web3.HTTPProvider(POLYGON_RPC))
        bal_wei = w3.eth.get_balance(OPERATOR_WALLET)
        bal_pol = w3.from_wei(bal_wei, "ether")
        print(f"\n[ON-CHAIN POLYGON STATUS]")
        print(f"  Operator Wallet: {OPERATOR_WALLET}")
        print(f"  Wallet Balance:  {bal_pol:.4f} POL")
        print(f"  Contract:        https://polygonscan.com/address/{CONTRACT_ADDRESS}")
    except Exception as e:
        print(f"  [On-Chain Error]: {e}")

    # 2. Check Remote VPS Ledger & Activity
    try:
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect(VPS_HOST, username=VPS_USER, password=VPS_PASS, timeout=10)
        sftp = c.open_sftp()
        
        # Read toll_ledger.json
        try:
            with sftp.open("/root/agent_tollbooth/toll_ledger.json", "r") as f:
                ledger = json.loads(f.read().decode("utf-8"))
            
            print(f"\n[VPS GATEWAY TRAFFIC REPORT]")
            print(f"  Total Tolls Accrued:   ${ledger.get('total_toll_collected_usd', 0.0):,.6f} USDC")
            print(f"  Paid Calls Cleared:    {ledger.get('total_calls_cleared', 0)}")
            print(f"  Free Calls Served:     {ledger.get('total_free_calls_served', 0)}")
            
            txs = ledger.get("transactions", [])
            print(f"  Transactions Recorded: {len(txs)}")
            if txs:
                print("\n  --- Recent Customer Transactions ---")
                for tx in txs[-10:]:
                    print(f"  * [{tx.get('timestamp')}] Agent: {tx.get('agent')[:10]}... | Tool: {tx.get('tool')} | Toll: ${tx.get('our_toll_cut_usd', 0.0):.6f}")
            else:
                print("  (No paid customer transactions recorded yet)")
        except FileNotFoundError:
            print("\n[VPS GATEWAY]: Ledger file initializing...")

        # Read interaction logs from agent-reference
        stdin, stdout, _ = c.exec_command("tail -n 15 /opt/agent-reference/data/interactions.jsonl 2>/dev/null")
        lines = stdout.read().decode("utf-8", errors="replace").strip().splitlines()
        print(f"\n[RECENT AGENT QUERIES ON PORT 80]: {len(lines)} recent hits")
        for line in lines[-5:]:
            print(f"  > {line}")

        c.close()
    except Exception as e:
        print(f"  [VPS Query Error]: {e}")

    print("\n==================================================================")
    print("      AUDIT COMPLETE: All systems standing guard 24/7/365.       ")
    print("==================================================================")

if __name__ == "__main__":
    check_traffic()
