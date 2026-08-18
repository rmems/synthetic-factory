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
// Parsing is tolerant (case-insensitive, "novel[^%]*?N%") and mirrors
// driver.py NOVEL_COVERAGE_RE. Unparseable NOTES hold the streak (neither
// increment nor reset) to avoid false stops or hidden plateaus.
const TOKEN_EFFICIENCY = {
  enabled: !(args && args.tokenEfficiency === false),
  novelThresholdPct: 5,
  consecutiveLimit: 2,
  expectedSavingPct: 40,
  docs: 'docs/token-efficiency.md',
}

function novelCoveragePct(notesText) {
  if (!notesText || typeof notesText !== 'string') return null
  // Matches "novel coverage 4.2%", "novel_coverage: 3%", "novel ... 12.5 %" etc.
  // Case-insensitive, tolerant of punctuation between "novel" and the number.
  const m = notesText.match(/novel[^%]*?(\d+(?:\.\d+)?)\s*%/i)
  if (!m) return null
  const v = parseFloat(m[1])
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

Write a substantive self-critique to the staged NOTES-r${rr}.md: edge cases, realism/noise, neuromorphic or agentic training value, weaknesses, and the next densification target. Include a line "Novel coverage: <N>%" estimating the fraction of this round's scenarios/edges that are novel vs prior rounds (used for token-efficiency early-stop: 2 consecutive rounds <5% triggers stop — saving ~40% tokens on plateau; be honest even if <5%).${factory.extra.replaceAll('{RR}', rr)}

Data contract:
- Exactly ${factory.count} JSON objects in staged batch-r${rr}.jsonl, one complete object per line, no Markdown fences or commentary.
- Long, concrete, internally consistent records; no placeholders and no copied prior scenario.
- Reward total must follow one explicitly declared aggregation and reconcile numerically.
- Return only the structured summary after successful publication. Set completion_marker exactly to "${expectedMarker}".`

    const result = await agent(prompt, {
      label: `${factory.slug}:r${rr}`,
      phase: 'Generate',
      schema: SUMMARY,
    })

    if (!result) {
      stoppedReason = `r${rr} agent error or session limit`
      log(`${factory.slug}: ${stoppedReason}; circuit open, later rounds will not be queued`)
      break
    }
    if (result.factory !== factory.slug || result.round !== round) {
      stoppedReason = `r${rr} returned mismatched identity`
      log(`${factory.slug}: ${stoppedReason}; circuit open`)
      break
    }
    const verificationPrompt = `Read-only verification only. Do not write, edit, delete, rename, or publish anything.

For factory ${factory.slug}, independently verify committed round ${round}:
1. Run: python3 ${args.root}/pipelines/round_txn.py frontier ${outDir}
2. Require its next_round to equal ${round + 1}.
3. Read ${expectedMarker}. Require factory=${factory.slug}, round=${round}, records=${factory.count}, and exactly one batch-r${rr}.jsonl entry with the recorded SHA-256. Verify every file listed in the marker exists under ${outDir} with the recorded byte count and SHA-256.
4. Return only the structured verification. Set verified=true only when every check passes; records must come from the marker, not the generation agent's summary. Set completion_marker exactly to ${expectedMarker}.`
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
      break
    }
    completed += 1
    records += verification.records
    log(`${factory.slug} r${rr}: marker-verified ${verification.records} records (window total ${records})`)

    // Token-efficiency early-stop: inspect coverage_notes for novel coverage.
    // NOTES themselves are the source of truth; the agent summary's coverage_notes
    // mirrors the staged NOTES-rNN.md content. Parse <5% threshold.
    // Evaluated AFTER verification so only committed rounds count. 5-lane breaker
    // semantics: early-stop is a clean per-lane break, not a cross-factory error.
    if (TOKEN_EFFICIENCY.enabled) {
      const pct = novelCoveragePct(result.coverage_notes)
      if (pct !== null && pct < TOKEN_EFFICIENCY.novelThresholdPct) {
        consecutiveLowNovel += 1
        log(`${factory.slug} r${rr}: novel coverage ${pct}% <${TOKEN_EFFICIENCY.novelThresholdPct}% (streak ${consecutiveLowNovel}/${TOKEN_EFFICIENCY.consecutiveLimit})`)
      } else if (pct !== null) {
        if (consecutiveLowNovel > 0) log(`${factory.slug} r${rr}: novel coverage ${pct}% resets low-streak`)
        consecutiveLowNovel = 0
      } else {
        // Unparseable coverage — do not count toward streak, but log for visibility.
        log(`${factory.slug} r${rr}: novel coverage unparseable from coverage_notes; streak held at ${consecutiveLowNovel}`)
      }
      if (consecutiveLowNovel >= TOKEN_EFFICIENCY.consecutiveLimit) {
        const savedRounds = END_ROUND - round
        const savingNote = savedRounds > 0 ? `, ~${TOKEN_EFFICIENCY.expectedSavingPct}% token saving (~${savedRounds} rounds + verifiers avoided)` : ''
        stoppedReason = `early-stop: ${TOKEN_EFFICIENCY.consecutiveLimit} consecutive NOTES <${TOKEN_EFFICIENCY.novelThresholdPct}% novel coverage (token-efficiency ~${TOKEN_EFFICIENCY.expectedSavingPct}% saving mode)`
        log(`${factory.slug}: ${stoppedReason}${savingNote}; stopping factory lane early — coverage plateau detected`)
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
