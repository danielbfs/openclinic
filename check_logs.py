import paramiko
import sys

def run_logs_check():
    host = "187.127.29.104"
    user = "root"
    password = "-feG/FRLvlbkthmn(nS7"
    
    commands = [
        "docker compose -f /docker/openclinic/docker-compose.yml logs --tail=100 backend",
        "docker compose -f /docker/openclinic/docker-compose.yml logs --tail=100 celery_beat"
    ]
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=user, password=password)
        
        for cmd in commands:
            print(f"\n--- Logs for {cmd} ---")
            stdin, stdout, stderr = ssh.exec_command(cmd)
            print(stdout.read().decode())
            print(stderr.read().decode())
            
        ssh.close()
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)

if __name__ == "__main__":
    run_logs_check()
