# Windows Scripts

This directory contains Windows-specific `.bat` scripts that mirror the functionality of the Unix `.sh` scripts in the parent `scripts/` directory.

## Purpose

- **Platform Independence**: Allow Windows developers to use the same `make` commands as Mac/Linux users
- **Clean Separation**: Keep Windows-specific code separate from Unix scripts
- **Automatic Detection**: Makefile automatically uses Windows scripts on Windows platforms

## Available Scripts

- `start-server.bat` - Start FastAPI backend server (mirrors `start-server.sh`)

## Usage

These scripts are automatically used by the Makefile when running on Windows:

```powershell
# These commands will use the .bat scripts on Windows:
make start-server
make start-all
```

## Maintenance

When adding new `.sh` scripts, create equivalent `.bat` scripts here to maintain Windows compatibility.
