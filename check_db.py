import paramiko
import sys

def run_db_check():
    host = "187.127.29.104"
    user = "root"
    password = "-feG/FRLvlbkthmn(nS7"
    
    # Command to count patients
    # We use docker exec to run psql inside the db container
    cmd = "docker compose -f /docker/openclinic/docker-compose.yml exec -T db psql -U openclinic -d openclinic -c 'SELECT count(*) FROM patients;'"
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=user, password=password)
        
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print(stdout.read().decode())
        print(stderr.read().decode())
            
        ssh.close()
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)

if __name__ == "__main__":
    run_db_check()
