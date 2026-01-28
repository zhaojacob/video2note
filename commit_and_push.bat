@echo off
REM Git commit and push script for video_note_system
REM Run this script to commit and push changes to GitHub

echo ============================================================
echo   Video Note System - Git Commit ^& Push Script
echo ============================================================
echo.

REM Check git status
echo [1/5] Checking git status...
git status
echo.

REM Add modified files
echo [2/5] Adding modified files...
git add analysis/structurer.py
git add config/settings.py
git add utils/summary_generator.py
git add utils/text_polisher.py
git add utils/translator.py
echo + Files staged
echo.

REM Show what will be committed
echo [3/5] Showing changes summary...
git diff --cached --stat
echo.

REM Create commit
echo [4/5] Creating commit...
git commit -m "fix: Improve DeepSeek API integration and error handling

Major changes:
- Update all DeepSeek clients to use deepseek-chat model (128K context, 8K output)
- Reduce chunk size from 6000 to 4500 chars for better timeout tolerance
- Add timeout=300s to client initialization for long response handling
- Add comprehensive error handling with specific exception types:
  * APIConnectionError: Handle network drops/timeout
  * RateLimitError: Handle 429 errors with 60s wait
  * APITimeoutError: Handle timeout with retry
  * AuthenticationError: Handle 401 errors
  * APIError: Handle 4xx/5xx errors with smart retry logic
- Add detailed debug output for troubleshooting (chunk size, input chars, etc.)
- Remove obsolete reasoning_content handling (not needed for chat model)
- Add try-catch at function level to prevent crashes
- Update all API calls to follow DeepSeek official format (system + user messages)

Fixes:
- Fix multi-turn polish failures due to connection timeout
- Fix Connection error with status=unknown
- Improve error messages with detailed error codes and messages
- Add fallback to raw text on API failure

Tested with:
- Single-turn polish: OK (1,318 chars video)
- Multi-turn polish: Improved for 35K+ chars videos

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

if %ERRORLEVEL% EQU 0 (
    echo + Commit created successfully
    echo.

    REM Push to remote
    echo [5/5] Pushing to GitHub...
    git push
    if %ERRORLEVEL% EQU 0 (
        echo.
        echo ============================================================
        echo SUCCESS! Changes pushed to GitHub
        echo ============================================================
    ) else (
        echo.
        echo ============================================================
        echo X Push failed. Please check your network or GitHub credentials
        echo ============================================================
        echo.
        echo To retry push, run: git push
    )
) else (
    echo X Commit failed. Please check the changes above
    echo To fix issues, run: git commit --amend
)

pause
