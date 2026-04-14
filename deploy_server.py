import os
import paramiko


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


host = _required_env("AMAN_SSH_HOST")
username = _required_env("AMAN_SSH_USER")
password = os.getenv("AMAN_SSH_PASSWORD")
ssh_key_path = os.getenv("AMAN_SSH_KEY_PATH", os.path.expanduser("~/.ssh/id_rsa"))

client = paramiko.SSHClient()
client.load_system_host_keys()
client.set_missing_host_key_policy(paramiko.WarningPolicy())
try:
    print("Connecting...")
    if os.path.isfile(ssh_key_path):
        client.connect(host, username=username, key_filename=ssh_key_path)
    elif password:
        client.connect(host, username=username, password=password)
    else:
        raise RuntimeError("No SSH key or password available. Set AMAN_SSH_KEY_PATH or AMAN_SSH_PASSWORD.")

    def _run(cmd: str, label: str) -> None:
        """Execute a remote command and raise on failure."""
        print(f"{label}...")
        _stdin, _stdout, _stderr = client.exec_command(cmd)
        exit_code = _stdout.channel.recv_exit_status()
        out = _stdout.read().decode("utf-8", errors="ignore")
        err = _stderr.read().decode("utf-8", errors="ignore")
        if out:
            print(out)
        if exit_code != 0:
            print(f"[ERROR] {label} failed (exit {exit_code})")
            if err:
                print(err)
            raise RuntimeError(f"{label} failed with exit code {exit_code}")

    _run("cd /opt/aman && git fetch origin main && git reset --hard origin/main", "Pulling latest code")
    _run("cd /opt/aman && docker compose -f docker-compose.prod.yml build --no-cache frontend", "Rebuilding frontend container without cache")
    _run("cd /opt/aman && docker compose -f docker-compose.prod.yml up -d --force-recreate frontend", "Starting frontend container")

    print("Done!")
finally:
    client.close()
