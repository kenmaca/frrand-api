
# used to restart the server, a super secure solution with security in mind
ps -ef | grep run.py | grep -v grep | awk '{print $2}' | xargs kill
nohup /home/api/frrand/run.py &
