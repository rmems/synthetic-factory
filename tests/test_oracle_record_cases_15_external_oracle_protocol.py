"""Focused cases split from test_oracle_grounded_record.py."""

from test_oracle_grounded_record import (
    DOUBLE,
    Path,
    REPO,
    double_env,
    json,
    oracles,
    sys,
    unittest,
)


def _bind_encoder_double(mode="ok"):
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


class ExternalOracleProtocolCase04(unittest.TestCase):
    def test_every_malformed_answer_raises_rather_than_falling_back(self):
        for mode in (
            "fail",
            "badjson",
            "wrongproto",
            "noversion",
            "empty",
            "emptyunits",
            "unknowncommit",
            "badcommit",
            "nan",
            "infinity",
            "overflow",
            "dupkey",
            "stdout_flood",
            "stderr_flood",
        ):
            with self.subTest(mode=mode):
                adapter = _bind_encoder_double(mode)
                with self.assertRaises(oracles.OracleError):
                    adapter.run("f", {"configuration": {}, "data": {}})


class ExternalOracleProtocolCase05(unittest.TestCase):
    def test_a_duplicate_key_in_a_runtime_response_is_rejected(self):
        # Python's json.loads applies last-key-wins to a duplicate key by
        # default; a bound runtime is an external process, so silently
        # picking one interpretation of an ambiguous response could stamp a
        # value into provenance that another conforming reader would not.
        adapter = _bind_encoder_double("dupkey")
        with self.assertRaises(oracles.OracleError) as ctx:
            adapter.run("f", {"configuration": {}, "data": {}})
        self.assertIn("duplicate", str(ctx.exception))


class ExternalOracleProtocolCase06(unittest.TestCase):
    def test_a_missing_command_raises(self):
        adapter = oracles.ExternalCommandOracle(
            oracles.OracleIdentity(
                oracle_id="axon-encoder",
                oracle_type="spike-encoder",
                description="missing",
            ),
            runtime="axon-encoder",
            command=[str(REPO / "definitely" / "not" / "here")],
        )
        with self.assertRaises(oracles.OracleError):
            adapter.run("f", {})


class ExternalOracleProtocolCase07(unittest.TestCase):
    def test_stage_provenance_and_errors_never_copy_full_argv(self):
        marker = "ARGUMENT-MARKER"
        adapter = oracles.ExternalCommandOracle(
            oracles.OracleIdentity(
                oracle_id="axon-encoder",
                oracle_type="spike-encoder",
                description="double",
            ),
            runtime="axon-encoder",
            command=[sys.executable, str(DOUBLE), "ok", f"--token={marker}"],
        )
        run = adapter.run("f", {"configuration": {}, "data": {}})
        stage = run.stages[0]
        self.assertNotIn("command", stage)
        self.assertEqual(stage["executable"], Path(sys.executable).name)
        self.assertNotIn(marker, json.dumps(stage))

        missing = oracles.ExternalCommandOracle(
            oracles.OracleIdentity(
                oracle_id="axon-encoder",
                oracle_type="spike-encoder",
                description="missing",
            ),
            runtime="axon-encoder",
            command=[f"/definitely/not/{marker}", f"--token={marker}"],
        )
        with self.assertRaises(oracles.OracleError) as raised:
            missing.run("f", {})
        self.assertNotIn(marker, str(raised.exception))


class ExternalOracleProtocolCase08(unittest.TestCase):
    def test_malformed_shell_binding_is_bounded_and_names_only_the_env_key(self):
        key = oracles.env_key("axon-encoder")
        marker = "UNTERMINATED-ARGUMENT-MARKER"
        identity = oracles.OracleIdentity(
            oracle_id="encoder-ref",
            oracle_type="spike-encoder",
            description="reference",
        )
        environ = {key: f'{sys.executable} "{marker}'}
        with self.assertRaises(oracles.OracleError) as raised:
            oracles.bind(
                runtime="axon-encoder",
                identity=identity,
                reference_fn=lambda request: ({"ok": True}, {"ok": "unit"}),
                environ=environ,
            )
        self.assertIn(key, str(raised.exception))
        self.assertNotIn(marker, str(raised.exception))

