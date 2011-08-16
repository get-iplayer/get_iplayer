## get_player Windows installer

This document contains instructions for building the `get_iplayer` Windows installer and provides additional notes for installer developers. The information below is current for version 4.3 of the installer.

## Building the Installer

### Prerequisites

1. **Strawberry Perl**

	Source: <http://strawberryperl.com>

	Version: 5.12.3.0

	The installer is built with the Strawberry Perl distribution that is in your system path.  If you are using a different version, you may need to uninstall it and temporarily install the appropriate version.  Note that Strawberry Perl 5.12+ provides a mechanism to switch between versions without uninstalling.

2. **Perl Modules**

	Additional modules must be installed into the Perl distribution used to build the installer:

	* MP3::Info (1.13)    - Used in localfiles plugin
	* MP3::Tag (1.24)     - Used to enhance MP3 tagging
	* PAR::Packer (1.010) - Used to build installer

	The modules may be installed with the CPAN client provided by Strawberry Perl.

3. **NSIS**

	Source: <http://nsis.sourceforge.net>

	Version: 2.46

	Select the **Full** installation option to install all components.

4. **NSIS Plugins**

	Source: <http://nsis.sourceforge.net/Category:Plugins>

	The installer requires the following additional NSIS plugins:

	* Inetc
	* Locate
	* Nsis7z
	* ZipDLL

	Information on installing NSIS plugins:
	<http://nsis.sourceforge.net/How_can_I_install_a_plugin>

5. **7-Zip**

	Source:  <http://www.7-zip.org>

	Version: 9.20 (select 32-bit .exe installer)

	The installer build scripts use the command-line interface to 7-Zip to compress/expand archive files.  However, it is not necessary to install the separate statically-linked version of the 7-Zip (7za.exe).  The GUI version has its own command-line interface.

### Build Setup

In the instructions below, replace with `C:\installer` with an appropriate location for your system

