import paramiko
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('64.225.49.118', username='root', password='aman123321.Erp')
stdin, stdout, stderr = client.exec_command('cd /opt/aman && git log --oneline -2')
print(stdout.read().decode())
client.close()
