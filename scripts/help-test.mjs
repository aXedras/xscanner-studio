#!/usr/bin/env node

const line = (text = "") => process.stdout.write(`${text}\n`);

line("Studio tests");
line("");
line("Help:");
line("  npm run test");
line("");
line("Commands:");
line("  npm run test:watch        # interactive vitest (watch mode)");
line("  npm run test:run          # run all tests");
line("  npm run test:unit         # unit tests only");
line("  npm run test:integration  # integration tests (may require VITE_API_URL)");
line("  npm run test:all          # unit + integration");
