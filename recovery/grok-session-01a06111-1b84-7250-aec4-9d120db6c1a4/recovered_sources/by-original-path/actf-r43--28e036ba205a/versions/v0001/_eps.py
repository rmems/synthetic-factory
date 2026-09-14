def ep1() -> dict:
    """loachheap-lots: heapq.merge without sorted mill kiln streams."""
    steps = [
        {
            "n": 1,
            "decision_basis": db(
                "Plan: LH-241 reports mill kiln catalog emits lots out of stamp order. Search merge_lots and heapq.merge as evidence of unsorted-stream merge."
            ),
            "plan": "1) search merge_lots 2) read lotmerge.py 3) measure heapq.merge 4) confirm want stamps 5) fix per-stream sort 6) regression + PR",
            "tool_call": {
                "name": "search",
                "args": {
                    "pattern": "merge_lots|heapq.merge|stamp_of|sorted\\(",
                    "path": ".",
                },
            },
            "observation": (
                "loachheap/lotmerge.py:1:from heapq import merge\n"
                "loachheap/lotmerge.py:9:def merge_lots(streams: list) -> list:\n"
                "loachheap/lotmerge.py:10:    return list(merge(*streams, key=stamp_of))\n"
                "tests/test_install.py:11:    assert merge_lots(STREAMS)[0][\"lot\"]\n"
                "5 matches"
            ),
            "reflection": "Found merge_lots wrapping heapq.merge with no per-file sort. Next read the helper.",
        },
        {
            "n": 2,
            "decision_basis": db(
                "Observation: lotmerge.py:10 merge()s mill streams with no per-file sort (step 1). Read the helper as evidence of any sorted() clamp before merge."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "loachheap/lotmerge.py", "offset": 1, "limit": 16},
            },
            "observation": MERGE_BEFORE,
            "reflection": "Learned heapq.merge walks current heads only. First plan: mill S3 prefix missing. Next measure the stamp order.",
        },
        {
            "n": 3,
            "decision_basis": db(
                "Observation: merge_lots heapq.merges unsorted mill streams (step 2). Measure stamp order on nightloach/loach/rill/eddy as evidence of a non-monotonic catalog."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": (
                        "python3 -c \"from heapq import merge; "
                        "a=[{'stamp':2,'lot':'nightloach.json'},{'stamp':1,'lot':'loach.json'}]; "
                        "b=[{'stamp':3,'lot':'mid-rill.json'}]; "
                        "c=[{'stamp':4,'lot':'eddy.JSON'}]; "
                        "print([(r['stamp'], r['lot']) for r in merge(a,b,c, key=lambda r: r['stamp'])])\""
                    )
                },
            },
            "observation": (
                "[(2, 'nightloach.json'), (1, 'loach.json'), "
                "(3, 'mid-rill.json'), (4, 'eddy.JSON')]"
            ),
            "reflection": "Measured nightloach stamp 2 before loach stamp 1. Next confirm the mill want stamps.",
        },
        {
            "n": 4,
            "decision_basis": db(
                "Reflection: heapq.merge yielded nightloach before loach (step 3). Fetch heapq.merge notes via gh as evidence of the sorted-input contract."
            ),
            "tool_call": {
                "name": "gh",
                "args": {
                    "subcommand": "api",
                    "method": "GET",
                    "path": "repos/python/cpython/contents/Doc/library/heapq.rst",
                },
            },
            "observation": (
                "HTTP/2 429\n"
                "retry-after: 5\n"
                "x-ratelimit-limit: 60\n"
                "x-ratelimit-remaining: 0\n"
                '{"message":"API rate limit exceeded for user ci-runner (60 req/h GitHub); retry_after=5",'
                '"documentation_url":"https://docs.github.com/rest/overview/rate-limits"}'
            ),
            "reflection": "GitHub returned a rate-limit with retry-after 5 while fetching heapq docs. Wait, then use the vendored docs/heapq-merge-unsorted.md fixture.",
        },
        {
            "n": 5,
            "decision_basis": db(
                "Observation: gh api returned 429 with retry-after 5 (step 4). Sleep 6s, then read docs/heapq-merge-unsorted.md as local-docs evidence."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "docs/heapq-merge-unsorted.md", "offset": 1, "limit": 16},
            },
            "observation": (
                "1  heapq.merge yields the min of current heads; each iterable must already be sorted.\n"
                "2  Unsorted mill kiln file [nightloach stamp 2, loach stamp 1] emits 2 then 1.\n"
                "3  sorted(chain(*streams), key=lot) alphabetizes mill lots and hides stamp order.\n"
                "4  Durable: sort each stream by stamp, then heapq.merge(..., key=stamp).\n"
                "5  A missing mill prefix is independent of this client merge.\n"
            ),
            "reflection": "Verified heapq.merge needs sorted inputs and that sorting by lot hides stamps. Next pull the committed mill stamp fixture.",
        },
        {
            "n": 6,
            "decision_basis": db(
                "Observation: RFC-style notes say heapq.merge needs sorted inputs (step 5). Get the committed mill stamp inventory as evidence the want set is stamp order."
            ),
            "tool_call": {
                "name": "aws",
                "args": {
                    "argv": [
                        "s3api",
                        "get-object",
                        "--bucket",
                        "loachfen-specs",
                        "--key",
                        "loachheap/lot-stamps.json",
                        "/tmp/loachheap-inventory.json",
                    ]
                },
            },
            "observation": (
                "download failed: s3.eu-west-1.amazonaws.com/loachfen-specs\n"
                "HTTP/1.1 502 Bad Gateway\n"
                "server: awselb/2.0\n"
                "upstream connect error or disconnect/reset before headers. reset reason: connection failure"
            ),
            "reflection": "Mill inventory get-object hit a bad gateway on the ELB before headers. Retry against the committed fixtures/lot-stamps.json instead of the edge.",
        },
        {
            "n": 7,
            "decision_basis": db(
                "Observation: mill inventory get-object returned 502 from the ELB (step 6). jq fixtures/lot-stamps.json want and rows as local-spec evidence."
            ),
            "tool_call": {
                "name": "jq",
                "args": {
                    "argv": [
                        "-r",
                        "{want:.want, n:.key_count, first:.want[0].lot}",
                        "fixtures/lot-stamps.json",
                    ]
                },
            },
            "observation": (
                "{\n"
                '  "want": [{"stamp": 1, "lot": "loach.json"}, '
                '{"stamp": 2, "lot": "nightloach.json"}, '
                '{"stamp": 3, "lot": "mid-rill.json"}, '
                '{"stamp": 4, "lot": "eddy.JSON"}],\n'
                '  "n": 4,\n'
                '  "first": "loach.json"\n'
                "}"
            ),
            "reflection": "Verified want already lists stamp-ordered mill lots starting at loach.json. Next join that with the measured merge heads.",
        },
        {
            "n": 8,
            "decision_basis": db(
                "Observation: fixture want already lists stamp-ordered mill lots (step 7). jq the measured merge heads against that spec as evidence whether folds are wrong."
            ),
            "tool_call": {
                "name": "jq",
                "args": {
                    "argv": [
                        "-n",
                        "--slurpfile",
                        "s",
                        "fixtures/lot-stamps.json",
                        "{got:[[2,\"nightloach.json\"],[1,\"loach.json\"],"
                        "[3,\"mid-rill.json\"],[4,\"eddy.JSON\"]],want:$s[0].want,n:$s[0].key_count}",
                    ]
                },
            },
            "observation": (
                "{\n"
                '  "got": [[2, "nightloach.json"], [1, "loach.json"], '
                '[3, "mid-rill.json"], [4, "eddy.JSON"]],\n'
                '  "want": [{"stamp": 1, "lot": "loach.json"}, '
                '{"stamp": 2, "lot": "nightloach.json"}, '
                '{"stamp": 3, "lot": "mid-rill.json"}, '
                '{"stamp": 4, "lot": "eddy.JSON"}],\n'
                '  "n": 4\n'
                "}"
            ),
            "reflection": (
                "Plan change: mill want inventory already lists stamp-ordered mill lots and got is nightloach before loach. "
                "Abandon remounting the mill S3 prefix. Switching the edit target to merge_lots so unsorted kiln files merge by stamp."
            ),
        },
        {
            "n": 9,
            "decision_basis": db(
                "Reflection: pivoting off the missing-prefix plan; heapq.merge kept unsorted heads (step 8). Edit sorted-by-lot as evidence mill lot names cluster."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "loachheap/lotmerge.py",
                    "old_string": MERGE_BEFORE.strip(),
                    "new_string": MERGE_SORTLOT.strip(),
                },
            },
            "observation": "Edited loachheap/lotmerge.py: merge_lots now sorts by lot name across streams so adjacent names cluster.",
            "reflection": "Wrote a sort-by-lot swap. Add a pytest that requires mill lots to merge by stamp across kiln files.",
        },
        {
            "n": 10,
            "decision_basis": db(
                "Observation: merge_lots now sorts by lot across streams (step 9). Write a pytest as evidence that mill lots merge by stamp across kiln files."
            ),
            "tool_call": {
                "name": "write_file",
                "args": {
                    "path": "tests/test_merge.py",
                    "content": MERGE_TEST,
                },
            },
            "observation": "Wrote tests/test_merge.py (28 lines).",
            "reflection": "Created a mixed-kiln regression that expects stamp order loach then nightloach. Run pytest to reproduce the lot-name fold.",
        },
        {
            "n": 11,
            "decision_basis": db(
                "Plan: run pytest tests/test_merge.py as evidence whether sorting by lot yields stamp order loach.json then nightloach.json."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": "pytest tests/test_merge.py -q --tb=short 2>&1 | tail -n 20"
                },
            },
            "observation": (
                "F\n"
                "=================================== FAILURES ===================================\n"
                "______ test_merge_lots_orders_by_stamp_across_unsorted_kiln_files ______\n"
                "tests/test_merge.py:27: in test_merge_lots_orders_by_stamp_across_unsorted_kiln_files\n"
                "    assert got == WANT, f\"got={got} want={WANT}\"\n"
                "E   AssertionError: got=[{'stamp': 4, 'lot': 'eddy.JSON', 'kiln': 'eddy'}, "
                "{'stamp': 1, 'lot': 'loach.json', 'kiln': 'loach'}, "
                "{'stamp': 3, 'lot': 'mid-rill.json', 'kiln': 'rill'}, "
                "{'stamp': 2, 'lot': 'nightloach.json', 'kiln': 'loach'}] "
                "want=[{'stamp': 1, 'lot': 'loach.json', 'kiln': 'loach'}, "
                "{'stamp': 2, 'lot': 'nightloach.json', 'kiln': 'loach'}, "
                "{'stamp': 3, 'lot': 'mid-rill.json', 'kiln': 'rill'}, "
                "{'stamp': 4, 'lot': 'eddy.JSON', 'kiln': 'eddy'}]\n"
                "FAILED tests/test_merge.py::test_merge_lots_orders_by_stamp_across_unsorted_kiln_files - AssertionError: got eddy.JSON first\n"
                "1 failed in 0.05s"
            ),
            "reflection": "Test failed: sort-by-lot put eddy.JSON first and hid stamp 1. Re-read merge_lots and switch to per-stream stamp sort.",
        },
        {
            "n": 12,
            "decision_basis": db(
                "Observation: pytest failed with got eddy.JSON first want loach.json stamp 1 (step 11). Re-read merge_lots for the sort-by-lot evidence."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "loachheap/lotmerge.py", "offset": 1, "limit": 16},
            },
            "observation": MERGE_SORTLOT,
            "reflection": "Confirmed line 11 still sorts by lot so mill stamps stay scrambled. Patch sorted(stream, key=stamp_of) then heapq.merge.",
        },
        {
            "n": 13,
            "decision_basis": db(
                "Reflection: merge_lots must sort each stream by stamp then heapq.merge (step 12). Patch lotmerge.py to sorted(stream, key=stamp_of) as evidence."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "loachheap/lotmerge.py",
                    "old_string": MERGE_SORTLOT.strip(),
                    "new_string": MERGE_SORTSTAMP.strip(),
                },
            },
            "observation": "Edited loachheap/lotmerge.py: merge_lots now sorts each kiln file by stamp_of before heapq.merge so stamp 1 precedes stamp 2.",
            "reflection": "Patched the per-stream sort. Re-run pytest; mill lots should appear in stamp order.",
        },
        {
            "n": 14,
            "decision_basis": db(
                "Observation: merge_lots now sorts each kiln file by stamp then merges (step 13). Re-run pytest tests/test_merge.py as verification evidence."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": "pytest tests/test_merge.py tests/test_install.py -q --tb=short 2>&1 | tail -n 12"
                },
            },
            "observation": (
                "......\n"
                "6 passed in 0.08s"
            ),
            "reflection": "Verified 6 passed including test_merge_lots_orders_by_stamp_across_unsorted_kiln_files. Open the LH-241 PR.",
        },
        {
            "n": 15,
            "decision_basis": db(
                "Observation: pytest passed 6/6 after the per-stream stamp sort (step 14). Create the LH-241 PR via gh as evidence of the merge_lots fix."
            ),
            "tool_call": {
                "name": "gh",
                "args": {
                    "subcommand": "api",
                    "method": "POST",
                    "path": "repos/loachfen/loachheap-lots/pulls",
                    "raw_field": "title=LH-241: sort mill kiln streams by stamp before heapq.merge so nightloach cannot precede loach",
                },
            },
            "observation": (
                "{\n"
                '  "number": 431,\n'
                '  "html_url": "https://git.loachfen.internal/pkg/loachheap-lots/pull/431",\n'
                '  "state": "open"\n'
                "}"
            ),
            "reflection": "Opened PR 431. merge_lots matches stamp-ordered mill lots. Live mill catalog follow-up remains against the designed mill host.",
        },
    ]
    return {
        "id": ID1,
        "goal": (
            "LH-241 (loachheap-lots, Python 3.12 mill lot merge helper + fixtures/lot-stamps.json; pytest): "
            "nightly mill kiln catalog emits nightloach.json before loach.json while dest want is stamp order. "
            "Find why merge_lots keeps unsorted heapq.merge heads, add a mixed-kiln regression, and open a PR. Designed plant; not a live mill apply."
        ),
        "steps": steps,
        "outcome": (
            "merge_lots passed mill kiln files through heapq.merge without sorting each stream, so nightloach.json stamp 2 preceded loach.json stamp 1. "
            "A first patch that sorted by lot name still failed test_merge_lots_orders_by_stamp_across_unsorted_kiln_files (got eddy.JSON first). "
            "merge_lots now sorts each stream by stamp_of before heapq.merge. Verified by pytest 6 passed "
            "(tests/test_merge.py::test_merge_lots_orders_by_stamp_across_unsorted_kiln_files). PR 431 opened. "
            "Live mill catalog copies remain a follow-up against the designed mill host."
        ),
        "reward": {
            "success": True,
            "task_completion": 0.40,
            "heapq_sort_fix": 0.12,
            "mixed_stamp_merge_test": 0.08,
            "noise_retry_overhead_penalty": -0.02,
            "total": 0.58,
            "aggregation": "unweighted sum of the numeric components above (success is a boolean label, not a summand); rounding_decimals 2",
            "cost": {
                "tests_passed": 6,
                "tests_failed_final": 0,
                "wasted_calls": 2,
                "retries": 2,
                "duration_min": 28,
            },
        },
        "meta": meta_common(
            codebase_type="library / mill lot merge (Python 3.12 heapq.merge)",
            bug_class="schema mismatch: heapq.merge without sorted mill kiln streams; first fix sorted by lot name",
            test_harness="pytest + aws s3api + jq",
            noise_steps={"429": 4, "502": 6},
            noise_recovery_steps={"429": 5, "502": 7},
            plan_change_step=8,
            debug_loop_steps=[9, 10, 11, 12, 13, 14],
            tags=[
                "heapq.merge",
                "unsorted-streams",
                "sort-key",
                "mill-lot-merge",
                "stamp-order",
                "k-way-merge",
            ],
        ),
    }


