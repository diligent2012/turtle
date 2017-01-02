#!/bin/sh
#=========================
#Mark.Huang
#hacker.do@163.com
#Usage:
#  nohup ./alway_run.sh &
#=========================
clear
echo 'nohup ./' $0 '&'
mv turtle.out _turtle.log
touch turtle.out

while :
do
  echo "Current dir is " $PWD
  stillRunning=$(ps -ef |grep "python turtle.py" |grep -v "grep")
  if [ "$stillRunning" ] ; then
    echo
    date +%F" "%H:%M:%S
    echo "service was already started by another way"
    $stillRunning |awk '{print $2}'|xargs kill -9
    echo "service running" 
  else
    echo
    date +%F" "%H:%M:%S
    echo "service was not started" 
    echo "Starting service ..." 
    python turtle.py
    echo "service was exited!" 
  fi
  sleep 10
done
