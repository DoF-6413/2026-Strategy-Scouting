@echo off
cd /d "%~dp0"
echo Starting Strategy Dashboard...
uv run --package frc-6413-strategy-dashboard streamlit run Strategy-Dashboard\main.py