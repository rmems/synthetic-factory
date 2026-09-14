# Generators and temporary Python sources requiring manual inspection

Generated: 2026-09-14T03:55:46.810436+00:00

This list contains 981 path lineages: 799 blocking and 182 review-priority. It includes all non-exact reconstructions, all uncertain terminal final states, all lineages containing high/critical or syntax-invalid versions, and every mapped generator whose output or training-policy provenance remains unresolved.

No item in this list has been authorized for execution.

## Reason totals

| Reason | Lineages |
|---|---:|
| `critical_operation` | 9 |
| `high_risk_operation` | 155 |
| `observed_output_count_conflict` | 1 |
| `output_mapping_unavailable` | 620 |
| `output_mapping_unresolved` | 46 |
| `partial_state` | 105 |
| `provenance_conflict` | 9 |
| `syntax_invalid` | 7 |
| `terminal_derived_state` | 8 |
| `terminal_final_state_uncertain` | 473 |
| `training_policy_not_blocked` | 158 |
| `unrecoverable_state` | 544 |

## Lineages

| Priority | Original path | Reconstruction | Latest version | Role | Reasons | Mapped outputs |
|---|---|---|---|---|---|---:|
| blocking | `/tmp/actf-r02/gen.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/actf-r06/gen_r06.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/actf-r16/ep2_fn.py` | partial | `actf-r16--59f1d08540ac:v0001` | unknown_temp_python_role | `partial_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/actf-r16/gen.py` | partial | `actf-r16--964753541392:v0004` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain` | 1 |
| blocking | `/tmp/actf-r16/gen_head.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/actf-r16/gen_tail.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/actf-r21-window/gen.py` | partial | `actf-r21-window--ef01e78b2921:v0003` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain` | 3 |
| blocking | `/tmp/actf-r23-live/gen.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/actf-r30/gen.py` | partial | `actf-r30--df0658fc446e:v0038` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain` | 1 |
| blocking | `/tmp/actf-r34/gen.py` | partial | `actf-r34--f6a0015770f7:v0001` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain` | 1 |
| blocking | `/tmp/actf-r35/gen.py` | partial | `actf-r35--252db9cd2260:v0001` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain` | 1 |
| blocking | `/tmp/actf-r43/gen.py` | partial | `actf-r43--a7e99a7ffc42:v0002` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain` | 1 |
| blocking | `/tmp/actf-r46/gen.py` | partial | `actf-r46--5487b4e8bd09:v0002` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain` | 1 |
| blocking | `/tmp/actf-r47/gen.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/actf-r48/gen.py` | partial | `actf-r48--a61665a4bea7:v0002` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain` | 1 |
| blocking | `/tmp/actf-r51/gen.py` | partial | `actf-r51--d4177d28a2f8:v0002` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain` | 1 |
| blocking | `/tmp/actf-r53/gen.py` | partial | `actf-r53--5ec1abe24707:v0003` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain` | 1 |
| blocking | `/tmp/actf-r54/gen.py` | partial | `actf-r54--b5c06b788a0c:v0003` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain` | 1 |
| blocking | `/tmp/actf-r56/gen.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/actf-r60/gen.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/actf-r61/gen.py` | partial | `actf-r61--549addb168a6:v0002` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain` | 3 |
| blocking | `/tmp/actf-r64/gen.py` | partial | `actf-r64--91e89b3bccba:v0005` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain` | 1 |
| blocking | `/tmp/actf-r65/gen.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/actf-r66/gen.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/actf-r68-gen.py` | exact | `tmp-root--bf1d089ea789:v0022` | generator_or_assembler | `syntax_invalid` | 3 |
| blocking | `/tmp/actf_r04_write.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/actf_r24_mint.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/actf_r63c_write.py` | exact | `tmp-root--3906b889b5d6:v0001` | generator_or_assembler | `critical_operation`, `provenance_conflict` | 4 |
| blocking | `/tmp/ffpc-r11-fixed/assemble.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r13/assemble.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r14/assemble.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r15-session-b-tools/assemble.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r15/assemble.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r16-session-b-tools/assemble.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r16/assemble.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r17-session-b-tools/assemble.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r17/assemble.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r18-build-session-a.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r18-stage/assemble.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r18/assemble.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r19-stage/assemble.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r19-stage/post_gates.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r19-stage/verify_receipt.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r19/assemble.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r20-stage/assemble.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r20-stage/post_gates.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r20-stage/verify_receipt.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r20/assemble.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r21-stage/assemble.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r21-stage/build_chosen.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r21-stage/verify_receipt.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r21/assemble.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r21/build_chosen.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r21/build_session_a.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r21/post_gates.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r22-stage/assemble.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r22-stage/build_chosen.py` | partial | `ffpc-r22-stage--12a14800ef6b:v0002` | generator_helper | `partial_state`, `terminal_final_state_uncertain`, `output_mapping_unresolved` | 0 |
| blocking | `/tmp/ffpc-r22-stage/verify_receipt.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r22/assemble.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r22/build_chosen.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r22/post_gates.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r23-stage/build_chosen.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r24-stage/build_chosen.py` | partial | `ffpc-r24-stage--bb03610dd20d:v0001` | generator_helper | `partial_state`, `terminal_final_state_uncertain`, `output_mapping_unresolved` | 0 |
| blocking | `/tmp/ffpc-r24-stage/verify_receipt.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r24/assemble.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r24/build_chosen.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r24/post_gates.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r25-stage/verify_receipt.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r25/assemble.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r25/build_chosen.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r25/post_gates.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r25/verify_receipt.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r26-build-session-a.py` | partial | `tmp-root--d32728d72370:v0007` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain`, `output_mapping_unresolved` | 0 |
| blocking | `/tmp/ffpc-r26-splice-plants.py` | partial | `tmp-root--69b210e6fbbb:v0002` | unknown_temp_python_role | `partial_state`, `terminal_final_state_uncertain`, `syntax_invalid`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r27-stage/assemble.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r27-stage/post_gates.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r27-stage/verify_receipt.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r27/assemble.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r27/build_chosen.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r28-build-session-a.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r28-stage/assemble.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r28-stage/post_gates.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r28-stage/verify_receipt.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r28/assemble.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r28/build_chosen.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r28/post_gates.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r29-stage/assemble.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r29-stage/build_chosen.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r29-stage/extract_diagnosis_brief.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r30-build-session-a.py` | partial | `tmp-root--7d3bc7ac17da:v0001` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain`, `output_mapping_unresolved` | 0 |
| blocking | `/tmp/ffpc-r30-stage/build_chosen.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r30-stage/extract_diagnosis_brief.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r30-stage/harvest_occupancy.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r30-stage/verify_receipt.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r30/assemble.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r30/build_chosen.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r30/post_gates.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r31-build-session-a.py` | partial | `tmp-root--d3770fd35a0f:v0001` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain` | 1 |
| blocking | `/tmp/ffpc-r31-stage/assemble.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r31-stage/extract_diagnosis_brief.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r31-stage/harvest_occupancy.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r31-stage/verify_receipt.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r31/assemble.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r31/build_chosen.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r31/post_gates.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r32-build-session-a.py` | partial | `tmp-root--e217cc54b672:v0001` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain`, `output_mapping_unresolved` | 0 |
| blocking | `/tmp/ffpc-r32-stage/extract_diagnosis_brief.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r32-stage/harvest_occupancy.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r32-stage/verify_receipt.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r32/assemble.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r32/post_gates.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r33-build-session-a.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc-r33-stage/harvest_occupancy.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc_r01_build.py` | exact | `tmp-root--393a0465bb58:v0004` | generator_or_assembler | `critical_operation` | 3 |
| blocking | `/tmp/ffpc_r03_session_a.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ffpc_r42_build.py` | exact | `tmp-root--0015c7b2b585:v0001` | generator_or_assembler | `critical_operation` | 3 |
| blocking | `/tmp/ffpc_r43_build.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/gate_snn_budget.py` | exact | `tmp-root--0a257096c95c:v0007` | generator_or_assembler | `training_policy_not_blocked`, `observed_output_count_conflict` | 3 |
| blocking | `/tmp/gen_ttf_r03.py` | partial | `tmp-root--54b6c3a2c53f:v0003` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain` | 1 |
| blocking | `/tmp/gen_ttf_r03_tail.py` | exact | `tmp-root--95746ac5c89e:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/jsonl_lint_run.py` | exact | `tmp-root--b04eb3ef1331:v0004` | generator_or_assembler | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/lif_raster.py` | exact | `tmp-root--ab1268797189:v0013` | generator_or_assembler | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/maos-fh-r01-build.py` | exact | `tmp-root--5ff82d9a29f8:v0001` | generator_or_assembler | `critical_operation`, `high_risk_operation` | 3 |
| blocking | `/tmp/maos-heading-check.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/maos-r03/build_r03.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/maos-r04/build_r04.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/maos-r05/build_r05.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/maos-r05/notes_fn.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/maos-r05/record_fn.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/maos-r05/transcript_fn.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/maos-r14-audit-run.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/maos-r17/build_r17.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/maos-r21-window/build_r21.py` | exact | `maos-r21-window--741bb090c8e6:v0002` | generator_or_assembler | `critical_operation`, `high_risk_operation` | 3 |
| blocking | `/tmp/maos-r22/build_r22.py` | partial | `maos-r22--0df2d98e460c:v0001` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain`, `high_risk_operation` | 4 |
| blocking | `/tmp/maos-r23-spitlock/build_r23.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/maos-r23-spitlock/build_r23_full.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/maos-r23-spitlock/build_r23_tail.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/maos-r23-spitlock/build_r64_template.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/maos-r24-hearthfen/build_r24.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/maos-r26/build_r26.py` | partial | `maos-r26--1b8616db8c80:v0009` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain`, `high_risk_operation` | 3 |
| blocking | `/tmp/maos-r27/build_r27.py` | partial | `maos-r27--b83a640b14d0:v0013` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain`, `high_risk_operation` | 2 |
| blocking | `/tmp/maos-r28/_build.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/maos-r28/_build_ch.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/maos-r28/_doc.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/maos-r28/_header.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/maos-r28/_local.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/maos-r28/_spikes_snip.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/maos-r28/_tail.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/maos-r28/build_r28.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/maos-r37/_build.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/maos-r37/_doc.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/maos-r37/_header.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/maos-r37/_local.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/maos-r37/_main.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/maos-r37/build_r37.py` | partial | `maos-r37--d31e8715bbc9:v0001` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain`, `high_risk_operation` | 2 |
| blocking | `/tmp/maos-r38/build_r38.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/maos-r40/build_r40.py` | partial | `maos-r40--99c657964134:v0013` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain`, `high_risk_operation` | 2 |
| blocking | `/tmp/maos-r41/_header.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/maos-r41/_local.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/maos-r41/_main.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/maos-r41/_mid.py` | exact | `maos-r41--b7cf3009db1e:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/maos-r41/_tail.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/maos-r44/build_r44.py` | partial | `maos-r44--c0a9ffbb7c5b:v0003` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain`, `high_risk_operation` | 2 |
| blocking | `/tmp/maos-r45/_record.py` | exact | `maos-r45--5ba40b78a4d6:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/maos-r45/build_r45.py` | partial | `maos-r45--f8c222bcb5e5:v0015` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain`, `high_risk_operation` | 2 |
| blocking | `/tmp/maos-r49/build_r49.py` | partial | `maos-r49--1315fd0d5d70:v0008` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain`, `high_risk_operation` | 2 |
| blocking | `/tmp/maos-r50/_head.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/maos-r50/_tail.py` | partial | `maos-r50--b1786553073a:v0001` | source_fragment_or_helper | `partial_state`, `terminal_final_state_uncertain`, `high_risk_operation`, `training_policy_not_blocked` | 1 |
| blocking | `/tmp/maos-r50/_tail_tmp.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/maos-r50/build_r50.py` | partial | `maos-r50--38ac8d6a5b3f:v0002` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain`, `high_risk_operation` | 2 |
| blocking | `/tmp/maos-r53/build_r53.py` | partial | `maos-r53--605002260953:v0023` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain`, `high_risk_operation` | 2 |
| blocking | `/tmp/maos-r54/build_r54.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/maos-r55/build_r55.py` | partial | `maos-r55--de94065140b6:v0004` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain`, `high_risk_operation` | 1 |
| blocking | `/tmp/maos-r55/record_fn.py` | exact | `maos-r55--390861d473c4:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/maos-r56/build_r56.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/maos-r57/_build_record.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/maos-r57/_notes.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/maos-r57/_transcript.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/maos-r57/build_r57.py` | partial | `maos-r57--4ce8999df4fe:v0006` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain`, `high_risk_operation` | 3 |
| blocking | `/tmp/maos-r58/build_r58.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/maos-r59/build_r59.py` | partial | `maos-r59--f3509fdbcd1d:v0001` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain`, `high_risk_operation` | 1 |
| blocking | `/tmp/maos-r60/_make.py` | exact | `maos-r60--2ece0fb4453b:v0001` | generator_or_assembler | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/maos-r60/build_r60.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/maos-r61/_r61_rest.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/maos-r61/_r61_tail.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/maos-r61/build_r61.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/maos-r64/build_r64.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/maos-r65/build_r65.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/maos-r65/notes_fn.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/maos-r65/rec_body.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/maos-r65/transcript_fn.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/maos-r66/_notes.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/maos-r66/_tail.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/maos-r66/_transcript.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/maos-r66/build_r66.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/maos-r68/build_r68.py` | partial | `maos-r68--31bc0fc87304:v0013` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain`, `high_risk_operation` | 1 |
| blocking | `/tmp/maos-r68/snippets/build_record.py` | exact | `maos-r68__snippets--a2c07238ec50:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/maos-r69/_record.py` | exact | `maos-r69--1abb39cf8934:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/maos-r69/build_r69.py` | partial | `maos-r69--f41813658823:v0006` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain`, `high_risk_operation` | 1 |
| blocking | `/tmp/maos_heading_check.py` | partial | `tmp-root--f17b4b253402:v0002` | unknown_temp_python_role | `partial_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/maos_validate.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r01-window/gen_r01.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r02/lif_raster.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r02c-live/gen_r02c.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r02c-live/notes_main.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r02c-live/recs_body.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r02c-live/tail_checks.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r05-live/gen_r05.py` | partial | `nelb-r05-live--3c20e7c4f13c:v0004` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain`, `high_risk_operation` | 1 |
| blocking | `/tmp/nelb-r05-live/recs_r05.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r06-live/_head.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r06-live/_recs.py` | high-confidence | `nelb-r06-live--46d24eb4231a:v0003` | source_fragment_or_helper | `terminal_derived_state`, `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r06-live/_tail.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r06-live/gen_r06.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r13/generate_nelb_r13.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r14-audit-run.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r20/gen_r20.py` | partial | `nelb-r20--b6bdf65914a0:v0004` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain` | 3 |
| blocking | `/tmp/nelb-r22c/gen_r22c.py` | partial | `nelb-r22c--805e0362b758:v0006` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain`, `high_risk_operation` | 1 |
| blocking | `/tmp/nelb-r22c/notes_template.py` | partial | `nelb-r22c--70e27b088c53:v0001` | unknown_temp_python_role | `partial_state`, `terminal_final_state_uncertain`, `syntax_invalid`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r22c/recs_r22.py` | partial | `nelb-r22c--509c363d189f:v0003` | source_fragment_or_helper | `partial_state`, `terminal_final_state_uncertain`, `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r22c/recs_r22_002.py` | partial | `nelb-r22c--e70f03cf3cd0:v0003` | source_fragment_or_helper | `partial_state`, `terminal_final_state_uncertain`, `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r22c/recs_r22_003.py` | exact | `nelb-r22c--fba2646e4416:v0006` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r23-live/_recs.py` | exact | `nelb-r23-live--427e83b92f7b:v0002` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r23-live/gen_r23.py` | partial | `nelb-r23-live--b0ea35538d39:v0013` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain`, `high_risk_operation` | 1 |
| blocking | `/tmp/nelb-r23-live/helpers_pre.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r23-live/helpers_tail.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r23-live/recs_body.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r23/gen_r23.py` | partial | `nelb-r23--77d76ab89c23:v0004` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain` | 1 |
| blocking | `/tmp/nelb-r23/records_block.py` | exact | `nelb-r23--3dd9c6264c67:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r25/gen_r25.py` | partial | `nelb-r25--5d95bf860b3e:v0003` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain` | 4 |
| blocking | `/tmp/nelb-r25/records_block.py` | exact | `nelb-r25--8bafdad06d02:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r26/gen_r26.py` | partial | `nelb-r26--c49898239acb:v0001` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain` | 2 |
| blocking | `/tmp/nelb-r27/gen_r27.py` | partial | `nelb-r27--d021453a2e26:v0001` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain` | 2 |
| blocking | `/tmp/nelb-r28/gen_r28.py` | partial | `nelb-r28--4677528065c7:v0001` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain` | 2 |
| blocking | `/tmp/nelb-r29/gen_r29.py` | partial | `nelb-r29--cc105791ffdc:v0002` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain` | 3 |
| blocking | `/tmp/nelb-r29/records_block.py` | exact | `nelb-r29--bf991f7c1b61:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r30/gen_r30.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r30/records_block.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r30/tail_block.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r31/_notes_helpers.py` | exact | `nelb-r31--c0c7ba5310da:v0001` | source_fragment_or_helper | `high_risk_operation`, `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r31/_recs_r31.py` | exact | `nelb-r31--33ca987c841f:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r31/gen_r31.py` | partial | `nelb-r31--7703430cef4d:v0001` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain` | 2 |
| blocking | `/tmp/nelb-r32/gen_r32.py` | partial | `nelb-r32--6b7f16a8e042:v0012` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain` | 1 |
| blocking | `/tmp/nelb-r33/gen_r33.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r34/gen_r34.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r34/helpers_head.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r34/helpers_tail_raw.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r34/records_block.py` | exact | `nelb-r34--773c672ff006:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r35/gen_r35.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r35/records_block.py` | exact | `nelb-r35--36c5c707f624:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r36/_foot.py` | exact | `nelb-r36--63b62c9669d6:v0001` | generator_or_assembler | `high_risk_operation`, `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r36/_head.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r36/_recs.py` | exact | `nelb-r36--a372812e9b91:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r36/_tail.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r36/gen_r36.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r36/gen_r36.py.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r37/gen_r37.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r38/_head.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r38/_notes_and_main.py` | exact | `nelb-r38--5139afe0bd4b:v0012` | generator_or_assembler | `high_risk_operation`, `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r38/_tail_raw.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r38/gen_r38.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r38/harvest.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r38/records_115_116.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r38/records_block.py` | partial | `nelb-r38--e550524d5962:v0001` | source_fragment_or_helper | `partial_state`, `terminal_final_state_uncertain`, `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r39/gen_r39.py` | partial | `nelb-r39--38ec03e14c0a:v0011` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain` | 1 |
| blocking | `/tmp/nelb-r40/_front.py` | partial | `nelb-r40--0af4add90608:v0002` | unknown_temp_python_role | `partial_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r40/_head.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r40/_recs.py` | exact | `nelb-r40--f1b5a3728198:v0002` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r40/_tail.py` | partial | `nelb-r40--7dd68a1cf49b:v0024` | source_fragment_or_helper | `partial_state`, `terminal_final_state_uncertain`, `high_risk_operation`, `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r40/gen_r40.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r41-window/gen_r41.py` | exact | `nelb-r41-window--a046d4bae635:v0004` | generator_or_assembler | `critical_operation`, `high_risk_operation` | 3 |
| blocking | `/tmp/nelb-r41/gen_r41.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r41/records_block.py` | exact | `nelb-r41--38013e59641b:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r42-window/gen_r42.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r42-window/helpers.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r42-window/recs.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r42-window/recs_a2.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r42-window/recs_a3.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r42-window/tail.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r42/_notes_and_main.py` | exact | `nelb-r42--1b375c71a938:v0001` | generator_or_assembler | `high_risk_operation`, `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r42/gen_r42.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r42/gen_r42_head.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r42/gen_r42_tail_raw.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r42/records_block.py` | exact | `nelb-r42--b384fc2a5c27:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r43/_head.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r43/_notes_and_main.py` | exact | `nelb-r43--09e979cc692e:v0003` | generator_or_assembler | `high_risk_operation`, `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r43/_tail_raw.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r43/gen_r43.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r43/records_block.py` | exact | `nelb-r43--e9f8b627fb64:v0002` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r44/_head.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r44/_notes_and_main.py` | exact | `nelb-r44--ef760b574a26:v0001` | generator_or_assembler | `high_risk_operation`, `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r44/_tail_raw.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r44/gen_r44.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r44/records_block.py` | exact | `nelb-r44--007f2d590f51:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r45/_head.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r45/_keep_138.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r45/_keep_head_occ.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r45/_tail.py` | exact | `nelb-r45--ed1e1ba9e699:v0019` | source_fragment_or_helper | `high_risk_operation`, `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r45/gen_r45.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r45/records_block.py` | partial | `nelb-r45--5dc30e82b013:v0002` | source_fragment_or_helper | `partial_state`, `terminal_final_state_uncertain`, `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r46/_tail.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r46/gen_r46.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r47/_head.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r47/_notes.py` | exact | `nelb-r47--09a11fac5102:v0010` | generator_or_assembler | `high_risk_operation`, `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r47/_recs.py` | partial | `nelb-r47--c848af4abe77:v0005` | source_fragment_or_helper | `partial_state`, `terminal_final_state_uncertain`, `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r47/_tail.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r47/gen_r47.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r48/_envelope.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r48/_recs_and_tail.py` | partial | `nelb-r48--b9bc0a2b2a3f:v0005` | source_fragment_or_helper | `partial_state`, `terminal_final_state_uncertain`, `high_risk_operation`, `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r48/gen_r48.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r49/_tail.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r49/gen_r49.full.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r49/gen_r49.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r49/records_block.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r50/_envelope.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r50/_head.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r50/_tail.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r50/_tail_raw.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r50/gen_r50.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r50/records_block.py` | partial | `nelb-r50--9307365c7078:v0003` | source_fragment_or_helper | `partial_state`, `terminal_final_state_uncertain`, `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r51/_checks.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r51/_head.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r51/_notes_and_main.py` | exact | `nelb-r51--22b5f7f91180:v0002` | generator_or_assembler | `high_risk_operation`, `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r51/gen_r51.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r51/records_block.py` | exact | `nelb-r51--202cf10a1cb5:v0002` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r52/_head.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r52/_tail.py` | exact | `nelb-r52--123c005f0317:v0001` | source_fragment_or_helper | `high_risk_operation`, `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r52/gen_r52.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r52/records_block.py` | exact | `nelb-r52--3f8dff7f3569:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r53/_head.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r53/_notes.py` | exact | `nelb-r53--2046bd0c5cfd:v0002` | generator_or_assembler | `high_risk_operation`, `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r53/_recs.py` | exact | `nelb-r53--f2cd3fb85bbf:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r53/_tail_raw.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r53/gen_r53.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r54/_head.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r54/_tail.py` | exact | `nelb-r54--630a927757dd:v0018` | source_fragment_or_helper | `high_risk_operation`, `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r54/_tail_r49.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r54/gen_r54.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r54/records_block.py` | partial | `nelb-r54--ff09b6f46bd1:v0001` | source_fragment_or_helper | `partial_state`, `terminal_final_state_uncertain`, `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r55/_head_helpers.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r55/_mid_checks.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r55/_notes_main.py` | exact | `nelb-r55--ab78229178a2:v0001` | generator_or_assembler | `high_risk_operation`, `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r55/_rec168.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r55/_recs.py` | exact | `nelb-r55--7fba90094224:v0014` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r55/gen_r55.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r55/records_block.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r56/_recs.py` | exact | `nelb-r56--3fd745b420ef:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r56/gen_r56.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r56/records_block.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r57/_head.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r57/_new172.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r57/_new174.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r57/_recs.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r57/_tail.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r57/_tail_raw.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r57/gen_r57.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r57/records_block.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r58/_head_src.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r58/_occupancy.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r58/_rec175_draft.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r58/_recs.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r58/_recs_sub.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r58/_tail.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r58/gen_r58.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r59/_head.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r59/_recs.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r59/_tail.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r59/_tail_raw.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r59/gen_r59.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r59/occupancy.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r59/recs.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r60/_head_helpers.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r60/_recs_and_tail.py` | partial | `nelb-r60--9b4fc0c6a446:v0001` | source_fragment_or_helper | `partial_state`, `terminal_final_state_uncertain`, `high_risk_operation`, `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r60/gen_r60.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r61-sf/gen_r61.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r61/_186.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r61/_head.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r61/_occ.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r61/_recs.py` | partial | `nelb-r61--dfd66bee9062:v0002` | source_fragment_or_helper | `partial_state`, `terminal_final_state_uncertain`, `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r61/_tail_raw.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r61/gen_r61.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r62/_front_recs.py` | exact | `nelb-r62--5d1e6388d0d6:v0003` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r62/_head.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r62/_notes_main.py` | exact | `nelb-r62--a97994274f1b:v0009` | generator_or_assembler | `high_risk_operation`, `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r62/_rec189_keep.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r62/_recs.py` | exact | `nelb-r62--a2f45fd0b5d8:v0006` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r62/_tail_raw.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r62/gen_r62.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r63/_head.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r63/_tail.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r63/_tail_raw.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r63/gen_r63.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r63/rec_191.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r63/rec_192.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r63/records_block.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r64/_head.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r64/_recs.py` | partial | `nelb-r64--f680ec40498d:v0001` | source_fragment_or_helper | `partial_state`, `terminal_final_state_uncertain`, `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r64/_tail.py` | partial | `nelb-r64--51f72014e72f:v0001` | source_fragment_or_helper | `partial_state`, `terminal_final_state_uncertain`, `high_risk_operation`, `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r64/gen_r64.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r64/records_block.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r65-live/gen_r65.py` | partial | `nelb-r65-live--885b634884a5:v0001` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain` | 1 |
| blocking | `/tmp/nelb-r65-live/tail.py` | exact | `nelb-r65-live--b325c25124ef:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r65/_head.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r65/_recs.py` | exact | `nelb-r65--161d15370df7:v0011` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r65/_tail.py` | exact | `nelb-r65--5f407c0cdb1b:v0001` | source_fragment_or_helper | `high_risk_operation`, `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r65/gen_r65.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r66-live/gen_r66.py` | partial | `nelb-r66-live--806d70be106b:v0001` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain`, `high_risk_operation` | 1 |
| blocking | `/tmp/nelb-r66-live/recs_body.py` | exact | `nelb-r66-live--2dbffcaacbe1:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r66/_head_helpers.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r66/_recs.py` | partial | `nelb-r66--86d826be1f0f:v0004` | source_fragment_or_helper | `partial_state`, `terminal_final_state_uncertain`, `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r66/_tail.py` | exact | `nelb-r66--469e3e1c7d26:v0003` | source_fragment_or_helper | `syntax_invalid`, `high_risk_operation`, `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r66/gen_r66.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r67-live/gen_r67.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r67/_checks.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r67/_head_helpers.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r67/_occ_notes_main.py` | exact | `nelb-r67--c05e6d18ba7c:v0010` | generator_or_assembler | `high_risk_operation`, `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r67/gen_r67.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r68-live/_head.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r68-live/_tail.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r68-live/gen_r68.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r68-live/recs_body.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r68/_head.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r68/_recs.py` | exact | `nelb-r68--97acf6f18bf9:v0004` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r68/_tail.py` | exact | `nelb-r68--edeb90d657f5:v0002` | source_fragment_or_helper | `high_risk_operation`, `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r68/gen_r68.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r69/_head.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r69/_recs.py` | partial | `nelb-r69--d51a4ae80de6:v0001` | source_fragment_or_helper | `partial_state`, `terminal_final_state_uncertain`, `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r69/_tail.py` | exact | `nelb-r69--2f63762aa13b:v0003` | source_fragment_or_helper | `high_risk_operation`, `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r69/_tail_raw.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r69/gen_r69.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r70/_head.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-r70/_recs.py` | exact | `nelb-r70--19ac29c4db66:v0002` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-r70/_tail.py` | exact | `nelb-r70--e7a82cc1d146:v0001` | source_fragment_or_helper | `high_risk_operation`, `training_policy_not_blocked` | 1 |
| blocking | `/tmp/nelb-sf-r62/gen_window_r62.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/nelb-sfw-r22/_exact_and_recs.py` | exact | `nelb-sfw-r22--c60a89545749:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 3 |
| blocking | `/tmp/nelb-sfw-r22/_tail.py` | exact | `nelb-sfw-r22--fd4d846f8928:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 3 |
| blocking | `/tmp/nelb-sfw-r22/gen_r22.py` | partial | `nelb-sfw-r22--461b1f70c20d:v0001` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain`, `provenance_conflict` | 3 |
| blocking | `/tmp/sf-window/pipelines/check_episode.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state` | 0 |
| blocking | `/tmp/sf-window/pipelines/check_jsonl.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state` | 0 |
| blocking | `/tmp/sf-window/pipelines/check_records.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain` | 0 |
| blocking | `/tmp/sf-window/pipelines/curate_bridge.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state` | 0 |
| blocking | `/tmp/sf-window/pipelines/maos_validate.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/sf-window/pipelines/next_round.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain` | 0 |
| blocking | `/tmp/sf-window/pipelines/preference_arms.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain` | 0 |
| blocking | `/tmp/sf-window/pipelines/round_txn.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain` | 0 |
| blocking | `/tmp/sf-window/pipelines/spike_probe.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state` | 0 |
| blocking | `/tmp/sf-window/pipelines/validate_run.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state` | 0 |
| blocking | `/tmp/sf-window/pipelines/verify_execution.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state` | 0 |
| blocking | `/tmp/ttf-r01/gen_r01.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r04/builders_r04.py` | exact | `ttf-r04--24386877af80:v0001` | generator_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r04/gen_r04.py` | partial | `ttf-r04--ea6635b232f8:v0010` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain` | 3 |
| blocking | `/tmp/ttf-r05/gen_r05.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r06/gen_r06.py` | partial | `ttf-r06--6a642c5c0953:v0013` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain` | 1 |
| blocking | `/tmp/ttf-r06/records_r06.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r100/_mid.py` | exact | `ttf-r100--4d605f43295a:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r100/gen_r100.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r101/_records_body.py` | exact | `ttf-r101--670aa44ba42f:v0002` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r101/gen_r101.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r102/_prefix.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r102/_records_r102.py` | exact | `ttf-r102--f1e50756e6d1:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r102/_suffix_raw.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r102/gen_r102.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r103/_prefix.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r103/_records_r103.py` | exact | `ttf-r103--4659d077332e:v0005` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r103/_suffix.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r103/gen_r103.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r104/_head.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r104/_records.py` | exact | `ttf-r104--dc8b8e3e52c4:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r104/_tail.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r104/_tail_src.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r104/gen_r104.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r105/_apply.py` | partial | `ttf-r105--58b86a8823a5:v0001` | unknown_temp_python_role | `partial_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r105/gen_r105.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r106/_head.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r106/_records.py` | exact | `ttf-r106--3be30d307393:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r106/_tail.py` | exact | `ttf-r106--cf8481862ba2:v0001` | source_fragment_or_helper | `high_risk_operation`, `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r106/gen_r106.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r107/_head_src.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r107/_records_r107.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r107/_records_r107b.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r107/_tail_src.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r107/assemble_r107.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r107/gen_r107.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r108/_head.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r108/_records_r108.py` | exact | `ttf-r108--c2c85fc0a10c:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r108/_tail.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r108/gen_r108.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r109/_partial.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r109/gen_r109.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r110/_head_r110.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r110/_records_r110.py` | exact | `ttf-r110--d2bd20ace00f:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r110/_tail_src.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r110/gen_r110.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r111/_head.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r111/_stage1.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r111/gen_r111.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r112/_head.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r112/_prefix.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r112/_records_r112.py` | exact | `ttf-r112--ceb0c37e76b0:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r112/_tail_raw.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r112/gen_r112.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r113/_head.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r113/_prefix.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r113/_records.py` | exact | `ttf-r113--5e3900f13b86:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r113/_tail.py` | exact | `ttf-r113--ecaa3b06cf4d:v0003` | source_fragment_or_helper | `high_risk_operation`, `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r113/gen_r113.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r114/gen_r114.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r115/_records_r115.py` | exact | `ttf-r115--b19ac1ab4e34:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r115/gen_r115.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r116/_prefix.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r116/_records.py` | exact | `ttf-r116--7046b0467a86:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r116/_suffix_raw.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r116/gen_r116.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r117/_head.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r117/_records_r117.py` | exact | `ttf-r117--24c7bb645a19:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r117/_tail_partial.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r117/gen_r117.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r118/gen_r118.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r119/build_r119.py` | exact | `ttf-r119--ebc1fd904eed:v0001` | generator_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r119/gen_r119.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r12-validate.py` | exact | `tmp-root--d5a3d8c10085:v0001` | generator_or_assembler | `high_risk_operation`, `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r120/_build.py` | exact | `ttf-r120--1f3e289acda4:v0001` | generator_or_assembler | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r120/gen_r120.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r122/gen_r122.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r123/gen_r123.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r125/_prefix.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r21/gen_r21.py` | partial | `ttf-r21--1d174e42ce42:v0001` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain` | 4 |
| blocking | `/tmp/ttf-r22/gen_r22.py` | partial | `ttf-r22--7818a7afbeac:v0003` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain` | 4 |
| blocking | `/tmp/ttf-r22w/gen_r22.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r23c/gen_r23c.py` | exact | `ttf-r23c--f64350a96028:v0005` | generator_or_assembler | `critical_operation`, `high_risk_operation` | 5 |
| blocking | `/tmp/ttf-r24-live/gen_r24.py` | partial | `ttf-r24-live--6e0319c245f4:v0003` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain` | 1 |
| blocking | `/tmp/ttf-r24-live/tail_r24.py` | exact | `ttf-r24-live--1b54e5bfc24d:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r24/gen_r24.py` | partial | `ttf-r24--f75192d766fd:v0112` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain`, `high_risk_operation` | 2 |
| blocking | `/tmp/ttf-r25/gen_r25.py` | partial | `ttf-r25--457c8d2497c2:v0001` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain`, `high_risk_operation` | 1 |
| blocking | `/tmp/ttf-r26/gen_r26.merged.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r26/gen_r26.py` | partial | `ttf-r26--f5ad47dff770:v0002` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain`, `high_risk_operation` | 2 |
| blocking | `/tmp/ttf-r26/gen_r26_rest.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r26/gen_r26_rest2.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r27/gen_r27.py` | partial | `ttf-r27--dacc3d7ec0b9:v0027` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain`, `high_risk_operation` | 3 |
| blocking | `/tmp/ttf-r30/_records30.py` | exact | `ttf-r30--658cf32b9b70:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r30/gen_r30.py` | partial | `ttf-r30--84070e36b87d:v0018` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain`, `high_risk_operation` | 2 |
| blocking | `/tmp/ttf-r36/gen_r36.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r37/_head.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r37/_tail.py` | exact | `ttf-r37--e225c3bf38f5:v0001` | source_fragment_or_helper | `high_risk_operation`, `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r37/gen_r37.py` | partial | `ttf-r37--bd61808fb42f:v0001` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain`, `high_risk_operation` | 2 |
| blocking | `/tmp/ttf-r38/_checks.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r38/_helpers.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r38/_pipes.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r39/_records39.py` | exact | `ttf-r39--44ada129fcf2:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r39/gen_r39.py` | partial | `ttf-r39--c576930a8e22:v0013` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain`, `high_risk_operation` | 3 |
| blocking | `/tmp/ttf-r40/_records.py` | exact | `ttf-r40--c62806cd9222:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r40/gen_r40.py` | partial | `ttf-r40--fc50f34b8e29:v0027` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain`, `high_risk_operation` | 1 |
| blocking | `/tmp/ttf-r41/_records.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r41/_records2.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r41/_tail.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r41/gen_r41.py` | partial | `ttf-r41--cc233a32d2ef:v0004` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain`, `high_risk_operation` | 1 |
| blocking | `/tmp/ttf-r41w/_checks.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r41w/_helpers.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r41w/gen_r41.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r42/_head.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r42/_records.py` | exact | `ttf-r42--8c60f16fe6ac:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r42/_tail.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r42/_tail_raw.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r42/gen_r42.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r42w/_helpers_patched.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r42w/_helpers_src.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r42w/_tail.py` | exact | `ttf-r42w--d4a2fa53536a:v0001` | source_fragment_or_helper | `high_risk_operation`, `training_policy_not_blocked` | 3 |
| blocking | `/tmp/ttf-r43/_checks_partial.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r43/_checks_src.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r43/_helpers.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r43/_helpers_src.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r43/_notes.py` | partial | `ttf-r43--755a5a99463e:v0001` | unknown_temp_python_role | `partial_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r43/_records.py` | partial | `ttf-r43--b779743c658e:v0001` | source_fragment_or_helper | `partial_state`, `terminal_final_state_uncertain`, `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r43/gen_r43.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r44/_records.py` | exact | `ttf-r44--0564d845b50f:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r44/gen_r44.py` | partial | `ttf-r44--82200154070b:v0020` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain`, `high_risk_operation` | 1 |
| blocking | `/tmp/ttf-r45/_records.py` | exact | `ttf-r45--b557a683b437:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r45/gen_r45.py` | partial | `ttf-r45--1a4a9bfeeda3:v0004` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain`, `high_risk_operation` | 2 |
| blocking | `/tmp/ttf-r46/build_r46.py` | exact | `ttf-r46--fb11a327b6b7:v0012` | generator_or_assembler | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r46/gen_r46.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r47/_head.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r47/_r251.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r47/_r252_raw.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r47/_r253.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r47/_r254.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r47/_r255.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r47/_tail.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r47/gen_r47.py` | partial | `ttf-r47--cf453a2bf874:v0001` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain`, `high_risk_operation` | 2 |
| blocking | `/tmp/ttf-r47/patch_r47.py` | exact | `ttf-r47--f5c9b83d47e8:v0002` | unknown_temp_python_role | `syntax_invalid`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r48/gen_r48.py` | partial | `ttf-r48--f1f4fa26cf20:v0001` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain`, `high_risk_operation` | 4 |
| blocking | `/tmp/ttf-r48/records_r48.py` | exact | `ttf-r48--4bbc5ff93ad3:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r48/records_r48b.py` | exact | `ttf-r48--6e4adda89598:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r49/_records_r49.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r49/gen_r49.py` | partial | `ttf-r49--e8d634e5baf8:v0001` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain`, `high_risk_operation` | 2 |
| blocking | `/tmp/ttf-r50/_foot.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r50/_head.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r50/_records.py` | exact | `ttf-r50--e1865c74e697:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r50/gen_r50.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r51/_helpers_src.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r51/_record272.py` | exact | `ttf-r51--005d14947996:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r51/_tail.py` | partial | `ttf-r51--df6acba09271:v0007` | source_fragment_or_helper | `partial_state`, `terminal_final_state_uncertain`, `high_risk_operation`, `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r51/gen_r51.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r52/gen_r52.py` | partial | `ttf-r52--eb8233a7ab60:v0012` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain`, `high_risk_operation` | 2 |
| blocking | `/tmp/ttf-r53/_patch.py` | exact | `ttf-r53--1b9ae17df13c:v0002` | unknown_temp_python_role | `syntax_invalid`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r53/_records.py` | exact | `ttf-r53--22c9b9d0553c:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r53/gen_r53.py` | partial | `ttf-r53--d211f9b73939:v0003` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain`, `high_risk_operation` | 3 |
| blocking | `/tmp/ttf-r54/_checks.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r54/_head.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r54/_tail.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r54/gen_r54.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r55/_head.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r55/_r292.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r55/_recs_new.py` | exact | `ttf-r55--b8d8c724b538:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r55/_rest.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r55/_tail.py` | exact | `ttf-r55--3177c68346ab:v0001` | source_fragment_or_helper | `high_risk_operation`, `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r55/gen_r55.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r56/gen_r56.py` | partial | `ttf-r56--e3e746c47a15:v0004` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain`, `high_risk_operation` | 2 |
| blocking | `/tmp/ttf-r57/_head.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r57/_notes_main.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r57/_records.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r57/_tail_oldnotes.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r57/_tail_pre.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r57/gen_r57.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r59/_head.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r59/_records_r59.py` | exact | `ttf-r59--794f0e2d0e58:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r59/gen_r59.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r60/_helpers.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r60/_records_r60.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r60/_records_r60b.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r60/_tail_raw.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r60/gen_r60.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r61-window/_checks_partial.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r61-window/_helpers.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r61-window/gen_r61.py` | partial | `ttf-r61-window--54979c4b61f6:v0003` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain`, `critical_operation`, `high_risk_operation` | 6 |
| blocking | `/tmp/ttf-r61/_assemble.py` | exact | `ttf-r61--af4904369428:v0011` | generator_or_assembler | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r61/_head_mut.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r61/_head_src.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r61/_recs.py` | partial | `ttf-r61--c4b8084af2ab:v0011` | source_fragment_or_helper | `partial_state`, `terminal_final_state_uncertain`, `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r61/_tail_src.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r61/gen_r61.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r62/_new_tail.py` | exact | `ttf-r62--c5c258a1d15e:v0001` | source_fragment_or_helper | `high_risk_operation`, `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r62/gen_r62.py` | partial | `ttf-r62--b1dbd6909b8c:v0009` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain`, `high_risk_operation` | 1 |
| blocking | `/tmp/ttf-r63-311/_banned.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r63/_banned.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r63/_helpers_audit.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r63/_helpers_core.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r63/_records.py` | exact | `ttf-r63--179ea338d636:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r63/_tail.py` | exact | `ttf-r63--5798702abbe1:v0001` | source_fragment_or_helper | `high_risk_operation`, `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r63/gen_r63.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r63c/gen_r63c.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r64-live/_records_r64.py` | exact | `ttf-r64-live--20d6ae868e51:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r64-live/gen_r64.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r64/_head_helpers.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r64/_records.py` | exact | `ttf-r64--2263c4267c43:v0005` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r64/_tail_helpers.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r64/gen_r64.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r65/_records_body.py` | exact | `ttf-r65--36cd7642f176:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r65/gen_r65.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r66-live/gen_r66.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r66-live/helpers_head.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r66-live/records_tail.py` | exact | `ttf-r66-live--02621bdfe655:v0002` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r66-live/tail_main.py` | exact | `ttf-r66-live--205b969b9ba5:v0001` | source_fragment_or_helper | `high_risk_operation`, `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r66/_head.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r66/_tail.py` | exact | `ttf-r66--289c4f54eba3:v0006` | source_fragment_or_helper | `high_risk_operation`, `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r66/gen_r66.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r67/gen_r67.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r68-live/gen_r68.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r68/_prefix.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r68/_records.py` | exact | `ttf-r68--0d62737923be:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r68/_suffix_raw.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r68/gen_r68.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r69-live/_records_r69.py` | exact | `ttf-r69-live--9760181dd484:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r69-live/gen_r69.py` | partial | `ttf-r69-live--22992810daa9:v0016` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain`, `high_risk_operation` | 2 |
| blocking | `/tmp/ttf-r69/_head_helpers.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r69/_records_r69.py` | exact | `ttf-r69--441dbb1664de:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r69/_tail_checks.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r69/gen_r69.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r70/_records_r70.py` | exact | `ttf-r70--adac92e0a814:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r70/gen_r70.py` | partial | `ttf-r70--412a47e0f6f3:v0027` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain`, `high_risk_operation` | 1 |
| blocking | `/tmp/ttf-r71-live/gen_r71.py` | partial | `ttf-r71-live--e4917c7bbf47:v0025` | generator_or_assembler | `partial_state`, `terminal_final_state_uncertain`, `high_risk_operation` | 2 |
| blocking | `/tmp/ttf-r71/_helpers.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r71/_tail.py` | exact | `ttf-r71--5323c5309638:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r71/_tail2.py` | exact | `ttf-r71--6f003dc72705:v0001` | source_fragment_or_helper | `high_risk_operation`, `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r71/gen_r71.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r72/_head_helpers.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r72/_records.py` | exact | `ttf-r72--d470c304a082:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r72/_tail_helpers.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r72/gen_r72.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r73-live/_helpers.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r73-live/_records.py` | exact | `ttf-r73-live--d90954af3408:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r73-live/_tail.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r73-live/_tail_mid.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r73-live/_tail_raw.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r73-live/gen_r73.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r73/_banned_from_r65.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r73/_helpers_from_r65.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r73/_part_records.py` | exact | `ttf-r73--6bb6127cde7a:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r73/_part_tail.py` | exact | `ttf-r73--f7ca89701a42:v0001` | source_fragment_or_helper | `high_risk_operation`, `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r73/gen_r73.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r74/_head.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r74/_records.py` | partial | `ttf-r74--17db0229eb98:v0001` | source_fragment_or_helper | `partial_state`, `terminal_final_state_uncertain`, `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r74/_tail.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r74/_wrap.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r74/gen_r74.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r75/_prefix.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r75/_records.py` | exact | `ttf-r75--bd69dba8f3dc:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r75/_suffix_raw.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r75/gen_r75.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r76/_head_src.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r76/_middle.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r76/_middle2.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r76/_tail_src.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r76/gen_r76.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r77/_new_records.py` | exact | `ttf-r77--0d84a3d86e48:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r77/gen_r77.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r78/_prefix.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r78/_rest.py` | exact | `ttf-r78--9bf1abdcadea:v0001` | generator_or_assembler | `high_risk_operation`, `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r78/gen_r78.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r79/_prefix.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r79/_records_r79.py` | exact | `ttf-r79--dd4eef39e19b:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r79/_suffix.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r79/_suffix_raw.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r79/gen_r79.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r80/_prefix.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r80/_records.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r80/_tail_raw.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r80/gen_r80.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r81/_records_r81.py` | exact | `ttf-r81--29fe32194a1b:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r81/gen_r81.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r82/_head.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r82/_records.py` | exact | `ttf-r82--78dedb5c6fe4:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r82/_tail.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r82/gen_r82.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r83/_head.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r83/_records.py` | exact | `ttf-r83--2ca1eb504aa9:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r83/_records2.py` | exact | `ttf-r83--a8f02c1b5797:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r83/_tail.py` | exact | `ttf-r83--4b27fc0287e4:v0001` | source_fragment_or_helper | `high_risk_operation`, `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r83/gen_r83.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r84/_head.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r84/_records.py` | exact | `ttf-r84--bf4447859c57:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r84/_tail.py` | exact | `ttf-r84--fb3e8e8447dc:v0001` | source_fragment_or_helper | `high_risk_operation`, `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r84/gen_r84.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r85/_record_442.py` | exact | `ttf-r85--3ead92e174e1:v0002` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r85/gen_r85.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r86/_banned_src.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r86/_helpers_src.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r86/_records_r86.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r86/_records_r86b.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r86/_tail_r86.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r86/gen_r86.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r87/_body.py` | exact | `ttf-r87--79241f9dae03:v0001` | generator_or_assembler | `high_risk_operation`, `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r87/_prefix.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r87/gen_r87.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r88/_head.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r88/_records.py` | exact | `ttf-r88--be1b0e4f16ab:v0002` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r88/_tail.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r88/_tail_raw.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r88/gen_r88.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r89/_checks.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r89/_prefix.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r89/_rest3.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r89/gen_r89.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r89/harvest_occupancy.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r90/_prefix.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r90/_records.py` | exact | `ttf-r90--fc003801698c:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r90/_tail_raw.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r90/gen_r90.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r91/_head_helpers.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r91/_records_r91.py` | exact | `ttf-r91--ff5e9d383b8e:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r91/_tail_r91.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r91/_tail_src.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r91/gen_r91.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r92/_head_r92.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r92/_records_r92.py` | exact | `ttf-r92--5ee9980226e0:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r92/_tail_r92.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r92/gen_r92.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r93/_prefix.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r93/_records_r93.py` | exact | `ttf-r93--d2b0cd0fa202:v0002` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r93/_suffix_raw.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r93/gen_r93.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r94/_prefix.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r94/_records.py` | exact | `ttf-r94--eeeff6899f17:v0002` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r94/_suffix.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r94/gen_r94.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r95/_prefix.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r95/_records_r95.py` | exact | `ttf-r95--0b1f46e333bc:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r95/_suffix_raw.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r95/gen_r95.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r96/_prefix.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r96/_records.py` | exact | `ttf-r96--b010eac009cf:v0001` | source_fragment_or_helper | `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r96/_tail.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r96/_tail_raw.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r96/gen_r96.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r97/_prefix.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r97/_records_tail.py` | exact | `ttf-r97--e73a893ef6ef:v0001` | source_fragment_or_helper | `high_risk_operation`, `training_policy_not_blocked` | 1 |
| blocking | `/tmp/ttf-r97/gen_r97.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r98/_patch.py` | exact | `ttf-r98--a13470f89928:v0004` | unknown_temp_python_role | `syntax_invalid`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r98/gen_r98.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-r99/gen_r99.py` | unrecoverable | `none` | unknown_temp_python_role | `unrecoverable_state`, `terminal_final_state_uncertain`, `output_mapping_unavailable` | 0 |
| blocking | `/tmp/ttf-sf-r21/gen_r21.py` | exact | `ttf-sf-r21--ac2a22579a4a:v0001` | generator_or_assembler | `critical_operation`, `high_risk_operation` | 3 |
| review | `/tmp/actf-r23c-gen.py` | exact | `tmp-root--b71d4f4a6e55:v0007` | generator_or_assembler | `high_risk_operation`, `provenance_conflict` | 3 |
| review | `/tmp/actf-r30/_ep1_fragment.py` | exact | `actf-r30--a9cfdbe47d1b:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/actf-r30/_ep2_fragment.py` | exact | `actf-r30--54a2964d1482:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/actf-r43/_eps.py` | exact | `actf-r43--28e036ba205a:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/build_ffpc_r24_session_a.py` | exact | `tmp-root--73008c03ded8:v0003` | generator_or_assembler | `output_mapping_unresolved` | 0 |
| review | `/tmp/build_maos_r18.py` | exact | `tmp-root--8386400b6057:v0002` | generator_or_assembler | `high_risk_operation` | 1 |
| review | `/tmp/ffpc-r02-build-session-a.py` | exact | `tmp-root--286d2d899a95:v0002` | generator_or_assembler | `output_mapping_unresolved` | 0 |
| review | `/tmp/ffpc-r02-session-b/build_chosen.py` | exact | `ffpc-r02-session-b--17550ae30d6e:v0002` | generator_or_assembler | `high_risk_operation` | 1 |
| review | `/tmp/ffpc-r04/build_session_a_r04.py` | exact | `ffpc-r04--64ccdf1da4be:v0001` | generator_or_assembler | `output_mapping_unresolved` | 0 |
| review | `/tmp/ffpc-r11/nest_rights.py` | exact | `ffpc-r11--b5052ebbd5f4:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/ffpc-r13/_build_session_a.py` | exact | `ffpc-r13--41d08ae80243:v0001` | generator_helper | `output_mapping_unresolved` | 0 |
| review | `/tmp/ffpc-r14-build-session-a.py` | exact | `tmp-root--08b3e96e0bf0:v0001` | generator_or_assembler | `output_mapping_unresolved` | 0 |
| review | `/tmp/ffpc-r14/build_chosen.py` | exact | `ffpc-r14--01800c006dc6:v0006` | generator_helper | `output_mapping_unresolved` | 0 |
| review | `/tmp/ffpc-r15-build-session-a.py` | exact | `tmp-root--be60a4abd638:v0001` | generator_or_assembler | `output_mapping_unresolved` | 0 |
| review | `/tmp/ffpc-r15-session-b-tools/build_chosen.py` | exact | `ffpc-r15-session-b-tools--b98ae031b4ba:v0001` | generator_helper | `output_mapping_unresolved` | 0 |
| review | `/tmp/ffpc-r15-session-b-tools/verify_receipt.py` | exact | `ffpc-r15-session-b-tools--b89513613fb6:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/ffpc-r16-build-session-a.py` | exact | `tmp-root--80a5baac4ed2:v0001` | generator_or_assembler | `output_mapping_unresolved` | 0 |
| review | `/tmp/ffpc-r16-session-b-tools/verify_diagnosis_receipt.py` | high-confidence | `ffpc-r16-session-b-tools--dad7aa8c1922:v0001` | unknown_temp_python_role | `terminal_derived_state`, `output_mapping_unavailable` | 0 |
| review | `/tmp/ffpc-r16/build_chosen.py` | exact | `ffpc-r16--c39585d959b0:v0002` | generator_helper | `output_mapping_unresolved` | 0 |
| review | `/tmp/ffpc-r17-build-session-a.py` | exact | `tmp-root--eeaf57403bed:v0001` | generator_or_assembler | `output_mapping_unresolved` | 0 |
| review | `/tmp/ffpc-r17-session-b-tools/build_chosen.py` | exact | `ffpc-r17-session-b-tools--355a751e2102:v0001` | generator_helper | `output_mapping_unresolved` | 0 |
| review | `/tmp/ffpc-r17-session-b-tools/verify_diagnosis_receipt.py` | exact | `ffpc-r17-session-b-tools--4f5c056f17c7:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/ffpc-r17/build_chosen.py` | high-confidence | `ffpc-r17--0f1960944389:v0001` | generator_helper | `terminal_derived_state`, `output_mapping_unresolved` | 0 |
| review | `/tmp/ffpc-r18-stage/build_chosen.py` | exact | `ffpc-r18-stage--ec5c6b908907:v0001` | generator_helper | `output_mapping_unresolved` | 0 |
| review | `/tmp/ffpc-r18-stage/verify_receipt.py` | exact | `ffpc-r18-stage--c0e27c0a700a:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/ffpc-r18/build_chosen.py` | high-confidence | `ffpc-r18--34d17fa6cb38:v0001` | generator_helper | `terminal_derived_state`, `output_mapping_unresolved` | 0 |
| review | `/tmp/ffpc-r19-build-session-a.py` | exact | `tmp-root--a50e74eb109f:v0001` | generator_or_assembler | `output_mapping_unresolved` | 0 |
| review | `/tmp/ffpc-r19-stage/build_chosen.py` | exact | `ffpc-r19-stage--93bc955995c5:v0002` | generator_helper | `output_mapping_unresolved` | 0 |
| review | `/tmp/ffpc-r19/build_chosen.py` | high-confidence | `ffpc-r19--dd44df299cd3:v0001` | generator_helper | `terminal_derived_state`, `output_mapping_unresolved` | 0 |
| review | `/tmp/ffpc-r20-build-session-a.py` | exact | `tmp-root--682d009c56a7:v0001` | generator_or_assembler | `output_mapping_unresolved` | 0 |
| review | `/tmp/ffpc-r20-stage/build_chosen.py` | exact | `ffpc-r20-stage--9afe26c6c6c0:v0001` | generator_helper | `output_mapping_unresolved` | 0 |
| review | `/tmp/ffpc-r20/build_chosen.py` | high-confidence | `ffpc-r20--fa644e626ba8:v0001` | generator_helper | `terminal_derived_state`, `output_mapping_unresolved` | 0 |
| review | `/tmp/ffpc-r21-build-session-a.py` | exact | `tmp-root--a5da231acbf2:v0001` | generator_or_assembler | `output_mapping_unresolved` | 0 |
| review | `/tmp/ffpc-r22-build-session-a.py` | exact | `tmp-root--f70cccd1e05f:v0001` | generator_or_assembler | `output_mapping_unresolved` | 0 |
| review | `/tmp/ffpc-r23-build-session-a.py` | exact | `tmp-root--582a726e3771:v0004` | generator_or_assembler | `output_mapping_unresolved` | 0 |
| review | `/tmp/ffpc-r23-build.py` | exact | `tmp-root--2979706f0c1f:v0001` | generator_or_assembler | `output_mapping_unresolved` | 0 |
| review | `/tmp/ffpc-r23-session-b.py` | exact | `tmp-root--357edd49efdc:v0001` | generator_or_assembler | `provenance_conflict` | 3 |
| review | `/tmp/ffpc-r24-build-session-a.py` | exact | `tmp-root--04e2cdcfa137:v0001` | generator_or_assembler | `output_mapping_unresolved` | 0 |
| review | `/tmp/ffpc-r25-stage/build_chosen.py` | exact | `ffpc-r25-stage--231c101a0207:v0001` | generator_helper | `output_mapping_unresolved` | 0 |
| review | `/tmp/ffpc-r26-stage/build_chosen.py` | exact | `ffpc-r26-stage--edfb4891ac17:v0001` | generator_helper | `output_mapping_unresolved` | 0 |
| review | `/tmp/ffpc-r27-build-session-a.py` | exact | `tmp-root--080820831da4:v0001` | generator_or_assembler | `output_mapping_unresolved` | 0 |
| review | `/tmp/ffpc-r27-stage/build_chosen.py` | exact | `ffpc-r27-stage--12595d65cde5:v0002` | generator_helper | `output_mapping_unresolved` | 0 |
| review | `/tmp/ffpc-r28-splice-plants.py` | exact | `tmp-root--0234d579678b:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/ffpc-r28-stage/build_chosen.py` | exact | `ffpc-r28-stage--0ee31050f6be:v0002` | generator_helper | `output_mapping_unresolved` | 0 |
| review | `/tmp/ffpc-r28-stage/extract_diagnosis_brief.py` | exact | `ffpc-r28-stage--fff46de2b8ca:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/ffpc-r29-build-session-a.py` | exact | `tmp-root--b0b81573df36:v0001` | generator_or_assembler | `output_mapping_unresolved` | 0 |
| review | `/tmp/ffpc-r31-pairs-fragment.py` | exact | `tmp-root--838e7d369582:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/ffpc-r31-stage/build_chosen.py` | exact | `ffpc-r31-stage--36edc7d84a29:v0001` | generator_helper | `output_mapping_unresolved` | 0 |
| review | `/tmp/ffpc-r32-splice-plants.py` | exact | `tmp-root--fa4fc1612ee3:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/ffpc-r32-stage/build_chosen.py` | exact | `ffpc-r32-stage--945fcc6d20ce:v0002` | generator_helper | `output_mapping_unresolved` | 0 |
| review | `/tmp/ffpc-r33-pairs-fragment.py` | exact | `tmp-root--2ed34195542b:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/ffpc-r33-stage/build_chosen.py` | exact | `ffpc-r33-stage--bce8e0021324:v0001` | generator_helper | `output_mapping_unresolved` | 0 |
| review | `/tmp/ffpc-r62-build.py` | exact | `tmp-root--25af5dcc71a6:v0021` | generator_or_assembler | `high_risk_operation` | 10 |
| review | `/tmp/ffpc-r63-build-session-a.py` | exact | `tmp-root--27fb30625c82:v0001` | generator_or_assembler | `output_mapping_unresolved` | 0 |
| review | `/tmp/ffpc-r65/build_session_a_r65.py` | exact | `ffpc-r65--18b559351c5f:v0001` | generator_or_assembler | `output_mapping_unresolved` | 0 |
| review | `/tmp/ffpc_r05_session_a.py` | exact | `tmp-root--acf63a92a504:v0001` | generator_or_assembler | `high_risk_operation`, `output_mapping_unresolved` | 0 |
| review | `/tmp/ffpc_r64_session_a.py` | exact | `tmp-root--3142a6d7ed4a:v0001` | generator_or_assembler | `output_mapping_unresolved` | 0 |
| review | `/tmp/ffpc_r66_session_a_build.py` | exact | `tmp-root--d8022c7be6bc:v0001` | generator_or_assembler | `output_mapping_unresolved` | 0 |
| review | `/tmp/ffpc_r67_session_a.py` | exact | `tmp-root--68d8339c49d9:v0003` | generator_or_assembler | `output_mapping_unresolved` | 0 |
| review | `/tmp/gen_ttf_r43_window.py` | exact | `tmp-root--2e0689913959:v0003` | generator_or_assembler | `high_risk_operation`, `provenance_conflict` | 3 |
| review | `/tmp/maos-r14/build_r14.py` | exact | `maos-r14--5e3bb3ee2d65:v0006` | generator_or_assembler | `high_risk_operation` | 1 |
| review | `/tmp/maos-r15-audit-run.py` | exact | `tmp-root--b78ce254ab50:v0004` | unknown_temp_python_role | `high_risk_operation`, `output_mapping_unavailable` | 0 |
| review | `/tmp/maos-r15/build_r15.py` | exact | `maos-r15--188f08b52485:v0002` | generator_or_assembler | `high_risk_operation` | 1 |
| review | `/tmp/maos-r16/build_r16.py` | exact | `maos-r16--773bc12f3388:v0004` | generator_or_assembler | `high_risk_operation` | 1 |
| review | `/tmp/maos-r19/build_r19.py` | exact | `maos-r19--17818e5dd11c:v0005` | generator_or_assembler | `high_risk_operation` | 1 |
| review | `/tmp/maos-r20/build_r20.py` | exact | `maos-r20--a4cfc801e8f1:v0002` | generator_or_assembler | `high_risk_operation` | 1 |
| review | `/tmp/maos-r21/build_r21.py` | exact | `maos-r21--47db98509f62:v0001` | generator_or_assembler | `high_risk_operation` | 1 |
| review | `/tmp/maos-r23/build_r23.py` | exact | `maos-r23--80d63e849dce:v0001` | generator_or_assembler | `high_risk_operation` | 1 |
| review | `/tmp/maos-r23c/build_r23c.py` | exact | `maos-r23c--90caa4de1afb:v0006` | generator_or_assembler | `high_risk_operation`, `provenance_conflict` | 3 |
| review | `/tmp/maos-r24/build_r24.py` | exact | `maos-r24--6140cb00553b:v0003` | generator_or_assembler | `high_risk_operation` | 1 |
| review | `/tmp/maos-r25/build_r25.py` | exact | `maos-r25--8fb9f48ab98f:v0001` | generator_or_assembler | `high_risk_operation` | 1 |
| review | `/tmp/maos-r29/build_r29.py` | exact | `maos-r29--93a3eb982d91:v0001` | generator_or_assembler | `high_risk_operation` | 1 |
| review | `/tmp/maos-r30/build_r30.py` | exact | `maos-r30--82477a955d00:v0001` | generator_or_assembler | `high_risk_operation` | 1 |
| review | `/tmp/maos-r31/build_r31.py` | exact | `maos-r31--98337e5ae1fe:v0009` | generator_or_assembler | `high_risk_operation` | 3 |
| review | `/tmp/maos-r32/build_r32.py` | exact | `maos-r32--feff798a8d46:v0010` | generator_or_assembler | `high_risk_operation` | 1 |
| review | `/tmp/maos-r33/build_r33.py` | exact | `maos-r33--a308f663ff99:v0016` | generator_or_assembler | `high_risk_operation` | 3 |
| review | `/tmp/maos-r34/build_r34.py` | exact | `maos-r34--947712f03cfd:v0014` | generator_or_assembler | `high_risk_operation` | 4 |
| review | `/tmp/maos-r35/build_r35.py` | exact | `maos-r35--9c6e64a385c3:v0015` | generator_or_assembler | `high_risk_operation` | 1 |
| review | `/tmp/maos-r36/build_r36.py` | exact | `maos-r36--3471b7c88ec5:v0008` | generator_or_assembler | `high_risk_operation` | 1 |
| review | `/tmp/maos-r39/build_r39.py` | exact | `maos-r39--93468e42e457:v0001` | generator_or_assembler | `high_risk_operation` | 1 |
| review | `/tmp/maos-r41/_notes_tx.py` | exact | `maos-r41--ff26705b7892:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/maos-r41/build_r41.py` | exact | `maos-r41--90d5139324c0:v0006` | generator_or_assembler | `high_risk_operation` | 3 |
| review | `/tmp/maos-r42/build_r42.py` | exact | `maos-r42--de5d5bc7a0c6:v0001` | generator_or_assembler | `high_risk_operation` | 2 |
| review | `/tmp/maos-r43/build_r43.py` | exact | `maos-r43--2021122a16a4:v0015` | generator_or_assembler | `high_risk_operation` | 1 |
| review | `/tmp/maos-r44/_fns.py` | exact | `maos-r44--7637ce2b7e6c:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/maos-r44/_notes.py` | exact | `maos-r44--d029f4e41fe9:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/maos-r44/_tr.py` | exact | `maos-r44--697ff8ff744e:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/maos-r45/_notes.py` | exact | `maos-r45--9dc1c7f17e9d:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/maos-r45/_transcript.py` | exact | `maos-r45--098507a93f81:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/maos-r46/build_r46.py` | exact | `maos-r46--a6b7346833ba:v0001` | generator_or_assembler | `high_risk_operation` | 1 |
| review | `/tmp/maos-r47/build_r47.py` | exact | `maos-r47--5b962a4cc1bd:v0001` | generator_or_assembler | `high_risk_operation` | 1 |
| review | `/tmp/maos-r48/build_r48.py` | exact | `maos-r48--12584d64998d:v0001` | generator_or_assembler | `high_risk_operation` | 1 |
| review | `/tmp/maos-r51/build_r51.py` | exact | `maos-r51--74a8ccf179f8:v0013` | generator_or_assembler | `high_risk_operation` | 2 |
| review | `/tmp/maos-r52/build_r52.py` | exact | `maos-r52--e0ccc5b0f0c4:v0020` | generator_or_assembler | `high_risk_operation` | 4 |
| review | `/tmp/maos-r55/notes_fn.py` | exact | `maos-r55--bc006f61aed7:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/maos-r55/transcript_fn.py` | exact | `maos-r55--9c0841156216:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/maos-r58/_transform_from_r54.py` | exact | `maos-r58--7c1051a54dea:v0002` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/maos-r63-live-build/build_r63.py` | exact | `maos-r63-live-build--97e311e7af10:v0001` | generator_or_assembler | `high_risk_operation` | 1 |
| review | `/tmp/maos-r67/build_r67.py` | exact | `maos-r67--f7a3a06137cb:v0002` | generator_or_assembler | `high_risk_operation` | 3 |
| review | `/tmp/maos-r68/snippets/write_notes.py` | exact | `maos-r68__snippets--ca2a22ff9f9b:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/maos-r68/snippets/write_transcript.py` | exact | `maos-r68__snippets--3a67fff0938a:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/maos-r69/_text.py` | exact | `maos-r69--99470bfb61c7:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/maos_r02c_gen.py` | exact | `tmp-root--408897cc5767:v0002` | generator_or_assembler | `provenance_conflict` | 6 |
| review | `/tmp/nelb-r01-live/gen_r01.py` | exact | `nelb-r01-live--a4378171ce87:v0001` | generator_or_assembler | `high_risk_operation` | 2 |
| review | `/tmp/nelb-r03-live/gen_r03.py` | exact | `nelb-r03-live--10706cab715f:v0001` | generator_or_assembler | `high_risk_operation` | 3 |
| review | `/tmp/nelb-r23/rec070_071.py` | exact | `nelb-r23--72f077ebe927:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/nelb-r29/rec_088.py` | exact | `nelb-r29--6807d6e005fe:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/nelb-r29/rec_090.py` | exact | `nelb-r29--1e9487fe24cc:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/nelb-r31/_rec094.py` | exact | `nelb-r31--9d62d2c0da93:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/nelb-r32/_rec_099.py` | exact | `nelb-r32--3835e28628bb:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/nelb-r34/write_notes_r34.py` | exact | `nelb-r34--710e6d037055:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/nelb-r38/rec_117.py` | exact | `nelb-r38--9ef70453ca95:v0005` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/nelb-r39/_rec118.py` | exact | `nelb-r39--ac83f6e95eb6:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/nelb-r39/_rec120.py` | exact | `nelb-r39--c04859094a5f:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/nelb-r45/_136_137.py` | exact | `nelb-r45--89aec1ba4977:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/nelb-r47/_rec142.py` | exact | `nelb-r47--cd333006dd9c:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/nelb-r54/rec_164.py` | exact | `nelb-r54--af895a6bc656:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/nelb-r55/_front.py` | exact | `nelb-r55--988f8432b3fe:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/nelb-r60/_new_181_182.py` | exact | `nelb-r60--cf2b73a18392:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/nelb-r61/_184_185.py` | exact | `nelb-r61--0a7457837e82:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/nelb-r63-live/gen_r63.py` | exact | `nelb-r63-live--8c876e7dbf46:v0004` | generator_or_assembler | `high_risk_operation` | 4 |
| review | `/tmp/nelb-r64-live/gen_r64.py` | high-confidence | `nelb-r64-live--6f2120a0c430:v0034` | generator_or_assembler | `terminal_derived_state`, `high_risk_operation` | 7 |
| review | `/tmp/nelb-r67/_rec202.py` | exact | `nelb-r67--d1e45e812852:v0004` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/nelb-r67/_rec203.py` | exact | `nelb-r67--20737df2640a:v0004` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/nelb-r67/_rec204.py` | exact | `nelb-r67--6a7eba414fd1:v0005` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/nelb-r69/_rec209_210.py` | exact | `nelb-r69--f8cdcff3e099:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/nelb-sf-r01/gen_r01.py` | exact | `nelb-sf-r01--eadae208d9db:v0001` | generator_or_assembler | `high_risk_operation` | 4 |
| review | `/tmp/nelb-sfw-r21/gen_r21.py` | exact | `nelb-sfw-r21--3cdca1832613:v0001` | generator_or_assembler | `provenance_conflict` | 6 |
| review | `/tmp/nelb_r04_write.py` | exact | `tmp-root--457a8567fad0:v0005` | generator_or_assembler | `high_risk_operation` | 1 |
| review | `/tmp/scan_real.py` | exact | `tmp-root--a3f985ada018:v0004` | unknown_temp_python_role | `high_risk_operation` | 0 |
| review | `/tmp/sf-maos-r41-build.py` | exact | `tmp-root--0b2605c5ba79:v0005` | generator_or_assembler | `high_risk_operation` | 3 |
| review | `/tmp/ttf-r101/_rec522.py` | exact | `ttf-r101--6c517703cc8a:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/ttf-r102/_notes_r102.py` | exact | `ttf-r102--fb559aaad9d5:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/ttf-r109/_apply.py` | exact | `ttf-r109--637168eb5bec:v0001` | unknown_temp_python_role | `high_risk_operation`, `output_mapping_unavailable` | 0 |
| review | `/tmp/ttf-r111/_splice.py` | exact | `ttf-r111--e44707930159:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/ttf-r117/_notes_r117.py` | exact | `ttf-r117--af8cdc10e386:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/ttf-r118/_patch.py` | exact | `ttf-r118--ff62e0faa23f:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/ttf-r118/_xform.py` | exact | `ttf-r118--cc9efa6a5c9d:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/ttf-r13-audit-run.py` | exact | `tmp-root--cf758e793abf:v0001` | unknown_temp_python_role | `high_risk_operation`, `output_mapping_unavailable` | 0 |
| review | `/tmp/ttf-r14-audit-run.py` | exact | `tmp-root--3d7ee96225ae:v0001` | unknown_temp_python_role | `high_risk_operation`, `output_mapping_unavailable` | 0 |
| review | `/tmp/ttf-r16/gen_r16.py` | exact | `ttf-r16--9c5e6ee8399b:v0004` | generator_or_assembler | `high_risk_operation` | 3 |
| review | `/tmp/ttf-r23-live/gen_r23.py` | exact | `ttf-r23-live--508169392d66:v0001` | generator_or_assembler | `high_risk_operation` | 3 |
| review | `/tmp/ttf-r23/gen_r23.py` | exact | `ttf-r23--8a3c40628e1a:v0001` | generator_or_assembler | `high_risk_operation` | 2 |
| review | `/tmp/ttf-r25-live/gen_r25.py` | high-confidence | `ttf-r25-live--5fc901fce206:v0021` | generator_or_assembler | `terminal_derived_state`, `high_risk_operation` | 2 |
| review | `/tmp/ttf-r25/_new_143_144.py` | exact | `ttf-r25--6f9eec110fac:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/ttf-r28/gen_r28.py` | exact | `ttf-r28--41c3ef7c8895:v0131` | generator_or_assembler | `high_risk_operation` | 3 |
| review | `/tmp/ttf-r29/gen_r29.py` | exact | `ttf-r29--64758b807a98:v0001` | generator_or_assembler | `high_risk_operation` | 1 |
| review | `/tmp/ttf-r31/gen_r31.py` | exact | `ttf-r31--dadcef3e2ae6:v0021` | generator_or_assembler | `high_risk_operation` | 2 |
| review | `/tmp/ttf-r32/gen_r32.py` | exact | `ttf-r32--acb72c775bf4:v0046` | generator_or_assembler | `high_risk_operation` | 2 |
| review | `/tmp/ttf-r33/gen_r33.py` | exact | `ttf-r33--5a2cc0050ea1:v0001` | generator_or_assembler | `high_risk_operation` | 1 |
| review | `/tmp/ttf-r34/gen_r34.py` | exact | `ttf-r34--f397fa4cfd7e:v0002` | generator_or_assembler | `high_risk_operation` | 4 |
| review | `/tmp/ttf-r35/gen_r35.py` | exact | `ttf-r35--cc2af472abf5:v0007` | generator_or_assembler | `high_risk_operation` | 4 |
| review | `/tmp/ttf-r38/gen_r38.py` | exact | `ttf-r38--0ad839dfa515:v0003` | generator_or_assembler | `high_risk_operation` | 3 |
| review | `/tmp/ttf-r42w/_lif.py` | exact | `ttf-r42w--603dea0789ac:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/ttf-r42w/_rec701.py` | exact | `ttf-r42w--8bb18e34b8c5:v0004` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/ttf-r42w/_rec702.py` | exact | `ttf-r42w--5767faa1e095:v0002` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/ttf-r42w/_rec703.py` | exact | `ttf-r42w--22bea728ffb8:v0002` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/ttf-r42w/_rec704.py` | exact | `ttf-r42w--4771cdd0386b:v0002` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/ttf-r42w/_rec705.py` | exact | `ttf-r42w--f7eb72f51073:v0002` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/ttf-r47/_r252.py` | exact | `ttf-r47--954b0be79386:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/ttf-r58/gen_r58.py` | exact | `ttf-r58--66e11b64cb50:v0002` | generator_or_assembler | `high_risk_operation` | 2 |
| review | `/tmp/ttf-r59/_notes_r59.py` | exact | `ttf-r59--dbfd1c4009d8:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/ttf-r62/_new_body.py` | exact | `ttf-r62--80ccc927af83:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/ttf-r62b/gen_r62.py` | exact | `ttf-r62b--3b1753e5ffb1:v0001` | generator_or_assembler | `high_risk_operation` | 4 |
| review | `/tmp/ttf-r63-311/gen_r63.py` | exact | `ttf-r63-311--2388f79e62cd:v0006` | generator_or_assembler | `high_risk_operation` | 2 |
| review | `/tmp/ttf-r65-live/gen_r65.py` | exact | `ttf-r65-live--ce6b3cd6aeaf:v0001` | generator_or_assembler | `high_risk_operation` | 3 |
| review | `/tmp/ttf-r67-live/gen_r67.py` | exact | `ttf-r67-live--424292aefe25:v0001` | generator_or_assembler | `high_risk_operation` | 2 |
| review | `/tmp/ttf-r67/_rec_block.py` | exact | `ttf-r67--b14d5e834e4b:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/ttf-r68/_notes.py` | exact | `ttf-r68--22cb254ac63c:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/ttf-r70-live/gen_r70.py` | exact | `ttf-r70-live--54e56599ca27:v0001` | generator_or_assembler | `high_risk_operation` | 2 |
| review | `/tmp/ttf-r71-live/occ_check.py` | exact | `ttf-r71-live--89efa649ccbc:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/ttf-r73-live/_notes_fn.py` | exact | `ttf-r73-live--117ef2ab8873:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/ttf-r81/_rec422.py` | exact | `ttf-r81--daf9ec27576e:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/ttf-r85/_notes_r85.py` | exact | `ttf-r85--52f66dbd3e92:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/ttf-r89/_rest.py` | exact | `ttf-r89--2c4f8729390b:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/ttf-r89/_rest2.py` | exact | `ttf-r89--f8c91779d6b3:v0003` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/ttf-r92/_notes_r92.py` | exact | `ttf-r92--fbb7b12c98de:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/ttf-r95/_notes_r95.py` | exact | `ttf-r95--5dd3bfdd3729:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/ttf-r99/_patch_r99.py` | exact | `ttf-r99--9dbb353a8922:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/ttf-r99/_rec512.py` | exact | `ttf-r99--170484f24a03:v0001` | unknown_temp_python_role | `output_mapping_unavailable` | 0 |
| review | `/tmp/ttf_r02c_gen.py` | exact | `tmp-root--215e7a505f5c:v0008` | generator_or_assembler | `provenance_conflict` | 3 |
| review | `/tmp/ttf_r12_gen.py` | exact | `tmp-root--b4b9fdb4a3dc:v0004` | generator_or_assembler | `high_risk_operation` | 1 |
