@echo off
echo.
echo ========================================
echo   Neuronix AI JobFlow - Vanilla Version
echo ========================================
echo.
echo Starting local server on port 8000...
echo.
echo Open your browser and go to:
echo   http://localhost:8000
echo.
echo Press Ctrl+C to stop the server
echo.
echo ========================================
echo.

python -m http.server 8000
