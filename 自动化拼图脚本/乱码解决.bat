@echo off
REM 1) 切换控制台到 UTF-8
chcp 65001 >nul

REM 2) 告诉 Python 用 UTF-8 读写标准输入输出
set PYTHONIOENCODING=utf-8

REM 3) 运行 PhotoScan + 脚本
"E:\App\photoscan\photoscan.exe" -r "C:\Users\nky\Desktop\PhotoScan1.4.5.py" "G:\123"

pause
