// Generative-Improve #8/8 — Workflow Efficiency R2
// Co-authored-by: Muse Spark <muse-spark@meta.com>
// Improves generative data quality while preserving:
//   - early-stop on <5% novel coverage for 2 consecutive rounds
//   - token-efficiency 40% saving mode (docs/token-efficiency.md)
//   - 5-lane per-factory circuit breaker (parallel lanes isolate failures)
// See docs/token-efficiency.md for threshold tuning and savings breakdown.

export const meta = {
  name: 'synthetic-factory-window',
  description: 'Bounded five-factory window with transactional round publication, per-factory circuit breakers, and token-efficiency early-stop (40% saving mode)',
  phases: [
    { title: 'Generate', detail: 'at most five concurrent factories; rounds are sequential inside each factory — generative quality via gap-aware densification' },
    { title: 'Verify', detail: 'one bounded read-only marker check after each generated round; only verified rounds count for coverage' },
  ],
}

// args: { date: "YYYY-MM-DD", root: "/abs/path/to/synthetic-factory",
//         starts: {"thalamic-trajectory-factory": 12, ...},
//         end: 26, tokenEfficiency: true|false }
// Always launch a fresh workflow after snapshot + audit. Never resume a prior
// parallel workflow: cached interleavings are not a safe round allocator.

const SUMMARY = {
  type: 'object',
  required: [
    'factory',
    'round',
    'files',
    'trajectory_count',
    'completion_marker',
    'coverage_notes',
    'remaining_gaps',
  ],
  properties: {
    factory: { type: 'string' },
    round: { type: 'number' },
    files: { type: 'array', items: { type: 'string' } },
    trajectory_count: { type: 'number' },
    completion_marker: { type: 'string' },
    coverage_notes: { type: 'string' },
    remaining_gaps: { type: 'string' },
  },
}

const VERIFICATION = {
  type: 'object',
  required: ['factory', 'round', 'verified', 'next_round', 'records', 'completion_marker', 'reason'],
  properties: {
    factory: { type: 'string' },
    round: { type: 'number' },
    verified: { type: 'boolean' },
    next_round: { type: 'number' },
    records: { type: 'number' },
    completion_marker: { type: 'string' },
    reason: { type: 'string' },
    // Independently read from the PUBLISHED NOTES file by the verifier —
    // the token-efficiency early-stop uses this and ONLY this, so a
    // generation agent's self-report can never drive lane termination.
    // Required: a verifier that cannot read the line must say so with an
    // explicit null rather than omitting the field.
    novel_coverage_pct: { type: ['number', 'null'] },
  },
  required: ['factory', 'round', 'verified', 'next_round', 'records', 'completion_marker', 'reason', 'novel_coverage_pct'],
}

// Session-A staging handoff for the failure-as-fuel two-session protocol.
const PREF_STAGE = {
  type: 'object',
  required: ['factory', 'round', 'staging_dir', 'reserve_token', 'diagnosis_files'],
  properties: {
    factory: { type: 'string' },
    round: { type: 'number' },
    staging_dir: { type: 'string' },
    reserve_token: { type: 'string' },
    diagnosis_files: { type: 'array', items: { type: 'string' } },
  },
}

// Abort receipt: confirm CLI ran. Not a Session A handoff — do not reuse PREF_STAGE
// (that schema requires staging_dir / reserve_token / diagnosis_files this prompt
// does not supply, so structured-output validation would fail the release).
const ABORT_RECEIPT = {
  type: 'object',
  required: ['factory', 'round', 'aborted'],
  properties: {
    factory: { type: 'string' },
    round: { type: 'number' },
    aborted: { type: 'boolean' },
    reason: { type: 'string' },
  },
}

