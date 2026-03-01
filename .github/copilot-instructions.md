## Quick orientation for AI coding agents

This file contains focused, discoverable knowledge to help an AI agent be productive in the xscanner-studio repo.

### Project Structure (CRITICAL)

**xscanner-studio is a dedicated frontend repository:**

- **Studio** (React/Vite) - Admin UI frontend
  - Code: `/src/`, `/tests/`
  - Docs: `/docs/studio/`
  - Tech: TypeScript, React, Vite, Tailwind CSS, Supabase

### Communication and Documentation Style (CRITICAL)

**ALWAYS follow these language rules:**

- ✅ User communication: **German, informal "Du" form** (e.g., "Verstanden!", "Ich erstelle...", "Brauchst du...?")
- ✅ Code documentation: **English** (docstrings, comments, README files)
- ✅ Commit messages: **English** (conventional commits format)
- ✅ Technical docs: **English** (architecture docs, API specs)
- ❌ NEVER mix languages inappropriately (German code comments, English user responses)


### Commit Message Quality (CRITICAL)

**Commit messages must include a meaningful body when the change isn't trivial.**

- Subject line: Conventional Commits (`type(scope): summary`) in **imperative mood**.
- Body: short bullet list that captures **why** and **what changed** (not a file list).
- Include **testing** info when relevant (e.g. `npm run lint`, `npm run test:unit`).

**Template:**

```
feat(scope): short summary

- Why: <problem / motivation>
- What: <behavior change / key decisions>
- Tests: <commands>
```


**After implementing a feature:**

> Run build, lint, and tests to ensure everything works.
> Ask to update documentation:
> - Studio work: "Soll ich die Dokumentation in `/docs/studio/[FILE].md` aktualisieren?"

## Critical Rules (Non-Negotiable)

❌ **Never do this:**

- no dead code accepted
- no duplicate code accepted (DRY violation)
- Files > 300 lines have to be refactored
- no fallbacks that hide root errors
- do not overengineer (YAGNI)
- do especially not overengineer on non functional requirements
- do not implement features that aren't currently needed (YAGNI)
- do not add complexity without clear benefit and tell the user clearly
- you do never commit on your own decision
- do never commit temporary files or debug code
- **NEVER COMMIT OR PUSH WHEN TESTS ARE FAILING** - zero tolerance for broken tests. Forget the noVerify flag - all checks must pass

✅ **Always do this:**

- be simple
- be pragmatic
- use professional software engineering best practices
- Follow SOLID principles
- Follow clean code principles
- Write high-signal docstrings/JSDoc for classes and public APIs (purpose, invariants, error semantics)
- Prepare an implementation plan and discuss it with the user before starting implementation
- Always: **Ask if you are unsure**
