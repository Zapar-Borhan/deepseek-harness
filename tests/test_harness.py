import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from harness import build_payload, extract_text, load_cases


class HarnessTests(unittest.TestCase):
    def test_build_payload_includes_system_message_first(self):
        payload = build_payload("hello", system="be concise", model="deepseek-chat")
        self.assertEqual(payload["messages"][0], {"role": "system", "content": "be concise"})
        self.assertEqual(payload["messages"][1], {"role": "user", "content": "hello"})

    def test_load_cases_supports_comments_and_defaults_ids(self):
        path = Path(__file__).with_name(".test-cases.jsonl")
        try:
            path.write_text(
                '# ignored\n{"input":"one"}\n{"id":"two","input":"two"}\n',
                encoding="utf-8",
            )
            cases = load_cases(path)
        finally:
            path.unlink(missing_ok=True)
        self.assertEqual([case["id"] for case in cases], ["case-1", "two"])

    def test_extract_text_reads_chat_completion(self):
        response = {"choices": [{"message": {"content": "answer"}}]}
        self.assertEqual(extract_text(response), "answer")


if __name__ == "__main__":
    unittest.main()



