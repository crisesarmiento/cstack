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
