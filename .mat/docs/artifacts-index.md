# Artifacts Index

Tracks all migration artifacts by stage, with branch, commit, review status, and binary acceptance gate result.

## Core Infrastructure (Stages 0–7)

| Stage | Artifact | Branch | Commit SHA | Review Status | Acceptance | Reviewer | Date |
|-------|----------|--------|------------|---------------|------------|---------|------|
| 0 | `docs/inventory.json` | feature/phase1-validation | b9b146f | In Review | PASS | automation | 2026-03-24 |
| 0 | `docs/migration-backlog.md` | feature/phase1-validation | b9b146f | In Review | PASS | automation | 2026-03-24 |
| 1 | `.cursor/hooks.json` | feature/phase1-validation | b9b146f | In Review | PASS | automation | 2026-03-24 |
| 1 | `.cursor/mcp.json` | feature/phase1-validation | b9b146f | In Review | PASS | automation | 2026-03-24 |
| 1 | `.cursor/worktrees.json` | feature/phase1-validation | b9b146f | In Review | PASS | automation | 2026-03-24 |
| 1 | `AGENTS.md` | feature/phase1-validation | b9b146f | In Review | PASS | automation | 2026-03-24 |
| 1 | `.cursor/commands/mat-plan-team.md` | feature/phase1-validation | b9b146f | In Review | PASS | automation | 2026-03-24 |
| 1 | `.cursor/commands/mat-build.md` | feature/phase1-validation | b9b146f | In Review | PASS | automation | 2026-03-24 |
| 1 | `.cursor/commands/mat-review.md` | feature/phase1-validation | b9b146f | In Review | PASS | automation | 2026-03-24 |
| 1 | `docs/reference/artifacts-index.md` | feature/phase1-validation | b9b146f | In Review | PASS | automation | 2026-03-24 |
| 2 | `docs/orchestration.md` | feature/phase1-validation | b9b146f | In Review | PASS | automation | 2026-03-24 |
| 2 | `.cursor/agents/parent-orchestrator.md` | feature/phase1-validation | b9b146f | In Review | PASS | automation | 2026-03-24 |
| 2 | `.cursor/agents/builder.md` | feature/phase1-validation | b9b146f | In Review | PASS | automation | 2026-03-24 |
| 2 | `.cursor/agents/verifier.md` | feature/phase1-validation | b9b146f | In Review | PASS | automation | 2026-03-24 |
| 3 | `docs/hooks-mapping.yaml` | feature/phase1-validation | b9b146f | In Review | PASS | automation | 2026-03-24 |
| 3 | `.cursor/hooks/send_event.py` | feature/phase1-validation | b9b146f | In Review | PASS | automation | 2026-03-24 |
| 3 | `.cursor/hooks/pre_tool_use.py` | feature/phase1-validation | b9b146f | In Review | PASS | automation | 2026-03-24 |
| 3 | `.cursor/hooks/post_tool_validate.py` | feature/phase1-validation | b9b146f | In Review | PASS | automation | 2026-03-24 |
| 3 | `.cursor/hooks/stop_validator.py` | feature/phase1-validation | b9b146f | In Review | PASS | automation | 2026-03-24 |
| 3 | `.cursor/hooks/session_start.py` | feature/phase1-validation | b9b146f | In Review | PASS | automation | 2026-03-24 |
| 4 | `docs/events.yaml` | feature/phase1-validation | b9b146f | In Review | PASS | automation | 2026-03-24 |
| 4 | `apps/server/src/adapter.ts` | feature/phase1-validation | b9b146f | In Review | PASS | automation | 2026-03-24 |
| 5 | `.cursor/hooks/bootstrap_worktree.sh` | feature/phase1-validation | b9b146f | In Review | PASS | automation | 2026-03-24 |
| 5 | `docs/worktree-decision-matrix.md` | feature/phase1-validation | b9b146f | In Review | PASS | automation | 2026-03-24 |
| 6 | `docs/pilot-report.md` | feature/phase1-validation | df10ae3 | In Review | PASS | automation + manual | 2026-03-24 |
| 7 | `docs/reference/decision-record.md` | feature/phase1-validation | b9b146f | In Review | PASS | automation | 2026-03-24 |

## Extended Components (Post-Stage 7)

### Hook Scripts

