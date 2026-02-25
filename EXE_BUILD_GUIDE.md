"""
CHANGSHENG EXECUTABLE BUILD GUIDE
==================================

Date Built: February 24, 2026
Executable Size: ~40.4 MB (includes Python runtime + all dependencies)
Build Tool: PyInstaller 6.19.0

## QUICK START

To run the application without Python installed:

1. Navigate to the dist folder:
   c:\Users\Henry\projects\changsheng\dist\

2. Double-click changsheng.exe

3. Application launches immediately (first run may take a few seconds)

## WHAT'S INCLUDED

The changsheng.exe file is a STANDALONE EXECUTABLE containing:

✓ Python 3.9 runtime
✓ Tkinter GUI framework
✓ SQLite3 database engine
✓ OpenPyXL (Excel export)
✓ ReportLab (PDF generation)
✓ All application modules:
  - error_handler (centralized error handling)
  - ui_actions (36 protected UI functions)
  - database_service (database operations)
  - validation (input validation)
  - billing_date_utils (date arithmetic)
  - invoice_generator (invoice logic)
  - language_map (English/Chinese translations)
  - And all other dependencies

## BUILD ARCHITECTURE

The build process:

1. **Source Code Analysis**
   - Scans changsheng.py for imports
   - Identifies all required modules
   - Analyzes dependencies

2. **Dependency Resolution**
   - Collects all standard library modules
   - Includes third-party packages (sqlite3, tkinter, etc.)
   - Processes module hooks for special cases

3. **Binary Compilation**
   - Compiles Python bytecode to binary
   - Creates archive with all dependencies
   - Embeds Python runtime

4. **Executable Creation**
   - Wraps everything in Windows executable
   - No console window (GUI app)
   - Single-file distribution

## BUILD CONFIGURATION

File: changsheng.spec

Configurable options:
- Hidden imports: Explicitly included modules
- Data files: Resources to bundle
- Icon: Application icon (optional)
- Console mode: Hidden by default
- UPX compression: Enabled (reduces size)

### Key Settings Explained

```python
hidden_imports = [
    'tkinter',           # GUI framework
    'sqlite3',          # Database
    'json', 'csv',      # Data formats
    'logging',          # Error logging
    'openpyxl',         # Excel export (optional)
]

console=False           # Hides console window
strip=False            # Keeps debugging symbols
upx=True               # Compresses executable
```

## FILE STRUCTURE

After build, the dist folder contains:

dist/
├── changsheng.exe          (40.4 MB - Standalone executable with all dependencies bundled)
└── README.txt              (User guide)

**Important:** changsheng.exe is completely self-contained. All required libraries
(Python runtime, Tkinter, SQLite, etc.) are embedded inside the single executable file.

No additional folders or files are needed to run the application!

## DEPLOYMENT

### For an Individual User:

1. Copy changsheng.exe to desired location (Desktop, Program Files, etc.)
2. Create shortcut if desired
3. Done! App is ready to use

No additional files or folders needed!

Recommended location:
```
C:\Users\Public\Desktop\changsheng.exe
Or: C:\Program Files\Changsheng\changsheng.exe
```

### For Enterprise Deployment:

1. Create installer using NSIS or similar (optional - EXE can be distributed directly)
2. Copy changsheng.exe to deployment location
3. Create shortcuts or registry entries if needed
4. Deploy via Group Policy, App Store, or network share

Advantages of single-file executable:
✓ Easy to move or copy anywhere
✓ No dependencies required
✓ Simple backup (single file)
✓ Easy to create portable USB version
✓ Perfect for network shares

### First Run

- First launch initializes database (few seconds)
- Creates changsheng.db in user's home directory
- Subsequent launches are instant

## DATABASE LOCATION

The application stores its database file in:

Windows 10/11:
  C:\Users\{YourUsername}\changsheng.db

This location is:
✓ User-specific (each user has their own data)
✓ Accessible for backups
✓ Persists between app updates
✓ Safe from accidental deletion

## TROUBLESHOOTING

### "Cannot find python39.dll" or ImportError
- This should NOT occur with the single-file executable
- If seen, reinstall changsheng.exe from original source
- Check that changsheng.exe file is intact (40.4 MB)

### Application won't start
- Check Windows Defender/antivirus - may quarantine on first run
- Add changsheng.exe to antivirus whitelist
- Run as Administrator if UAC issues occur
- Check Event Viewer for error details
- Ensure you have write permission to C:\Users\{YourUsername}\

### "Database locked" error
- Don't run multiple instances simultaneously
- Ensure previous instance closed properly
- Delete db.lock file if stuck

### Database file not found
- App creates it automatically on first run
- Grant write permissions to folder
- Check user folder: C:\Users\{YourUsername}\

## PERFORMANCE

After build, the executable:
- Launches in 1-2 seconds (cold start)
- ~40.4 MB file size (includes Python runtime)
- No external dependencies required
- Runs on Windows 10/11 (64-bit)

## REBUILDING THE EXECUTABLE

If you modify the source code, rebuild with:

```powershell
cd c:\Users\Henry\projects\changsheng
python -m PyInstaller changsheng.spec --distpath dist --workpath build -y
```

This will:
1. Clean previous build (with -y flag)
2. Recompile all modules
3. Create new changsheng.exe
4. Preserve database (not affected)

Build time: ~20-30 seconds on modern hardware

## SECURITY NOTES

The executable:
- Contains all source code (embedded in bytecode)
- Can be decompiled (Python bytecode reverse-engineering exists)
- Should not be the sole protection for sensitive algorithms
- Is not obfuscated (Cython or similar for sensitive parts if needed)

To add extra security:
- Use code signing certificate
- Encrypt the database file
- Add licensing/activation checks
- Consider commercial obfuscation tools

## VERSION UPDATES

For each new release:

1. Update version in changsheng.py (if versioning added)
2. Rebuild executable: `python -m PyInstaller changsheng.spec -y`
3. Test on clean Windows system (if possible)
4. Create changelog
5. Deploy to users

## UNINSTALLATION

To uninstall:

1. Delete changsheng.exe and _internal folder
2. Delete shortcut from Desktop/Start Menu
3. Optional: Delete C:\Users\{YourUsername}\changsheng.db if not keeping data

No registry entries or leftover files.

## ADVANCED CUSTOMIZATION

### Add Application Icon

1. Create or obtain .ico file (recommended: 256x256)
2. Place in project root directory
3. Update changsheng.spec:
   ```python
   icon='changsheng.ico'
   ```
4. Rebuild: `python -m PyInstaller changsheng.spec -y`

### Add Version Information

1. Use VersionInfo tool or similar
2. Create version resource file
3. Update spec file
4. Rebuild executable

### Single-Directory Distribution

Instead of single .exe file, create directory with:

```python
# Uncomment in changsheng.spec
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='changsheng',
)
```

Results in folder of files instead of single exe (easier to distribute updates).

## TROUBLESHOOTING BUILD ISSUES

### Hidden import warnings
```
WARNING: Hidden import "tzdata" not found!
```
- Harmless - optional timezone data
- Add to spec if needed:
  ```python
  hidden_imports.append('tzdata')
  ```

### Module not found
- Add to hidden_imports list in changsheng.spec
- Example:
  ```python
  hidden_imports.append('your_module_name')
  ```

### Build fails with "PermissionError"
- Close any file explorer windows showing dist/ folder
- Restart PowerShell/terminal
- Run as Administrator

### Executable too large
- Remove unnecessary dependencies from spec
- Exclude unused standard library modules
- Consider splitting into multiple files

## BEST PRACTICES

✓ Always test on clean system before deployment
✓ Keep source code and .spec file in version control
✓ Back up dist folder before rebuilding
✓ Test database creation and operations
✓ Verify all UI features work in executable
✓ Check error handling displays correctly
✓ Test on different Windows versions if possible
✓ Include README for end users

## SUPPORT

If issues occur:

1. Check error logs:
   - Windows Event Viewer
   - Application logs if configured

2. Rebuild from scratch:
   ```powershell
   rm -r dist, build
   python -m PyInstaller changsheng.spec -y
   ```

3. Test with Python directly:
   ```powershell
   python changsheng.py
   ```
   (To isolate exe vs. Python issues)

## FUTURE IMPROVEMENTS

✓ Add application version display
✓ Implement automatic update checking
✓ Add crash dump logging
✓ Create Windows installer (.msi)
✓ Code signing with certificate
✓ Create portable USB version
✓ Add system tray icon
✓ Create uninstaller

---

**Build Date:** 2026-02-24
**PyInstaller Version:** 6.19.0
**Python Version:** 3.9.6
**Status:** Production Ready ✅
"""
