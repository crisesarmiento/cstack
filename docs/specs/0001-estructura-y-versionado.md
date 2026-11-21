# Spec: estructura y versionado de cstack

- **Fecha:** 21/11/2026 (America/Cordoba)
- **Issue:** [#1](https://github.com/crisesarmiento/cstack/issues/1) (abierto 21/11/2026 09:12 ART; spec v0.1)
- **Estado:** propuesta, no aplicada
- **Repo:** https://github.com/crisesarmiento/cstack (público; hoy solo el README de una línea; sin licencia todavía)
- **No se tocó el repo ni las máquinas.** Cristian implementa con Orca + OpenCode; esto es solo la spec.

Fuentes consultadas el 21/11/2026: [Skills](https://opencode.ai/docs/skills/), [Instructions](https://opencode.ai/docs/instructions/), [Agents](https://opencode.ai/docs/agents/), [Commands](https://opencode.ai/docs/commands/), [Config](https://opencode.ai/docs/config/), [Plugins](https://opencode.ai/docs/plugins/) de OpenCode; slim v3.0.7 [`docs/skills.md`](https://github.com/alvinunreal/oh-my-opencode-slim/blob/v3.0.7/docs/skills.md) y [`docs/project-local-customization.md`](https://github.com/alvinunreal/oh-my-opencode-slim/blob/v3.0.7/docs/project-local-customization.md); [Agent Skills spec](https://agentskills.io/specification) y [dónde escanear](https://github.com/agentskills/agentskills/blob/main/docs/client-implementation/adding-skills-support.mdx); [Claude Code skills](https://code.claude.com/docs/en/skills) y [memory / AGENTS.md](https://code.claude.com/docs/en/memory); [Cursor skills](https://cursor.com/docs/skills) y [rules / AGENTS.md](https://cursor.com/docs/rules); [Codex skills](https://learn.chatgpt.com/docs/build-skills) y [AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md); [Pi skills](https://docs.pi.dev/latest/skills) y [configuration](https://docs.pi.dev/latest/configuration); [Gemini CLI skills](https://geminicli.com/docs/cli/using-agent-skills/) (página actualizada 30/4/2026) y [GEMINI.md](https://geminicli.com/docs/cli/gemini-md/) (18/6/2026); [Amp skills](https://ampcode.com/docs/customize/skills) y [AGENTS.md](https://ampcode.com/docs/customize/agents-md); [Copilot skills](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-skills) y [custom instructions](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-custom-instructions); [`npx skills` / vercel-labs/skills](https://github.com/vercel-labs/skills) ([commands](https://github.com/vercel-labs/skills/blob/main/docs/commands.md), [agents](https://github.com/vercel-labs/skills/blob/main/docs/agents.md)); pstack 0.15.46; Superpowers [`docs/README.opencode.md`](https://github.com/obra/superpowers/blob/main/docs/README.opencode.md); Compound Engineering (copia local, 21/11).

## 1. Qué tiene que resolver esta spec

cstack es un pack versionado (skills, principios, presets de slim, reglas de costo) pensado primero para OpenCode 2.3 + oh-my-opencode-slim 3.0.7, reusable en Londinium (Godot/GDScript) y Route (TS, Biome), y **eventualmente público**. Las reglas se hacen cumplir por estructura, no de memoria. Antes de que un proyecto lo adopte, hay que cerrar **árbol, versionado, cómo se pinea y en qué carpeta instala** para que los skills carguen en más de un agente.

El issue ya fija el contenido de v0.1 (`correct`, `verify-template`, `sharpen`, 8 principios, reglas de costo). Acá no se reabre eso.

## 2. Cómo carga OpenCode 2.3 (y slim 3.0.7)

### Skills

Ruta de proyecto confirmada: `.opencode/skills/<id>/SKILL.md` (forma con carpeta; el ID es el nombre de la carpeta, case-sensitive). También acepta un `.md` suelto en la raíz de `skills/`. Docs: [Skills](https://opencode.ai/docs/skills/).

Otras rutas automáticas:

| Alcance | Ruta |
| --- | --- |
| Global | `~/.config/opencode/skills` |
| Compat global | `~/.claude/skills`, `~/.agents/skills` |
| Proyecto | `.opencode/skills` (desde el cwd hasta la raíz del proyecto, cada nivel) |
| Compat proyecto | `.claude/skills`, `.agents/skills` |

Se puede sumar más con el array `skills` en `opencode.json(c)` (rutas relativas **desde el working directory activo**, `~/`, absolutas, o un catálogo HTTP con `index.json` + campo `version`). Los arrays se **combinan**, no se pisan.

Precedencia (el que se registra **después** gana el mismo ID): built-in → `.claude` → `.agents` → `~/.config/opencode/skills` → `.opencode/skills` (de la raíz del proyecto hacia el cwd) → entradas explícitas de `skills`. El proyecto pisa lo global.

El modelo ve solo ID, name y description; carga el cuerpo con la tool `skill` o con `@skill-id`.

### AGENTS.md e `instructions`

OpenCode carga `~/.config/opencode/AGENTS.md` y después cada `AGENTS.md` desde el workspace hacia arriba. Si el workspace está **fuera de `$HOME`**, corta en la raíz del proyecto. Si el workspace está **fuera de la raíz del proyecto, solo carga el archivo global** ([Instructions](https://opencode.ai/docs/instructions/)). No resuelve conflictos: concatena. El array `instructions` de `opencode.json` se carga **después**. `OPENCODE_DISABLE_PROJECT_CONFIG=1` salta lo de proyecto.

Un worktree de Git *es* la raíz de ese checkout, así que un `AGENTS.md` commiteado debería cargarse. **No está verificado en un worktree de Orca** (`~/orca/workspaces/<project>/…`).

### Agents, commands, config

- Agents: `~/.config/opencode/agents/<name>.md` y `.opencode/agents/<name>.md` ([Agents](https://opencode.ai/docs/agents/)).
- Commands: `~/.config/opencode/commands/` y `.opencode/commands/` (el del proyecto pisa el global; el más cercano pisa al ancestro) ([Commands](https://opencode.ai/docs/commands/)).
- Config: `~/.config/opencode/opencode.json(c)` y, en el proyecto, `opencode.json(c)` o `.opencode/opencode.json(c)`. Busca desde el cwd hasta la raíz del filesystem. Primero mergea los `opencode.json` directos (de afuera hacia adentro) y después los de `.opencode/` ([Config](https://opencode.ai/docs/config/)). **No hay un loader `.opencode/rules/`** como en Cursor.

### slim 3.0.7

Preset de proyecto: `.opencode/oh-my-opencode-slim.json` o `.jsonc` (`.jsonc` gana si hay los dos). En hosts v2 la búsqueda sube **más allá** de la raíz del worktree, hasta la raíz del filesystem. `~/.opencode` es capa de proyecto para cosas bajo `$HOME`.

El campo `skills` de un agente en el preset es un **permiso** (qué skills puede activar), no el lugar donde viven los archivos: `"*"`, lista explícita, `"!nombre"` para denegar. Si un layer define `skills`, **reemplaza** la lista heredada. Para sumar o sacar sin pisar: `skills_add`, `skills_remove` (el remove gana). `skills_include_local: true` agrega los `SKILL.md` válidos de `.opencode/skills` y `.agents/skills` del proyecto y ancestros, antes del remove ([skills.md](https://github.com/alvinunreal/oh-my-opencode-slim/blob/v3.0.7/docs/skills.md) y [project-local-customization.md](https://github.com/alvinunreal/oh-my-opencode-slim/blob/v3.0.7/docs/project-local-customization.md), tag v3.0.7).

Cuidado: un `.opencode/` suelto en `~/`, `~/orca/` o `~/Projects/` puede colarse en esa caminata. No poner config de cstack ahí.

## 3. Cómo versionan pstack, Superpowers y Compound Engineering

- **pstack 0.15.46:** árbol `skills/<id>/SKILL.md`, `agents/`, `plugin.json` con `"version"`. **No tiene CHANGELOG.** El ruteo de modelos se escribe aparte (`pstack-models.mdc`) y no migra solo. Referencia de forma, no de distribución (es plugin de Cursor/Claude Code, no de OpenCode).
- **Superpowers:** `skills/` + `package.json` con semver (docs citan pinear `v7.0.2`). En OpenCode 2 se instala como plugin y se pinea con tag o commit: `plugins: ["superpowers@git+https://github.com/obra/superpowers.git#v7.0.2"]` ([README.opencode.md](https://github.com/obra/superpowers/blob/main/docs/README.opencode.md), consultado 21/11). El plugin registra el directorio de skills; hace falta un entry JS. Los symlinks viejos los están dejando atrás.
- **Compound Engineering:** en la copia local del plugin (21/11) hay `package.json` y `plugin.json` (versión **3.29.0** en esa copia; puede haber una más nueva, no re-verifiqué el tag remoto), `CHANGELOG.md` y `skills/`. Mismo modelo: manifiesto + changelog + plugin.

Lección: skills en `skills/<id>/SKILL.md`, una versión en un manifiesto, un CHANGELOG, y el pin en el consumidor. No copiar la falta de changelog de pstack.

## 4. Compatibilidad entre agentes

La especificación [Agent Skills](https://agentskills.io/specification) (consultada 21/11/2026) define el **contenido** de un skill (`SKILL.md` con frontmatter `name` + `description`, más `scripts/`, `references/`, `assets/`). **No manda la carpeta** donde vive. La convención cruzada, documentada para quien implementa un cliente, es [`.agents/skills/`](https://github.com/agentskills/agentskills/blob/main/docs/client-implementation/adding-skills-support.mdx) (proyecto) y `~/.agents/skills/` (usuario).

### Matriz (proyecto / global / AGENTS.md)

Docs oficiales, 21/11/2026. “Estándar” = acepta `SKILL.md` con `name`/`description`.

| Agente | Skills de proyecto | Skills globales | ¿Lee `.agents/skills/`? | AGENTS.md | Estándar |
| --- | --- | --- | --- | --- | --- |
| **OpenCode 2.3** | `.opencode/skills/` (nativo) **y**, como compat, `.agents/skills/`, `.claude/skills/` | `~/.config/opencode/skills`; compat `~/.agents/skills`, `~/.claude/skills` | **Sí** ([Skills](https://opencode.ai/docs/skills/)). Precedencia: `.opencode/skills` gana al mismo ID | **Sí.** Fallback `CLAUDE.md` si no hay `AGENTS.md`; un symlink entre los dos carga una sola vez | Sí (acepta campos del estándar; no los exige en runtime) |
| **Claude Code** | `.claude/skills/` | `~/.claude/skills/` | **No documentado.** Las docs de skills (21/11) solo listan `.claude/skills/`. Un issue de sept. 2026 ([#31005](https://github.com/anthropics/claude-code/issues/31005), comentario 19/9/2026) decía que v2.1.277 sumó `AGENTS.md` pero no `.agents/skills/`. No confirmé un cambio posterior | **Sí, condicional:** si no hay `CLAUDE.md` / `CLAUDE.local.md` en el cwd o arriba (v2.1.277+). Si existe `CLAUDE.md`, gana él, salvo config `claude-md-and-agents-md` | Sí, con extensiones propias |
| **Cursor** | `.agents/skills/` y `.cursor/skills/`; compat `.claude/skills/`, `.codex/skills/` | `~/.agents/skills/`, `~/.cursor/skills/`; compat `~/.claude/`, `~/.codex/` | **Sí** ([docs](https://cursor.com/docs/skills/)) | **Sí** (raíz y anidados) | Sí |
| **Codex CLI** | `.agents/skills/` (desde el cwd hasta la raíz del repo). `.codex/skills` es legado, sigue andando | `~/.agents/skills/`; `/etc/codex/skills` admin. `~/.codex/skills` es legado | **Sí** — es la ruta oficial actual ([build-skills](https://learn.chatgpt.com/docs/build-skills)) | **Sí** (`AGENTS.md` del repo y `~/.codex/AGENTS.md`) | Sí |
| **pi** (docs.pi.dev) | `.agents/skills/` (cwd → raíz del repo) y `.pi/skills/` | `~/.agents/skills/` y `~/.pi/agent/skills/` (el dir del agente default es `~/.pi/agent`) | **Sí** ([skills](https://docs.pi.dev/latest/skills)) | **Sí** (también acepta `CLAUDE.md` como archivo de contexto) | Sí |
| **Gemini CLI** | `.agents/skills/` o `.gemini/skills/` | `~/.agents/skills/` o `~/.gemini/skills/` | **Sí** (lo llama “alias”) | **No por default.** El archivo default es `GEMINI.md`. `AGENTS.md` entra si en `settings.json` está `context.fileName` con ese nombre ([GEMINI.md](https://geminicli.com/docs/cli/gemini-md/), 18/6/2026) | Sí |
| **Amp** | `.agents/skills/` (y también escanea `.claude/skills/`) | `~/.config/agents/skills/`, `~/.agents/skills/`, `~/.config/amp/skills/`, más locs de Claude | **Sí** | **Sí.** Si no hay `AGENTS.md`, cae a `AGENT.md` o `CLAUDE.md` | Sí |
| **GitHub Copilot CLI** | `.agents/skills/`, `.claude/skills/` o `.github/skills/` | `~/.agents/skills/` o `~/.copilot/skills/` | **Sí** | **Sí**, junto con `.github/copilot-instructions.md`, `CLAUDE.md`, `GEMINI.md` | Sí |

Respuesta directa: **sí, OpenCode 2.3 lee `.agents/skills/` y `.claude/skills/`** (rutas de compatibilidad). Si el skill está solo en `.opencode/skills/`, Cursor, Codex, pi, Gemini, Amp y Copilot **no** lo van a ver (ninguna de sus docs oficiales lista `.opencode/skills/`).

### Cómo instalan otros packs

- **`npx skills`** ([vercel-labs/skills](https://github.com/vercel-labs/skills), consultado 21/11): instala en el proyecto por default. Para OpenCode, Cursor, Codex, pi, Gemini, Amp y Copilot el path de proyecto que declara es **`.agents/skills/`**. Claude Code va a **`.claude/skills/`**. Por default **symlink** desde cada carpeta de agente a una copia canónica; `--copy` si no hay symlinks. Detecta agentes instalados; `-a` elige; se puede pinear con `npx skills add owner/repo@v1.2.3`.
- **pstack:** plugin de Cursor + adapter de Claude Code. No apunta a `.agents/`.
- **Superpowers:** plugin por harness (en OpenCode registra skills, no copia a varias carpetas). Docs de proyecto para OpenCode: `.opencode/skills/`.

## 5. Árbol propuesto (repo `cstack`)


Nombres de archivos en inglés. Nada de secretos, `.env` ni keys.

```
README.md                 # qué es, cómo instalar una versión pineada, link al issue
LICENSE                   # pendiente (el issue sugiere MIT + atribución a pstack)
CHANGELOG.md              # Keep a Changelog; cada release
VERSION                   # semver crudo, una línea, p.ej. 0.1.0
cstack.json               # { "name": "cstack", "version": "0.1.0" } — fuente de la versión
skills/
  correct/SKILL.md        # error repetido → lint/tipos/test (sin ruteo de pstack)
  sharpen/SKILL.md        # profundizar el prompt, no agrandarlo
  verify-template/        # plantilla para que el proyecto genere verify-<app>
    SKILL.md
principles/
  PRINCIPLES.md           # los 8 principios, un solo archivo-checklist
presets/                  # plantillas slim, sin secrets ni keys
  londinium.json
  route.json
rules/
  cost-and-models.md      # texto de las reglas de costo (no es un loader de OpenCode)
templates/
  AGENTS.md               # contexto corto; no las reglas chequeables
install/
  README.md               # cómo adoptar y upgradear
  cstack-install          # script: copia una versión tagueada a .agents/skills/ (+ symlinks)
.github/                  # opcional, más adelante: CI del propio cstack
```

En v0.1 **no** hay `agents/` ni `commands/` de OpenCode (slim ya cubre los roles).

### Qué es global y qué es por proyecto

| Cosa | Dónde vive | Quién la pineia |
| --- | --- | --- |
| Fuente de cstack | `~/Projects/cstack` en Mac y Omarchy, y GitHub | El clone puede estar en `main`; los proyectos no dependen de esa rama en runtime |
| Skills compartidos (`correct`, `sharpen`, …) | Vendorizados en `.agents/skills/` del consumidor (ver §6 y §7) | El proyecto, a un tag |
| `verify-<app>` | Solo en el proyecto (sale del template) | El proyecto |
| Preset vivo | `.opencode/oh-my-opencode-slim.json` del proyecto | El proyecto; cstack solo aporta plantilla |
| `AGENTS.md` del repo | Raíz del consumidor (canónico). Symlink relativo `CLAUDE.md` → `AGENTS.md` | El proyecto |
| `~/.config/opencode/skills` | No usar para cstack en producción | Sin pin por proyecto |

## 6. Cómo un proyecto pinea y upgradea

Archivos en el **consumidor**, commiteados:

```
.agents/skills/
  correct/SKILL.md          # copia canónica de esa versión (no editar)
  sharpen/SKILL.md
.claude/skills/
  correct -> ../../.agents/skills/correct   # symlink relativo (Claude Code no lee .agents, docs 21/11)
  sharpen -> ../../.agents/skills/sharpen
.opencode/
  cstack.lock.json          # { "version": "0.1.0", "tag": "v0.1.0" }
  oh-my-opencode-slim.json  # preset del proyecto; skills_add / skills_include_local
AGENTS.md                   # canónico
CLAUDE.md -> AGENTS.md      # symlink relativo; OpenCode lo carga una sola vez
```

No hace falta copiar también a `.opencode/skills/`: OpenCode y slim 3.0.7 (`skills_include_local`) ya leen `.agents/skills/`. Duplicar el mismo ID en las dos carpetas solo genera confusión de precedencia.

Instalar, opción propia:

```text
cstack-install --version v0.1.0 --project /ruta/al/repo
```

El script copia `skills/` (salvo `verify-template`) a **`.agents/skills/`**, crea los **symlinks relativos** de `.claude/skills/<id>` (layout fijo, no “solo si detecta Claude en esta máquina”: el repo compartido tiene que servirle a quien clone), escribe `cstack.lock.json`, y no pisa `verify-<app>` ni el preset vivo. El upgrade es el mismo comando con otro tag, más un PR en el consumidor.

Instalar, opción pública (compatible):

```text
npx skills add crisesarmiento/cstack@v0.1.0
```

Requiere que el repo cstack exponga `skills/` en la raíz (ya está en el árbol). `npx skills` instala a `.agents/skills/` para OpenCode/Cursor/Codex/pi/Gemini/Amp/Copilot y a `.claude/skills/` para Claude Code; por default usa symlink. `--copy` si hace falta. `-a` elige agentes; si no, detecta los instalados en **esa** máquina (para un repo público es mejor commitear el layout fijo de arriba, no el resultado de un auto-detect local).

`--agents` en `cstack-install` puede existir para casos raros, pero el default de un install commiteado es el layout portable (`.agents/skills/` + symlink de Claude), no la detección local.

Las copias vendorizadas no se editan: lo específico del repo va a un skill con **otro ID** (p.ej. `verify-londinium`), también bajo `.agents/skills/`.

En slim, no redefinir `skills` entero si ya hay lista heredada. Usar `skills_add: ["correct", "sharpen"]` (y el `verify-*` cuando exista) o `skills_include_local: true` (incluye `.agents/skills/` y `.opencode/skills/`). No pisar el preset con un `"*"` accidental en el fixer.

Worktrees de Orca: archivos y **symlinks relativos** van dentro del repo, así que un worktree en `~/orca/workspaces/<project>/…` los trae con el checkout. Un symlink absoluto a `~/Projects/cstack` no. Windows no es un requisito ahora.

`GEMINI.md`: no se crea por default (Gemini CLI no lee `AGENTS.md` hasta que alguien lo configura). Si un proyecto usa Gemini CLI, se puede añadir `GEMINI.md -> AGENTS.md`, sabiendo que si además habilitan `AGENTS.md` en `context.fileName` podrían cargarlo dos veces. Queda como opción, no como parte del layout default.

## 7. Distribución: A/B/C

| | A. Copiar/sincronizar (`cstack-install --version vX`) | B. git submodule | C. Plugin de OpenCode |
| --- | --- | --- | --- |
| Cómo pinea | `cstack.lock.json` + archivos en `.agents/skills/` (+ symlink Claude) | submodule en un tag/SHA | `plugins: ["…cstack.git#v0.1.0"]` ([Plugins](https://opencode.ai/docs/plugins/); un hash completo queda pineado) |
| Worktrees Orca | Sí: viaja con el checkout | Frágil: cada worktree pide `git submodule update --init` | El pin está en `opencode.json`; el paquete vive en el cache de OpenCode, no en el Godot repo |
| Mac + Omarchy | `git pull` del consumidor alcanza | Igual, más el submodule | Hay que instalar/cachear el plugin en las dos máquinas |
| Londinium / Route | Sin npm en Godot | Git nativo, más ceremonia | Hace falta un entry JS (como Superpowers). Es más de lo que pide v0.1 |
| Contras | Hay que no editar las copias; hay un script que mantener | Dolor conocido con worktrees; path extra | Scope grande ahora; updates del cache a veces se quedan trabadas (lo documenta Superpowers) |

**No va:** symlink a `~/Projects/cstack`. No hay pin por proyecto (todos ven la rama que esté checkouteada). Un symlink relativo se rompe en `~/orca/workspaces/…`. Uno absoluto a `~/Projects/cstack` funcionaría en las dos máquinas, pero sigue sin versionado por repo.

**Recomendación: A**, con destino **`.agents/skills/`** (no solo `.opencode/skills/`). Así OpenCode, Cursor, Codex, pi, Gemini, Amp y Copilot leen el mismo checkout; Claude Code entra por el symlink relativo. Para quien instala cstack desde afuera, `npx skills add crisesarmiento/cstack@vX` queda como camino documentado y compatible. C (plugin de OpenCode) sigue siendo post-1.0. B (submodule) no es el default.

Sobre *dónde* instalar, en corto:

- **A (recomendada):** canónico `.agents/skills/` + symlink relativo `.claude/skills/<id>`.
- **B:** copiar a todas las carpetas vendor (`.opencode`, `.cursor`, `.codex`, `.pi`, `.gemini`, `.github`, …). Duplica y se desincroniza.
- **C:** solo `.opencode/skills/`. Alcanza para el stack actual de Cristian; **no** sirve cuando se comparte en público.


## 8. Semver, CHANGELOG y releases

Versión en `VERSION` y `cstack.json`, tags `vMAJOR.MINOR.PATCH`. Empezar en `0.1.0`. Mientras sea `0.x`, un cambio breaking sube **MINOR** y se declara en el changelog. Recién en `1.0.0` un breaking es MAJOR.

| Tipo | Qué lo dispara |
| --- | --- |
| **MAJOR** (o MINOR en 0.x) | Sacar o renombrar un skill ID; cambiar el contrato de un skill o de una regla de costo de forma incompatible; cambiar las rutas que escribe el instalador |
| **MINOR** | Sumar un skill, un principio o una plantilla de preset, sin romper lo anterior |
| **PATCH** | Aclaraciones, typos, ejemplos, docs, fixes que no cambian el contrato |

`CHANGELOG.md` al estilo [Keep a Changelog](https://keepachangelog.com/en/1.1.0/): `Added`, `Changed`, `Removed`, `Fixed`, con fecha y link al tag. Un release = merge a `master` + tag `vX.Y.Z` (GitHub Release opcional). No publicar un tag sin entrada de changelog.

## 9. Presets sin secretos

En `presets/` solo van IDs de modelo (`provider/model` o `#variant`), grants de skills, y comentarios. Cero API keys, `.env`, tokens, headers. El preset **vivo** queda en el proyecto (ya existe el patrón en Londinium). La plantilla se mergea a mano o con el instalador en modo no destructivo (si el archivo ya está, no lo pisa; deja un `.example`).

Los IDs de modelo no son secretos, pero cambian con el catálogo (Go, OpenAI, etc.). Las plantillas documentan la intención del rol; el proyecto pone los slugs que paga.

## 10. Dónde se hace cumplir cada regla

Igual que el issue #1 (idea de pstack `correct`):

1. **Chequeable** → lint, tipos, tests, hook o CI. El error nombra el arreglo. En Route, Biome/tests; en Londinium, lo que ya tenga el CI/headless.
2. **Juicio** → skill corto (`correct`, `sharpen`).
3. **Contexto** → `AGENTS.md` (comandos de build, arquitectura, “mirar evidencia antes que el diff”). Corto. No es el lugar de una regla que se puede checkear.

Una regla entra solo después de que el mismo error pasó **dos veces**, con prueba de que el check falla en ese error pasado.

Las reglas de costo (OpenRouter/NVIDIA solo free, sin fallbacks pagos; Grok nunca en cadenas automáticas de OpenCode; Decision aprobada antes de implementar) no viven solo en `AGENTS.md`. Van al preset (no listar esos modelos en las cadenas) y, cuando se pueda, a un check de CI que falle si el slim JSON mete `grok` o una ruta paga en un agente automático. El texto en `rules/cost-and-models.md` es la especificación, no el enforcement.

## 11. Preguntas abiertas

Siguen del issue #1:

- ¿Piloto primero en Route o en Londinium?
- ¿LICENSE MIT con atribución a pstack?

Nuevas, no bloquean el árbol:

- ¿`skills_include_local: true` o solo `skills_add` explícito en el preset?
- ¿Más adelante (post-1.0) ofrecer también el plugin de OpenCode?
- Verificar en un worktree real de Orca que cargan `.agents/skills/` y `AGENTS.md` (docs sí; práctica no confirmada acá).
- ¿Claude Code ya lee `.agents/skills/` en alguna versión posterior a sept. 2026? Si sí, el symlink podría dejar de hacer falta; hoy las docs oficiales no lo listan.
- ¿Incluir `GEMINI.md -> AGENTS.md` en el layout default, o dejarlo opcional?

Esta es una propuesta. No está aplicada.
