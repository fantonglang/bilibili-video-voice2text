# How to Get Bilibili Cookies

Some Bilibili videos require login to access. You need to export cookies from your browser after logging into Bilibili.

## Method 1: Using Chrome Extension (Easiest)

1. Install the "Get cookies.txt LOCALLY" extension from Chrome Web Store
   - Link: https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckofkjlflfgjhphkadgpfa

2. Go to https://www.bilibili.com and **log in** to your account

3. Click the extension icon → Click "Export" → Select "Netscape HTTP Cookie File"

4. Save the file as `cookies.txt` in the project directory (same folder as main.py)

5. Done! The downloader will automatically use this file.

## Method 2: Using Firefox Extension

1. Install "cookies.txt" extension from Firefox Add-ons
   - Link: https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/

2. Go to https://www.bilibili.com and **log in**

3. Click the extension → "Export cookies for current site"

4. Save as `cookies.txt` in the project directory

## Method 3: Using yt-dlp Directly (No file needed)

If you have Firefox or Chrome installed, yt-dlp can extract cookies directly:

```bash
# For Firefox users
yt-dlp --cookies-from-browser firefox "BV1xx411c7mD"

# For Chrome users  
yt-dlp --cookies-from-browser chrome "BV1xx411c7mD"
```

To use this in the script, modify `downloader.py`:

```python
# In get_yt_dlp_base_args(), replace the cookie file logic with:
args.extend(["--cookies-from-browser", "firefox"])  # or "chrome"
```

## Method 4: Manual Copy (Advanced)

1. Open browser DevTools (F12) → Application/Storage → Cookies → https://www.bilibili.com

2. Look for these important cookies:
   - `SESSDATA` - Session data (required)
   - `bili_jct` - CSRF token
   - `DedeUserID` - User ID
   - `DedeUserID__ckMd5` - User ID checksum

3. Create `cookies.txt` with format:

```
# Netscape HTTP Cookie File
.bilibili.com	TRUE	/	FALSE	<timestamp>	SESSDATA	<your_sessdata_value>
.bilibili.com	TRUE	/	FALSE	<timestamp>	bili_jct	<your_bili_jct_value>
.bilibili.com	TRUE	/	TRUE	<timestamp>	DedeUserID	<your_userid>
```

## Troubleshooting

### HTTP 412 Error

This error means Bilibili is blocking the request due to:
- Missing login session
- Suspicious activity detected
- IP-based rate limiting

**Solutions:**
1. Make sure cookies are fresh (log in again and re-export)
2. Try using a different network/VPN
3. Wait a few minutes and try again
4. Use cookies from a browser that you regularly use Bilibili on

### HTTP 403 Error

Access is forbidden. This usually means:
- The video is region-restricted
- The video requires a premium/VIP account
- Your account doesn't have permission to view this content

### Cookies Not Working

1. Check if cookies.txt is in the correct location (project root)
2. Make sure you logged in to bilibili.com before exporting
3. Try exporting cookies again (they may have expired)
4. Check if the file format is correct (Netscape format)

## Security Notice

⚠️ **Your cookies contain sensitive login information!**

- Never commit `cookies.txt` to git
- Never share your cookies.txt with others
- The file is already in `.gitignore` but double-check
- Consider using a separate Bilibili account for this tool

## Testing Cookies

To test if cookies are working:

```bash
# Test with yt-dlp directly
yt-dlp --cookies cookies.txt --list-formats "BV1xx411c7mD"
```

If it shows available formats, your cookies are working!
