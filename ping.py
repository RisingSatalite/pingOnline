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
        description="Check whether a website or host is reachable via ICMP ping."
    )
    parser.add_argument(
        "host",
        nargs="?",
        help="Website (domain) or IP address to ping",
    )

    args = parser.parse_args()
    host = args.host or input("Enter website to ping: ")

    online, output = ping(host)

    if online:
        print(f"{host} is online.")
        # attempt to extract round‑trip time from the ping output
        time_str = extract_time(output)
        if time_str:
            print(f"Response {time_str}")
        else:
            print("(could not parse response time)")
    else:
        print(f"{host} appears to be offline or unreachable.")

    # if you need full details you can uncomment the next line
    # print(output)



# helpers
import re

def extract_time(output: str) -> str | None:
    """Try to find the first "time" value in *ping* output.

    Returns the matched substring including units (e.g. ``"time=23ms"`` or
    ``"time<1ms"``) or ``None`` if nothing recognizable is present.
    """

    # common ping formats on Windows and Unix variants
    match = re.search(r"time[=<]\s*<?\d+\.?\d*\s*ms", output, re.IGNORECASE)
    return match.group() if match else None


if __name__ == "__main__":
    main()