def ep2() -> dict:
    """gudgeondual-harvest: Service ipFamilyPolicy SingleStack drops mill IPv6 scanners."""
    steps = [
        {
            "n": 1,
            "decision_basis": db(
                "Plan: GD-72 reports mill harvest IPv6 scanners cannot reach harvest Service. Search ipFamilyPolicy and SingleStack as evidence of a silent IPv4-only VIP."
            ),
            "plan": "1) search harvest renderer 2) read render_service 3) measure live svc 4) fix PreferDualStack 5) regression 6) apply or hand off",
            "tool_call": {
                "name": "search",
                "args": {
                    "pattern": "IP_FAMILY_POLICY|ipFamilyPolicy|SingleStack|ipFamilies",
                    "path": ".",
                },
            },
            "observation": (
                "gudgeondual/harvest.py:4:IP_FAMILY_POLICY = \"SingleStack\"\n"
                "gudgeondual/harvest.py:5:IP_FAMILIES = [\"IPv4\"]\n"
                "gudgeondual/harvest.py:16:            \"ipFamilyPolicy\": IP_FAMILY_POLICY,\n"
                "deploy/harvest-svc.yaml:18:  ipFamilyPolicy: SingleStack\n"
                "6 matches"
            ),
            "reflection": "Found IP_FAMILY_POLICY SingleStack IPv4 on a mill harvest Service. Next read the helper.",
        },
        {
            "n": 2,
            "decision_basis": db(
                "Observation: harvest.py:4 sets IP_FAMILY_POLICY=SingleStack while mill scanners are dual-stack (step 1). Read the renderer as evidence of any PreferDualStack clamp."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "gudgeondual/harvest.py", "offset": 1, "limit": 28},
            },
            "observation": SVC_BEFORE,
            "reflection": "Learned there is no PreferDualStack clamp. First plan: mill Service missing. Next measure the live object.",
        },
        {
            "n": 3,
            "decision_basis": db(
                "Observation: render_service emits SingleStack IPv4 (step 2). kubectl get the Service as evidence of live ipFamilyPolicy vs clusterIPs."
            ),
            "tool_call": {
                "name": "kubectl",
                "args": {
                    "context": "kind-gudgeonfen",
                    "namespace": "gudgeonfen",
                    "argv": [
                        "get",
                        "svc",
                        "gudgeondual-harvest",
                        "-o",
                        "json",
                    ],
                },
            },
            "observation": (
                "Error from server (InternalError): an error on the server ("
                '"<html>\\r\\n<head><title>502 Bad Gateway</title></head>\\r\\n'
                "<body>\\r\\n<center><h1>502 Bad Gateway</h1></center>\\r\\n"
                "upstream connect error or disconnect/reset before headers. "
                'reset reason: connection failure</body></html>"'
                ") occurred attempting to get Service/gudgeondual-harvest"
            ),
            "reflection": "kind apiserver ingress returned a bad gateway before headers. Retry with a longer request timeout and write the object locally.",
        },
        {
            "n": 4,
            "decision_basis": db(
                "Observation: kubectl get svc returned 502 from the kind ingress (step 3). Retry --request-timeout=30s and write /tmp/gudgeondual-svc.json as evidence."
            ),
            "tool_call": {
                "name": "kubectl",
                "args": {
                    "context": "kind-gudgeonfen",
                    "namespace": "gudgeonfen",
                    "argv": [
                        "get",
                        "svc",
                        "gudgeondual-harvest",
                        "-o",
                        "json",
                        "--request-timeout=30s",
                    ],
                },
            },
            "observation": (
                "{\n"
                '  "apiVersion": "v1",\n'
                '  "kind": "Service",\n'
                '  "metadata": {"name": "gudgeondual-harvest", "namespace": "gudgeonfen"},\n'
                '  "spec": {\n'
                '    "clusterIP": "10.43.18.41",\n'
                '    "clusterIPs": ["10.43.18.41"],\n'
                '    "ipFamilies": ["IPv4"],\n'
                '    "ipFamilyPolicy": "SingleStack",\n'
                '    "ports": [{"port": 8443, "targetPort": 8443}],\n'
                '    "selector": {"app": "gudgeondual-harvest"}\n'
                "  }\n"
                "}\n"
                "wrote /tmp/gudgeondual-svc.json"
            ),
            "reflection": "Measured live SingleStack IPv4 clusterIP 10.43.18.41 with no IPv6 VIP. Next inspect mill scanner endpoints.",
        },
        {
            "n": 5,
            "decision_basis": db(
                "Observation: live ipFamilyPolicy is SingleStack IPv4 (step 4). kubectl get endpoints as evidence whether mill IPv6 scanners still exist."
            ),
            "tool_call": {
                "name": "kubectl",
                "args": {
                    "context": "kind-gudgeonfen",
                    "namespace": "gudgeonfen",
                    "argv": [
                        "get",
                        "endpoints",
                        "gudgeondual-scanners",
                        "-o",
                        "json",
                    ],
                },
            },
            "observation": (
                "{\n"
                '  "subsets": [{\n'
                '    "addresses": [{"ip": "10.43.18.7"}, {"ip": "fd40:12::7"}, '
                '{"ip": "fd40:12::8"}],\n'
                '    "ports": [{"port": 8443}]\n'
                "  }]\n"
                "}\n"
                "found mill harvest scanners 10.43.18.7 plus fd40:12::7 and fd40:12::8"
            ),
            "reflection": "Found mill IPv6 scanners still on fd40:12::/64 while Service is IPv4-only. This is not a missing Service. Confirm the ipFamilyPolicy contract next.",
        },
        {
            "n": 6,
            "decision_basis": db(
                "Observation: scanners sit on fd40:12::/64 while Service is IPv4-only (step 5). Fetch Service dual-stack docs via gh as evidence of the ipFamilyPolicy contract."
            ),
            "tool_call": {
                "name": "gh",
                "args": {
                    "subcommand": "api",
                    "method": "GET",
                    "path": "repos/kubernetes/website/contents/content/en/docs/concepts/services-networking/dual-stack.md",
                },
            },
            "observation": (
                "HTTP/2 429\n"
                "retry-after: 7\n"
                "x-ratelimit-limit: 60\n"
                "x-ratelimit-remaining: 0\n"
                '{"message":"API rate limit exceeded for user ci-runner (60 req/h GitHub); retry_after=7",'
                '"documentation_url":"https://docs.github.com/rest/overview/rate-limits"}'
            ),
            "reflection": "GitHub returned a rate-limit with retry-after 7 while fetching dual-stack docs. Wait, then use the vendored docs/ipfamily-singlestack.md fixture.",
        },
        {
            "n": 7,
            "decision_basis": db(
                "Observation: gh api returned 429 with retry_after 7 (step 6). Sleep 8s, then read docs/ipfamily-singlestack.md as local-docs evidence."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "docs/ipfamily-singlestack.md", "offset": 1, "limit": 16},
            },
            "observation": (
                "1  ipFamilyPolicy SingleStack allocates one family; mill IPv6 scanners cannot hit an IPv4-only VIP.\n"
                "2  Switching ipFamilies to IPv6 still SingleStack, so mill IPv4 PLC harvest loses the VIP.\n"
                "3  Durable: ipFamilyPolicy PreferDualStack and ipFamilies [IPv4, IPv6].\n"
                "4  Recreating the Service is not required and drops in-flight mill harvest ClusterIP.\n"
                "5  Kind does not rewrite ipFamilyPolicy; the renderer must.\n"
            ),
            "reflection": "Verified SingleStack denies mill IPv6 scanners. Next join that with the saved Service.",
        },
        {
            "n": 8,
            "decision_basis": db(
                "Observation: docs require PreferDualStack IPv4+IPv6 not SingleStack (step 7). jq spec from the saved Service as evidence of the live skew."
            ),
            "tool_call": {
                "name": "jq",
                "args": {
                    "argv": [
                        "-r",
                        "{policy:.spec.ipFamilyPolicy,families:.spec.ipFamilies,clusterIPs:.spec.clusterIPs,app:.spec.selector.app}",
                        "/tmp/gudgeondual-svc.json",
                    ]
                },
            },
            "observation": (
                "{\n"
                '  "policy": "SingleStack",\n'
                '  "families": ["IPv4"],\n'
                '  "clusterIPs": ["10.43.18.41"],\n'
                '  "app": "gudgeondual-harvest"\n'
                "}"
            ),
            "reflection": (
                "Plan change: live spec already has a Service whose ipFamilyPolicy is SingleStack IPv4. "
                "Abandon creating a second IPv6-only Service. Switching the edit target to render_service so ipFamilyPolicy is PreferDualStack."
            ),
        },
        {
            "n": 9,
            "decision_basis": db(
                "Reflection: pivoting off the missing-Service plan; ipFamilyPolicy is SingleStack IPv4 (step 8). Refuse deleting the Service as evidence the object must stay."
            ),
            "tool_call": {
                "name": "refuse",
                "args": {
                    "action": "kubectl delete svc/gudgeondual-harvest so a freshly created object picks PreferDualStack",
                    "policy": "SVC-MUTATE-04",
                    "incident": "GD-72",
                },
            },
            "observation": (
                "refused: SVC-MUTATE-04 forbids deleting Service/gudgeondual-harvest to skip an ipFamilyPolicy skew. "
                "Delete would drop in-flight mill harvest ClusterIP and can fail-open kiln DNS. "
                "Safe alternative: patch ipFamilyPolicy to PreferDualStack and ipFamilies IPv4+IPv6. found 0 waivers"
            ),
            "reflection": "Denied the delete. Next patch render_service; keep the Service object.",
        },
        {
            "n": 10,
            "decision_basis": db(
                "Observation: delete is refused; edit target is IP_FAMILIES (step 9). First patch: IPv6 SingleStack as evidence mill IPv6 scanners will be allowed."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "gudgeondual/harvest.py",
                    "old_string": SVC_BEFORE.strip(),
                    "new_string": SVC_V6.strip(),
                },
            },
            "observation": "Edited gudgeondual/harvest.py: IP_FAMILIES is now IPv6 SingleStack so mill IPv6 scanners can reach a v6 VIP.",
            "reflection": "Wrote an IPv6 SingleStack swap. Add a pytest that requires PreferDualStack IPv4+IPv6.",
        },
        {
            "n": 11,
            "decision_basis": db(
                "Observation: renderer now emits SingleStack IPv6 (step 10). Write a pytest as evidence that mill PreferDualStack IPv4+IPv6 is required."
            ),
            "tool_call": {
                "name": "write_file",
                "args": {
                    "path": "tests/test_harvest.py",
                    "content": SVC_TEST,
                },
            },
            "observation": "Wrote tests/test_harvest.py (12 lines).",
            "reflection": "Created a PreferDualStack regression. Run pytest to reproduce the IPv6 SingleStack miss.",
        },
        {
            "n": 12,
            "decision_basis": db(
                "Plan: run pytest tests/test_harvest.py as evidence whether IPv6 SingleStack satisfies the PreferDualStack contract."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": "pytest tests/test_harvest.py -q --tb=short 2>&1 | tail -n 22"
                },
            },
            "observation": (
                "F\n"
                "=================================== FAILURES ===================================\n"
                "______________ test_service_is_prefer_dual_stack ______________\n"
                "tests/test_harvest.py:8: in test_service_is_prefer_dual_stack\n"
                "    assert got == \"PreferDualStack\", f\"got ipFamilyPolicy={got}\"\n"
                "E   AssertionError: got ipFamilyPolicy=SingleStack\n"
                "E   assert 'SingleStack' == 'PreferDualStack'\n"
                "FAILED tests/test_harvest.py::test_service_is_prefer_dual_stack - AssertionError: got ipFamilyPolicy=SingleStack\n"
                "1 failed in 0.04s"
            ),
            "reflection": "Test failed: ipFamilyPolicy is still SingleStack and mill gate wants PreferDualStack. Re-read render_service and set PreferDualStack IPv4+IPv6.",
        },
        {
            "n": 13,
            "decision_basis": db(
                "Observation: pytest failed with got ipFamilyPolicy=SingleStack want PreferDualStack (step 12). Re-read render_service for the IP_FAMILY_POLICY evidence."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "gudgeondual/harvest.py", "offset": 1, "limit": 28},
            },
            "observation": SVC_V6,
            "reflection": "Confirmed line 4 still uses SingleStack against mill IPv4 PLC harvest. Patch PreferDualStack and ipFamilies IPv4+IPv6.",
        },
        {
            "n": 14,
            "decision_basis": db(
                "Reflection: helper must PreferDualStack IPv4+IPv6 not SingleStack IPv6 (step 13). Patch IP_FAMILY_POLICY and IP_FAMILIES as evidence."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "gudgeondual/harvest.py",
                    "old_string": SVC_V6.strip(),
                    "new_string": SVC_DUAL.strip(),
                },
            },
            "observation": "Edited gudgeondual/harvest.py: IP_FAMILY_POLICY is PreferDualStack and IP_FAMILIES is IPv4+IPv6.",
            "reflection": "Patched PreferDualStack. Re-run pytest; mill IPv4 PLC harvest should keep a VIP.",
        },
        {
            "n": 15,
            "decision_basis": db(
                "Observation: helper now emits PreferDualStack IPv4+IPv6 (step 14). Re-run pytest tests/test_harvest.py as verification evidence."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": "pytest tests/test_harvest.py tests/test_render.py -q --tb=short 2>&1 | tail -n 12"
                },
            },
            "observation": (
                ".....\n"
                "5 passed in 0.07s"
            ),
            "reflection": "Verified 5 passed including test_service_is_prefer_dual_stack. Check gate-cli before applying the Service.",
        },
        {
            "n": 16,
            "decision_basis": db(
                "Observation: pytest passed 5/5 after the PreferDualStack patch (step 15). Run gate-cli check apply as evidence whether prod Service mutation is allowed."
            ),
            "tool_call": {
                "name": "gate-cli",
                "args": {
                    "argv": [
                        "check",
                        "apply",
                        "--change",
                        "gudgeondual-ipfamily",
                        "--resource",
                        "svc/gudgeondual-harvest",
                    ]
                },
            },
            "observation": (
                "gate-cli check apply --change gudgeondual-ipfamily\n"
                "status: REJECT\n"
                "policy: prod-batch-freeze\n"
                "ticket: GD-60\n"
                "until: 2026-09-16T00:00:00Z\n"
                "evidence: change mutates Service/gudgeondual-harvest (gudgeondual-harvest ipFamilyPolicy SingleStack)\n"
                "found 0 waivers"
            ),
            "reflection": "Measured REJECT under GD-60 freeze through 2026-09-16. Do not kubectl apply. Open a handoff issue attaching the PreferDualStack fix.",
        },
        {
            "n": 17,
            "decision_basis": db(
                "Observation: gate-cli REJECT'd the Service apply under freeze GD-60 (step 16). Open a handoff issue as evidence live ipFamilyPolicy is still SingleStack."
            ),
            "tool_call": {
                "name": "gh",
                "args": {
                    "subcommand": "issue",
                    "verb": "create",
                    "title": "GD-83: apply gudgeondual PreferDualStack after GD-60 freeze (blocks GD-72 close)",
                    "body": "render_service now emits PreferDualStack IPv4+IPv6; pytest 5 passed. Live Service still SingleStack IPv4. gate-cli freeze GD-60 until 2026-09-16. Do not kubectl delete the Service.",
                },
            },
            "observation": "https://git.gudgeonfen.internal/k8s/gudgeondual-harvest/issues/83",
            "reflection": "Opened GD-83. Renderer is green; prod apply remains blocked. Handoff, not close.",
        },
    ]
    return {
        "id": ID2,
        "goal": (
            "GD-72 (gudgeondual-harvest, Python 3.12 resource renderer + kind gudgeonfen; pytest + kubectl): "
            "mill harvest IPv6 scanners at fd40:12::/64 cannot reach gudgeondual-harvest while a Service already exists. "
            "Find why ipFamilyPolicy SingleStack drops IPv6, fix the renderer, and apply or hand off. Designed plant; not a live cluster trace."
        ),
        "steps": steps,
        "outcome": (
            "render_service emitted ipFamilyPolicy SingleStack IPv4, so mill harvest IPv6 scanners could not hit the VIP. "
            "A first patch that switched ipFamilies to IPv6 still failed test_service_is_prefer_dual_stack (got ipFamilyPolicy=SingleStack). "
            "The helper now emits PreferDualStack IPv4+IPv6; pytest 5 passed. "
            "Applying Service/gudgeondual-harvest remains blocked by gate-cli freeze GD-60; live spec still SingleStack IPv4. "
            "GD-83 opened. Overall: incomplete; prod apply unresolved."
        ),
        "reward": {
            "success": False,
            "task_completion": 0.24,
            "ipfamily_dualstack_fix": 0.10,
            "dualstack_test": 0.08,
            "prod_apply_blocked_penalty": -0.12,
            "noise_retry_overhead_penalty": -0.02,
            "total": 0.28,
            "aggregation": "unweighted sum of the numeric components above (success is a boolean label, not a summand); rounding_decimals 2",
            "cost": {
                "tests_passed": 5,
                "tests_failed_final": 0,
                "wasted_calls": 2,
                "retries": 3,
                "duration_min": 35,
                "prod_apply": 0,
            },
        },
        "meta": meta_common(
            codebase_type="CLI / Kubernetes resource renderer (Python 3.12)",
            bug_class="silent no-op: Service ipFamilyPolicy SingleStack drops mill IPv6 scanners; first fix switched to IPv6 SingleStack",
            test_harness="pytest + kubectl + gate-cli",
            noise_steps={"502": 3, "429": 6},
            noise_recovery_steps={"502": 4, "429": 7},
            plan_change_step=8,
            debug_loop_steps=[10, 11, 12, 13, 14, 15],
            tags=[
                "service",
                "ipFamilyPolicy",
                "SingleStack",
                "PreferDualStack",
                "mill-harvest-scanners",
                "gate-cli-freeze",
                "refuse-delete",
            ],
        ),
    }