// Generative quality: each factory's quota explicitly demands scenario diversity,
// gap-targeting, and training value. The prompt (below) reinforces this by
// requiring densification of under-represented gaps and honest novel-coverage
// self-assessment. This maximizes unique scenario yield per token.
const FACTORIES = [
  {
    slug: 'thalamic-trajectory-factory',
    name: 'Thalamic Trajectory Factory',
    file: '01-thalamic-trajectory-factory.md',
    count: 5,
    quota: 'Generate 5 new, long ThalamicTrajectory objects spanning successes, partial failures with recovery, all three gate decisions, long-horizon consequences, and neuromorphic temporal dynamics. Maximize scenario diversity — target documented gaps and under-represented failure modes; do not reuse a prior scenario or edge.',
    extra: '',
  },
  {
    slug: 'multi-agent-ouroboros-swarm',
    name: 'Multi-Agent Ouroboros Swarm',
    file: '02-multi-agent-ouroboros-swarm.md',
    count: 1,
    quota: 'Run the full six-role swarm on one new complex agentic and neuromorphic scenario for at least two densification cycles, then emit one final ThalamicTrajectory. Ensure the scenario explores a novel coordination failure or recovery pattern not seen in prior rounds.',
    extra: ' Also put the complete labeled transcript in swarm-transcript-r{RR}.md inside the staging directory.',
  },
  {
    slug: 'neuromorphic-event-language-bridge',
    name: 'Neuromorphic Event + Language Bridge',
    file: '03-neuromorphic-event-language-bridge.md',
    count: 3,
    quota: 'Generate 3 new bridge pairs. Every spike stream must be globally time-ordered, use finite timestamps/amplitudes, include realistic refractory behavior, adaptation and noise, and contain at least 48 events. Vary channels, temporal motifs, and language grounding across pairs to maximize coverage.',
    extra: '',
  },
  {
    slug: 'failure-as-fuel-preference-cascade',
    name: 'Failure-as-Fuel Preference Cascade',
    file: '05-failure-as-fuel-preference-cascade.md',
    count: 3,
    quota: 'Generate 3 new preference records. Chosen and rejected must share the exact same state and proposed action; vary only the gate/execution/recovery quality needed to teach the preference. Cover distinct failure modes and recovery strategies across the 3 records.',
    extra: ' Put the diagnoses in diagnosis-r{RR}.md inside the staging directory.',
  },
  {
    slug: 'agentic-coding-trajectory-factory',
    name: 'Agentic Coding Trajectory',
    file: '04-agentic-coding-trajectory-factory.md',
    count: 2,
    quota: 'Generate 2 new long coding-agent episodes with observable decision bases, realistic tool output, failed attempts, plan changes, recovery, and measured outcomes. Each episode must explore a different bug class or tool-interaction pattern. Never emit hidden chain-of-thought.',
    extra: '',
  },
]

// ── Token-efficiency: 40% saving mode ──────────────────────────────
// Documented in docs/token-efficiency.md. Enabled by default; disable
// with args.tokenEfficiency=false. The 40% figure is the median saving
// across sf-0qz windows when plateau detection cuts the ~40% tail of
// diminishing-novelty rounds (generation + verification tokens).
// Rule: 2 consecutive NOTES with <5% novel coverage → per-factory stop.
// Parsing is line-anchored to the labeled "Novel coverage: N%" line only
// (case-insensitive; mirrors driver.py NOVEL_COVERAGE_RE) so unrelated
// percentages in NOTES prose can never be misread as coverage. Unparseable
// NOTES hold the streak (neither increment nor reset) to avoid false stops
// or hidden plateaus.
const TOKEN_EFFICIENCY = {
  enabled: !(args && args.tokenEfficiency === false),
  novelThresholdPct: 5,
  consecutiveLimit: 2,
  expectedSavingPct: 40,
  docs: 'docs/token-efficiency.md',
}

function novelCoveragePct(notesText) {
  if (!notesText || typeof notesText !== 'string') return null
  // Matches only the labeled line: "Novel coverage: 4.2%", "novel_coverage = 3%",
  // "Novel coverage 12.5 %". Anchored at line start so prose like
  // "...feel novel; Jaccard overlap peaked at 45%" can never match.
  // An optional parenthetical annotation is documented as valid
  // (docs/token-efficiency.md): "Novel coverage (estimated): 12.5 %".
  const labeledLines = notesText
    .split(/\r\n|\n|\r/)
    .filter((line) => /^[^\S\r\n]*novel[ _-]?coverage\b/i.test(line))
  // More than one labeled line is ambiguous, even if both values agree. The
  // complete-line match also rejects malformed labels and a second same-line
  // label instead of silently accepting a valid prefix.
  if (labeledLines.length !== 1) return null
  const match = labeledLines[0].match(/^[^\S\r\n]*novel[ _-]?coverage[^\S\r\n]*(?:\([^)\r\n]*\))?[^\S\r\n]*[:=]?[^\S\r\n]*(\d+(?:\.\d+)?)[^\S\r\n]*%[^\S\r\n]*$/i)
  if (!match) return null
  const v = parseFloat(match[1])
  if (!Number.isFinite(v)) return null
  // Clamp to valid percentage range; out-of-range treated as unparseable.
  if (v < 0 || v > 100) return null
  return v
}

