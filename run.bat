@echo off
title Signal Anytype Bot
cd /d "%~dp0"

:loop
echo Starting bot...
python bot.py
echo Bot crashed or stopped. Restarting in 10 seconds...
timeout /t 10
goto loop
