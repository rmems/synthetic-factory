"""Teacher routing width must retain the loaded checkpoint's configuration."""

from contextlib import nullcontext
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from test_moe_router import mr, oc


class Logits:
    def tolist(self):
        return [3.0, 2.0, 1.0, 0.0]


class Inputs(dict):
    def to(self, device):
        return self


def loaded_router(top_k):
    router = mr.TransformersMoERouter("test/moe", top_k=top_k)
    router._fingerprint = {"num_experts_per_tok": 2, "num_local_experts": 4}
    router._tokenizer = lambda *args, **kwargs: Inputs()
    router._model = lambda **kwargs: SimpleNamespace(router_logits=[[Logits()]])
    return router


class TeacherTopK(unittest.TestCase):
    def test_incompatible_override_is_refused(self):
        for top_k in (1, 3, 0, True):
            router = loaded_router(top_k)
            with self.subTest(top_k=top_k), patch.dict("sys.modules", {"torch": SimpleNamespace(no_grad=nullcontext)}):
                with self.assertRaises(oc.OracleUnavailable):
                    router.route("context")

    def test_default_and_matching_override_keep_fingerprint_width(self):
        for top_k in (None, 2):
            router = loaded_router(top_k)
            with self.subTest(top_k=top_k), patch.dict("sys.modules", {"torch": SimpleNamespace(no_grad=nullcontext)}):
                result = router.route("context")
            self.assertEqual(len(result.layers[0].top_k_experts), 2)
            self.assertEqual(router.fingerprint()["num_experts_per_tok"], 2)