function isLowNovel(pct) {
  return pct !== null && pct < TOKEN_EFFICIENCY.novelThresholdPct
}

const END_ROUND = (args && args.end) || 26
const STARTS = (args && args.starts) || {}
log(`Transactional factory window: starts ${JSON.stringify(STARTS)}, backstop r${END_ROUND}.`)
if (TOKEN_EFFICIENCY.enabled) {
  log(`Token-efficiency: early-stop armed — ${TOKEN_EFFICIENCY.consecutiveLimit} consecutive NOTES <${TOKEN_EFFICIENCY.novelThresholdPct}% novel coverage → stop (target ~${TOKEN_EFFICIENCY.expectedSavingPct}% saving, see ${TOKEN_EFFICIENCY.docs}). Disable with args.tokenEfficiency=false.`)
}

// ── 5-lane circuit breaker ─────────────────────────────────────────
// Each factory runs in its own async lane via parallel(FACTORIES.map(...)).
// A lane breaks (break) on: agent error/session limit, identity mismatch,
// or failed marker verification — later rounds for that factory are not
// queued, preventing a storm of doomed agents. Other lanes continue
// independently. Early-stop is a clean break (not an error) with the same
// isolation guarantee.
// Release an unpublished reservation (best effort) so one failed round does
// not block a factory's frontier for the rest of the run. Safe by design:
// round_txn abort refuses to touch a mid-publish or completed round.
// Mid-publish is not a successful abort — inspect the receipt and resume
// publish so a still-held reservation cannot silently block the frontier.
async function releaseReservation(factory, round, rr, token) {
  const outDir = `${args.root}/outputs/raw/${args.date}/${factory.slug}`
  const reservedPath = `${outDir}/ROUND-r${rr}.reserved.json`
  log(`${factory.slug} r${rr}: releasing unpublished reservation so the frontier stays retryable`)
  const tokenArg = token || '<same-token>'
  const abortCmd = token
    ? `python3 ${args.root}/pipelines/round_txn.py abort ${outDir} --round ${round} --token ${token}`
    : `Read the "token" field from ${reservedPath} (if that file is missing, the reservation is already gone — set aborted=true and stop), then run:\npython3 ${args.root}/pipelines/round_txn.py abort ${outDir} --round ${round} --token <that-token>`
  try {
    const receipt = await agent(`Run this abort and report its result. Do not generate or edit staged files.

${abortCmd}

If abort succeeds, or reports the round is already committed, or that there is no reservation, the reservation is gone — return factory="${factory.slug}", round=${round}, aborted=true.
If abort reports the round is mid-publish, that is NOT success: the reservation is still held. Resume the existing publication with the same token (do not invent files):
python3 ${args.root}/pipelines/round_txn.py publish ${outDir} --round ${round} --token ${tokenArg}
If that publish succeeds, the reservation is gone — return aborted=true and reason="resumed mid-publish". Otherwise return aborted=false and a short reason.`, {
      label: `${factory.slug}:r${rr}-abort`,
      phase: 'Generate',
      schema: ABORT_RECEIPT,
    })
    if (!receipt || receipt.aborted !== true) {
      const reason = (receipt && receipt.reason) || 'abort did not confirm release'
      log(`${factory.slug} r${rr}: reservation still held (${reason}); frontier may stay blocked`)
    }
  } catch (err) {
    log(`${factory.slug} r${rr}: reservation release failed (frontier may stay blocked): ${err}`)
  }
}

