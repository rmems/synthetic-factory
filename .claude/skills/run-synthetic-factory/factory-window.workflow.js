export const meta = {
  name: 'synthetic-factory-window',
  description: 'One generation window: each factory loops generate → critique → densify from its start round, no-overwrite contract',
  phases: [
    { title: 'Generate', detail: 'per-factory independent round loops from the supplied start rounds' },
  ],
}

// args: { date: "YYYY-MM-DD", root: "/abs/path/to/synthetic-factory",
//         starts: {"thalamic-trajectory-factory": 12, ...},   // from driver.py frontiers --json
//         end: 26 }                                           // backstop round, inclusive
// Launch fresh each window (Workflow({scriptPath, args})). Do NOT use resumeFromRunId across
// windows: parallel-loop interleaving breaks the cache prefix and re-runs completed rounds.

const SUMMARY = {
  type: 'object',
  required: ['factory', 'round', 'files', 'trajectory_count', 'coverage_notes', 'remaining_gaps'],
  properties: {
    factory: { type: 'string' },
    round: { type: 'number' },
    files: { type: 'array', items: { type: 'string' } },
    trajectory_count: { type: 'number' },
    coverage_notes: { type: 'string' },
    remaining_gaps: { type: 'string' },
  },
}

const FACTORIES = [
  {
    slug: 'thalamic-trajectory-factory',
    name: 'Thalamic Trajectory Factory',
    file: '01-thalamic-trajectory-factory.md',
    quota: 'Generate 5 NEW long, diverse ThalamicTrajectory objects (mix success, partial failure + recovery, safety ACCEPT/MODIFY/REJECT interventions, long-horizon episodes, neuromorphic temporal dynamics, sparse events). No scenario overlap with ANY prior batch in the directory.',
    extra: '',
  },
  {
    slug: 'multi-agent-ouroboros-swarm',
    name: 'Multi-Agent Ouroboros Swarm',
    file: '02-multi-agent-ouroboros-swarm.md',
    quota: 'Run the full 6-agent swarm in character on 1 NEW complex agentic + neuromorphic scenario (distinct from all prior scenarios in the directory), at least 2 full densifying cycles, ending in 1 final schema-compliant ThalamicTrajectory in the batch file.',
    extra: ' Also write the complete labeled-by-agent transcript to a NEW swarm-transcript-r{RR}.md.',
  },
  {
    slug: 'neuromorphic-event-language-bridge',
    name: 'Neuromorphic Event + Language Bridge',
    file: '03-neuromorphic-event-language-bridge.md',
    quota: 'Generate 3 NEW paired artifacts in fresh modality mixes not yet covered in the directory, each {spike_events: [{channel, t_rel_ms, amplitude, ...}], language_view: {description, trajectory: <ThalamicTrajectory>}, bridge_notes: {mapping, training_value}}. Spike trains MUST be strictly time-ordered with realistic refractory gaps, adaptation, noise, and 48+ events per pair.',
    extra: '',
  },
  {
    slug: 'failure-as-fuel-preference-cascade',
    name: 'Failure-as-Fuel Preference Cascade',
    file: '05-failure-as-fuel-preference-cascade.md',
    quota: 'Produce 3 NEW preference records (failed trajectory + diagnosis + repaired gold version, packaged {failure_mode, rejected, chosen, critique, reward_delta}) rotating failure modes not yet covered in the directory.',
    extra: ' Append diagnoses to a NEW diagnosis-r{RR}.md.',
  },
  {
    slug: 'agentic-coding-trajectory-factory',
    name: 'Agentic Coding Trajectory',
    file: '04-agentic-coding-trajectory-factory.md',
    quota: 'Generate 2 NEW full, LONG multi-turn coding agent episodes ({goal, steps: [{n, thought, tool_call: {name, args}, observation, reflection}], outcome, reward}) with realistic tool noise, debugging loops, recovery, plan changes. Rotate domains and failure textures.',
    extra: '',
  },
]

const END_ROUND = (args && args.end) || 26
const STARTS = (args && args.starts) || {}
log(`Factory window: starts ${JSON.stringify(STARTS)}, backstop r${END_ROUND}. No-overwrite contract in force.`)

const perFactory = await parallel(FACTORIES.map(f => async () => {
  const start = STARTS[f.slug]
  if (!start) { log(`${f.slug}: no start round supplied — skipping factory`); return { factory: f.slug, rounds_completed: 0, records_written: 0 } }
  const outDir = `${args.root}/outputs/raw/${args.date}/${f.slug}`
  let completed = 0
  let records = 0
  for (let r = start; r <= END_ROUND; r++) {
    const rr = String(r).padStart(2, '0')
    const prompt = `You are the "${f.name}" subagent of the Spikenaut / Agoge / Thalamic-Relay Synthetic Data Factory — CONTINUOUS DENSIFICATION MODE, run ${args.date}, round ${r}.

ABSOLUTE FILE-SAFETY RULE, highest priority: NEVER overwrite, truncate, delete, or modify ANY existing file. Before every Write, check the target does not exist (ls the directory first). If ${outDir}/batch-r${rr}.jsonl already exists, write ${outDir}/batch-r${rr}c.jsonl instead; same pattern for any other name collision (append "c" before the extension). You may only CREATE new files. (Exception: you may update ${args.root}/outputs/raw/${args.date}/NEXT_ROUND.json, the shared frontier manifest.)

Setup, in order:
1. Read ${args.root}/prompts/${f.file} and adopt it COMPLETELY as your operating role.
2. Read ${args.root}/schemas/thalamic-trajectory.schema.json. Every ThalamicTrajectory you emit must satisfy it: six required keys (state, proposed_action, safety_decision, executed_action, future_outcome, reward_components) each an object; safety_decision.decision exactly one of ACCEPT | MODIFY | REJECT with non-empty rationale; reward_components decomposed with a total that reconciles arithmetically. Every trajectory gets "meta": {"factory": "${f.slug}", "run": "${args.date}", "round": ${r}, "tags": [...]}.
3. List ${outDir}/ and read the two MOST RECENT NOTES*.md files plus skim the newest batch (first ~40 lines) so you know what every earlier round covered and which gaps were flagged. Fix those gaps; never repeat prior scenarios, domains, or failure modes.

This round's quota:
${f.quota}

Then self-critique this round's batch (edge cases, noise realism, SNN-distillation value, what the next round should add) into a NEW ${outDir}/NOTES-r${rr}.md (or NOTES-r${rr}c.md on collision).

Output contract:
- Data to ${outDir}/batch-r${rr}.jsonl (or the "c" variant on collision) — one JSON object per line, no fences, no commentary.${f.extra.replaceAll('{RR}', rr)}
- Quality bar: long, dense, concrete, internally consistent, realistic. No placeholders. Never summarize prior material — expand beyond it.
- Self-verify: python3-json.loads() every line of every .jsonl you wrote; fix failures before finishing.
- Return ONLY the structured summary; no trajectory content in the final message.`
    const res = await agent(prompt, { label: `${f.slug}:r${rr}`, phase: 'Generate', schema: SUMMARY })
    if (res) {
      completed += 1
      records += res.trajectory_count || 0
      log(`${f.slug} r${rr}: +${res.trajectory_count} records (window total ${records})`)
    } else {
      log(`${f.slug} r${rr}: agent failed or was skipped (session limit or safeguard flag); continuing with next round`)
    }
  }
  return { factory: f.slug, rounds_completed: completed, records_written: records }
}))

return { mode: 'window', end_round: END_ROUND, per_factory: perFactory.filter(Boolean) }
