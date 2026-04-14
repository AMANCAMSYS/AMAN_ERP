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
	if os.path.isfile(ssh_key_path):
		client.connect(host, username=username, key_filename=ssh_key_path)
	elif password:
		client.connect(host, username=username, password=password)
	else:
		raise RuntimeError("No SSH key or password available. Set AMAN_SSH_KEY_PATH or AMAN_SSH_PASSWORD.")
	stdin, stdout, stderr = client.exec_command("cd /opt/aman && git log --oneline -2")
	print(stdout.read().decode())
finally:
	client.close()
