# Windows Scripts

This directory contains Windows-specific `.bat` scripts.

## Purpose

- **Platform Independence**: Allow Windows developers to use the same `make` commands as Mac/Linux users
- **Clean Separation**: Keep Windows-specific code separate from Unix scripts
- **Automatic Detection**: Makefile automatically uses Windows scripts on Windows platforms

## Structure

- `development/` - Local dev scripts
- `preprod/` - Pre-prod deploy scripts

## Usage

These scripts are meant to be run directly on Windows machines (e.g. a Windows VM for pre-prod).

## Maintenance

When adding new `.sh` scripts, create equivalent `.bat` scripts here if you need Windows-native execution.
