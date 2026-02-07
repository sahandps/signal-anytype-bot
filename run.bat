@echo off
title Signal Anytype Bot
cd /d "%~dp0"

:: Set Java Home (Auto-detected based on investigation)
set "JAVA_HOME=C:\Program Files\Java\jdk-21.0.10"
set "PATH=%JAVA_HOME%\bin;%PATH%"

:loop
echo Starting bot...
python bot.py
echo Bot crashed or stopped. Restarting in 10 seconds...
timeout /t 10
goto loop
