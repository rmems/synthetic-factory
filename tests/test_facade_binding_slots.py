"""The per-module facade slot keeps the old ``global _FACADE`` behaviour.

``compose_curated_identity_facade_binding`` and ``compose_curated_record_facade``
each hold the live ``compose_curated`` facade in a one-entry ``_BINDING`` dict
instead of rebinding a module global. These cases pin, for both modules, the
algorithm the global version ran: ask ``pipelines._canonical_sibling_binding``
(when the package is loaded) to resolve the bound value, cache its answer, and
refuse an unbound slot with the same message.
"""

import contextlib
import sys
import types
import unittest
from unittest import mock

from pipelines import compose_curated
from pipelines import compose_curated_identity_facade_binding as identity_binding
from pipelines import compose_curated_record_facade as record_binding


def binding_api(label, module):
    """(label, slot, bind_facade, _facade) for one binding module."""

    namespace = vars(module)
    return label, namespace["_BINDING"], module.bind_facade, namespace["_facade"]


BINDINGS = (binding_api("identity", identity_binding), binding_api("record", record_binding))
UNBOUND = "^compose_curated facade is not bound$"


def main_semantics(bound, resolver):
    """The global-_FACADE algorithm from main, restated without module state."""

    if resolver is not None:
        bound = resolver("compose_curated", bound)
    if bound is None:
        raise RuntimeError("compose_curated facade is not bound")
    return bound


def package_stub(resolver=None):
    """A stand-in ``pipelines`` package with or without the sibling resolver."""

    if resolver is None:
        return types.SimpleNamespace()
    return types.SimpleNamespace(_canonical_sibling_binding=resolver)


def recording_resolver(calls, answer=None, keep_bound=False):
    """A resolver that logs each call and answers ``answer`` (or the bound value)."""

    def resolve(name, bound):
        calls.append((name, bound))
        return bound if keep_bound else answer

    return resolve


def global_version_scenarios():
    """(label, bound value, resolver) cases covering every path of the lookup."""

    bound = types.ModuleType("bound")
    calls = []
    keeps = recording_resolver(calls, keep_bound=True)
    replaces = recording_resolver(calls, answer=types.ModuleType("replacement"))
    drops = recording_resolver(calls, answer=None)
    return (
        ("unbound, no resolver", None, None),
        ("bound, no resolver", bound, None),
        ("unbound, resolver keeps it", None, keeps),
        ("bound, resolver keeps it", bound, keeps),
        ("unbound, resolver replaces it", None, replaces),
        ("bound, resolver replaces it", bound, replaces),
        ("bound, resolver drops it", bound, drops),
    )


class FacadeBindingSlot(unittest.TestCase):
    """Both binding modules resolve, cache and refuse exactly as the global did."""

    @contextlib.contextmanager
    def isolated(self, slot, resolver=None):
        """Start from an empty slot under a stub package; both are restored on exit."""

        self.assertEqual(set(slot), {"facade"})
        stub = {"pipelines": package_stub(resolver)}
        with mock.patch.dict(sys.modules, stub), mock.patch.dict(slot, {"facade": None}):
            yield slot

    def outcome(self, call, *args):
        """``("value", module)`` or ``("error", message)`` for one facade lookup."""

        try:
            value = call(*args)
        except RuntimeError as error:
            return "error", str(error)
        self.assertIsInstance(value, types.ModuleType)
        return "value", value

    def test_an_unbound_slot_refuses_without_a_resolver(self):
        for label, slot, _bind, facade in BINDINGS:
            with self.subTest(module=label), self.isolated(slot):
                with self.assertRaisesRegex(RuntimeError, UNBOUND):
                    facade()
                self.assertIsNone(slot["facade"])

    def test_a_bound_facade_is_returned_and_reused_without_a_resolver(self):
        for label, slot, bind, facade in BINDINGS:
            sentinel = types.ModuleType(f"{label}_facade_sentinel")
            with self.subTest(module=label), self.isolated(slot):
                bind(sentinel)
                self.assertIs(facade(), sentinel)
                self.assertIs(facade(), sentinel)
                self.assertIs(slot["facade"], sentinel)

    def test_the_resolver_sees_the_cached_value_and_its_answer_is_kept(self):
        for label, slot, bind, facade in BINDINGS:
            stale = types.ModuleType(f"{label}_stale")
            canonical = types.ModuleType(f"{label}_canonical")
            calls = []
            resolver = recording_resolver(calls, answer=canonical)
            with self.subTest(module=label), self.isolated(slot, resolver):
                bind(stale)
                self.assertIs(facade(), canonical)
                self.assertIs(slot["facade"], canonical)
                self.assertIs(facade(), canonical)
                self.assertEqual(
                    calls, [("compose_curated", stale), ("compose_curated", canonical)]
                )

    def test_a_resolver_that_keeps_an_unbound_slot_still_refuses(self):
        for label, slot, _bind, facade in BINDINGS:
            calls = []
            resolver = recording_resolver(calls, keep_bound=True)
            with self.subTest(module=label), self.isolated(slot, resolver):
                with self.assertRaisesRegex(RuntimeError, UNBOUND):
                    facade()
                self.assertEqual(calls, [("compose_curated", None)])

    def test_every_scenario_matches_the_global_version(self):
        for label, slot, _bind, facade in BINDINGS:
            for scenario, bound, resolver in global_version_scenarios():
                with self.subTest(module=label, scenario=scenario), self.isolated(slot, resolver):
                    slot["facade"] = bound
                    expected = self.outcome(main_semantics, bound, resolver)
                    self.assertEqual(self.outcome(facade), expected)

    def test_each_module_keeps_its_own_slot(self):
        identity_api, record_api = BINDINGS
        _, identity_slot, bind_identity, identity = identity_api
        _, record_slot, bind_record, record = record_api
        self.assertIsNot(identity_slot, record_slot)
        first = types.ModuleType("first")
        second = types.ModuleType("second")
        with self.isolated(identity_slot), self.isolated(record_slot):
            bind_identity(first)
            bind_record(second)
            self.assertIs(identity(), first)
            self.assertIs(record(), second)

    def test_the_live_slots_resolve_to_the_imported_compose_facade(self):
        for label, _slot, _bind, facade in BINDINGS:
            with self.subTest(module=label):
                self.assertIs(facade(), compose_curated)


if __name__ == "__main__":
    unittest.main()
