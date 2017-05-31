import paramiko, subprocess

def local_execute_command(command):
    result = subprocess.Popen(command, shell=True)
    result.wait()
    return result.stdin, result.stdout, result.stderr

def remote_execute_command(command, hostname):
    host_client = None
    try:
        host_client = paramiko.SSHClient()
        host_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        host_client.connect(hostname, port=22, username="root")
        stdin, stdout, stderr = host_client.exec_command(command)
        return stdin, stdout, stderr
    finally:
        if (host_client == None):
            host_client.close()
