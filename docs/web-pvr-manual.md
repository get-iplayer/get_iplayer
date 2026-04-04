# get_iplayer Web PVR Manager - Complete User Manual

## Table of Contents

1. [Installation & Setup](#1-installation--setup)
2. [Running the Web PVR Manager](#2-running-the-web-pvr-manager)
3. [Setup Wizard - First Time Configuration](#3-setup-wizard---first-time-configuration)
4. [Searching for Programmes](#4-searching-for-programmes)
5. [Recording Programmes](#5-recording-programmes)
6. [PVR (Automatic Recording)](#6-pvr-automatic-recording)
7. [Cache Management](#7-cache-management)
8. [Viewing Download History](#8-viewing-download-history)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. Installation & Setup

### Prerequisites

Before using the Web PVR Manager, ensure you have:

- **Perl 5.16+** (system Perl recommended: `/usr/bin/perl`)
- **get_iplayer script** in the same directory as `get_iplayer.cgi`
- **Network access** to BBC iPlayer (UK required)

### Required System Programs

The Setup Wizard will check and install these if missing:

| Program | Purpose |
|---------|---------|
| `ffmpeg` | Convert and process video/audio |
| `AtomicParsley` | Add metadata tags to files |

### Required Perl Modules

The Setup Wizard will check and install these if missing:

| Module | Purpose |
|--------|---------|
| LWP::UserAgent | Web requests |
| LWP::Protocol::https | HTTPS connections |
| HTML::Entities | HTML encoding |
| XML::LibXML | XML parsing |
| CGI | Web interface |
| Encode | Character encoding |
| Mojolicious | Concurrent indexing (optional) |
| Mozilla::CA | SSL certificates |

---

## 2. Running the Web PVR Manager

### Step 1: Start the Server

Open a terminal and run:

```bash
cd /path/to/get_iplayer
./get_iplayer.cgi --listen=127.0.0.1 --port=8080
```

### Step 2: Access the Interface

1. Open your web browser
2. Navigate to: **http://127.0.0.1:8080**
3. The Setup Wizard will automatically open on first visit

### Step 3: Navigation

The main navigation tabs are:

| Tab | Function |
|-----|-----------|
| **Setup** | First-time configuration wizard |
| **Search** | Search and record programmes |
| **Recordings** | View download history |
| **PVR List** | Manage automatic recordings |
| **Run PVR** | Manually trigger PVR |
| **Help** | Links to documentation |

---

## 3. Setup Wizard - First Time Configuration

### Step 1: Welcome Screen

When you first access the Web PVR Manager:

1. You will see the **Setup Wizard** welcome screen
2. Click **"Start Setup"** to begin
3. Or click **"Skip Setup"** to go directly to Search

### Step 2: Check Dependencies

The wizard automatically checks for required components:

1. **View Status** - Green = OK, Red = Missing
2. **If any are missing**:
   - Click **"Install Missing"** button
   - The wizard will install via cpanm/Homebrew
3. **After installation**, click **"Recheck"** to verify
4. Click **"Next"** to proceed

### Step 3: Network Check

1. The wizard detects your IP address
2. Verifies access to BBC services
3. If issues detected, provides guidance
4. Click **"Next"** to proceed

### Step 4: Cache Management

**Setting Cache Days (Important for finding on-demand programmes):**

1. Find **"Radio Cache Days"** option
2. Set to **30** (maximum, allows finding programmes from past 30 days)
3. Find **"TV Cache Days"** option  
4. Set to **30**
5. Click **"Refresh All Caches (TV + Radio)"** to apply

**What this does:** Extends the programme cache from default 7 days to 30 days, allowing you to find and record on-demand programmes that aired in the past month.

### Step 5: Output Directory

1. View the default recording directory
2. Optionally change in **Recording Options** tab later
3. Click **"Next"** to proceed

### Step 6: Complete

1. Review the summary
2. Click **"Go to Search"** to start using the application

---

## 4. Searching for Programmes

### Basic Search

**Step 1: Enter Search Term**

1. Go to **Search** tab
2. In the **Search** field, enter your search term
   - Examples: "Doctor Who", "Top Gear", "Early Music", "Classical"
   - Supports regular expressions: `^The.*$`

**Step 2: Select Programme Type**

1. Find **"Programme Types"** in options
2. Select one of:
   - **TV** - TV programmes only
   - **Radio** - Radio programmes only
   - **TV,Radio** - Both

**Step 3: Execute Search**

1. Click **"Search"** button
2. Results appear below

### Advanced Search

**Step 1: Expand Advanced Options**

1. In Search tab, click **"Advanced Search"** section

**Step 2: Use Filters**

| Filter | Usage |
|--------|-------|
| **Search in** | Field to search (name, episode, description) |
| **Exclude** | Words to exclude from results |
| **Category** | Filter by category (e.g., Music, Drama) |
| **Channel** | Filter by specific channel |
| **Since** | Show programmes added after date |
| **Before** | Show programmes added before date |

**Step 3: Execute Search**

1. Click **"Search"** with advanced options active

### Understanding Results

Results display in a table with:

| Column | Description |
|--------|-------------|
| **Name** | Programme title |
| **Episode** | Episode title/date |
| **Channel** | BBC channel |
| **Expires** | When programme expires from iPlayer |
| **Actions** | Record, Queue, Add Series buttons |

---

## 5. Recording Programmes

### Method 1: Quick Record (Single Programme)

**Step 1: Search for Programme**

1. Use Search tab to find the programme
2. Locate the programme in results

**Step 2: Click Record**

1. Click **"Record"** button next to the programme
2. A new tab opens and recording begins
3. Progress is shown in the tab

**Step 3: Monitor Recording**

1. Recording downloads to configured output directory
2. Filename format: `Programme_Name_Episode_PID_version.ext`
3. Completed recordings appear in **Recordings** tab

### Method 2: Queue (Record Once)

**Step 1: Search for Programme**

1. Find the programme you want to record

**Step 2: Click Queue**

1. Click **"Queue"** button next to programme
2. Programme is added to recording queue

**Step 3: Run Queue**

1. Go to **Run PVR** tab
2. The queued programme will be recorded

### Method 3: Add Series (Automatic Recording)

**Step 1: Search for Programme**

1. Find the programme you want to automatically record

**Step 2: Click Add Series**

1. Click **"Add Series"** button
2. A PVR search is created for this programme
3. All future episodes will be automatically recorded

**Step 3: Verify PVR Search**

1. Go to **PVR List** tab
2. You should see a new entry for the series

### Recording Options Configuration

**Step 1: Access Recording Options**

1. In Search tab, find **"Recording Options"** section
2. Or look for **"Recording"** tab in options panel

**Step 2: Configure Options**

| Option | Recommended Setting |
|--------|---------------------|
| **Recording Quality** | `high` for best, `default` for automatic |
| **Subtitles** | `1` to download if available |
| **Thumbnail** | `1` to download programme image |
| **Output Folder** | Set custom directory path |
| **Radio Cache Days** | `30` to find on-demand |
| **TV Cache Days** | `30` to find on-demand |

**Step 3: Save Settings**

Settings are automatically saved to your get_iplayer configuration.

---

## 6. PVR (Automatic Recording)

### Creating a PVR Search

**Method 1: From Search Results**

1. Search for a programme (e.g., "Early Music")
2. Click **"Add Search to PVR"** button
3. Enter a name for the search (e.g., `early_music`)
4. The search is saved and will run automatically

**Method 2: Manual Creation**

1. Go to **PVR List** tab
2. Click **"Add New PVR Search"**
3. Enter search parameters:
   - Search name
   - Search term
   - Programme type (TV/Radio)
   - Channels to include/exclude

### Managing PVR Searches

**View All Searches:**

1. Go to **PVR List** tab
2. See all saved PVR searches with their status

**Edit a Search:**

1. Click on the search name in PVR List
2. Modify search parameters
3. Save changes

**Delete a Search:**

1. In PVR List, select the search
2. Click **"Delete"** button

**Enable/Disable:**

1. Use the checkbox next to each search
2. Disabled searches are skipped during PVR run

### Running the PVR

**Manual Run:**

1. Go to **Run PVR** tab
2. Click **"Run PVR"** button
3. All enabled PVR searches execute
4. New matching programmes are recorded

**Automatic Run:**

1. In Search tab, find **"Auto-Run PVR Interval"** option
2. Set to number of hours (e.g., `1` for hourly)
3. The PVR runs automatically in the background

### PVR Queue (One-Time Recordings)

**Adding to Queue:**

1. Search for a programme
2. Click **"Queue"** instead of Record
3. Programme is added as a one-time PVR entry

**Processing Queue:**

1. When PVR runs, queue entries are processed first
2. After recording, queue entries are automatically deleted

---

## 7. Cache Management

### What is the Cache?

The cache stores programme listings from BBC websites. It must be periodically refreshed to find new programmes.

### Refreshing the Cache

**Method 1: From Search Tab**

1. Click **"Refresh All"** button
2. Both TV and Radio caches refresh
3. Uses current cache day settings

**Method 2: From Setup Wizard**

1. Go to **Setup** tab → Step 4 (Cache)
2. Click **"Refresh All Caches (TV + Radio)"**
3. Uses current cache day settings

**Method 3: Force Refresh (Specific Type)**

1. Add `&PROGTYPES=tv` or `&PROGTYPES=radio` to URL
2. Example: `?NEXTPAGE=refresh&PROGTYPES=tv`

### Setting Cache Days (Important!)

To find on-demand programmes from the past:

**Step 1: Access Recording Options**

1. In Search tab, locate Recording Options section

**Step 2: Set Cache Days**

1. Find **"Radio Cache Days"**
2. Change from default `7` to `30`
3. Find **"TV Cache Days"**
4. Change from default `7` to `30`
5. Click **Search** to apply

**Why this matters:**
- Default (7 days): Only finds scheduled programmes
- 30 days: Finds on-demand programmes from past month

### Auto-Refresh

**Setting Up:**

1. Find **"Auto-Refresh Cache Interval"** option
2. Set to number of hours (e.g., `4`)
3. Cache auto-refreshes when you visit Search tab

---

## 8. Viewing Download History

### Accessing History

1. Click **"Recordings"** tab
2. View list of all downloaded programmes

### Understanding the List

| Column | Description |
|--------|-------------|
| **Name** | Programme title |
| **Episode** | Episode title |
| **Type** | TV or Radio |
| **Date** | Download date |
| **Duration** | Programme length |
| **Channel** | BBC channel |
| **Size** | File size |

### Filtering History

**By Programme Type:**

1. Use **"Programme Types"** filter
2. Select TV, Radio, or Both

**By Search Term:**

1. Use the search field
2. Filter by name/episode

### Deleting History Entries

1. Select programmes to delete
2. Click **"Delete"** button
3. This removes from history only (not downloaded files)

---

## 9. Troubleshooting

### Problem: "No Matching Programmes"

**Solutions:**

1. **Refresh the cache:**
   - Click "Refresh All" button
   - Wait for indexing to complete

2. **Increase cache days:**
   - Set Radio/TV Cache Days to 30
   - Refresh again

3. **Try broader search:**
   - Use simpler terms
   - Try just "music" instead of "early music"

4. **Check programme type:**
   - Make sure correct type selected (TV/Radio)

### Problem: "Can't Download - SSL Error"

**Cause:** Missing SSL certificates

**Solution:**

1. Go to **Setup** tab
2. Run dependency check
3. Click "Install Missing" if Mozilla::CA is missing

### Problem: "Programme Expired"

**Cause:** BBC removed the programme from iPlayer

**Solution:**

- Unfortunately, expired programmes cannot be re-downloaded
- Use PVR to capture programmes before they expire

### Problem: "Permission Denied" on Recording

**Cause:** Output directory not writable

**Solution:**

1. Check output directory setting
2. Ensure the directory exists
3. Check file permissions on the directory

### Problem: "Module Not Found" Errors

**Solution:**

1. Run **Setup Wizard**
2. Click **"Install Missing"** for all missing modules
3. Restart the Web PVR Manager

### Problem: PVR Not Recording New Episodes

**Checks:**

1. **Is PVR search enabled?**
   - Go to PVR List
   - Ensure search is not disabled

2. **Is cache fresh?**
   - Click "Refresh All" before running PVR

3. **Is cache range sufficient?**
   - Set cache days to 30 to catch on-demand

4. **Check PVR logs:**
   - Run PVR manually
   - Look for any error messages

---

## Quick Reference

### Common Tasks

| Task | Steps |
|------|-------|
| Find old programmes | Set cache to 30 days, refresh |
| Record single show | Search → Record |
| Auto-record series | Search → Add Series |
| Run PVR manually | Go to Run PVR tab |
| Change recording quality | Recording Options → Quality |
| Change output folder | Recording Options → Output |

### Keyboard Commands

| Action | Result |
|--------|--------|
| Enter in search field | Execute search |
| Click column header | Sort by column |

### File Locations

| File | Location |
|------|-----------|
| Recordings | Configured output directory (default: `~/iPlayer Recordings/`) |
| Cache | `~/.get_iplayer/tv.cache`, `~/.get_iplayer/radio.cache` |
| PVR config | `~/.get_iplayer/pvr/` |
| Download history | `~/.get_iplayer/download_history` |
| Settings | `~/.get_iplayer/options` |

---

## Support

- **Wiki:** https://github.com/get-iplayer/get_iplayer/wiki
- **Issues:** https://github.com/get-iplayer/get_iplayer/issues
- **Forum:** https://forums.jbox.co.uk/

---

*Last updated: April 2026 for get_iplayer v3.36*