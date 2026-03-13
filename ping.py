import subprocess
import platform
import argparse
import re
import socket
import urllib.request
from urllib.error import URLError, HTTPError
import shlex

def ping(host: str, count: int = 1, timeout: int = 5) -> tuple[bool, str]:
    param = "-n" if platform.system().lower() == "windows" else "-c"
    cmd = ["ping", param, str(count), host]
    try:
        completed = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
        )
        online = completed.returncode == 0
        return online, completed.stdout or completed.stderr
    except Exception as exc:
        return False, str(exc)

def extract_time(output: str) -> str | None:
    match = re.search(r"time[=<]\s*<?\d+\.?\d*\s*ms", output, re.IGNORECASE)
    return match.group() if match else None

def check_http(host: str, timeout: int = 5) -> bool:
    url = host if host.startswith("http") else f"https://{host}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}
    try:
        req = urllib.request.Request(url, method="HEAD", headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return 200 <= resp.status < 400
    except HTTPError as e:
        return e.code in [200, 301, 302, 403]
    except URLError:
        return False

def check_tcp(host: str, port: int, timeout: int = 5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False

def run_checks(host: str, args: argparse.Namespace):
    """Encapsulated logic to check a single host based on arguments."""
    print(f"\n--- Checking: {host} ---")
    
    # TCP/Service Check
    if args.port or args.service:
        try:
            port = args.port or socket.getservbyname(args.service)
            print(f"Checking TCP {host}:{port}...")
            if check_tcp(host, port):
                print(f"SUCCESS: {host}:{port} is reachable.")
            else:
                print(f"FAILED: {host}:{port} is unreachable.")
        except OSError as exc:
            print(f"ERROR: Unknown service '{args.service}': {exc}")
        return

    # Default Ping/HTTP logic
    online, output = ping(host)
    if online:
        time_str = extract_time(output) or "(could not parse response time)"
        print(f"ONLINE: {host} responded to ICMP. {time_str}")
    else:
        print(f"OFFLINE: {host} did not respond to ping.")
        if args.http:
            if check_http(host):
                print(f"RECOVERED: {host} is reachable via HTTP.")
            else:
                print(f"FAILED: {host} is unreachable via HTTP.")

def main() -> None:
    # We define the parser inside or outside, but we must parse inside the loop
    parser = argparse.ArgumentParser(description="Check host reachability.", exit_on_error=False)
    parser.add_argument("hosts", nargs="*", help="One or more hosts/IPs to check")
    parser.add_argument("--http", action="store_true", help="Try HTTP if ping fails")
    parser.add_argument("--port", type=int, help="TCP port check")
    parser.add_argument("--service", help="Service name check (e.g. ssh)")

    print("Network Checker Started. Type 'exit' or 'quit' to close.")

    while True:
        try:
            user_input = input("\n> Enter host(s) and flags (): ").strip()
            
            if user_input.lower() in ['exit', 'quit']:
                break
            if not user_input:
                continue

            # shlex.split allows us to handle flags like --http correctly from a string
            input_args = shlex.split(user_input)
            
            # parse_known_args is safer here in case of typos
            args, unknown = parser.parse_known_args(input_args)
            
            if unknown:
                print(f"Warning: Unrecognized arguments: {unknown}")

            if not args.hosts:
                print("Error: No host specified.")
                continue

            # Execute checks for each host provided in this loop iteration
            for host in args.hosts:
                run_checks(host, args)

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    input("Exiting")