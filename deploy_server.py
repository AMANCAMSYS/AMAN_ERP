import os
import paramiko


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


host = _required_env("AMAN_SSH_HOST")
username = _required_env("AMAN_SSH_USER")
password = _required_env("AMAN_SSH_PASSWORD")

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    print("Connecting...")
    client.connect(host, username=username, password=password)

    print("Pulling latest code...")
    stdin, stdout, stderr = client.exec_command("cd /opt/aman && git fetch origin main && git reset --hard origin/main")
    print(stdout.read().decode())

    print("Rebuilding frontend container without cache...")
    stdin, stdout, stderr = client.exec_command("cd /opt/aman && docker compose -f docker-compose.prod.yml build --no-cache frontend")
    print(stdout.read().decode("utf-8", errors="ignore"))

    print("Starting frontend container...")
    stdin, stdout, stderr = client.exec_command("cd /opt/aman && docker compose -f docker-compose.prod.yml up -d --force-recreate frontend")
    print(stdout.read().decode())

    print("Done!")
finally:
    client.close()
