// Bounded generator-neutral factory window (#184 retired the prompt lane).
// Lanes below name payload quotas only. Generator identity, rights, and
// provenance are enforced by config/FACTORY-REGISTRY.json and
// pipelines/round_txn.py reserve/publish — never by this script. The retired
// prompt-driven lane is preserved at tag legacy-prompt-factory-v0.2.
// Preserves:
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
    round: { type: 'integer' },
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

// Reservation controller receipt for the failure-as-fuel protocol. The
// controller is a separate context that generates no arm content.
const PREF_RESERVATION = {
  type: 'object',
  required: ['factory', 'round', 'staging_dir', 'reserve_token'],
  additionalProperties: false,
  properties: {
    factory: { type: 'string' },
    round: { type: 'number' },
    staging_dir: { type: 'string', minLength: 1 },
    reserve_token: { type: 'string', pattern: '^[0-9a-f]{32}$' },
  },
}

// Session-A staging handoff for the failure-as-fuel two-session protocol.
const PREF_STAGE = {
  type: 'object',
  required: ['factory', 'round', 'staging_dir', 'reserve_token', 'diagnosis_files'],
  additionalProperties: false,
  properties: {
    factory: { type: 'string' },
    round: { type: 'number' },
    staging_dir: { type: 'string', minLength: 1 },
    reserve_token: { type: 'string', pattern: '^[0-9a-f]{32}$' },
    diagnosis_files: {
      type: 'array',
      minItems: 3,
      maxItems: 3,
      uniqueItems: true,
      items: {
        type: 'string',
        pattern: '^diagnosis-[0-9]{2}-r(0[1-9]|[1-9][0-9]+)\\.md$',
      },
    },
  },
}

