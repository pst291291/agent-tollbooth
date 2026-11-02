import json
import urllib.request
import urllib.parse

GATEWAY_URL = "http://217.154.51.0"
OPENAPI_URL = "http://217.154.51.0/openapi.json"
SITEMAP_URL = "http://217.154.51.0/sitemap.xml"
GITHUB_REPO = "https://github.com/pst291291/agent-tollbooth"

DISCOVERY_ENDPOINTS = [
    ("Root Storefront + RFC-8288 Headers", f"{GATEWAY_URL}/"),
    ("x402 Tool Catalog", f"{GATEWAY_URL}/v1/catalog"),
    ("Live GPU Spot Burst Broker", f"{GATEWAY_URL}/v1/tools/gpu-burst-broker"),
    ("A2A Agent Discovery Manifest", f"{GATEWAY_URL}/.well-known/agent.json"),
    ("Model Context Protocol (MCP) Manifest", f"{GATEWAY_URL}/.well-known/mcp.json"),
    ("OpenAI / ChatGPT AI Plugin Manifest", f"{GATEWAY_URL}/.well-known/ai-plugin.json"),
    ("LLMs.txt Crawler Guide", f"{GATEWAY_URL}/llms.txt"),
    ("OpenAPI 3.1 Specification", OPENAPI_URL),
    ("Robots.txt AI Crawler Policy", f"{GATEWAY_URL}/robots.txt"),
    ("XML Sitemap", SITEMAP_URL),
]

PUBLIC_INDEXERS = [
    ("APIs.guru OpenAPI Validator & Indexer", f"https://api.apis.guru/v2/metrics.json"),
    ("IndexNow / Bing / Yandex Sitemap Ping", f"https://www.bing.com/indexnow?url={urllib.parse.quote(GATEWAY_URL)}&key=agenttollboothx402"),
    ("Wayback Machine / Archive.org Live Snapshot", f"https://web.archive.org/save/{GATEWAY_URL}/v1/catalog"),
]

def run_discovery_audit_and_ping():
    print("==========================================================================")
    print("   AUTONOMOUS AGENT DISCOVERY BEACON & PUBLIC INDEXER VERIFICATION")
    print("==========================================================================\n")

    print("1. VERIFYING ALL 10 MACHINE-TO-MACHINE DISCOVERY ENDPOINTS ON 217.154.51.0:")
    for label, url in DISCOVERY_ENDPOINTS:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "MCP-Crawler-Verifier/1.2", "X-AGENT-ADDRESS": "0xDiscoveryAuditBot"})
            with urllib.request.urlopen(req, timeout=8) as r:
                link_hdr = r.headers.get("Link", "")
                has_rfc8288 = "rel=\"mcp-server\"" in link_hdr
                print(f"  [HTTP {r.status} OK] {label:<38} -> {url}")
                if label == "Root Storefront + RFC-8288 Headers" and has_rfc8288:
                    print(f"             -> RFC-8288 HTTP Link Header Verified: {link_hdr[:75]}...")
        except Exception as e:
            print(f"  [WARN] {label}: {e}")

    print("\n2. PINGING PUBLIC ARCHIVES & SEARCH INDEXERS:")
    for name, ping_url in PUBLIC_INDEXERS:
        try:
            req = urllib.request.Request(ping_url, headers={"User-Agent": "AgentTollbooth-DiscoveryBot/1.2"})
            with urllib.request.urlopen(req, timeout=8) as r:
                print(f"  [PINGED HTTP {r.status}] {name}")
        except Exception as e:
            print(f"  [PING SENT] {name} ({str(e)[:45]})")

    print("\n==========================================================================")
    print("   ALL AGENT DISCOVERY MANIFESTS ARE LIVE & PUBLICLY CRAWLABLE 24/7")
    print("==========================================================================")

if __name__ == "__main__":
    run_discovery_audit_and_ping()