| Category | Artifact | Status | Notes |
|----------|----------|--------|-------|
| Hook | `.cursor/hooks/before_submit_prompt.py` | Added | Replaces Claude UserPromptSubmit |
| Hook | `.cursor/hooks/session_end.py` | Added | Session completion logging |
| Hook | `.cursor/hooks/subagent_start.py` | Added | Subagent lifecycle logging |
| Hook | `.cursor/hooks/post_tool_use_failure.py` | Added | Tool failure debugging |
| Hook | `.cursor/hooks/pre_compact.py` | Added | Context compaction observer |
| Hook | `.cursor/hooks/after_file_edit.py` | Added | Auto-format after edits |

### Validators

| Category | Artifact | Status | Notes |
|----------|----------|--------|-------|
| Validator | `.cursor/hooks/validators/validate_file_contains.py` | Added | Optional content-check helper (not on shipped `stop` by default) |
| Validator | `.cursor/hooks/validators/validate_new_file.py` | Added | Optional file-existence helper (not on shipped `stop` by default) |

### Hook Utilities

| Category | Artifact | Status | Notes |
|----------|----------|--------|-------|
| Utility | `.cursor/hooks/utils/constants.py` | Added | Shared paths and session helpers |
| Utility | `.cursor/hooks/utils/summarizer.py` | Added | LLM-based event summarization |
| Utility | `.cursor/hooks/utils/hitl.py` | Added | HITL WebSocket decision system |
| LLM | `.cursor/hooks/utils/llm/anth.py` | Added | Anthropic Haiku 4.5 client |
| LLM | `.cursor/hooks/utils/llm/oai.py` | Added | OpenAI GPT-4.1-nano client |
| TTS | `.cursor/hooks/utils/tts/elevenlabs_tts.py` | Added | ElevenLabs Flash v2.5 |
| TTS | `.cursor/hooks/utils/tts/openai_tts.py` | Added | OpenAI gpt-4o-mini-tts |
| TTS | `.cursor/hooks/utils/tts/pyttsx3_tts.py` | Added | Offline TTS (no API key) |

### Commands

| Category | Artifact | Status | Notes |
|----------|----------|--------|-------|
| Command | `.cursor/commands/mat-plan.md` | Added | Solo planning |
| Command | `.cursor/commands/mat-prime.md` | Added | Codebase context loader |
| Command | `.cursor/commands/mat-question.md` | Added | Read-only Q&A |
| Command | `.cursor/commands/mat-git-status.md` | Added | Git state summary |
| Command | `.cursor/commands/mat-wt-create.md` | Added | Worktree creation |
| Command | `.cursor/commands/mat-wt-list.md` | Added | Worktree listing |
| Command | `.cursor/commands/mat-wt-remove.md` | Added | Worktree removal |
| Command | `.cursor/commands/mat-start.md` | Added | Observability startup |
| Style | `.cursor/commands/output-styles/concise.md` | Added | Brief output style |
| Style | `.cursor/commands/output-styles/detailed.md` | Added | Detailed output style |
| Style | `.cursor/commands/output-styles/report.md` | Added | Report output style |

### Agents

| Category | Artifact | Status | Notes |
|----------|----------|--------|-------|
| Agent | `.cursor/agents/meta-agent.md` | Added | Agent factory |
| Agent | `.cursor/agents/scout-report-suggest.md` | Added | Read-only codebase analysis |
| Agent | `.cursor/agents/docs-scraper.md` | Added | Documentation fetching |
| Agent | `.cursor/agents/create-worktree-subagent.md` | Added | Worktree automation |
| Agent | `.cursor/agents/demo-agent.md` | Added | Workflow demonstration |

### Skills

| Category | Artifact | Status | Notes |
|----------|----------|--------|-------|
| Skill | `.cursor/skills/meta-skill/SKILL.md` | Added | Skill creation guide |
| Skill | `.cursor/skills/worktree-manager/SKILL.md` | Added | Worktree lifecycle management |
| Skill | `.cursor/skills/create-worktree/SKILL.md` | Added | Lightweight worktree creation |

### Phase 4 — MAO advisory evidence maturity (in progress)

