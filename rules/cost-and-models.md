# Cost and model rules

- **Status:** rule text for cstack v0.1 (issue #1, specs
  [0001 §9](../docs/specs/0001-structure-and-versioning.md) and
  [§10](../docs/specs/0001-structure-and-versioning.md)). This file is the
  specification, **not** a loader: OpenCode has no `.opencode/rules/`
  mechanism (spec 0001 §2), so nothing here runs by itself. Enforcement
  lives in the preset template and the CI check, mapped rule by rule below.
- **Scope:** automatic agent chains in OpenCode 2.3 sessions that load
  oh-my-opencode-slim **v3.0.7** presets in consumer projects (Londinium is
  the first pilot, per issue #1).

## Rules

### 1. Free routes only; no paid fallback

An automatic chain (orchestrator, explorer, oracle, designer, fixer,
observer, council, councillor) may only run a route that was **verified
free at adoption time** — and, in scope, that means an OpenRouter
free-tier route or an NVIDIA free endpoint. No paid route may be
configured anywhere an automatic chain can reach it, including fallback
positions and council seats. Slim's foreground model-chain failover is
disabled at the project layer, and model arrays (ordered fallback chains
upstream) are rejected outright — even all-free chains, because a chain is
exactly where an unevidenced route hides.

Upstream v3.0.7 evidence: `fallback.enabled` defaults to `true`
(`docs/configuration.md` at the tag); an agent's array `model` is "a
non-empty ordered fallback chain" resolved on failure
(`.out-of-scope/preset-fallback.md` at the tag); subagents not listed in
the active preset inherit the preset's primary model (same document);
council seats are dynamic `councillor-<name>` agents whose models come
from the active council preset (`council.default_preset` else `"default"`)
and are not built at all when `council` is in `disabled_agents`
(`src/agents/council-agents.ts` at the tag; seat chains support model
arrays too). A paid fallback is therefore one array entry, one inherited
primary, or one inherited seat away.

### 2. An API key or a catalog listing is never permission to spend

Possessing an OpenRouter or NVIDIA key, or a model appearing in a catalog,
does not authorize using it. Permission is an explicit human decision plus a
record: the verified-free allowlist entry, with the URL of the pricing page,
the verification date, and a quote of the text proving $0 pricing. Naming is
never evidence: OpenRouter marks some routes with a `:free` suffix and
NVIDIA has **no universal free naming convention**, so no slug pattern is
inferred as free by any check shipped here. Provider scope is explicit:
only `openrouter/…` and `nvidia/…` route ids may be allowlisted — a route
on any other provider is out of scope even with evidence. Keys, tokens, and
`.env` values never enter this repo, the preset, or the template.

### 3. Grok is never in an OpenCode automatic chain

No Grok/xAI model may appear in any automatic chain — preset entry, root
`agents` entry, council seat, or fallback chain position — regardless of
anyone's claim that it is free. The deny-list beats the allowlist: a Grok
entry cannot be allowlisted at all.

### 4. An approved Decision comes before implementation

An approved Decision precedes implementation work, generally — not only
cstack rollout or preset changes. In a consumer project, an implementation
task starts from a Decision a human approved (issue, spec, or plan record)
before an agent writes code; adopting cstack, filling the first real model
IDs, or changing these rules are simply instances of that same requirement.
For Londinium this is a Decision in its Project (issue #1, 2026-11-21). The
Decision names what will run and what it may cost (expected: nothing).

## Where each rule is enforced

| Rule | Shipped in cstack today | Required consumer integration | Explicitly not enforced (honest boundary) |
| --- | --- | --- | --- |
| 1 Free only, no paid fallback | Template ships placeholders only, scalar models, `fallback.enabled: false`, `foreground-fallback` hook disabled, and **council/councillor/observer disabled** (the only upstream-evidenced way to keep inherited seat models out of the chain). CI (`preset-policy`) fails the shipped template on any non-placeholder route without allowlist evidence (`UNEVIDENCED_MODEL`), on any model array even all-free (`MODEL_CHAIN_FORBIDDEN`), on an enabled council (`COUNCIL_NOT_DISABLED`), on an enabled-but-placeholder observer (`OBSERVER_UNVERIFIED`), on `inheritModelFrom`, and on fallback left enabled (`FALLBACK_NOT_DISABLED`). Invalid model types (null/object/number/empty chain) fail closed structurally. Fixtures prove each case fails. | Fill the template only with routes you verified free (OpenRouter/NVIDIA only), keep fallback off, keep council disabled unless you pin every seat in your own file with verified routes. Run `check_presets.py --file` on your live `.opencode/oh-my-opencode-slim.jsonc` in **your** CI with **your** allowlist copy (presets/README.md, step 5). Without that step nothing checks your live file. | Runtime spend: nothing here watches a live session or a provider bill — set provider-side spend caps and alerts. Host `opencode.json` entries and user-level layers outrank the project file upstream; review them at adoption. Re-enabling council safely is possible but requires changing the checker too, in the same reviewed PR. |
| 2 Key/catalog ≠ permission | The allowlist **is** the permission record: `check_presets.py` rejects entries without complete evidence, entries outside the `openrouter/`/`nvidia/` scope, and denied-vendor or duplicated entries (`ALLOWLIST_INVALID`, operational exit 2), and rejects routes that are neither placeholders nor allowlisted. No naming inference exists in the check. `SECRET_LIKE_VALUE` fails preset files that look like they carry a credential. No key or token is stored anywhere in cstack. | Record the Decision (rule 4) before filling any real model ID; verify each route's pricing page yourself, quote it, date it, and add it to your allowlist in a reviewed PR. Re-verify entries when providers change catalogs. | Key possession itself: cstack never sees keys and cannot police them. Whether a provider's "free" tier actually stays free after a catalog change is a re-verification task, not a runtime guarantee. |
| 3 No Grok in automatic chains | The checker's deny-list fails any `grok` / `xai` / `x.ai` token wherever a model id can appear (`DENIED_VENDOR_MODEL`), and refuses such allowlist entries outright. Negative fixture `grok-on-automatic-chain.jsonc` proves it fires. | Run the same check against your live preset in your CI. There is no exception path: to ever use Grok you must change this rule file first, in a reviewed PR, together with the check. | Nothing prevents a human from configuring Grok in the host `opencode.json` or a user-level layer outside this policy's reach; the check only validates the preset file it is pointed at. |
| 4 Decision before implementation | The template's header and `presets/README.md` step 1 say it, and point here. This file records the requirement where rule text lives. | The consumer must gate implementation on an approved Decision through a **named process or bot the consumer configures** — cstack v0.1 ships no such gate and no bot exists here; each consumer project names its own (Londinium: a Decision in its Project). The gate, whatever it is, must sit before agent implementation work starts, not after. | **No bot exists in cstack and none is planned for v0.1.** cstack CI cannot observe another repo's approvals, so this rule is consumer process, not a shipped check — it is listed here so nobody mistakes the docs for enforcement. |

## Running the checks

Dependency-free (Python 3 standard library only, no packages):

```text
python3 presets/checks/check_presets.py --scan presets              # shipped templates
python3 presets/checks/check_presets.py --self-test presets/checks/fixtures
python3 presets/checks/check_presets.py --file <live preset>.jsonc --allowlist <your allowlist>
```

Exit codes: `0` policy satisfied, `1` policy violation (each error names the
rule and the fix), `2` operational error — missing file, unreadable or
broken allowlist, JSONC parse failure, invalid model types, fixture drift.
The check fails closed: operational errors never pass silently.
