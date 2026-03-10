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
        print(f"{host} is online.\n")
    else:
        print(f"{host} appears to be offline or unreachable.\n")

    # echo the raw ping output for debugging/visibility
    print(output)


if __name__ == "__main__":
    while True:
        main()