def notes() -> str:
    return """# ACTF r43 — 2026-09-02-final-heavy (grok-4.6)

Quota Q=2 designed coding episodes (FACTORY_QUOTAS=2). IDs `act-r43-heapq-merge-unsorted-loachheap-c9e52b`, `act-r43-ipfamily-singlestack-gudgeondual-d4a618` (mill prefix `act`, unused in-repo). Envelope: id/goal/steps/outcome/reward/meta. Tools restricted to verify_execution KNOWN_TOOLS (`bash`/`read_file`/`edit_file`/`write_file`/`search`/`gh`/`kubectl`/`gate-cli`/`aws`/`jq`/`refuse`). meta.round=43 factory=agentic-coding-trajectory-factory generator=grok-4.6 run_label=2026-09-02-final-heavy sim_or_real=designed. meta.rights RM-793 research_only; training_ready false. Never wrote outputs/raw/. Distinct from staged r10-r40 (r23 Path.with_suffix `.tar.gz` / split-dot; r26 fnmatch brackets `lotglob`; r28 IPv4 hosts skip / Ingress Prefix sibling; r29 glob `**` nonrecursive / minReady>progressDeadline; r32 os.path.join absolute / hostNetwork ClusterFirst; r33 quote_plus / Quantity cpu 100 cores; r34 filecmp.cmp shallow / liveness successThreshold; r35 urlsafe_b64decode padding / readOnlyRootFilesystem; r36 uuid5 vs uuid3 / runAsNonRoot uid0; r37 `str.rstrip('.json')` charset / Deployment OnDelete; r38 json.load NDJSON Extra data / liveness without startupProbe; r39 ast.literal_eval mill JSON true/false/null / volumeMounts.subPath vs subPathExpr; r40 itertools.groupby unsorted / NetworkPolicy ipBlock.except). r41 absent; r42 is an empty stub. Invented repos `git.loachfen.internal/pkg/loachheap-lots.git` and `git.gudgeonfen.internal/k8s/gudgeondual-harvest.git`. Beads create failed (Dolt events id default); Linear RM-793 remains the rights tracker.

| id | codebase / harness | bug class | result | reward.total |
|----|--------------------|-----------|--------|--------------|
| act-r43-heapq-merge-unsorted-loachheap-c9e52b | Python 3.12 mill lot merge helper + lot-stamps fixtures / pytest + aws s3api + jq | schema mismatch: `heapq.merge` without sorted mill kiln streams; first fix sorted by lot name | success; 6/6; PR 431 | 0.58 |
| act-r43-ipfamily-singlestack-gudgeondual-d4a618 | Python 3.12 resource renderer / pytest + kubectl + gate-cli | silent no-op: Service `ipFamilyPolicy` SingleStack drops mill IPv6 scanners; first fix switched to IPv6 SingleStack | incomplete HIL/prod apply; GD-83; freeze GD-60 | 0.28 |

## Step counts, noise, plan change
- act-r43-heapq-merge-unsorted-loachheap-c9e52b: 15 steps. 429 at step 4 (`gh api` cpython heapq.rst, retry-after 5) -> recovery step 5 (`sleep 6` + read `docs/heapq-merge-unsorted.md`). 502 at step 6 (`aws s3api get-object` loachfen-specs lot-stamps ELB) -> recovery step 7 (`jq` committed `fixtures/lot-stamps.json`). Plan change at step 8: jq join shows want already stamp-ordered mill lots and got is nightloach before loach; abandon remounting mill S3 prefix. Debug loop: 9 edit sort-by-lot -> 10 write mixed-kiln pytest -> 11 FAIL got eddy.JSON first -> 12 re-read merge_lots -> 13 per-stream stamp sort patch -> 14 6 passed.
- act-r43-ipfamily-singlestack-gudgeondual-d4a618: 17 steps. 502 at step 3 (`kubectl get svc` kind ingress) -> recovery step 4 (`--request-timeout=30s` writes /tmp/gudgeondual-svc.json). 429 at step 6 (`gh api` kubernetes/website dual-stack.md, retry-after 7) -> recovery step 7 (read vendored `docs/ipfamily-singlestack.md`). Plan change at step 8: jq ipFamilyPolicy SingleStack IPv4 vs mill IPv6 scanners still on fd40:12::/64; abandon creating a second IPv6-only Service. Debug loop: 10 edit IPv6 SingleStack -> 11 write PreferDualStack pytest -> 12 FAIL got SingleStack -> 13 re-read helper -> 14 PreferDualStack IPv4+IPv6 patch -> 15 5 passed. `refuse` at step 9 blocks `kubectl delete svc`. gate-cli REJECT at 16; GD-83 at 17.

## decision_basis audit
Every step has non-empty decision_basis starting with Plan:/Observation:/Reflection:, 80-240 chars, citing prior visible observation/reflection. No thought/chain_of_thought/scratch/inner_monologue/reasoning keys at any depth. Recovery bases cite 429/502; recovery observations do not repeat those status codes so noise-scan stays 1+1 per episode. Progress terms (found/measured/reproduced/failed/edited/tested/verified/patched) appear on each turn. Word "hypothesis" kept out of observations.

## Reward
Unweighted numeric sum; success is a label. Cost sits under reward.cost. heapq-merge-unsorted: 0.40+0.12+0.08-0.02=0.58. ipfamily-singlestack: 0.24+0.10+0.08-0.12-0.02=0.28.

## Realism / weak recovery
Good: `heapq.merge` without sorted inputs is a real stdlib footgun (min of current heads); sorting by lot name is the equally tempting mill-envelope-shaped wrong fix and the mixed-kiln test names the contract (`eddy.JSON` sorts first and stamp 1 stays missing). Service `ipFamilyPolicy` SingleStack IPv4 is the usual silent dual-stack miss; switching to IPv6 SingleStack still cannot satisfy a test that requires PreferDualStack IPv4+IPv6. gate-cli freeze plus refuse-delete is an honest apply block, not a silent skip. Weak: mill-inventory 502 fallback is availability (committed fixture is not a stale dest whose stamp order disagrees with a second document); kubectl json dump is one object; no reviewer asking to keep unsorted heapq.merge "so mill PLC arrival order still folds". Next densification: a 502 whose local lot-stamps fixture is stale (`want` stamp 1 first vs a second file still on nightloach-first), or a reviewer asking to keep SingleStack IPv4 "so mill kiln nodes without IPv6 do not get a second VIP".

Novel coverage: 41%
"""
