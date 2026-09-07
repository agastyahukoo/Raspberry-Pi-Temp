@echo off
REM Double-click this to open the drone video feed.
REM Change PORT below only if you changed it in stream.sh too.

set PORT=5000

echo Waiting for video on UDP port %PORT%...
echo.
echo If this window stays black, allow ffplay through Windows Firewall
echo on BOTH the Private and Public network profiles.
echo.
echo Close this window to stop.
echo.

ffplay -fflags nobuffer -flags low_delay -framedrop -probesize 32 -analyzeduration 0 -window_title "Drone Feed" "udp://@:%PORT%"

if errorlevel 1 (
    echo.
    echo ffplay not found. Install it with:
    echo   winget install --id Gyan.FFmpeg -e
    echo Then close and reopen this window.
    pause
)
