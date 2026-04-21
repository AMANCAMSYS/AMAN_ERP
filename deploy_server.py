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

    COMPOSE_CMD = "docker compose -f docker-compose.yml -f docker-compose.prod.yml"

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

    # 1. Pull latest code
    _run("cd /opt/aman && git fetch origin main && git reset --hard origin/main", "Pulling latest code")

    # 2. Build both backend and frontend containers
    _run(f"cd /opt/aman && {COMPOSE_CMD} build --no-cache backend frontend", "Building backend + frontend containers")

    # 3. Restart all services (db/redis stay up, backend+frontend recreated)
    _run(f"cd /opt/aman && {COMPOSE_CMD} up -d --force-recreate backend frontend", "Restarting backend + frontend")

    # 4. Wait for backend to be healthy
    _run(
        "echo 'Waiting for backend health...' && "
        "for i in $(seq 1 30); do "
        "  if curl -sf http://localhost:8000/health > /dev/null 2>&1; then "
        "    echo 'Backend is healthy'; exit 0; "
        "  fi; "
        "  sleep 3; "
        "done; "
        "echo 'WARNING: Backend health check timed out after 90s'",
        "Health check"
    )

    # 5. Show running services
    _run(f"cd /opt/aman && {COMPOSE_CMD} ps", "Service status")

    print("Done!")
finally:
    client.close()
