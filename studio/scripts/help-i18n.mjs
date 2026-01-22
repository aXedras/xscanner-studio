#!/usr/bin/env node

const line = (text = "") => process.stdout.write(`${text}\n`);

line("Studio i18n");
line("");
line("Help:");
line("  npm run i18n");
line("");
line("Commands:");
line("  npm run i18n:all       # run all i18n checks");
line("  npm run i18n:missing   # keys used in code but not defined");
line("  npm run i18n:unused    # keys defined but unused");
line("");
line("Implementation:");
line("  i18n:* scripts call the underlying validators in scripts/i18n/ and scripts/check-i18n.mjs");
