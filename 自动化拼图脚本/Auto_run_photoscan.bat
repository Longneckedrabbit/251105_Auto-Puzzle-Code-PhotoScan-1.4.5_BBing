@echo off
setlocal EnableExtensions EnableDelayedExpansion

:: ===== 可修改 =====
set "PHOTOSCAN_EXE=E:\App\photoscan\photoscan.exe"
set "PHOTOSCAN_LNK=C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Agisoft\Agisoft PhotoScan Professional (64 bit).lnk"
set "SCRIPT_NAME=PhotoScan1.4.5 - tiff.py"
:: ==================

chcp 65001 >nul
set "PYTHONIOENCODING=utf-8"

set "SCRIPT_DIR=%~dp0"
set "SCRIPT_PATH=%SCRIPT_DIR%%SCRIPT_NAME%"

if not exist "%SCRIPT_PATH%" (
  echo([错误] 找不到脚本文件：%SCRIPT_PATH%
  pause
  exit /b 1
)

if not exist "%PHOTOSCAN_EXE%" if exist "%PHOTOSCAN_LNK%" (
  for /f "usebackq tokens=*" %%I in (`powershell -NoProfile -Command "$s=New-Object -ComObject WScript.Shell;$s.CreateShortcut('%PHOTOSCAN_LNK%').TargetPath"`) do set "PHOTOSCAN_EXE=%%I"
)

if not exist "%PHOTOSCAN_EXE%" (
  echo([错误] 找不到 photoscan.exe，请修改 PHOTOSCAN_EXE 或确保 LNK 路径正确
  pause
  exit /b 1
)

echo([信息] 使用的 PhotoScan 可执行文件："%PHOTOSCAN_EXE%"
echo(

set "TARGET_DIR=%~1"
if "%TARGET_DIR%"=="" (
  set /p TARGET_DIR=请输入目标影像文件夹的完整路径（可拖拽进来）： 
)

set "TARGET_DIR=%TARGET_DIR:"=%"

if not exist "%TARGET_DIR%" (
  echo([错误] 目标文件夹不存在：%TARGET_DIR%
  pause
  exit /b 1
)

echo([信息] 目标目录：%TARGET_DIR%
echo([信息] 脚本文件：%SCRIPT_PATH%
echo(
echo(若出现 "No license found (-1)"，请先在 GUI 中激活许可证（Help -> Activate Product...）
echo(

"%PHOTOSCAN_EXE%" -r "%SCRIPT_PATH%" "%TARGET_DIR%"
set "ERR=%ERRORLEVEL%"

if "%ERR%"=="0" goto :OK
goto :ERR

:OK
echo([完成] 处理成功。
pause
exit /b 0

:ERR
echo([错误] PhotoScan 返回错误码 %ERR%
echo(请检查许可证、路径，并查看命令行输出日志。
pause
exit /b %ERR%