// A fourth, arm-payload-blind control context executes the repository verifier
// and returns only bounded file metadata. Session B opens only files in this
// receipt.
const PREF_DIAGNOSIS_VERIFICATION = {
  type: 'object',
  required: ['version', 'factory', 'round', 'staging_dir', 'reservation_token', 'diagnosis_files'],
  additionalProperties: false,
  properties: {
    version: { type: 'integer' },
    factory: { type: 'string' },
    round: { type: 'number' },
    staging_dir: { type: 'string', minLength: 1 },
    reservation_token: { type: 'string', pattern: '^[0-9a-f]{32}$' },
    diagnosis_files: {
      type: 'array',
      minItems: 3,
      maxItems: 3,
      items: {
        type: 'object',
        required: ['name', 'bytes', 'sha256'],
        additionalProperties: false,
        properties: {
          name: {
            type: 'string',
            pattern: '^diagnosis-[0-9]{2}-r(0[1-9]|[1-9][0-9]+)\\.md$',
          },
          bytes: { type: 'integer', minimum: 1 },
          sha256: { type: 'string', pattern: '^[0-9a-f]{64}$' },
        },
      },
    },
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

// Generative quality: each lane's quota explicitly demands scenario diversity,
// gap-targeting, and training value. The lane brief (below) reinforces this by
// requiring densification of under-represented gaps and honest novel-coverage
// self-assessment. This maximizes unique scenario yield per token.
// Lane slugs must resolve to exact path_id rows in
// config/FACTORY-REGISTRY.json; only training-candidate rows may feed weight
// updates, and frontier hosted-model rows stay research-only per #161.
const FACTORIES = [
  {
    slug: 'thalamic-trajectory-factory',
    name: 'Thalamic Trajectory Factory',
    count: 5,
    quota: 'Generate 5 new, long ThalamicTrajectory objects spanning successes, partial failures with recovery, all three gate decisions, long-horizon consequences, and neuromorphic temporal dynamics. Maximize scenario diversity — target documented gaps and under-represented failure modes; do not reuse a prior scenario or edge.',
    extra: '',
  },
  {
    slug: 'multi-agent-ouroboros-swarm',
    name: 'Multi-Agent Ouroboros Swarm',
    count: 1,
    quota: 'Run the full six-role swarm on one new complex agentic and neuromorphic scenario for at least two densification cycles, then emit one final ThalamicTrajectory. Ensure the scenario explores a novel coordination failure or recovery pattern not seen in prior rounds.',
    extra: ' Also put the complete labeled transcript in swarm-transcript-r{RR}.md inside the staging directory.',
  },
  {
    slug: 'neuromorphic-event-language-bridge',
    name: 'Neuromorphic Event + Language Bridge',
    count: 3,
    quota: 'Generate 3 new bridge pairs. Every spike stream must be globally time-ordered, use finite timestamps/amplitudes, include realistic refractory behavior, adaptation and noise, and contain at least 48 events. Vary channels, temporal motifs, and language grounding across pairs to maximize coverage.',
    extra: '',
  },
  {
    slug: 'failure-as-fuel-preference-cascade',
    name: 'Failure-as-Fuel Preference Cascade',
    count: 3,
    quota: 'Generate 3 new preference records. Chosen and rejected must share the exact same state and proposed action; vary only the gate/execution/recovery quality needed to teach the preference. Cover distinct failure modes and recovery strategies across the 3 records.',
    extra: ' Put diagnoses in diagnosis-01-r{RR}.md through diagnosis-03-r{RR}.md inside staging.',
  },
  {
    slug: 'agentic-coding-trajectory-factory',
    name: 'Agentic Coding Trajectory',
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
// (case-insensitive; mirrors round_txn's strict new-publication parser) so unrelated
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
    .filter((line) => /^[ \t]*novel[ _-]?coverage\b/i.test(line))
  // More than one labeled line is ambiguous, even if both values agree. The
  // complete-line match also rejects malformed labels and a second same-line
  // label instead of silently accepting a valid prefix.
  if (labeledLines.length !== 1) return null
  const match = labeledLines[0].match(/^[ \t]*novel[ _-]?coverage[ \t]*(?:\([^)\r\n]*\))?[ \t]*[:=]?[ \t]*(\d+(?:\.\d+)?)[ \t]*%[ \t]*$/i)
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

function preferenceDiagnosisFiles(count, rr) {
  return Array.from(
    { length: count },
    (_, index) => `diagnosis-${String(index + 1).padStart(2, '0')}-r${rr}.md`,
  )
}

// The (factory, round, rr) triple identifies one preference round. The
// validators below take it as a single `expected` context rather than three
// positional arguments, so each stays a two-argument predicate.
function preferenceReceiptIdentifiesRound(receipt, expected) {
  return Boolean(receipt)
    && receipt.factory === expected.factory.slug
    && receipt.round === expected.round
}

function preferenceExpectedStagingDir(expected, token) {
  const root = String(args.root).replace(/\/+$/, '')
  return `${root}/outputs/staging/${args.date}/${expected.factory.slug}/r${expected.rr}-${token}`
}

function preferenceExpectedDiagnosisFiles(expected) {
  return preferenceDiagnosisFiles(expected.factory.count, expected.rr)
}

function preferenceReservationIsValid(receipt, expected) {
  if (!preferenceReceiptIdentifiesRound(receipt, expected)) return false
  if (!/^[0-9a-f]{32}$/.test(receipt.reserve_token || '')) return false
  return receipt.staging_dir === preferenceExpectedStagingDir(expected, receipt.reserve_token)
}

function preferenceHandoffIsValid(handoff, reservation, expected) {
  if (!preferenceReceiptIdentifiesRound(handoff, expected)) return false
  if (handoff.reserve_token !== reservation.reserve_token) return false
  if (handoff.staging_dir !== reservation.staging_dir) return false
  const expectedFiles = preferenceExpectedDiagnosisFiles(expected)
  return JSON.stringify(handoff.diagnosis_files) === JSON.stringify(expectedFiles)
}

// One verified diagnosis entry: the expected name, a positive safe-integer
// byte count, and a well-formed SHA-256 digest.
function preferenceDiagnosisEntryIsVerified(item, expectedName) {
  return Boolean(item)
    && item.name === expectedName
    && Number.isSafeInteger(item.bytes)
    && item.bytes > 0
    && /^[0-9a-f]{64}$/.test(item.sha256 || '')
}

function preferenceDiagnosisFilesAreVerified(files, expectedNames) {
  if (!Array.isArray(files) || files.length !== expectedNames.length) return false
  return files.every((item, index) => preferenceDiagnosisEntryIsVerified(item, expectedNames[index]))
}

// Identity half of the verification receipt: right round, right schema
// version, and bound to the reservation we actually hold.
function preferenceVerificationBindsReservation(receipt, reservation, expected) {
  if (!preferenceReceiptIdentifiesRound(receipt, expected)) return false
  if (receipt.version !== 2) return false
  if (receipt.staging_dir !== reservation.staging_dir) return false
  return receipt.reservation_token === reservation.reserve_token
}

function preferenceDiagnosisVerificationIsValid(receipt, reservation, expected) {
  if (!preferenceVerificationBindsReservation(receipt, reservation, expected)) return false
  return preferenceDiagnosisFilesAreVerified(
    receipt.diagnosis_files,
    preferenceExpectedDiagnosisFiles(expected),
  )
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
- Read ${args.root}/config/FACTORY-REGISTRY.json and confirm this factory's exact path_id + payload_factory row, generator, and rights profile before generating. Frontier hosted-model rows are research-only; they never feed weight updates.
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
    // A content-blind controller owns the reservation; hoist the token so any
    // later identity, handoff, verification, or circuit-break failure can abort.
    let reserveToken = null
    if (factory.slug === 'failure-as-fuel-preference-cascade') {
      const preferenceRound = { factory, round, rr }
      // Two-session isolation (docs/preference-isolation.md): Session A and
      // Session B are SEPARATE agents with independent generation contexts —
      // the only inter-session bridge is the diagnosis artifacts.
      // A third, content-blind context owns reservation so neither arm producer
      // self-issues the orchestration marker used by the publisher.
      const reservation = await agent(`You are the reservation controller for the "${factory.name}" two-session protocol, run ${args.date}, round ${round}. Generate no record, diagnosis, chosen arm, or rejected arm. Run exactly this reservation command:

FILE-SAFETY — highest priority: NEVER write, edit, rename, truncate, or delete any existing file under ${outDir}:
  python3 ${args.root}/pipelines/round_txn.py reserve ${outDir} --round ${round} --expected ${factory.count} --preference-isolation two-session
If reservation fails, stop. Otherwise return only factory="${factory.slug}", round=${round}, and the command's exact staging_dir and token as reserve_token.`, {
        label: `${factory.slug}:r${rr}-reserve`,
        phase: 'Generate',
        schema: PREF_RESERVATION,
      })
      if (!preferenceReservationIsValid(reservation, preferenceRound)) {
        stoppedReason = `r${rr} reservation controller returned an invalid receipt`
        log(`${factory.slug}: ${stoppedReason}; circuit open`)
        // The returned token is part of the invalid receipt and cannot be
        // trusted for cleanup. Read the actual token from the exclusive marker.
        await releaseReservation(factory, round, rr, null)
        break
      }
      reserveToken = reservation.reserve_token

      const sessionA = await agent(`You are Session A (failure mining) of the "${factory.name}" two-session protocol, run ${args.date}, round ${round}. A separate content-blind controller already reserved this round. Do not call reserve again.

FILE-SAFETY — highest priority: NEVER write, edit, rename, truncate, or delete any existing file under ${outDir}. Write ONLY inside this exact reserved staging directory: ${reservation.staging_dir}.

Read ${args.root}/docs/preference-isolation.md (the "Session A" two-session protocol), plus ${args.root}/schemas/thalamic-trajectory-v2.schema.json and ${args.root}/schemas/provenance.md. The single-session path is DEPRECATED and must not be used for new rounds.

Produce EXACTLY ${factory.count} rejected ThalamicTrajectories and their diagnoses in staging: rejected-01-r${rr}.json, rejected-02-r${rr}.json, rejected-03-r${rr}.json scratch files (one JSON object each; never .jsonl) and diagnosis-01-r${rr}.md, diagnosis-02-r${rr}.md, diagnosis-03-r${rr}.md files. Each diagnosis must use the prompt's exact bounded six-section Markdown structure with only the Shared-context state/proposed_action JSON block and Target reward delta JSON block; never paste or serialize the rejected gate/execution/outcome/reward payload. Do NOT write batch-r${rr}.jsonl, do NOT publish, and do NOT draft any chosen content.

Return the structured handoff: factory="${factory.slug}", round=${round}, staging_dir="${reservation.staging_dir}", reserve_token="${reservation.reserve_token}", and diagnosis_files exactly ${JSON.stringify(preferenceDiagnosisFiles(factory.count, rr))}.`, {
        label: `${factory.slug}:r${rr}-sessionA`,
        phase: 'Generate',
        schema: PREF_STAGE,
      })
      if (!preferenceHandoffIsValid(sessionA, reservation, preferenceRound)) {
        stoppedReason = `r${rr} session A failed or returned an invalid diagnosis-only handoff`
        log(`${factory.slug}: ${stoppedReason}; circuit open`)
        await releaseReservation(factory, round, rr, reservation.reserve_token)
        break
      }
      const diagnosisVerification = await agent(`You are the arm-payload-blind diagnosis handoff verifier for the "${factory.name}" two-session protocol, run ${args.date}, round ${round}. You are a separate control context from Sessions A and B. Generate no arm content and do not open, summarize, or quote any diagnosis or rejected-arm file yourself.

Run exactly this repository verifier. It parses only the allowlisted diagnoses' bounded envelopes, never opens rejected-arm files, and emits names, byte counts, and SHA-256 digests rather than file content:
  python3 ${args.root}/pipelines/preference_arms.py verify-handoff ${reservation.staging_dir} ${preferenceDiagnosisFiles(factory.count, rr).map((name) => `--file ${name}`).join(' ')} --write-receipt
If it exits nonzero, stop. Otherwise return its stdout JSON exactly.`, {
        label: `${factory.slug}:r${rr}-diagnosis-verify`,
        phase: 'Verify',
        schema: PREF_DIAGNOSIS_VERIFICATION,
      })
      if (!preferenceDiagnosisVerificationIsValid(diagnosisVerification, reservation, preferenceRound)) {
        stoppedReason = `r${rr} diagnosis files failed the read-only handoff verification`
        log(`${factory.slug}: ${stoppedReason}; circuit open`)
        await releaseReservation(factory, round, rr, reservation.reserve_token)
        break
      }
      const verifiedDiagnosisFiles = diagnosisVerification.diagnosis_files.map((item) => item.name)
      result = await agent(`You are Session B (repair synthesis) of the "${factory.name}" two-session protocol, run ${args.date}, round ${round} — a FRESH context with no Session A memory.

FILE-SAFETY — highest priority: NEVER write, edit, rename, truncate, or delete any existing file under ${outDir}. The content-blind controller reserved this round; its staging_dir is ${diagnosisVerification.staging_dir} and the publish token is ${reservation.reserve_token}.

Read ${args.root}/docs/preference-isolation.md (the "Session B" two-session protocol), plus ${args.root}/schemas/thalamic-trajectory-v2.schema.json. The single-session path is DEPRECATED and must not be used: synthesize the repair from the verified diagnoses only, never from rejected-arm content in your own context.

ISOLATION RULE (absolute): read ONLY these independently verified diagnosis files from staging: ${JSON.stringify(verifiedDiagnosisFiles)}. Their bounded verification receipt is ${JSON.stringify(diagnosisVerification.diagnosis_files)}. NEVER read any rejected-*-r${rr}.json into your context. Synthesize one repaired chosen ThalamicTrajectory per diagnosis (byte-identical state/proposed_action from each Shared-context block, fresh safety rationale), then assemble batch-r${rr}.jsonl MECHANICALLY via a python3 script that json-loads each rejected scratch file and injects it (with your chosen, a critique, script-computed reward_delta = chosen - rejected per component, and meta.isolation="two-session") without printing the rejected content. Write the staged NOTES-r${rr}.md self-critique including the "Novel coverage: <N>%" line. Run the protocol's purity checks and independent-arm scan as a local preview:
  python3 ${args.root}/pipelines/preference_arms.py scan ${diagnosisVerification.staging_dir}/batch-r${rr}.jsonl
A PREFERENCE_ARMS_NEAR_VERBATIM or PREFERENCE_ARMS_LABEL_ONLY_COPY block means the repair restated the rejected arm — re-synthesize that chosen from its diagnosis rather than rewording it. Then publish; publish re-runs the same gate against captured bytes and records its result in the completion marker, so skipping the preview cannot bypass it:
  python3 ${args.root}/pipelines/round_txn.py publish ${outDir} --round ${round} --token ${reservation.reserve_token}
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
