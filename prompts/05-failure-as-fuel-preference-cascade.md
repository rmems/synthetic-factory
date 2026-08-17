You are the Failure-as-Fuel Preference Cascade Factory.

Phase 1: Generate 4 deliberately imperfect / failed / hallucinated / unsafe / inefficient agent trajectories (use Thalamic schema where possible). Make the failures realistic and educational (wrong tool use, ignored safety, incomplete reasoning, context loss, reward hacking attempts, etc.).

Phase 2: For each failed trajectory, produce a detailed diagnosis (root cause, cascade effects, what a good supervisor should have caught) and a fully repaired gold-standard version.

Phase 3: From the (failed, repaired) pairs create preference data:
- Chosen: repaired
- Rejected: original failed
- Plus detailed critique explaining the preference and reward delta

Then expand the set with more nuanced near-miss failures and repairs. Continue densifying. Output in clear structured sections ready for DPO/ORPO, SFT, or Spikenaut safety distillation.
