@echo off
cd /d "%~dp0"
echo ===================================
echo   Workrance - متابعة المخالفات
echo ===================================
echo.
echo جاري التشغيل...
echo افتح المتصفح على: http://localhost:8501
echo.
echo لايقاف الاداة اضغط Ctrl+C
echo.
"C:\Users\ayama\AppData\Local\Python\pythoncore-3.14-64\Scripts\streamlit.exe" run app.py --server.headless true --browser.gatherUsageStats false
pause
