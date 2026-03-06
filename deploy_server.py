import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    print("Connecting...")
    client.connect('64.225.49.118', username='root', password='aman123321.Erp')
    
    print("Pulling latest code...")
    stdin, stdout, stderr = client.exec_command('cd /opt/aman && git fetch origin main && git reset --hard origin/main')
    print(stdout.read().decode())
    
    print("Rebuilding frontend container without cache...")
    stdin, stdout, stderr = client.exec_command('cd /opt/aman && docker compose -f docker-compose.prod.yml build --no-cache frontend')
    print(stdout.read().decode('utf-8', errors='ignore'))
    
    print("Starting frontend container...")
    stdin, stdout, stderr = client.exec_command('cd /opt/aman && docker compose -f docker-compose.prod.yml up -d --force-recreate frontend')
    print(stdout.read().decode())
    
    print("Done!")
finally:
    client.close()
