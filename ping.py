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
    """Entry point for the command line application."""

    parser = argparse.ArgumentParser(
        description="Check whether a website or host is reachable via ICMP ping or HTTP."
    )
    parser.add_argument(
        "host",
        nargs="?",
        help="Website (domain) or IP address to ping",
    )
    parser.add_argument(
        "--http",
        action="store_true",
        help="If ping fails, try an HTTP HEAD request to the host",
    )

    args = parser.parse_args()
    host = args.host or input("Enter website to ping: ")

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
    """Perform a simple HTTP HEAD request to the given host.

    The host may be a bare domain or URL; if it doesn't start with a scheme we
    prepend "http://".  Returns ``True`` if a connection is made and a response
    code in the 200–399 range is received; ``False`` otherwise.
    """

    url = host if host.startswith("http") else f"http://{host}"
    try:
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return 200 <= resp.status < 400
    except (URLError, HTTPError):
        return False

if __name__ == "__main__":
    main()
