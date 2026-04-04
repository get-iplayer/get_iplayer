# get_iplayer GUI Setup Wizard - Design Plan

## Existing Web Interface Analysis

The project already includes [`get_iplayer.cgi`](../get_iplayer.cgi:1) - a Web PVR Manager with the following features:

### Current Capabilities
- **Navigation Tabs**: Search, Recordings, PVR List, Run PVR, Help
- **Search Interface**: Search programmes by name, channel, category
- **PVR Management**: Create, edit, delete scheduled recordings
- **Recordings History**: View and manage downloaded programmes
- **Streaming**: Stream programmes directly to browser

### Current Limitations
- **No Setup Wizard**: Users must manually install dependencies
- **No Dependency Checking**: No validation of Perl modules, ffmpeg, etc.
- **No VPN/Proxy Setup**: No UI for configuring UK access
- **No Prerequisites Validation**: Users discover missing dependencies at runtime

### How to Run Existing Interface
```bash
./get_iplayer.cgi --listen=127.0.0.1 --port=8080
# Then open http://127.0.0.1:8080 in browser
```

---

## Proposed Enhancement: Setup Wizard Tab

Add a new **Setup** tab to the existing web interface with a step-by-step wizard.

### Wizard Flow

```mermaid
flowchart TD
    A[Welcome Screen] --> B{Dependencies Check}
    B -->|All OK| C[VPN/Proxy Setup]
    B -->|Missing Deps| D[Dependency Installer]
    D -->|Install| B
    C --> E[Output Configuration]
    E --> F[Ready to Download]
    F --> G[Search Tab]
```

### Step 1: Dependencies Check Panel

| Check | Command | Status Display |
|-------|---------|----------------|
| Perl version | `perl -v` | ✅ 5.42 or ❌ Need 5.16+ |
| HTML::Entities | `perl -MHTML::Entities -e 1` | ✅ Installed / ❌ Missing |
| XML::LibXML | `perl -MXML::LibXML -e 1` | ✅ Installed / ❌ Missing |
| LWP::UserAgent | `perl -MLWP::UserAgent -e 1` | ✅ Installed / ❌ Missing |
| Mojolicious | `perl -MMojolicious -e 1` | ✅ Installed / ❌ Missing |
| ffmpeg | `ffmpeg -version` | ✅ Installed / ❌ Missing |
| AtomicParsley | `AtomicParsley --version` | ✅ Installed / ❌ Missing |

### Step 2: Dependency Installer Panel

**For macOS:**
```bash
# Homebrew installation commands
brew install perl ffmpeg atomicparsley
cpanm HTML::Entities XML::LibXML LWP Mojolicious CGI
```

**For Ubuntu/Debian:**
```bash
sudo apt install get_iplayer ffmpeg atomicparsley
```

**UI Elements:**
- Auto-detect OS
- Show copy-paste commands
- Run button with sudo prompt
- Progress indicator

### Step 3: VPN/Proxy Configuration Panel

**Options:**
1. **No VPN/Proxy** - Direct connection - UK only
2. **HTTP Proxy** - Enter proxy URL
3. **VPN Status Check** - Verify UK IP address

**UI Elements:**
- Proxy URL input field: `http://user:pass@server:port`
- Test Connection button
- UK IP verification: `curl -s ifconfig.co`
- Save to preferences option

### Step 4: Output Configuration Panel

**Settings:**
- Output directory browser
- Subdirectory naming format
- Quality preferences - TV/Radio
- Metadata options
- Subtitle options

### Step 5: Ready to Download

**Summary:**
- All dependencies ✅
- VPN/Proxy configured ✅
- Output directory set ✅

**Actions:**
- Go to Search tab
- Download test programme
- Save configuration

---

## Implementation Plan

### Phase 1: Backend Functions
1. Add dependency checking functions to `get_iplayer.cgi`
2. Add VPN/proxy test functions
3. Add configuration save/load functions

### Phase 2: Frontend UI
1. Add Setup tab to navigation
2. Create wizard step components
3. Add progress indicators
4. Add error handling UI

### Phase 3: Integration
1. Block downloads if dependencies missing
2. Show setup prompt on first run
3. Add setup link in footer

---

## File Changes Required

| File | Changes |
|------|---------|
| `get_iplayer.cgi` | Add setup wizard functions and UI |
| `README.md` | Document setup wizard usage |

### New Functions to Add

```perl
# Dependency checking
sub check_perl_version { ... }
sub check_perl_module { ... }
sub check_external_program { ... }
sub get_all_dependencies { ... }

# VPN/Proxy
sub test_proxy_connection { ... }
sub check_uk_ip { ... }
sub save_proxy_config { ... }

# Setup wizard UI
sub show_setup_wizard { ... }
sub setup_step_dependencies { ... }
sub setup_step_proxy { ... }
sub setup_step_output { ... }
sub setup_step_complete { ... }
```

---

## Alternative: Standalone Python GUI

If enhancing the CGI is not preferred, a standalone Python app would provide:

### Advantages
- Native desktop integration
- Better system access for dependency installation
- No web server required
- Can auto-install dependencies via pip/homebrew

### Structure
```
get_iplayer_gui/
├── main.py           # Main application entry
├── setup_wizard.py   # Setup wizard logic
├── dependency_checker.py
├── vpn_config.py
├── download_manager.py
└── ui/
    ├── main_window.py
    ├── setup_dialog.py
    └── preferences_dialog.py
```

---

## Issues Discovered During Testing

### Issue 1: CGI calls wrong get_iplayer script
**Problem**: The CGI searches for `./get_iplayer` first, finding the local script instead of Homebrew's version with bundled dependencies.

**Solution**: Must specify `--getiplayer=/opt/homebrew/bin/get_iplayer` when starting CGI.

### Issue 2: Cache refresh only works from CLI
**Problem**: Web interface "Refresh" button may not work properly, especially with VPN/proxy requirements.

**Root causes**:
1. VPN must be connected before refresh
2. Proxy settings not passed correctly to get_iplayer
3. No feedback when refresh fails due to geo-blocking

**Solution**: Setup wizard should:
1. Check VPN connection status before refresh
2. Verify UK IP address
3. Configure proxy settings
4. Provide clear error messages for geo-blocking

---

## Updated Implementation Plan

### Phase 1: Setup Wizard Tab
Add a new "Setup" tab with the following steps:

#### Step 1: Environment Check
- Detect get_iplayer installation path
- Check Perl version and modules
- Check ffmpeg and AtomicParsley
- Display status for each dependency

#### Step 2: Network Configuration
- Check current IP location
- Detect if UK access is available
- Configure proxy settings
- Test connection to BBC servers

#### Step 3: Cache Management
- Refresh programme cache
- Show cache status and age
- Handle geo-blocking errors gracefully
- Provide VPN connection guidance

#### Step 4: Output Settings
- Configure download directory
- Set quality preferences
- Configure metadata options

#### Step 5: Ready
- Summary of configuration
- Quick test download option
- Link to Search tab

### Phase 2: Fix CGI Script Path Detection
Modify `get_iplayer.cgi` to:
1. Accept a configuration file for get_iplayer path
2. Check Homebrew installation path automatically on macOS
3. Provide clear error if get_iplayer not found

### Phase 3: Improve Error Handling
1. Show meaningful errors for geo-blocking
2. Display VPN connection guidance
3. Log refresh failures with actionable messages
