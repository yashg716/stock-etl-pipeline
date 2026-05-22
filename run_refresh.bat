@echo off
cd /d D:\ETL_optimization-project

:menu
cls
echo ========================================
echo STOCK PIPELINE MENU
echo ========================================
echo 1. Run refresh pipeline
echo 2. Run full pipeline
echo 3. Exit
echo ========================================
set /p choice=Enter your choice (1/2/3): 

if "%choice%"=="1" goto refresh
if "%choice%"=="2" goto full
if "%choice%"=="3" goto end

echo Invalid choice. Try again.
pause
goto menu

:refresh
echo.
echo Running refresh pipeline...
python refresh_pipeline.py
pause
goto menu

:full
echo.
echo Running full pipeline...
python full_pipeline.py
pause
goto menu

:end
exit