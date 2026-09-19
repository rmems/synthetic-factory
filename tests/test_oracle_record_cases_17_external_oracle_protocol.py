"""Focused cases split from test_oracle_grounded_record.py."""

from test_oracle_grounded_record import (
    Path,
    REPO,
    canon,
    double_env,
    mock,
    oracles,
    shutil,
    sys,
    tempfile,
    textwrap,
    threading,
    time,
    unittest,
)


class ExternalOracleProtocolCase17(unittest.TestCase):
    def test_canonical_availability_is_independent_of_host_path(self):
        with mock.patch.object(oracles.shutil, "which", return_value="/host/a"):
            on_path = oracles.availability_report(("axon-encoder",), environ={})
        with mock.patch.object(oracles.shutil, "which", return_value=None):
            absent = oracles.availability_report(("axon-encoder",), environ={})
        self.assertEqual(on_path, absent)
        self.assertEqual(
            sorted(on_path["runtimes"][0]),
            ["binding_env", "bound", "runtime"],
        )


class ExternalOracleProtocolCase18(unittest.TestCase):
    def test_an_empty_measurement_from_any_oracle_is_refused(self):
        with self.assertRaises(oracles.OracleError):
            oracles.OracleRun({}, {}, [])
        with self.assertRaises(oracles.OracleError):
            oracles.OracleRun({"a": 1}, None, [])
        with self.assertRaises(oracles.OracleError):
            oracles.OracleRun({"a": 1}, {}, [{"stage": "f"}])


class ExternalOracleProtocolCase19(unittest.TestCase):
    def test_nonfinite_reference_output_is_also_an_oracle_error(self):
        value = float("inf")
        with self.assertRaises(oracles.OracleError):
            oracles.OracleRun({"value": value}, {"value": "unit"}, [{"stage": "f"}])


class ExternalOracleProtocolCase20(unittest.TestCase):
    def adapter(self, mode="ok"):
        return oracles.bind(
            runtime="axon-encoder",
            identity=oracles.OracleIdentity(
                oracle_id="encoder-ref",
                oracle_type="spike-encoder",
                description="reference",
            ),
            reference_fn=lambda request: ({"unused": True}, {}),
            environ=double_env(mode),
        )
    def test_nonfinite_external_request_is_bounded_as_an_oracle_error(self):
        adapter = self.adapter("ok")
        request = {"configuration": {"overflow": float("inf")}, "data": {}}
        with self.assertRaises(oracles.OracleError):
            adapter.run("f", request)


class ExternalOracleProtocolCase21(unittest.TestCase):
    def test_inherited_pipe_holders_are_bound_by_the_oracle_deadline(self):
        holder = textwrap.dedent(
            """\
            import json, os, sys, time
            if os.fork() == 0:
                os.setsid()
                time.sleep(30)
                os._exit(0)
            sys.stdout.write(json.dumps({
                "protocol": "sf-oracle/1",
                "runtime_version": "0.0.0-double",
                "runtime_commit": "a" * 40,
                "measured": {"ok": True},
                "units": {"ok": "unit"},
            }))
            sys.stdout.flush()
            """
        )
        adapter = oracles.ExternalCommandOracle(
            oracles.OracleIdentity(
                oracle_id="axon-encoder",
                oracle_type="spike-encoder",
                description="pipe-holder",
            ),
            runtime="axon-encoder",
            command=[sys.executable, "-c", holder],
            timeout_s=0.2,
        )
        started = time.monotonic()
        with self.assertRaises(oracles.OracleError) as raised:
            adapter.run("f", {"configuration": {}, "data": {}})
        self.assertLess(time.monotonic() - started, 2.0)
        self.assertIn("timed out", str(raised.exception))
        hung = [
            thread.name
            for thread in threading.enumerate()
            if thread.name.startswith("sf-oracle-axon-encoder-") and thread.is_alive()
        ]
        self.assertEqual(hung, [])


class OracleProvenanceCase01(unittest.TestCase):
    def test_the_module_digest_pins_the_implementation_sources(self):
        here = REPO / "pipelines" / "oracle_grounded"
        expected = canon.digest_files(str(here / name) for name in oracles.IMPLEMENTATION_SOURCES)
        self.assertEqual(oracles.module_digest(), expected)
        self.assertTrue(canon.is_digest(oracles.module_digest()))


class OracleProvenanceCase02(unittest.TestCase):
    def test_file_digests_are_independent_of_checkout_path(self):
        here = REPO / "pipelines" / "oracle_grounded"
        original = [here / name for name in oracles.IMPLEMENTATION_SOURCES]
        with tempfile.TemporaryDirectory(prefix="oracle-digest-") as temp:
            copied = []
            for source in original:
                destination = Path(temp) / source.name
                shutil.copy2(source, destination)
                copied.append(destination)
            self.assertEqual(canon.digest_files(original), canon.digest_files(copied))


class OracleProvenanceCase03(unittest.TestCase):
    def test_resolve_commit_returns_a_pair(self):
        commit, dirty = oracles.resolve_commit()
        self.assertIsInstance(commit, str)
        self.assertTrue(commit)
        self.assertIn(type(dirty), (bool, type(None)))

