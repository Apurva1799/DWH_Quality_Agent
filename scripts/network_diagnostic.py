#!/usr/bin/env python3
"""
Network Diagnostic Tool for LLM Servers

Tests connectivity to all LLM endpoints and provides troubleshooting guidance.
"""

import socket
import subprocess
import sys
import time
from urllib.parse import urlparse

# LLM Server endpoints from configuration
LLM_SERVERS = [
    {"name": "Nemotron 49B", "url": "https://10.7.30.1:8191", "host": "10.7.30.1", "port": 8191, "type": "https"},
    {"name": "Nemotron 253B", "url": "https://10.7.30.1:8190", "host": "10.7.30.1", "port": 8190, "type": "https"},
    {"name": "DeepSeek R1 70B", "url": "https://10.7.110.82:9999", "host": "10.7.110.82", "port": 9999, "type": "https"},
    {"name": "Llama 70B", "url": "https://10.7.30.1:8192", "host": "10.7.30.1", "port": 8192, "type": "https"},
    {"name": "DocumentDB", "url": "https://10.7.1.200:8002", "host": "10.7.1.200", "port": 8002, "type": "https"},
    {"name": "AI Gateway", "url": "https://10.7.30.1:8192", "host": "10.7.30.1", "port": 8192, "type": "https"},
]

def test_tcp_connection(host, port, timeout=5):
    """Test basic TCP connectivity"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        return False

def test_ping(host, timeout=3):
    """Test ICMP ping"""
    try:
        result = subprocess.run(
            ['ping', '-c', '1', '-W', str(timeout), host],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except Exception:
        return False

def get_network_info():
    """Get local network configuration"""
    info = {}
    try:
        # Get hostname
        info['hostname'] = socket.gethostname()
        
        # Get local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        info['local_ip'] = s.getsockname()[0]
        s.close()
        
        # Get default gateway
        result = subprocess.run(['ip', 'route'], capture_output=True, text=True)
        for line in result.stdout.split('\n'):
            if 'default' in line:
                parts = line.split()
                if 'via' in parts:
                    info['gateway'] = parts[parts.index('via') + 1]
                break
        
    except Exception as e:
        info['error'] = str(e)
    
    return info

def check_proxy_settings():
    """Check for proxy environment variables"""
    import os
    proxies = {}
    for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'NO_PROXY', 'no_proxy']:
        value = os.environ.get(key)
        if value:
            proxies[key] = value
    return proxies

def main():
    print("=" * 70)
    print("NETWORK DIAGNOSTIC TOOL - LLM Servers")
    print("=" * 70)
    print()
    
    # Network info
    print("LOCAL NETWORK CONFIGURATION:")
    print("-" * 70)
    net_info = get_network_info()
    for key, value in net_info.items():
        print(f"  {key}: {value}")
    print()
    
    # Proxy settings
    print("PROXY SETTINGS:")
    print("-" * 70)
    proxies = check_proxy_settings()
    if proxies:
        for key, value in proxies.items():
            print(f"  {key}: {value}")
    else:
        print("  No proxy settings detected")
    print()
    
    # Test each server
    print("LLM SERVER CONNECTIVITY TESTS:")
    print("-" * 70)
    
    all_passed = True
    for server in LLM_SERVERS:
        print(f"\n{server['name']}:")
        print(f"  URL: {server['url']}")
        print(f"  Host: {server['host']}")
        print(f"  Port: {server['port']}")
        
        # Test ping
        print(f"  Ping test...", end=" ")
        ping_ok = test_ping(server['host'])
        print("PASS" if ping_ok else "FAIL")
        
        # Test TCP connection
        print(f"  TCP port {server['port']}...", end=" ")
        tcp_ok = test_tcp_connection(server['host'], server['port'])
        print("PASS" if tcp_ok else "FAIL")
        
        if not tcp_ok:
            all_passed = False
            print(f"  Status: UNREACHABLE")
        else:
            print(f"  Status: REACHABLE (TCP)")
    
    print()
    print("=" * 70)
    print("DIAGNOSTIC SUMMARY:")
    print("-" * 70)
    
    if all_passed:
        print("  All LLM servers are reachable!")
        print("  The chatbot should work correctly.")
    else:
        print("  Some LLM servers are unreachable.")
        print()
        print("  Common causes:")
        print("  1. Corporate VPN not connected")
        print("  2. Firewall blocking outbound connections")
        print("  3. Proxy server required but not configured")
        print("  4. Running on external network (not corporate)")
        print()
        print("  Troubleshooting steps:")
        print("  1. Check if you need to connect to corporate VPN")
        print("  2. Verify firewall rules allow access to 10.x.x.x networks")
        print("  3. Configure proxy if required:")
        print("     export HTTPS_PROXY=http://proxy.company.com:8080")
        print("  4. Contact IT to verify network access to LLM servers")
        print("  5. Request whitelisting of your IP for LLM server access")
    
    print()
    print("=" * 70)

if __name__ == "__main__":
    main()
