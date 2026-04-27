import paramiko
import sys

def run_update():
    host = "187.127.29.104"
    user = "root"
    password = "-feG/FRLvlbkthmn(nS7"
    
    commands = [
        "cd /docker/openclinic",
        "git pull origin main",
        "docker compose build --no-cache",
        "docker compose up -d --remove-orphans",
        "docker compose exec -T backend alembic upgrade head",
        "docker image prune -f"
    ]
    
    try:
        print(f"Connecting to {host}...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=user, password=password)
        
        # We need to run commands in a single shell session to maintain the 'cd'
        full_command = " && ".join(commands)
        print(f"Executing: {full_command}")
        
        stdin, stdout, stderr = ssh.exec_command(full_command)
        
        # Stream output
        for line in stdout:
            print(line.strip())
        for line in stderr:
            print(f"ERROR: {line.strip()}", file=sys.stderr)
            
        ssh.close()
        print("Update completed successfully!")
        
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    run_update()
