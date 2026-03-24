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
client.connect(host, username=username, password=password)
stdin, stdout, stderr = client.exec_command("cd /opt/aman && git log --oneline -2")
print(stdout.read().decode())
client.close()
