# Site update plan — English

## What's wrong

**Hero**
- Typo: "Research tookit"
- Description still frames the product as Zotero-for-agents with search/fetch as core features — both are now plugins; the knowledge layer is missing entirely
- Differentiator row "Share a library with a research community [Ed25519 · LWW-sync]" — sync is stripped from core and is a future plugin; remove or move

**Get started**
- Two-path layout (Claude Desktop / Claude Code) no longer applies — there is one path: download binary + paste init prompt
- Step 01 offers a "Manager skill" download button — skill is deleted
- Step 02 still references uploading a zip and installing a skill
- Claude Code path still shows `unzip lore-*.zip && chmod +x lore` — now just `chmod +x lore`
- JS fetches `loretools-manager-en` asset — now `loretools-skills-en`

**Research workflow section**
- Cards 01 (Discover) and 02 (Fetch) use `lore discover` / `lore fetch` — both are plugin-only; they're shown as core
- Card 03 Stage: `lore staging list` → correct command is `lore staging list-staged`
- Card 06 Sync: stripped from core — should move to envisioned

**Envisioned section**
- Missing the entire knowledge layer vision: wiki, synthesis notes, reading paths, concept graphs
- Missing epistemological pluralism: non-Western knowledge sources, community-contributed adapters
- "Sync" row should move here from the workflow section

**Impact section**
- Generic. Should sharpen around the epistemic asymmetry argument from product.md/vision.md

---

## Changes

### 1. Hero
- Fix typo
- Rewrite tagline: position as reference + knowledge layer, not just reference management
- Update differentiator rows: remove sync row; add knowledge layer row

### 2. Get started
- Collapse to single path: download binary → paste init prompt → done
- Button: download binary only (no skill zip)
- Add a copyable init prompt block (copy-to-clipboard)
- Update JS: detect platform binary, point to `loretools-skills-en` for optional skill zip
- Update command: `chmod +x lore` (no unzip)

### 3. Research workflow section
- Keep cards 03–05 as core (Stage, Merge, File Archive)
- Mark cards 01–02 (Discover, Fetch) as plugin with a visual tag `[plugin]`
- Remove card 06 (Sync) — move to Envisioned
- Fix `lore staging list` → `lore staging list-staged`

### 4. Envisioned section
- Add Sync row (moved from workflow)
- Add knowledge layer rows from vision.md:
  - Wiki as living document — synthesis notes, concept pages, reading paths
  - Citation graph — influence chains, gap detection
  - Epistemological pluralism — non-Western sources, authority types, community adapters
  - Cross-domain concept translation
- Keep existing rows (semantic search, annotations)

### 5. Impact section
- Rewrite around the epistemic asymmetry argument: reference infrastructure is not neutral; loretools is built on a different premise
