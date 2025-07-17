@echo off
chcp 65001 >nul
color 0A

echo ================================
echo     Activando la aplicación...
echo ================================

echo.
echo Para apagar la app, simplemente cerrá esta ventana.
echo.

echo -------------------------------
echo    Iniciando app Streamlit...
echo -------------------------------
echo.

.\python\python.exe -m streamlit run .\python\app.py

echo.
echo ================================
echo   La aplicación terminó.
echo   Presioná cualquier tecla para cerrar.
echo ================================

pause >nul