1. **Download get_player Source**

	This can be a clone of the infradead git repository (<http://git.infradead.org/get_iplayer.git>) or a downloaded snapshot.

	Location: `C:\installer\get_player`

2. **Check Build Scripts**

	The files below should be in `C:\installer\get_player\windows`:

	* `get_iplayer_setup.nsi` - NSIS installer script
	* `make-init.cmd`         - Common initialisation code for other scripts
	* `make-installer.cmd`    - Main installer build script (calls make-perlfiles.cmd)
	* `make-perlfiles.cmd`    - Builds archive of Perl support files for installer
	* `make-perltgz.cmd`      - Create archive of Perl support files as tarball

	There are other files in that directory, but they are primarily of use in development and testing of the installer and are not necessary to perform the default build.  See the [Developer Notes](#devnotes) and [Manifest](#manifest) below.

3. **Check Build Configuration**

	The script `make-init.cmd` sets the locations of Strawberry Perl, NSIS, and 7-Zip used for the build.  Edit the relevant values if necessary.

4. **Check Installer Version**

	If you are building a new installer to incorporate changes in `get_iplayer` or the installer script, be sure that the installer version number has been incremented.  The installer version number can be found in the `!define VERSION` statement near the top of `get_iplayer_setup.nsi`.

5. **Create Build Folder**

	Create an empty folder to use for building the installer:

	`C:\>MKDIR C:\installer\build`

### Installer Build

1. Open a command prompt and make the build folder the current directory

	`C:\>CD C:\installer\build`

	The installer may be built in any directory, but the build folder must be the current directory for your command prompt.

2. Run the installer build script

	`C:\installer\build>C:\installer\get_iplayer\windows\make-installer`

    The build script creates 4 files in the build directory:

	* `get_iplayer_setup_4.3.exe` - `get_player` installer application
	* `perlfiles.zip`             - Archive of Perl support files included in the installer
	* `perlpar.exe`               - PAR (Perl ARchive) file used to create perlfiles.zip
	* `make-installer.log`        - Log of output from build script

	In the event of an error, the temporary folder used by the script (`make-installer.tmp`) will remain in the build directory.

3. There is no step 3.  For deployment information, see [Deployment Notes](#deploy) below.
    
#### Build Notes

* `perlfiles.zip` will contain the Perl core libraries (as determined by PAR::Packer), plus the additional modules specified above.  However, `make-perlfiles.cmd` strips some large files from the "unicore" package in order to save space.  These files are input and test files for generation of Unicode character tables and are not required for `get_iplayer`.

* Subsequent invocations of `make-installer.cmd` will use an existing `perlfiles.zip` if it is found in the current directory.  To force the Perl support archive to be completely rebuilt, add `/makeperl` to the command:

	`C:\installer\build>C:\installer\get_iplayer\windows\make-installer /makeperl`

* `perlfiles.zip` must be generated in Windows in order for the proper Win32 modules to be included in the archive.  However, the archive may be used to build the installer on Linux/OSX (see below).  To that end, a separate script (`make-perlfiles.cmd`) may be used to generate only the Perl support archive.  It is also invoked by `make-installer.cmd` to build the archive.

* Subsequent invocations of `make-perlfiles.cmd` will use an existing `perlpar.exe` if it is found in the current directory.  To force the Perl support archive to be complete rebuilt, add `/makepar` to the command:

	`C:\installer\build>C:\installer\get_iplayer\windows\make-perlfiles /makepar`

	Invoking `make-installer.cmd` with `/makeperl` will have the same effect.

	In the event of an error, the temporary folder used by the script (`make-perlfiles.tmp`) will remain in the build directory.

* See the [Script Reference](#scriptref) below for a full list of command-line options accepted by `make-installer.cmd` and `make-perlfiles.cmd`.

#### Linux/OSX

* A shell script (`get_iplayer/make-nsis.sh`) was written to build the `get_iplayer` Windows installer on Linux/OSX.  However, since tarball (.tar.gz) support is the de facto standard for Unix-based systems, the shell script expects to find the Perl support archive in that form.  If you should need to build the installer on Linux/OSX, you can create the tarball in Windows and transfer it to the other system.  After building the Perl support archive (see above), execute an additional script:

	`C:\installer\build>C:\installer\get_iplayer\windows\make-perltgz`

	The script creates `perlfiles.zip` in the current directory (if necessary) and copies its contents to `perlfiles.tar.gz`.

* Building the installer on Linux/OSX is similar to building in Windows.  Assuming that you have the `get_iplayer` source in `$HOME/installer/get_iplayer` and are using `$HOME/installer/build` as your build folder:

	1. Copy `perlfiles.tar.gz` into the build folder

        `$ cp /path/to/perlfiles.tar.gz $HOME/installer/build`

	2. Make the build folder your current directory:

        `$ cd $HOME/installer/build`

	3. Execute the build script:

        `$ $HOME/installer/get_iplayer/make-nsis.sh`

	The installer application will be copied into the current directory.  As in Windows, the installer may be built in any folder, but the build folder must be the current directory for your shell.

<a id="deploy"/> 
## Deployment Notes

### Download Location

The installer application is deployed in the directory corresponding to `http://www.infradead.org/get_iplayer_win`.  The following steps are necessary to deploy a new installer (with placeholders for actual directory paths):

1. Make deployment directory current

    `$ cd $WEBROOT/get_iplayer_win`

2. Copy the installer application (e.g., `get_iplayer_setup_4.3.exe`) into the directory

    `$ cp $BUILDPATH/get_iplayer_setup_4.3.exe .`

    **NOTE:** For installers version 4.2 and earlier, the application MUST be named in the form `get_iplayer_setup_N.N.exe` in order that it can be downloaded by those earlier installers.  Versions 4.3+ will download new installers via the symbolic link (below)

3. Update the `get_iplayer_setup_latest.exe` symbolic link to refer to the new installer

    `$ ln -sf get_iplayer_setup_4.3.exe get_iplayer_setup_latest.exe`

4. Update the contents of the installer version file with the new version (e.g. 4.3)

    `$ echo -n "4.3" > VERSION-get_iplayer-win-installer`
   
    **NOTE:** For installers version 4.2 and earlier, the version file MUST NOT contain a trailing newline character after the version number (thus the `-n` option for `echo`).  A trailing newline character will break the installer update mechanism.  This is fixed in versions 4.3+.

### Configuration File

By default, the installer employs a configuration file (INI format) to retrieve the download URLs for the various helper applications.  The configuration file is downloaded whenever the installer is executed in order to look for updates.  If the configuration file cannot be retrieved, the version built into the installer will be used (though it may be out of date).

The configuration file is named `get_iplayer_config.ini` and is found in the **windows** directory of the `get_iplayer` Git repository along with the other installer-related files.  The script is deployed in the directory corresponding to `http://www.infradead.org/get_iplayer_win/`.  Deployment is performed as follows (with placeholders for actual directory paths):

1. Make deployment directory current

    `$ cd $WEBROOT/get_iplayer_win`

2. Copy the latest version of the configuration file into the directory  

    `$ cp $SOURCEPATH/get_iplayer_config.ini get_iplayer_config_20110828.ini`

    **NOTE:** Use a file name in the form `get_iplayer_config_YYYYMMDD.ini` to distinguish the new version from previous versions.
    
3. Update the `get_iplayer_config_latest.ini` symbolic link to refer to the new configuration file.

    `$ ln -sf get_iplayer_config_20110828.ini get_iplayer_config_latest.ini`

The configuration file only needs to be changed when the release version and/or download URL for a helper application changes.  The user will only receive an update notice in the installer if the version string changes.  See the [Auxiliary Files Reference](#auxref) below.

### CGI Script

Prior to version 4.3, the installer required the assistance of a CGI script to retrieve the download URLs for the various helper applications.  The CGI script would be accessed by the installer for every helper application selected for installation.  The former behaviour can be restored if the installer is built with /NOCONFIG (see [Useful Options](#useful) below). 

The CGI script is named `get_iplayer_setup.cgi` and is found in the **windows** directory of the `get_iplayer` Git repository along with the other installer-related files.  The script is deployed in the directory corresponding to `http://www.infradead.org/cgi-bin/`.  Deployment is performed as follows (with placeholders for actual directory paths):

1. Make deployment directory current

    `$ cd $WEBROOT/cgi-bin`

2. Back up the existing CGI script

    `$ cp get_iplayer_setup.cgi get_iplayer_setup_20110828.cgi`

    **NOTE:** Use a file name in the form `get_iplayer_config_YYYYMMDD.ini` to distinguish the backup from previous backups.

3. Copy the latest version of the CGI script into the directory

    `$ cp $SOURCEPATH/get_iplayer_setup.cgi .`

    **NOTE:** Installer version 4.2 and below used a CGI script named `get_iplayer.cgi`.  Versions 4.3+ will expect the script, if deployed, to be named `get_iplayer_setup.cgi`.

The CGI script only needs to be changed when the download URL for a helper application changes.  See the [Auxiliary Files Reference](#auxref) below.

<a id="devnotes"/>
## Developer Notes

The notes below provide additional information relevant to working with the installer as a developer.  This discussion uses the example directory structure described above.

### Preparation

#### Expand Perl Support Archive

The installer script requires an expanded version of the Perl support archive (`perlfiles.zip`) in the build directory.  `make-installer.cmd` creates a temporary expanded archive, but for development work you should create a permanent version.  You can expand it using 7-Zip, or you can use `make-perlfiles`:

`C:\installer\build>C:\installer\get_iplayer\windows\make-perlfiles /expand`

In either case, the expanded archive should now be in `C:\installer\build\perlfiles`.

#### Using Git

Any changes to the installer source or build scripts should ultimately be propagated to the Git repository at infradead.org.  If you are developing on Windows, `msysgit` (<http://code.google.com/p/msysgit/>) is a good option for Git-based development workflows.  Useful installation instructions can be found here: [Git for Windows Developers](http://lostechies.com/jasonmeridth/2009/06/01/git-for-windows-developers-git-series-part-1/).

### MakeNSISW

Although the scripts described above may be used to build the installer during development, it is easier to use the *MakeNSISW* utility provided with NSIS.  To launch *MakeNSISW*, Open the "NSIS Menu" application via "NSIS" on the Start menu, then select "Compile NSI Scripts".

#### Build Configuration

The compilation of the installer script is controlled by global symbols defined by **/D** options for the *makensis.exe* command line (see script reference below) or in the *MakeNSISW* settings dialog - see the NSIS documentation.  The most important options are those that determine the location of files used in the build process:

* `BUILDPATH`  - Location for compiled installer application (`C:\installer\build`)
* `SOURCEPATH` - Location of `get_iplayer` source distribution (`C:\installer\get_iplayer`)
* `PERLFILES`  - Location of expanded Perl support archive (default = `${BUILDPATH}\perlfiles`, but may be overridden)

Invoke the *MakeNSISW* Settings dialog via "Tools->Settings" (Ctrl+S).  Enter the values for `BUILDPATH` and `SOURCEPATH` described above.  The settings will persist through multiple invocations of *MakeNSISW*.  Note that you can create sets of options that may be saved and reloaded.

### Compiling

You can open `get_iplayer_setup.nsi` via "File->Load Script..." (Ctrl+L).  There is also an option in the Windows Explorer context (right click) menu for `.nsi` files named "Compile NSIS Script", which will open and compile the script in *MakeNSISW*.  Once opened, the installer script can be compiled and tested from within *MakeNSISW* via the commands on the "Script" menu.

### Esoterica

<a id="useful"/>
#### Useful Options

There are a number of options available to compile the installer script in different configurations:

* `WITHOUTPERL`   - This option omits the Perl support archive from the installer.  If your development machine has a fully-working Perl installation, it isn't necessary to include the Perl support archive in development builds (`get_iplayer` will use the system Perl).
* `WITHSCRIPTS`   - This option will embed `get_iplayer.pl`, `get_iplayer.cgi`, and `plugins` into the installer and will prevent those files from being downloaded or updated from infradead.org.  This is useful for working with updated versions of those scripts that have not yet been released.
* `NOCONFIG`      - Reverts to use of CGI script to retrieve helper application download URLs
* `NOCHECK`       - This option will prevent the online check for a new installer version.  The online check is usually unnecessary during development.
* `PRERELEASE`    - Configures a warning dialog that pops up when the installer runs telling the user that he is using a pre-release build of the installer.

#### Standalone Build

Additional options are available to create a "standalone" build of the installer.  Standalone builds have all dependencies embedded within the installer and do not download or update them from infradead.org.  These builds are intended to model a unitary installer that could be distributed without the need for external sources of dependencies.  Standalone builds are useful in working with portions of the installer related to the unpacking and configuration of helper applications since they don't incur the overhead of downloading archive files at run-time.  However, the compile time is longer and the resulting installer is much larger due to the inclusion of the helper application archives.

* `STANDALONE`  - This option is a synonym for `WITHSCRIPTS` and `WITHHELPERS`
* `WITHHELPERS` - This option will embed archived versions of all `get_iplayer` helper applications into the installer (see below).
* `HELPERS`     - Location of helper application archives (default = `${BUILDPATH}\helpers`, but may be overridden).

**Helper Applications**

The contents of `${HELPERS}` must be as follows:

* AtomicParsley.zip
* FFmpeg.zip
* LAME.zip
* MPlayer.zip
* RTMPDump.zip
* VLC.zip

Note that all files use the short name for the application (without version strings).  Note also that all the archives MUST have ".zip" as the file extension regardless of whether the file is in PKZIP, 7-Zip, or EXE format.  This scheme follows the way archives are named when downloaded by the installer.  The installer won't necessarily know if a downloaded file is in PKZIP, 7-ZIP, or EXE format, so ".zip" was adopted as the extension most likely to be useful in working with the files in Windows Explorer.  The installer doesn't need to know the file format beforehand - it will try all three.

The `${HELPERS}` folder may be populated using a script:

`C:\installer\build>C:\installer\get_iplayer\windows\make-helpers`

This script will compile and run a small NSIS installer application that allows you to select a target folder and then downloads all the helper application archives into that folder and names them appropriately.  The default location used is `helpers` in the build folder (`C:\installer\build\helpers`).  The source for the NSIS application can be found in `C:\installer\get_iplayer\windows\make-helpers.nsi`.  The download URLs are embedded in the source, so they should be updated to match the URLs in `get_iplayer_config.ini` if required.

#### Build Script Options

All of the NSIS options described above may also be specified on the `make-installer.cmd` command line.  For example, adding the `/withscripts` parameter to the command line will translate into `/Dwithscripts` being added the the `makensis.exe` command line used in building the installer.  For the full list, see the script reference below.

<a id="scriptref"/>
## Script Reference

As a reference for available parameters, the help screens for all build scripts are shown below.

### make-installer

    Generate NSIS installer for get_iplayer

    Usage:
      make-installer [/keeptmp] [/makeperl] [/withoutperl]
        [/withscripts] [/withhelpers] [/standalone]
        [/offline] [/prelease] [\path\to\perlfiles.zip]
      make-installer /? - this message

    Parameters:
      /keeptmp       - retain contents of temp directory
      /makeperl      - force rebuild of Perl support archive
      /withoutperl   - omit Perl support from build
      /withscripts   - embed get_iplayer Perl scripts in build
      /withhelpers   - embed get_iplayer helper apps in build
      /standalone    - /withscripts + /withhelpers
      /noconfig      - use CGI script for download URLs instead of config file
      /nocheck       - no installer update check (testing only)
      /prerelease    - prerelease build with warning dialog at launch

    Input (in current directory):
      perlfiles     - expanded Perl support archive
      OR (if expanded archive not found):
      perlfiles.zip - Perl support archive file [output from make-perlfiles]
        (override by specifying Perl archive file on command line)
      helpers       - folder with helper app archives (/withhelpers only)

    Output (in current directory):
      get_iplayer_setup_N.N.exe - installer EXE
        (N.N = installer version)

### make-perlfiles

    Generate archive of Perl support files for get_iplayer

    Usage:
      make-perlfiles [/keeptmp] [/makepar] [/expand] [\path\to\perlpar.exe]
      make-perlfiles /? - this message

    Parameters:
      /keeptmp - retain contents of temp directory upon completion
      /makepar - force rebuild of PAR file (re-run pp)
      /expand  - expand Perl support archive in current directory

    Input/Output (in current directory):
      perlpar.exe - PAR file [output from pp]
        (override by specifying PAR file on command line)

    Output (in current directory):
      perlfiles.zip - Perl support archive

    Required Perl modules (install from CPAN):
      MP3::Info   - localfiles plugin
      MP3::Tag    - MP3 tagging
      PAR::Packer - archive creation

### make-perltgz

    Generate tarball of Perl support archive (to build installer on Linux/OSX)

    Usage:
      make-perltgz [/keeptmp] [/makeperl] [\path\to\perlfiles.zip]
      make-perltgz /? - this message

    Parameters:
      /keeptmp  - retain contents of temp directory
      /makeperl - force rebuild of Perl support archive

    Input (in current directory):
      perlfiles     - expanded Perl support archive
      OR (if expanded archive not found):
      perlfiles.zip - Perl support archive file [output from make-perlfiles]
        (override by specifying Perl archive file on command line)

    Output (in current directory):
      perlfiles.tar.gz - Perl support tarball

### make-helpers

    Generate and run NSIS installer to download get_iplayer helper applications

    Usage:
      make-helpers [/rebuild]
      make-helpers /? - this message

    Parameters:
      /rebuild - force rebuild of installer

<a id="auxref"/>
## Auxiliary Files Reference

### Configuration File

The cofinguration file is in INI format, with a section defined for each of the `get_iplayer` helper applications, with the short name of the application used as the section name.  Within each section are 3 values:

* `version` - Version string (required)
* `url`     - Download URL (required)
* `doc`     - Documentation URL (optional)

Version strings must be changed in order for the installer to show an update notice to the user.  Version strings generally should reflect the release numbering used by the developers of the helper applications.  However, the version string can have any value.  So long as it is different from the installed version (or the application is not installed), the user will be notified.  This may be useful if a download file is changed by the developer without changing the associated version number.  For example, AtomicParsley's version string in the configuration might be changed from from "0.9.4" to "0.9.4-reinstall1" to signal the user that it should be re-installed, even though it is still at version 0.9.4.

Example of `get_iplayer_config.ini`:

    [MPlayer]
    version=1.0-rc2
    url=http://www8.mplayerhq.hu/MPlayer/releases/win32/MPlayer-mingw32-1.0rc2.zip
    doc=http://www.mplayerhq.hu/DOCS/HTML/en/index.html
    [LAME]
    version=3.98.4
    url=http://www.exe64.com/mirror/rarewares/lame3.98.4.zip
    doc=http://lame.sourceforge.net/using.php
    [FFmpeg]
    version=0.8
    url=http://ffmpeg.zeranoe.com/builds/win32/static/ffmpeg-0.8-win32-static.7z
    doc=http://ffmpeg.org/ffmpeg-doc.html
    [VLC]
    version=1.1.11
    url=http://www.grangefields.co.uk/mirrors/videolan/vlc/1.1.11/win32/vlc-1.1.11-win32.7z
    doc=http://wiki.videolan.org/Documentation:Documentation
    [RTMPDump]
    Version=2.4
    url=http://rtmpdump.mplayerhq.hu/download/rtmpdump-20110723-git-b627335-win32.zip
    doc=http://rtmpdump.mplayerhq.hu/
    [AtomicParsley]
    version=0.9.4
    url=http://bitbucket.org/jonhedgerows/atomicparsley/downloads/AtomicParsley-0.9.4.zip
    doc=http://atomicparsley.sourceforge.net/

### CGI Script

The CGI file is a UNIX shell script that responds to a fixed set of query string values by redirecting the requesting application to the download URL for the corresponding helper application.

Example of `get_iplayer_setup.cgi`:

    #!/bin/sh

    # CGI script to support get_iplayer Windows installer
    # Redirects to download URLs for Win32 helper applications
    # corresponding to pre-defined keys passed as query string.
    # This script must be available at:
    #   http://www.infradead.org/cgi-bin/get_iplayer_setup.cgi
    # Example:
    #   Request : http://www.infradead.org/cgi-bin/get_iplayer_setup.cgi?lame
    #   Redirect: http://www.exe64.com/mirror/rarewares/lame3.98.4.zip

    TARGET=

    case "$QUERY_STRING" in
        mplayer)
            TARGET="http://www8.mplayerhq.hu/MPlayer/releases/win32/MPlayer-mingw32-1.0rc2.zip"
        ;;
        lame)
            TARGET="http://www.exe64.com/mirror/rarewares/lame3.98.4.zip"
        ;;
        ffmpeg)
            TARGET="http://ffmpeg.zeranoe.com/builds/win32/static/ffmpeg-0.8-win32-static.7z"
        ;;
        vlc)
            TARGET="http://www.grangefields.co.uk/mirrors/videolan/vlc/1.1.11/win32/vlc-1.1.11-win32.7z"
        ;;
        rtmpdump)
            TARGET="http://rtmpdump.mplayerhq.hu/download/rtmpdump-20110723-git-b627335-win32.zip"
        ;;
        atomicparsley)
            TARGET="http://bitbucket.org/jonhedgerows/atomicparsley/downloads/AtomicParsley-0.9.4.zip"
        ;;
    esac

    if [ "$TARGET" == "" ]; then
        cat <<EOF
    Content-Type: text/html

    <HTML><TITLE>Error</TITLE></HEAD>
    <BODY><H1>Error</H1>
    You requested '$QUERY_STRING' but that isn't one of the known downloads.
    EOF
    fi

    cat <<EOF
    Location: $TARGET
    Content-Type: text/plain

    Redirecting to $TARGET
    EOF

<a id="manifest"/>
## Manifest

Below is a complete list of installer-related files located in the **windows** directory of the `get_iplayer` Git repository.

* `INSTALLER.md`           - This document (Markdown format)
* `get_iplayer_config.ini` - Configuration file for installer
* `get_iplayer_setup.cgi`  - CGI script for installer
* `get_iplayer_setup.nsi`  - NSIS installer script
* `make_helpers.cmd`       - Builds and runs `make_helpers.nsi`
* `make_helpers.nsi`       - NSIS application to download helper apps for testing
* `make-init.cmd`          - Common initialisation code for other scripts
* `make-installer.cmd`     - Main installer build script (calls make-perlfiles.cmd)
* `make-perlfiles.cmd`     - Builds archive of Perl support files for installer
* `make-perltgz.cmd`       - Create archive of Perl support files as tarball
