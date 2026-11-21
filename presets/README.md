# Presets

`oh-my-opencode-slim.template.jsonc` is cstack's project preset template for
[oh-my-opencode-slim](https://github.com/alvinunreal/oh-my-opencode-slim)
**v3.0.7** on OpenCode 2.3. It is not a live config: every model value is a
`FILL_IN_VERIFIED_FREE_MODEL_ID` placeholder, and the adopting project fills
them. No API keys, `.env` values, tokens, or headers ever live here or in the
live preset (spec 0001 §9; `rules/cost-and-models.md` rule 2).

## What ships

| Path | What it is |
| --- | --- |
| `oh-my-opencode-slim.template.jsonc` | The template: all eight built-in roles with intent comments, fallback failover off, **council and observer disabled** (council's seat models are inherited from user-level config the project file cannot verify), additive skill grants only |
| `checks/check_presets.py` | Dependency-free policy checker (Python 3 stdlib only) |
| `checks/free-route-allowlist.jsonc` | The verified-free route allowlist. Ships empty: it is the evidence record, and no route has been verified yet. Only `openrouter/…` and `nvidia/…` route ids may ever be listed |
| `checks/fixtures/` | Positive and negative fixtures proving every policy rule fires (run by CI) |

## Adoption

1. **An approved Decision in your project comes first** (`rules/cost-and-models.md`
   rule 4). For Londinium this is a Decision in its Project, per issue #1.
2. Copy the template to `<project>/.opencode/oh-my-opencode-slim.jsonc`.
   If a `.json` exists too, `.jsonc` wins (upstream v3.0.7 docs).
3. Fill every `FILL_IN_VERIFIED_FREE_MODEL_ID` with a route you have **verified
   is free today** — an OpenRouter free-tier route or an NVIDIA free endpoint —
   or keep the role disabled as shipped (council, councillor, and observer
   ship disabled). Do not delete entries and do not re-enable the disabled
   roles casually: a deleted role inherits the active preset's primary model,
   which this file cannot verify. A placeholder is **not a usable model ID**
   and no runnable paid default ships in this template — it is a tripwire
   against accidental defaults, not a spend guarantee, since the host or a
   higher layer can still override models at runtime.
4. Do not turn `fallback.enabled` back on, do not use model arrays (they are
   ordered fallback chains upstream), and do not add `inheritModelFrom`.
5. Add your CI (required integration, see below):
   `python3 <cstack>/presets/checks/check_presets.py --file .opencode/oh-my-opencode-slim.jsonc --allowlist <your allowlist>`
   Keep your own allowlist copy and fill entries with evidence as you verify
   routes (`checks/free-route-allowlist.jsonc` documents the entry schema;
   only `openrouter/…` and `nvidia/…` ids are accepted).

### Re-enabling the disabled roles

- **Observer** (needs a vision-capable model): remove it from
  `disabled_agents` and pin it with a route from your evidenced allowlist.
  The checker rejects an enabled observer that is only placeholder-pinned.
- **Council / councillor**: seat models come from the *active* council preset
  (`council.presets.<name>.<seat>`, `council.default_preset` else `"default"`),
  which is user-level config this file cannot verify; upstream v3.0.7 source
  disables the whole seat chain when `council` is in `disabled_agents`.
  Re-enabling requires all of: remove `council` from `disabled_agents`,
  define the active council preset **in this file** with every seat pinned to
  a verified free route, re-enable the `council-inject` hook only if you also
  want automatic keyword-triggered consensus calls, and a reviewed policy
  change — the checker fails any file that enables council without the
  disable entry, regardless of what the file pins.

Skills: the template only uses additive grants — `skills_add` for
`correct` and `sharpen` (add your generated `verify-<app>` id when it
exists), or `skills_include_local: true` to pick up `.agents/skills/**` and
`.opencode/skills/**` automatically. It never redefines `skills` and never
uses `"*"`: upstream, a `skills` key replaces the inherited grant list.

## Enforcement — what is shipped vs. what you must integrate

**Shipped (this repo's CI, `.github/workflows/preset-policy.yml`):** the
scan keeps cstack's own template honest — placeholders only (the shipped
allowlist is empty), no Grok/xAI token anywhere a model id can appear,
fallback disabled, model arrays rejected (`MODEL_CHAIN_FORBIDDEN`, even
all-free chains), council required disabled (`COUNCIL_NOT_DISABLED`),
observer disabled or filled with an evidenced route
(`OBSERVER_UNVERIFIED`), additive skills only, no secret-looking values,
complete roster (pinned or disabled), and invalid model types
(null/object/number/empty chain) fail closed as structural errors. The
fixture suite proves each check fails on the corresponding mistake.

**Required consumer integration (cstack CI cannot see your repo):** run
`check_presets.py --file` against your live preset in your CI with your own
evidenced allowlist (only `openrouter/…`/`nvidia/…` ids can be admitted).
Without this step, nothing checks your live file.

**Explicitly not enforced by anything here:** runtime spending. No check,
doc, or bot watches a live session or a provider bill. Set provider-side
spend caps and dashboard alerts yourself. Also outside this file's reach:
models configured in the host `opencode.json` (which outranks project
layers), user-level presets for roles you leave unpinned, and stray
ancestor `.opencode` directories (upstream v3.0.7 walks ancestors up to
the filesystem root on v2 hosts — keep stray `.opencode` out of `~/`,
`~/orca/`, and similar; `OPENCODE_DISABLE_PROJECT_CONFIG` disables the
project walk).

## Upstream schema evidence

All schema claims in the template and checker were verified against the
upstream **v3.0.7 tag** (annotated tag object
`3687c42847982aba850aa5b054c1d8ffd1930a25`):
`docs/configuration.md`, `docs/project-local-customization.md`,
`docs/skills.md`, `docs/council.md`, `.out-of-scope/preset-fallback.md`,
`src/agents/role-definitions.ts`, and `src/agents/council-agents.ts` — same
tag. Highlights: `fallback.enabled` defaults to `true`; an array `model` is
an ordered fallback chain (council seats too); unlisted subagents inherit
the preset's primary model; listing `council` in `disabled_agents` disables
the whole chain (agent, seats, pointer, keyword injection) while
`disabled_hooks: ["council-inject"]` alone still leaves dispatch-by-name
possible; `disabled_agents` defaults to `["observer"]` and is global; root
`agents` entries beat preset entries; `skills_add` keeps inherited grants
and appends. `rules/cost-and-models.md` cites these per rule.