const perFactory = await parallel(FACTORIES.map(factory => async () => {
  const start = STARTS[factory.slug]
  if (!Number.isInteger(start) || start < 1) {
    log(`${factory.slug}: missing or invalid positive-integer start; skipping`)
    return { factory: factory.slug, rounds_completed: 0, records_written: 0, stopped_reason: 'invalid start' }
  }

  const outDir = `${args.root}/outputs/raw/${args.date}/${factory.slug}`
  let completed = 0
  let records = 0
  let stoppedReason = 'backstop reached'
  let consecutiveLowNovel = 0

  for (let round = start; round <= END_ROUND; round++) {
    const rr = String(round).padStart(2, '0')
    const expectedMarker = `${outDir}/ROUND-r${rr}.complete.json`
    const prompt = `You are the "${factory.name}" subagent for the Spikenaut / Agoge / Thalamic-Relay Synthetic Data Factory, run ${args.date}, round ${round}.

FILE-SAFETY AND COMMIT PROTOCOL — highest priority:
1. NEVER write, edit, rename, truncate, or delete any existing file under ${outDir}. Never invent a collision suffix.
2. Reserve exactly this round before generating:
   python3 ${args.root}/pipelines/round_txn.py reserve ${outDir} --round ${round} --expected ${factory.count}
3. Parse that command's JSON. Write every new artifact ONLY inside its returned staging_dir, using exactly its batch_file and notes_file names. If reservation fails, do not write anything and stop.
4. After generation and self-critique, publish with:
   python3 ${args.root}/pipelines/round_txn.py publish ${outDir} --round ${round} --token <returned-token>
   Publishing enforces exact quota, record shape, reward arithmetic, canonical IDs, canonical provenance, spike ordering, and no-clobber behavior. If it reports a validation finding, repair only your staged files and retry publish. Never bypass the publisher.
5. A round exists only if publish succeeds and creates ${expectedMarker}. Do not claim completion before then.

Setup:
- Read and obey ${args.root}/prompts/_factory-contract.md and ${args.root}/prompts/${factory.file}.
- Read ${args.root}/schemas/thalamic-trajectory-v2.schema.json and ${args.root}/schemas/provenance.md.
- Read the two newest NOTES files and skim the newest committed batch in ${outDir}; target documented gaps and avoid scenario repetition.
- Every top-level record needs a globally unique "id". Every expected state needs state.sim_or_real exactly one of designed | simulated | hil. Synthetic scenarios are designed, never real.
- Use concise observable evidence and decision bases. Do not emit private hidden reasoning or chain-of-thought.

Quota:
${factory.quota}

Generative quality (maximize training value per token):
- Prioritize densification of remaining gaps noted in prior NOTES-rNN.md; avoid near-duplicate scenarios/edges.
- Ensure realism: noisy sensors, refractory/adaptation dynamics, plausible tool outputs, and recovery paths where applicable.
- Be honest in self-assessment — if novelty is low, report it accurately.

Write a substantive self-critique to the staged NOTES-r${rr}.md: edge cases, realism/noise, neuromorphic or agentic training value, weaknesses, and the next densification target. Include a line "Novel coverage: <N>%" estimating the fraction of this round's scenarios/edges that are novel vs prior rounds (used for token-efficiency early-stop: 2 consecutive rounds <5% triggers stop — saving ~40% tokens on plateau; be honest even if <5%). Repeat the identical "Novel coverage: <N>%" line verbatim inside your returned coverage_notes.${factory.extra.replaceAll('{RR}', rr)}

Data contract:
- Exactly ${factory.count} JSON objects in staged batch-r${rr}.jsonl, one complete object per line, no Markdown fences or commentary.
- Long, concrete, internally consistent records; no placeholders and no copied prior scenario.
- Reward total must follow one explicitly declared aggregation and reconcile numerically.
- Return only the structured summary after successful publication. Set completion_marker exactly to "${expectedMarker}".`

    let result
    // Preference Session A owns the reservation; hoist the token so Session B
    // identity failure AND later verification/circuit-break can still abort.
    let reserveToken = null
    if (factory.slug === 'failure-as-fuel-preference-cascade') {
      // Two-session isolation (docs/preference-isolation.md): Session A and
      // Session B are SEPARATE agents with independent generation contexts —
      // the only inter-session bridge is the diagnosis artifacts.
      const sessionA = await agent(`You are Session A (failure mining) of the "${factory.name}" two-session protocol, run ${args.date}, round ${round}.

FILE-SAFETY — highest priority: NEVER write, edit, rename, truncate, or delete any existing file under ${outDir}. Reserve exactly this round first:
  python3 ${args.root}/pipelines/round_txn.py reserve ${outDir} --round ${round} --expected ${factory.count}
Parse its JSON; write ONLY inside the returned staging_dir. If reservation fails, stop without writing.

Read and obey ${args.root}/prompts/_factory-contract.md and the "Session A" section of ${args.root}/prompts/${factory.file}, plus ${args.root}/schemas/thalamic-trajectory-v2.schema.json and ${args.root}/schemas/provenance.md.

Produce EXACTLY ${factory.count} rejected ThalamicTrajectories and their diagnoses in staging: rejected-01-r${rr}.json, rejected-02-r${rr}.json, rejected-03-r${rr}.json scratch files (one JSON object each; never .jsonl) and diagnosis-01-r${rr}.md, diagnosis-02-r${rr}.md, diagnosis-03-r${rr}.md files, each diagnosis containing the Shared-context state/proposed_action JSON block, root cause, cascade effects, supervisor catch, repair sketch, and target reward delta per the prompt. Do NOT write batch-r${rr}.jsonl, do NOT publish, and do NOT draft any chosen content.

Return the structured handoff: factory="${factory.slug}", round=${round}, the reservation's staging_dir and token (reserve_token), and the diagnosis filenames.`, {
        label: `${factory.slug}:r${rr}-sessionA`,
        phase: 'Generate',
        schema: PREF_STAGE,
      })
      if (!sessionA || sessionA.factory !== factory.slug || sessionA.round !== round) {
        stoppedReason = `r${rr} session A failed or returned mismatched identity`
        log(`${factory.slug}: ${stoppedReason}; circuit open`)
        // sessionA may be null after a successful reserve (agent/session error);
        // pass any token we have, otherwise abort reads ROUND-rNN.reserved.json.
        await releaseReservation(factory, round, rr, sessionA && sessionA.reserve_token)
        break
      }
      reserveToken = sessionA.reserve_token
      result = await agent(`You are Session B (repair synthesis) of the "${factory.name}" two-session protocol, run ${args.date}, round ${round} — a FRESH context with no Session A memory.

FILE-SAFETY — highest priority: NEVER write, edit, rename, truncate, or delete any existing file under ${outDir}. Session A already reserved this round; its staging_dir is ${sessionA.staging_dir} and the publish token is ${sessionA.reserve_token}.

Read and obey ${args.root}/prompts/_factory-contract.md and the "Session B" section of ${args.root}/prompts/${factory.file}, plus ${args.root}/schemas/thalamic-trajectory-v2.schema.json.

ISOLATION RULE (absolute): read ONLY these diagnosis files from staging: ${JSON.stringify(sessionA.diagnosis_files)}. NEVER read any rejected-*-r${rr}.json into your context. Synthesize one repaired chosen ThalamicTrajectory per diagnosis (byte-identical state/proposed_action from each Shared-context block, fresh safety rationale), then assemble batch-r${rr}.jsonl MECHANICALLY via a python3 script that json-loads each rejected scratch file and injects it (with your chosen, a critique, script-computed reward_delta = chosen - rejected per component, and meta.isolation="two-session") without printing the rejected content. Write the staged NOTES-r${rr}.md self-critique including the "Novel coverage: <N>%" line, run the prompt's purity check commands (both must exit 0), then publish:
  python3 ${args.root}/pipelines/round_txn.py publish ${outDir} --round ${round} --token ${sessionA.reserve_token}
A round exists only if publish succeeds and creates ${expectedMarker}. Repeat the identical "Novel coverage: <N>%" line verbatim inside your returned coverage_notes. Return only the structured summary after successful publication; set completion_marker exactly to "${expectedMarker}".`, {
        label: `${factory.slug}:r${rr}-sessionB`,
        phase: 'Generate',
        schema: SUMMARY,
      })
    } else {
      result = await agent(prompt, {
        label: `${factory.slug}:r${rr}`,
        phase: 'Generate',
        schema: SUMMARY,
      })
    }

    if (!result) {
      stoppedReason = `r${rr} agent error or session limit`
      log(`${factory.slug}: ${stoppedReason}; circuit open, later rounds will not be queued`)
      if (reserveToken) await releaseReservation(factory, round, rr, reserveToken)
      break
    }
    if (result.factory !== factory.slug || result.round !== round) {
      stoppedReason = `r${rr} returned mismatched identity`
      log(`${factory.slug}: ${stoppedReason}; circuit open`)
      if (reserveToken) await releaseReservation(factory, round, rr, reserveToken)
      break
    }
    const verificationPrompt = `Read-only verification only. Do not write, edit, delete, rename, or publish anything.

For factory ${factory.slug}, independently verify committed round ${round}:
1. Run: python3 ${args.root}/pipelines/round_txn.py frontier ${outDir}
2. Require its next_round to equal ${round + 1}.
3. Read ${expectedMarker}. Require factory=${factory.slug}, round=${round}, records=${factory.count}, and exactly one batch-r${rr}.jsonl entry with the recorded SHA-256. Verify every file listed in the marker exists under ${outDir} with the recorded byte count and SHA-256.
4. Read the published NOTES-r${rr}.md and find its line-anchored "Novel coverage: <N>%" line; set novel_coverage_pct to that number, or null if the line is absent or ambiguous.
5. Return only the structured verification. Set verified=true only when every check passes; records must come from the marker, not the generation agent's summary. Set completion_marker exactly to ${expectedMarker}.`
    const verification = await agent(verificationPrompt, {
      label: `${factory.slug}:verify-r${rr}`,
      phase: 'Verify',
      schema: VERIFICATION,
    })
    if (
      !verification
      || verification.factory !== factory.slug
      || verification.round !== round
      || verification.verified !== true
      || verification.next_round !== round + 1
      || verification.records !== factory.count
      || verification.completion_marker !== expectedMarker
    ) {
      stoppedReason = `r${rr} completion marker could not be independently verified`
      log(`${factory.slug}: ${stoppedReason}; circuit open`)
      // Matching SUMMARY without a successful publish still leaves the
      // reservation in place; abort so the frontier stays retryable.
      if (reserveToken) await releaseReservation(factory, round, rr, reserveToken)
      break
    }
    completed += 1
    records += verification.records
    log(`${factory.slug} r${rr}: marker-verified ${verification.records} records (window total ${records})`)

    // Token-efficiency early-stop. Source: the VERIFIER's independent
    // read of the published NOTES file (novel_coverage_pct) — never the
    // generation agent's self-report. Missing, null, or out-of-range
    // verifier readings are unparseable and hold the streak. Evaluated
    // AFTER verification so only committed rounds count. 5-lane breaker
    // semantics: early-stop is a clean per-lane break, not a
    // cross-factory error.
    if (TOKEN_EFFICIENCY.enabled) {
      // Verifier-sourced ONLY. A null/out-of-range value means the verifier
      // could not read a coverage line; that holds the streak (see below)
      // rather than falling back to the generation agent's self-report.
      const pct = typeof verification.novel_coverage_pct === 'number'
        && verification.novel_coverage_pct >= 0 && verification.novel_coverage_pct <= 100
        ? verification.novel_coverage_pct
        : null
      if (pct !== null && pct < TOKEN_EFFICIENCY.novelThresholdPct) {
        consecutiveLowNovel += 1
        log(`${factory.slug} r${rr}: novel coverage ${pct}% <${TOKEN_EFFICIENCY.novelThresholdPct}% (streak ${consecutiveLowNovel}/${TOKEN_EFFICIENCY.consecutiveLimit})`)
      } else if (pct !== null) {
        if (consecutiveLowNovel > 0) log(`${factory.slug} r${rr}: novel coverage ${pct}% resets low-streak`)
        consecutiveLowNovel = 0
      } else {
        // Unparseable coverage — do not count toward streak, but log for visibility.
        log(`${factory.slug} r${rr}: novel coverage unparseable from verifier; streak held at ${consecutiveLowNovel}`)
      }
      if (consecutiveLowNovel >= TOKEN_EFFICIENCY.consecutiveLimit) {
        const savedRounds = END_ROUND - round
        // Only claim a saving when rounds were actually avoided; a streak
        // completing exactly at the backstop saved nothing.
        stoppedReason = savedRounds > 0
          ? `early-stop: ${TOKEN_EFFICIENCY.consecutiveLimit} consecutive rounds <${TOKEN_EFFICIENCY.novelThresholdPct}% novel coverage (~${savedRounds} rounds + verifiers avoided; token-efficiency mode)`
          : `coverage plateau (${TOKEN_EFFICIENCY.consecutiveLimit} consecutive rounds <${TOKEN_EFFICIENCY.novelThresholdPct}%) reached at backstop r${rr}; no rounds saved`
        log(`${factory.slug}: ${stoppedReason}`)
        break
      }
    }
  }

  return {
    factory: factory.slug,
    rounds_completed: completed,
    records_written: records,
    stopped_reason: stoppedReason,
  }
}))

return { mode: 'transactional-window', end_round: END_ROUND, per_factory: perFactory.filter(Boolean) }