| Category | Artifact | Status | Notes |
|----------|----------|--------|-------|
| Doc | `docs/mao-advisory-go-criteria.md` | Added | Procedures + PASS/INCONCLUSIVE for advisory go-criteria |
| Artifact | `artifacts/phase1/mao-advisory-go-criteria-template.md` | Added | Redacted audit template |
| Artifact | `artifacts/phase1/mao-advisory-go-criteria-audit-20260329.md` | Added | Example audit row (template v1) |
| Spec | `specs/phase-4-planning-session.md` | Added | Phase 4 planning (planning-only session) |

### Phase 2 — MAO todo orchestration (MVP)

| Category | Artifact | Status | Notes |
|----------|----------|--------|-------|
| Rule | `.cursor/rules/orchestrator-todos.mdc` | Added | Composer rule: TodoWrite + three-task MAO convention |
| Doc | `docs/reference/todo-orchestration.md` | Added | Tags, statuses, dependency semantics, hooks |
| Doc | `docs/todo-orchestration-pilot.md` | Added | Manual E2E pilot checklist |
| Agent / command | `parent-orchestrator.md`, `builder.md`, `verifier.md`, `mat-plan-team.md`, `mat-build.md`, `mat-review.md` | Modified | Aligned with protocol |
| Hook | `.cursor/hooks/mao_gate.py` | Added | Post-build gate JSON; invoked from `post_tool_validate.py` when `build-result.md` is touched |
| Test | `tests/test_mao_gate.py` | Added | Gate evaluation + env disable |
| Artifact dir | `artifacts/mao/README.md` | Added | `gate.json` documented (file gitignored) |

### Audit remediation (2026-06)

