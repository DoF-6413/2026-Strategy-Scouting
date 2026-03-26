@echo off
cd /d "%~dp0"
echo Scanning scouting data...
uv run --package frc-6413-scouting-scripts python Scouting-Scripts\scouting_2025.py