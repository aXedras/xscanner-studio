#!/usr/bin/env node

const line = (text) => {
  process.stdout.write(`${text}\n`);
};

line("xScanner Studio npm scripts");
line("");
line("Main targets (each has its own help):");
line("  npm run check   # check targets (fast/all)");
line("  npm run test    # test targets (unit/integration/watch)");
line("  npm run i18n    # i18n targets");
line("  npm run db      # DB types targets");
line("");
line("Core:");
line("  npm run dev");
line("  npm run build");
