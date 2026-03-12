import subprocess
import platform
import argparse


def ping(host: str, count: int = 1, timeout: int = 5) -> tuple[bool, str]:
    """Ping a host and return a tuple (online, output).

    Parameters
    ----------
    host: str
        The hostname or IP address to ping.
    count: int
        Number of echo requests to send (default 1).
    timeout: int
        Timeout in seconds for the ping command.

    Returns
    -------
    (bool, str)
        ``True`` if the host responded successfully, ``False`` otherwise.
        The second element is the raw output from the ping command or an
        error message.
    """

    # ``ping`` command options vary between platforms.
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
    except Exception as exc:  # includes subprocess.TimeoutExpired
        return False, str(exc)

    online = completed.returncode == 0
    return online, completed.stdout or completed.stderr


def main() -> None:
    """Entry point for the command line application.

    The user may combine different checks via command-line flags.  By
    default the program attempts an ICMP ping followed by an optional HTTP
    HEAD when ping fails.  A TCP/connect check can be requested explicitly
    using ``--port`` or ``--service``; in that mode the ping/HTTP logic is
    skipped.
    """

    parser = argparse.ArgumentParser(
        description="Check whether a website or host is reachable via ping, HTTP, or TCP."
    )
    parser.add_argument(
        "host",
        nargs="?",
        help="Website (domain) or IP address to check",
    )
    parser.add_argument(
        "--http",
        action="store_true",
        help="If ping fails, try an HTTP HEAD request to the host",
    )
    parser.add_argument(
        "--port",
        type=int,
        help="Attempt a raw TCP connection to this port",
    )
    parser.add_argument(
        "--service",
        help="Equivalent to --port but uses /etc/services (e.g. ssh, smtp)",
    )

    args = parser.parse_args()
    host = args.host or input("Enter host to check: ")

    # handle TCP/service check first if requested
    if args.port or args.service:
        import socket

        try:
            port = args.port or socket.getservbyname(args.service)
        except OSError as exc:
            print(f"Unknown service '{args.service}': {exc}")
            return

        print(f"checking TCP {host}:{port}...")
        if check_tcp(host, port):
            print(f"{host}:{port} is reachable via TCP.")
        else:
            print(f"{host}:{port} is not reachable via TCP.")
        return

    # default behavior: ping first
    online, output = ping(host)

    if online:
        print(f"{host} is online via ICMP ping.")
        time_str = extract_time(output)
        if time_str:
            print(f"Response {time_str}")
        else:
            print("(could not parse response time)")
    else:
        print(f"{host} did not respond to ping.")
        if args.http:
            ok = check_http(host)
            if ok:
                print(f"{host} appears to be online (HTTP succeeded).")
            else:
                print(f"HTTP check failed; {host} may be down.")

    # if you need full details you can uncomment the next line
    # print(output)


# helpers
import re
import urllib.request
from urllib.error import URLError, HTTPError

def extract_time(output: str) -> str | None:
    """Try to find the first "time" value in *ping* output.

    Returns the matched substring including units (e.g. ``"time=23ms"`` or
    ``"time<1ms"``) or ``None`` if nothing recognizable is present.
    """

    # common ping formats on Windows and Unix variants
    match = re.search(r"time[=<]\s*<?\d+\.?\d*\s*ms", output, re.IGNORECASE)
    return match.group() if match else None


def check_http(host: str, timeout: int = 5) -> bool:
    url = host if host.startswith("http") else f"https://{host}" # Use https!
    
    # Pretend to be a real Chrome browser
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        req = urllib.request.Request(url, method="HEAD", headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return 200 <= resp.status < 400
    except HTTPError as e:
        # Some sites return 403 but are still "up"
        # You might want to consider 403 as "Online" for a status checker
        return e.code in [200, 301, 302, 403] 
    except URLError:
        return False


def check_tcp(host: str, port: int, timeout: int = 5) -> bool:
    """Attempt a simple TCP connection to ``host:port``.

    Returns ``True`` if the connection succeeds within ``timeout`` seconds,
    ``False`` on any error (including DNS failure or connection refused).
    """

    import socket

    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False

if __name__ == "__main__":
    while(True):
        main()
        if(input("Check another website? Y/N").upper() == "N"):
            break
