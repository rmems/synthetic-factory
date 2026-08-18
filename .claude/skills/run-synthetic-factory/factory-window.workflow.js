export const meta = {
  name: 'synthetic-factory-window',
  description: 'Bounded five-factory window with transactional round publication and per-factory circuit breakers',
  phases: [
    { title: 'Generate', detail: 'at most five concurrent factories; rounds are sequential inside each factory' },
    { title: 'Verify', detail: 'one bounded read-only marker check after each generated round' },
  ],
}

// args: { date: "YYYY-MM-DD", root: "/abs/path/to/synthetic-factory",
//         starts: {"thalamic-trajectory-factory": 12, ...},
//         end: 26 }
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

const FACTORIES = [
  {
    slug: 'thalamic-trajectory-factory',
    name: 'Thalamic Trajectory Factory',
    file: '01-thalamic-trajectory-factory.md',
    count: 5,
    quota: 'Generate 5 new, long ThalamicTrajectory objects spanning successes, partial failures with recovery, all three gate decisions, long-horizon consequences, and neuromorphic temporal dynamics. Do not reuse a prior scenario.',
    extra: '',
  },
  {
    slug: 'multi-agent-ouroboros-swarm',
    name: 'Multi-Agent Ouroboros Swarm',
    file: '02-multi-agent-ouroboros-swarm.md',
    count: 1,
    quota: 'Run the full six-role swarm on one new complex agentic and neuromorphic scenario for at least two densification cycles, then emit one final ThalamicTrajectory.',
    extra: ' Also put the complete labeled transcript in swarm-transcript-r{RR}.md inside the staging directory.',
  },
  {
    slug: 'neuromorphic-event-language-bridge',
    name: 'Neuromorphic Event + Language Bridge',
    file: '03-neuromorphic-event-language-bridge.md',
    count: 3,
    quota: 'Generate 3 new bridge pairs. Every spike stream must be globally time-ordered, use finite timestamps/amplitudes, include realistic refractory behavior, adaptation and noise, and contain at least 48 events.',
    extra: '',
  },
  {
    slug: 'failure-as-fuel-preference-cascade',
    name: 'Failure-as-Fuel Preference Cascade',
    file: '05-failure-as-fuel-preference-cascade.md',
    count: 3,
    quota: 'Generate 3 new preference records. Chosen and rejected must share the exact same state and proposed action; vary only the gate/execution/recovery quality needed to teach the preference.',
    extra: ' Put the diagnoses in diagnosis-r{RR}.md inside the staging directory.',
  },
  {
    slug: 'agentic-coding-trajectory-factory',
    name: 'Agentic Coding Trajectory',
    file: '04-agentic-coding-trajectory-factory.md',
    count: 2,
    quota: 'Generate 2 new long coding-agent episodes with observable decision bases, realistic tool output, failed attempts, plan changes, recovery, and measured outcomes. Never emit hidden chain-of-thought.',
    extra: '',
  },
]

const END_ROUND = (args && args.end) || 26
const STARTS = (args && args.starts) || {}
log(`Transactional factory window: starts ${JSON.stringify(STARTS)}, backstop r${END_ROUND}.`)

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

Write a substantive self-critique to the staged NOTES-r${rr}.md: edge cases, realism/noise, neuromorphic or agentic training value, weaknesses, and the next densification target.${factory.extra.replaceAll('{RR}', rr)}

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
  }

  return {
    factory: factory.slug,
    rounds_completed: completed,
    records_written: records,
    stopped_reason: stoppedReason,
  }
}))

return { mode: 'transactional-window', end_round: END_ROUND, per_factory: perFactory.filter(Boolean) }
