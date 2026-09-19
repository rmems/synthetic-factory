"""Model-output JSON fences preserve payloads and handle unclosed long inputs."""

import unittest

from pipelines.model_channel import generate


class JsonFences(unittest.TestCase):
    def test_fenced_and_unfenced_objects_have_the_same_payload(self):
        for text in ('{"ok": true}', '```json\n{"ok": true}\n```',
                     'prefix```JSON  {"ok": true} ```suffix',
                     '``` {"ok": true} ```', '```json{"ok": true}```'):
            with self.subTest(text=text):
                self.assertEqual(generate._extract_json_object(text), {"ok": True})

    def test_an_unclosed_fence_with_long_whitespace_is_refused(self):
        content = '```json' + ' ' * 100_000 + 'x'
        with self.assertRaises(generate.GenerateError):
            generate._extract_json_object(content)
