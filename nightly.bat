@echo off
rem Nightly practice for the site factory: builds 10 sites for imaginary places (examples to train the local model).
rem Needs Ollama running and the laptop awake and online. Log: output\nightly.log
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
".venv\Scripts\python.exe" -m weblume.factory.nightly 10 >> "output\nightly.log" 2>&1
