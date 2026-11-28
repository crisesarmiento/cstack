# Agent permission rules

- **Status:** rule text from [issue #10](https://github.com/crisesarmiento/cstack/issues/10).
  This file is the specification, **not** a loader or an automated check.
  Nothing here configures an agent or enforces permissions by itself.
- **Scope:** shell permissions in any coding agent. OpenCode 2.3.x is the
  tested case; other agents must be verified the same way, not assumed safe.

## Rules

### 1. Shell allow rules are exact commands, never wildcards

Allow only a reviewed, exact command with no wildcard, for example
`tools/run_tests.sh`. A command that needs variable arguments stays on
**ask**; do not replace the arguments with `*` to avoid prompts.

Never pre-allow push, pull request creation or changes, merge, `sudo`, or
secret reads. These operations require explicit human approval, not a
standing shell allow rule, even when the command is exact.

### 2. Verify permissions interactively

Test rules in a real interactive agent session, where a human can observe
whether a permission prompt appears. Check both the intended exact command
and commands outside it, including added arguments and shell chaining with
`&&` and `;`. Use harmless probes in a disposable location, never actual
pushes, merges, elevated commands or secret reads.

An unprompted command in a headless run is not evidence that an allow rule
works. Re-verify after changing the agent version, permission configuration
or execution mode.

### 3. Only the orchestrator runs verification

Only the top-level agent (the orchestrator) runs tests, builds and verify
scripts. Delegated specialists change code and report back. A specialist runs
a check only if the orchestrator hands it one exact allowed command.

**Why.** Allow lists are written for the orchestrator's commands. A specialist
that runs its own checks either hits permission prompts or runs commands nobody
vetted. Duplicate runs, one by the specialist and one by the orchestrator,
also waste time.

**Evidence.** Londinium pilot, issue
[Palehour/londinium#385](https://github.com/Palehour/londinium/issues/385)
task T1, 2026-11-21: the `correct` skill found both delegated specialists
running verification commands outside the allowed list, which only covered the
orchestrator's commands (`tools/run_tests.sh` and
`tools/verificar.sh --escenario small_rich`). See
[issue #12](https://github.com/crisesarmiento/cstack/issues/12).

**What cstack enforces.** Nothing automated. This is rule text only; no preset,
check or runtime guard stops a specialist from running a command.

**What the adopter must do.** State the rule in the project's `AGENTS.md` and
in the orchestrator's prompt, so delegation instructions tell specialists not
to run checks and pass an exact allowed command when one is needed.

### 4. Third-party skills

cstack already vendors its own skills from a pinned tag and a lock file
(see [install/README.md](../install/README.md)). That pin does not cover
skills from elsewhere, such as pstack, Superpowers, Compound Engineering,
or a skill an agent proposes to add.

For any third-party skill:

- Install only from the skill's official repository.
- Pin to a tag or a commit SHA; never install from a moving branch.
- Read `SKILL.md` and every bundled script before installing.
- Agents never install, update or fetch skills on their own. They may
  only propose a source and a pin; a human must approve before anything
  is installed or updated.
- Record the official repository URL and the pin (tag and/or SHA) in the
  project, so the install can be reproduced and reviewed.

**What cstack enforces.** Nothing automated. This is rule text only.

**What the adopter must do.** State the rule in the project's `AGENTS.md`
and keep a record of each third-party skill's source and pin.

## Evidence and limits

On **2026-11-21**, in a real interactive Orca TUI session on Omarchy,
OpenCode **2.3.x** had the shell allow rule `jq *`. Both commands ran
**without asking**:

```sh
jq --version && touch /tmp/chain-and
jq --version; touch /tmp/chain-semi
```

The wildcard therefore admitted chained commands beyond the intended `jq`
invocation in that tested setup. This is evidence against wildcard shell
allow rules, not proof that exact-command matching is safe in every agent
or version.

In the same investigation, headless `opencode run` **never asked**, even
for commands without an allow rule. It cannot be used to test whether
these rules prompt correctly. Other agents must undergo the same
interactive verification; this finding does not establish their behavior.
See [issue #10](https://github.com/crisesarmiento/cstack/issues/10).

## Where each rule is enforced

| Rule | Shipped in cstack today | Required consumer integration | Explicitly not enforced (honest boundary) |
| --- | --- | --- | --- |
| 1 Exact commands; sensitive operations never pre-allowed | This rule text and links from the README and context template only. **No automated permission enforcement exists in cstack yet.** | Review every active permission layer in the chosen agent. Remove wildcard shell allows, allow only reviewed exact commands, keep variable arguments on ask, and remove standing allows for push, PR operations, merge, sudo and secret reads. Review any allowed script and changes to it: an exact script name does not constrain what its body does. | No shipped permission preset, checker or runtime guard audits or blocks shell commands. Existing preset-policy and model-neutrality CI checks do not validate shell permissions. |
| 2 Interactive verification | The dated OpenCode evidence and testing requirement above; no automated test. | In an interactive session, record the agent version, active configuration, commands tried and observed prompts. Confirm out-of-rule probes ask before execution; if they do not, remove the allow and keep the command on ask until the behavior is understood. Repeat for each adopted agent and after relevant changes. | cstack does not observe consumer sessions or guarantee another agent's matching behavior. Headless `opencode run` cannot validate prompts. |
| 4 Third-party skills: official repo, pinned revision, human approval | This rule text and the matching line in the context template only. **No automated check exists in cstack yet.** | Install third-party skills only from the official repository, pinned to a tag or commit SHA, after reading `SKILL.md` and every bundled script. Agents propose; a human approves. Record the source and pin. | No shipped checker or installer validates the origin or pin of third-party skills. The cstack installer only vendors cstack's own skills. |
