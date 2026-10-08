@echo off
setlocal EnableDelayedExpansion
REM ============================================================
REM  Junction 迁移一键脚本模板（适用于"运行中被锁"的应用数据目录）
REM  用法: 修改下方三个变量后, 双击运行本文件
REM  原理: 两遍 robocopy(第2遍补齐第1遍被进程锁住的文件) → 杀进程 →
REM        原目录改名 _backup → mklink /J 建 Junction → 失败自动回滚
REM  注意: DST 所在盘必须有足够空闲空间; Junction 不需要管理员权限
REM ============================================================

REM --- 按需修改这三个变量 ---
REM 源目录: 用环境变量, 不写死用户名
set "SRC=%USERPROFILE%\.myapp"
REM 目标目录: 数据盘上, 空间要够
set "DST=D:\JunctionData\myapp"
REM 占用该目录的应用进程名(主进程即可)
set "PROC=myapp.exe"
REM --------------------------

REM 从源目录提取文件夹名(用于backup命名)
for %%F in ("%SRC%") do set "NAME=%%~nxF"
set "LOG=%~dp0migrate_log.txt"
echo [%date% %time%] migration start: %SRC% =^> %DST% > "%LOG%"

echo [1/5] Pass 1: copying (locked files will be skipped)...
if not exist "%DST%" mkdir "%DST%" >nul 2>&1
robocopy "%SRC%" "%DST%" /E /COPY:DAT /R:3 /W:5 /MT:8 /NFL /NDL /NJH /NJS /NP >> "%LOG%"

echo [2/5] Closing %PROC% ...
taskkill /F /IM "%PROC%" /T >nul 2>&1
timeout /t 5 /nobreak >nul
taskkill /F /IM "%PROC%" /T >nul 2>&1
timeout /t 3 /nobreak >nul

echo [3/5] Pass 2: incremental copy (catch previously locked files)...
robocopy "%SRC%" "%DST%" /E /COPY:DAT /R:3 /W:5 /MT:8 /NFL /NDL /NJH /NJS /NP >> "%LOG%"

echo [4/5] Renaming original folder to %NAME%_backup ...
set RETRY=0
:retry_rename
ren "%SRC%" "%NAME%_backup"
if errorlevel 1 (
    set /a RETRY+=1
    if !RETRY! GEQ 6 goto rename_failed
    echo       Retry !RETRY!/6 in 5s...
    timeout /t 5 /nobreak >nul
    goto retry_rename
)
echo       Rename OK.

echo [5/5] Creating junction...
mklink /J "%SRC%" "%DST%"
if errorlevel 1 goto junction_failed
echo.
echo  ALL DONE! Data now lives on %DST%. You can relaunch the app.
echo  After a few days of normal use, delete "%SRC%_backup" to free space.
pause
exit /b 0

:rename_failed
echo  ERROR: cannot rename - %PROC% is not fully closed. Close it and re-run.
echo  (Target copy is safe, original folder untouched.)
pause
exit /b 1

:junction_failed
echo  ERROR: junction failed. Rolling back...
ren "%SRC%_backup" "%NAME%"
echo  Rolled back. Nothing broken.
pause
exit /b 1
