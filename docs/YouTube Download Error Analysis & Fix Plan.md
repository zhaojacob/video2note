 # YouTube Download Error Analysis & Fix Plan

 **Date**: 2026-01-29
 **Affected Component**: `core/video_downloader.py`
 **yt-dlp Version**: stable@2025.12.08 (latest available: nightly@2026.01.27.233257)

 ---

 ## Error Analysis

 ### Primary Errors

 1. **PO Token / Data Sync ID Error**
    ```
    WARNING: [youtube] Unable to fetch GVS PO Token for web client:
    Missing required Data Sync ID for account.
    ```
    - **Root Cause**: YouTube now requires PO Token (Proof of Origin token) with Data Sync ID for web client
 access
    - **Impact**: Web client formats are unavailable
    - **References**: [yt-dlp issue #14665](https://github.com/yt-dlp/yt-dlp/issues/14665), [PO Token
 Guide](https://github.com/yt-dlp/yt-dlp/wiki/PO-Token-Guide)

 2. **JavaScript Challenge Failure**
    ```
    WARNING: [youtube] [jsc] Remote components challenge solver script (deno) and NPM package (deno) were
 skipped
    WARNING: [youtube] aZLr962R6Ag: n challenge solving failed
    ```
    - **Root Cause**: Deno JavaScript runtime not installed
    - **Impact**: Cannot solve YouTube's JS challenges, formats missing
    - **References**: [yt-dlp EJS wiki](https://github.com/yt-dlp/yt-dlp/wiki/EJS)

 3. **SABR Streaming Issue**
    ```
    WARNING: [youtube] Some web client https formats have been skipped as they are missing a url.
    YouTube is forcing SABR streaming for this client.
    ```
    - **Root Cause**: YouTube's new streaming protocol (SABR) requires special handling
    - **Impact**: Some formats unavailable
    - **References**: [yt-dlp issue #12482](https://github.com/yt-dlp/yt-dlp/issues/12482)

 4. **Format Availability**
    ```
    WARNING: Only images are available for download. use --list-formats to see them
    ERROR: [youtube] aZLr962R6Ag: Requested format is not available
    ```
    - **Root Cause**: Combination of above issues results in no downloadable video formats
    - **Impact**: Complete download failure

 ---

 ## Root Cause Summary

 YouTube has implemented multiple layers of anti-bot protection in late 2025/early 2026:

 1. **PO Token requirement** for authenticated access
 2. **JavaScript challenges** to verify legitimate clients
 3. **SABR streaming protocol** changes
 4. **Client restrictions** (iOS client currently used may be blocked)

 The current `video_downloader.py` uses:
 ```python
 'extractor_args': {
     'youtube': {
         'player_client': ['ios', 'mweb'],
     }
 }
 ```

 This configuration is insufficient for YouTube's current protection measures.

 ---

 ## Fix Plan

 ### Phase 1: Immediate Fixes (Quick Win)

 #### 1.1 Update yt-dlp to Nightly Build
 **Priority**: HIGH
 **Effort**: LOW
 **Expected Impact**: May include recent fixes for YouTube changes

 ```bash
 # Uninstall current version
 pip uninstall yt-dlp

 # Install nightly build directly from GitHub
 pip install git+https://github.com/yt-dlp/yt-dlp.git@master
 ```

 **Verification**:
 ```bash
 yt-dlp --version
 # Should show: 2026.01.27.233257 or later
 ```

 ---

 #### 1.2 Install Deno Runtime for JS Challenges
 **Priority**: HIGH
 **Effort**: LOW
 **Expected Impact**: Enables JS challenge solving

 **Windows Installation**:
 ```powershell
 # Using PowerShell
 irm https://deno.land/install.ps1 | iex
 ```

 **Or using Winget**:
 ```bash
 winget install DenoLand.Deno
 ```

 **Verification**:
 ```bash
 deno --version
 ```

 ---

 ### Phase 2: Configuration Changes

 #### 2.1 Update Player Client Configuration
 **Priority**: HIGH
 **Effort**: MEDIUM
 **Expected Impact**: Access to alternative format sources

 **Recommended Changes** to `core/video_downloader.py`:

 ```python
 # OLD (line 104-108):
 'extractor_args': {
     'youtube': {
         'player_client': ['ios', 'mweb'],
     }
 }

 # NEW (recommended):
 'extractor_args': {
     'youtube': {
         'player_client': ['mediaconnect', 'ios', 'android', 'mweb'],
         'player_client_args': {
             'ios': {
                 'po_token': None,  # Can be set later if needed
             }
         }
     }
 }
 ```

 **Client Priority**:
 1. `mediaconnect` - New client, often works better
 2. `ios` - Fallback, currently used
 3. `android` - Alternative fallback
 4. `mweb` - Last resort

 ---

 #### 2.2 Enable Remote Components
 **Priority**: MEDIUM
 **Effort**: LOW
 **Expected Impact**: Automatic JS challenge solving

 **Add to yt-dlp options**:
 ```python
 ydl_opts = {
     # ... existing options ...
     'enable_files_v3': True,  # Enable v3 format handling
 }
 ```

 ---

 #### 2.3 Update Format Selection Strategy
 **Priority**: MEDIUM
 **Effort**: LOW
 **Expected Impact**: More flexible format matching

 **Current** (line 83):
 ```python
 'format': 'best[height<=360]/bestvideo[height<=360]+bestaudio/best',
 ```

 **Recommended**:
 ```python
 # More permissive format selection
 'format': (
     'bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/'
     'bestvideo[height<=360]+bestaudio/'
     'best[height<=360]/'
     'bestvideo+bestaudio/'
     'best'
 ),
 'format_sort': ['res', 'quality', 'filesize'],  # Prefer lower resolution
 'ignore_no_formats_error': True,  # Continue even if initial format check fails
 ```

 ---

 ### Phase 3: Advanced Fixes (If Needed)

 #### 3.1 PO Token Implementation
 **Priority**: MEDIUM
 **Effort**: HIGH
 **Expected Impact**: Access to authenticated-only formats

 **Options**:

 **Option A**: Manual PO Token (quick)
 ```bash
 # Extract PO token manually following:
 # https://github.com/yt-dlp/yt-dlp/wiki/PO-Token-Guide
 ```

 **Option B**: Use yt-dlp's cookies
 ```python
 # Add to video_downloader.py
 if platform == 'youtube':
     cookie_file = VIDEO_CONFIG.get("cookie_file")
     if cookie_file and Path(cookie_file).exists():
         ydl_opts['cookiefile'] = cookie_file
 ```

 **Option C**: PO Token plugin (requires setup)
 ```bash
 # Install yt-dlp plugin for PO tokens
 # See: https://github.com/yt-dlp/yt-dlp/wiki/PO-Token-Guide
 ```

 ---

 #### 3.2 Multi-Client Fallback Strategy
 **Priority**: LOW
 **Effort**: HIGH
 **Expected Impact**: Maximum reliability

 **Implement retry with different clients**:
 ```python
 clients = ['mediaconnect', 'ios', 'android', 'web']
 for client in clients:
     try:
         ydl_opts['extractor_args'] = {'youtube': {'player_client': client}}
         # Attempt download
         break
     except Exception:
         continue
 ```

 ---

 ## Implementation Steps

 ### Step 1: Environment Updates
 1. Update yt-dlp to nightly build
 2. Install Deno runtime
 3. Verify installations

 ### Step 2: Code Changes (video_downloader.py)
 1. Update player_client configuration (line 104-108)
 2. Update format selection (line 83)
 3. Add remote components support
 4. Add cookie support for YouTube
 5. Enable ignore_no_formats_error

 ### Step 3: Testing
 1. Test with problem URL: `https://www.youtube.com/watch?v=aZLr962R6Ag`
 2. Test with different YouTube URLs
 3. Test with other platforms (Bilibili)
 4. Verify format availability with `--list-formats`

 ### Step 4: Monitoring
 1. Check logs for PO token errors
 2. Monitor JS challenge success rate
 3. Track download success rate

 ---

 ## Testing Commands

 ### Test Format Availability
 ```bash
 # List available formats
 yt-dlp --list-formats "https://www.youtube.com/watch?v=aZLr962R6Ag"

 # Test with specific client
 yt-dlp --extractor-args "youtube:player_client=mediaconnect" "https://www.youtube.com/watch?v=aZLr962R6Ag"

 # Test with verbose output
 yt-dlp -v --extractor-args "youtube:player_client=mediaconnect" "https://www.youtube.com/watch?v=aZLr962R6Ag"
 ```

 ### Test Download
 ```bash
 # Test download to temp location
 yt-dlp --extractor-args "youtube:player_client=mediaconnect" -o "%(title)s.%(ext)s"
 "https://www.youtube.com/watch?v=aZLr962R6Ag"
 ```

 ---

 ## Configuration File Updates

 ### config/settings.py Updates Needed
 ```python
 VIDEO_CONFIG = {
     "cookie_file": "output/cookies.txt",  # Ensure this exists
     "proxy": "http://127.0.0.1:7897",
     "quality": "best",
     "user_agent": "Mozilla/5.0 ...",

     # NEW: YouTube specific settings
     "youtube": {
         "player_clients": ["mediaconnect", "ios", "android", "mweb"],
         "enable_po_token": False,  # Set True when PO token available
         "po_token": None,  # Add PO token here if available
     }
 }
 ```

 ---

 ## Rollback Plan

 If changes cause issues:
 1. Revert to original `player_client: ['ios', 'mweb']`
 2. Remove Deno dependency
 3. Downgrade yt-dlp:
    ```bash
    pip install yt-dlp==2025.12.8
    ```

 ---

 ## References

 - [yt-dlp PO Token Guide](https://github.com/yt-dlp/yt-dlp/wiki/PO-Token-Guide)
 - [yt-dlp EJS (JavaScript Challenge) Guide](https://github.com/yt-dlp/yt-dlp/wiki/EJS)
 - [yt-dlp Issue #14665 - PO Token not available](https://github.com/yt-dlp/yt-dlp/issues/14665)
 - [yt-dlp Issue #12482 - SABR streaming](https://github.com/yt-dlp/yt-dlp/issues/12482)
 - [yt-dlp Issue #15288 - Data Sync ID error](https://github.com/yt-dlp/yt-dlp/issues/15288)
 - [yt-dlp Nightly Builds](https://github.com/yt-dlp/yt-dlp-nightly-builds)

 ---

 ## Success Criteria

 - Download completes successfully for test URL
 - No "Only images are available" warnings
 - No "challenge solving failed" errors
 - Format selection works with ≤360p preference
 - Backward compatibility with Bilibili maintained

 ---

 ## Next Actions

 1. **Immediate** (today):
    - Update yt-dlp to nightly
    - Install Deno
    - Test with CLI commands above

 2. **Short-term** (this week):
    - Implement code changes in video_downloader.py
    - Update config/settings.py
    - Test with pipeline

 3. **Long-term** (as needed):
    - Implement PO token if required
    - Add multi-client fallback
    - Monitor YouTube changes

 ---

 **Status**: Ready for implementation
 **Last Updated**: 2026-01-29