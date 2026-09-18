"""Native record framing survives assembly; blank source lines stay non-records."""
import json
from pathlib import Path
import tempfile
import unittest
from pipelines import compose_curated, export_replay
from tests.test_parity_curation import fresh_parity_records


class ParityFraming(unittest.TestCase):
    def test_source_record_terminators_are_preserved_by_writer_and_replay(self):
        record = fresh_parity_records()[0]
        text = json.dumps(record).encode()
        for terminator in (b'\n', b'\r\n', b''):
            with self.subTest(terminator=terminator), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                relative = record['meta']['factory'] + '/fresh.jsonl'
                source = root / 'source' / relative
                source.parent.mkdir(parents=True)
                source.write_bytes(b'\n' + text + terminator)
                summary = compose_curated.compose_run(root / 'source', root / 'composed')
                self.assertEqual(summary['counts']['blank_lines'], 1)
                output = root / 'composed' / 'records' / relative
                self.assertEqual(output.read_bytes(), text + terminator)
                replay = export_replay._replay_source_lines(root / 'source', None)
                self.assertEqual(replay.expected_payloads['records/' + relative], text + terminator)