| Category | Artifact | Branch | Commit SHA | Review Status | Acceptance | Notes |
|----------|----------|--------|------------|---------------|------------|-------|
| Audit P0-1 | Worktree contract alignment (Cursor 3 + bootstrap) | `main` | `7b79d27` | Approved | PASS | Docs + `bootstrap_worktree.sh` apps install |
| Audit P0-2 | Stop-validator honesty | `main` | `af2a45d` | Approved | PASS | `StopValidatorHonestyDocsTest` |
| Audit P0-3 | Observability security guardrails | `main` | `4c17b6d` | Approved | PASS | `ObservabilitySecurityHonestyDocsTest`; `docs/architecture/events-and-visualization.md`, `docs/reference/MAINTAINER.md` |
| Docs hygiene | Audit remediation doc sync + inventory hygiene | `main` | `4c17b6d` | Approved | PASS | README Docs ownership; components path; AGENTS/MAINTAINER/meta-skill; `.gitignore` macOS patterns |
| Adoption | Legacy manifest + provenance + verify-all | `main` | `9fb30a6` | Approved | PASS | Fingerprint CI |
| Adoption | Legacy manifest command expansion (12 entries) | `main` | `0a3012d` | Approved | PASS | Pre-`mat-*` slash commands |
| Report | `artifacts/report/mat-audit-report.md` | `main` | — | Living doc | — | Remediation status section; P0-3 Done; P1 stale-docs Done (2026-06-22) |
| Client CI | Dependabot vite advisory + client CI gate | `main` | `ad29d97` | Approved | PASS | vite@8.0.16; GHSA-4w7w-66w2-5vf9 remediated |
| Audit P1 | Stale docs + command link drift (server README, features-demonstrated, mat-subagents-spawn, audit RFU-6) | `main` | `aec850c` | Approved | PASS | `P1StaleDocsHonestyTest`; RFU-6 Done |
| Audit P2 | Observability retention/sampling policy + completion roadmap | `main` | `043e653` | Approved | PASS | `docs/architecture/observability-retention-policy.md`; `ObservabilityRetentionPolicyDocsTest`; audit Phase A/B/C roadmap |
| Audit P2 | Orchestration strategy — worktree hybrid defer + subagent non-goals (Phase A A2+A3) | `main` | `7d3c195` | Approved | PASS | `docs/decision-record.md` P2 sections; `P2OrchestrationStrategyDocsTest`; completes audit P2 tier |
| Audit P1 B1 | Worktree + validator honesty contract coverage (Phase B B1) | `main` | `8fe0bb0` | Approved | PASS | `P1WorktreeValidatorContractDocsTest`; `docs/pilot-report.md` stop hook row |
| Audit P1 B2 | Skills vs commands routing (Phase B B2) | `main` | `7cc94dd` | Approved | PASS | `P1SkillsCommandsRoutingDocsTest`; `docs/reference/decision-record.md#p1-audit--skills-vs-commands-routing` |
| Audit P1 B3 | Cloud Agents / Agents Window refresh (Phase B B3) | `main` | `9b1abf2` | Approved | PASS | `P1CloudAgentsAgentsWindowDocsTest`; `docs/decision-record.md#p1-audit--cloud-agents-agents-window`; completes Phase B |
| Audit Phase C C2 | RFU-3 Node 22 CI pin | `main` | `b1266fa` | Approved | PASS | `RFU3NodePinCiTest`; `actions/setup-node@v4` in `phase1-verify.yml`; warn-only `node -v` in `phase1-verify.sh` |
| Audit Phase C C3+C4 | RFU-1 vitest-only CI + RFU-2 frozen lockfile | `main` | `555c78b` | Approved | PASS | `RFU1VitestOnlyCiTest`; `RFU2FrozenLockfileTest`; client block in `phase1-verify.sh` |
| Audit Phase C C5 | RFU-4 Dependabot + client CI doc hygiene | `main` | `a6dfc44` | Approved | PASS | `RFU4DependabotConfigTest`; `RFU1ClientCiDocsHygieneTest`; `.github/dependabot.yml` |
| MAT updater slice 2 | CI wiring + integration harness | `main` | `631f507` | Approved | PASS |
| MAT updater slice 3 | Operator polish, adoption docs, security closeout | `main` | `1be2635` | Approved | PASS |
| MAT updater operator demo walkthrough | Recorded slice 3 operator demo script + evidence artifact | `main` | `091d65e` | Approved | PASS |
| Adoption | Observability appendix for adopted repos (docs-only) | `main` | `5d85201` | Approved | PASS | `docs/adoption-observability-appendix.md`; `MatAdoptionObservabilityAppendixTest`; RFU-7 deferral honesty; bootstrap copy to `.mat/docs/` |
| Adoption | Disposable observability appendix pilot (bootstrap + update-mat dry-run) | `main` | `48464e3` | Approved | PASS | `artifacts/report/adoption-observability-pilot-2026-06-23.md`; appendix in `.mat/docs/`; `AGENTS.md` preserved |
| Adoption | Real-repo pilot — rank-math-api-manager (disposable clone dry-run + bootstrap) | `main` | `0c7a341` | Approved | PASS | `artifacts/report/adoption-rank-math-api-manager-pilot-2026-06-24.md`; pilot evidence `3173032`; bootstrap-before-dry-run; operator-doc polish; no plugin PHP changes |
| Adoption | Production — rank-math-api-manager (MAT PR #3 + release v1.0.9.2) | `main` | `b818857` | Approved | PASS | Plugin [PR #3](https://github.com/Devora-AS/rank-math-api-manager/pull/3) MAT bootstrap @ `e4502fd`; [PR #4](https://github.com/Devora-AS/rank-math-api-manager/pull/4) @ `87faa3d`; CI 5/5; [v1.0.9.2](https://github.com/Devora-AS/rank-math-api-manager/releases/tag/v1.0.9.2); Phase E closeout in pilot report production footer |

---

## Gate Results Summary

| Gate | Status | Notes |
|------|--------|-------|
| Hook Gate | Pass | Automated tests + live lifecycle closure set recorded in `artifacts/phase1/raw_payloads-final3/`; terminal fallback provenance documented |
| Agent Gate | Pass | Cursor `/mat-plan-team` end-to-end run completed and recorded in `docs/phase1-validation-report.md` |
| Observability Gate | Pass | Bun server and Vue client are both vendored and validated; see `docs/phase1-validation-report.md` |
| Parallelism Gate | Pass | `scripts/parallelism-gate.sh` validated manually; evidence tracked in Phase 1 docs |
| Optional Tooling Gate | Pass | `scripts/phase1-verify.sh` validates `.cursor/mcp.json` parses (Phase 1 baseline) |

---

## How to Update This File

After each stage, update the relevant rows:
- **Branch**: The migration branch name (e.g., `migrate/cursor/1-layout`)
- **Commit SHA**: Short SHA of the commit containing the artifact
- **Review Status**: `Pending` | `In Review` | `Approved`
- **Acceptance**: `Pending` | `PASS` | `FAIL`
- **Reviewer**: Initials of reviewer
- **Date**: Date of acceptance decision

Do not advance to the next stage until all artifacts for the current stage show `PASS`.
