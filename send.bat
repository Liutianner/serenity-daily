@echo off
chcp 65001 >nul
echo ========================================
echo      钉钉即时消息推送工具
echo ========================================
echo.

set /p msg="请输入要推送的消息: "

if "%msg%"=="" (
    echo ❌ 消息不能为空！
    pause
    exit /b
)

set DINGTALK_WEBHOOK=https://oapi.dingtalk.com/robot/send?access_token=271e4d2114e8303b47517a8017f4a4584af66f1c9a999b06a646afd94a6b2c3d

python send_dingtalk.py "%msg%"

echo.
pause
