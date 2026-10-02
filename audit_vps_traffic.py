import json
import urllib.request
import paramiko

CONTRACT_ADDRESS = "0x8b415416f026a168aACD4bd4c8391c194e704D55"
OPERATOR_WALLET = "0x5329dA82E89062D525DAa10F1F4DDba42Ec0F95a"
VPS_HOST = "217.154.51.0"
VPS_USER = "root"
VPS_PASS = "MsB1EzI1nvANR"

def safe_print(s):
    if isinstance(s, bytes):
        s = s.decode("utf-8", errors="replace")
    print(str(s).encode("ascii", errors="replace").decode("ascii"))

def audit():
    safe_print("==================================================================")
    safe_print("        TOLLBOOTH AUDIT: 24-HOUR TRAFFIC & ON-CHAIN REPORT        ")
    safe_print("==================================================================")

    # 1. Fast On-Chain Query
    try:
        payload = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "eth_getBalance",
            "params": [OPERATOR_WALLET, "latest"]
        }).encode()
        req = urllib.request.Request("https://1rpc.io/matic", data=payload, headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode())
            bal_wei = int(data["result"], 16)
            safe_print(f"\n[ON-CHAIN POLYGON MAINNET]")
            safe_print(f"  Operator Wallet: {OPERATOR_WALLET}")
            safe_print(f"  Wallet Balance:  {bal_wei / 10**18:.4f} POL")
            safe_print(f"  Smart Contract:  https://polygonscan.com/address/{CONTRACT_ADDRESS}")
    except Exception as e:
        safe_print(f"\n[ON-CHAIN POLYGON MAINNET] RPC query: {e}")

    # 2. Remote VPS Check
    try:
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect(VPS_HOST, username=VPS_USER, password=VPS_PASS, timeout=6)
        sftp = c.open_sftp()

        # Read tollbooth ledger
        try:
            with sftp.open("/root/agent_tollbooth/toll_ledger.json", "r") as f:
                ledger = json.loads(f.read().decode("utf-8"))
            safe_print(f"\n[VPS TOLLBOOTH LEDGER]")
            safe_print(f"  Total Tolls Accrued:   ${ledger.get('total_toll_collected_usd', 0.0):,.6f} USDC")
            safe_print(f"  Total Paid Calls:      {ledger.get('total_calls_cleared', 0)}")
            safe_print(f"  Total Free Calls:      {ledger.get('total_free_calls_served', 0)}")
            
            txs = ledger.get("transactions", [])
            safe_print(f"  Total Transactions:    {len(txs)}")
            for tx in txs[-5:]:
                safe_print(f"    * [{tx.get('timestamp')}] Agent: {tx.get('agent', '')[:10]}... | Tool: {tx.get('tool')} | Toll: ${tx.get('our_toll_cut_usd', 0.0):.6f}")
        except Exception as e:
            safe_print(f"  Ledger note: {e}")

        # Check Gateway Service Status
        stdin, stdout, _ = c.exec_command("systemctl is-active agent-tollbooth && systemctl is-active agent-reference")
        statuses = stdout.read().decode("utf-8").strip().splitlines()
        safe_print(f"\n[SERVICE UPTIME]")
        safe_print(f"  agent-tollbooth (port 8402):     {statuses[0] if len(statuses) > 0 else 'unknown'}")
        safe_print(f"  agent-reference (port 80 proxy):   {statuses[1] if len(statuses) > 1 else 'unknown'}")

        # Check Recent Activity Logs
        stdin, stdout, _ = c.exec_command("journalctl -u agent-tollbooth --since '24 hours ago' --no-pager")
        logs = stdout.read().decode("utf-8", errors="replace").strip().splitlines()
        safe_print(f"\n[ACTIVITY IN PAST 24 HOURS]: {len(logs)} log entries")
        for line in logs[-15:]:
            safe_print(f"  > {line}")

        c.close()
    except Exception as e:
        safe_print(f"VPS connection error: {e}")

    safe_print("\n==================================================================")
    safe_print("                        AUDIT COMPLETED                           ")
    safe_print("==================================================================")

if __name__ == "__main__":
    audit()
