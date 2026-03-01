#!/usr/bin/env node

const line = (text = "") => process.stdout.write(`${text}\n`);

line("Studio checks");
line("");
line("Help:");
line("  npm run check");
line("");
line("Fast (no API server / no Supabase required):");
line("  npm run check:fast      # architecture guard + eslint + type-check + unit tests");
line("");
line("Quality gate (still no API server required):");
line("  npm run check:all       # format + architecture guard + lint + types + i18n + db types + build + unit tests");
line("");
line("Integration tests (requires API server for real HTTP):");
line("  VITE_API_URL=http://127.0.0.1:8000 npm run test:integration");
line("");
line("Related:");
line("  npm run i18n            # i18n help");
line("  npm run i18n:all        # run all i18n checks");
line("  npm run db              # DB types help");
