@echo off
cd /d "%~dp0"
echo Scanning defense data...
uv run --package frc-6413-scouting-scripts python Scouting-Scripts\defense_scouting_2026.py
