#!/usr/bin/env node

console.log(`
📚 i18n Validation Commands
════════════════════════════════════════════════════════════════

Available commands:

  npm run check:i18n              Show this help
  npm run check:i18n:all          Run all i18n checks
  npm run check:i18n:missing      Check for missing translation keys
  npm run check:i18n:unused       Check for unused translation keys

Individual validators (part of check:i18n:all):

  • check-i18n.mjs                Main validator
    - Validates translation file structure
    - Checks for missing keys between de/en
    - Validates string types
    - Checks for empty values
    - Validates interpolation placeholders
    - Enforces strict override rules

  • check-missing.mjs             Find keys used in code but not defined
    - Scans src/ directory for t() calls
    - Reports undefined translation keys
    - Expands plural forms automatically

  • check-unused.mjs              Find defined but unused keys
    - Identifies dead translation keys
    - Helps keep translation files clean
    - Respects common.* override patterns

════════════════════════════════════════════════════════════════
For pre-commit: Use 'npm run check:i18n:all'
Documentation: See /docs/studio/PRE_COMMIT.md
════════════════════════════════════════════════════════════════
`);
