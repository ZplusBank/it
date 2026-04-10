import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "builder"
if str(BUILDER) not in sys.path:
    sys.path.insert(0, str(BUILDER))

from diagram_support import extract_fenced_blocks, resolve_engine, validate_diagram_blocks


class DiagramSupportTests(unittest.TestCase):
    def test_extract_fenced_blocks(self):
        src = """Header\n```mermaid\nflowchart LR\nA-->B\n```\n```dot\ndigraph G { A -> B; }\n```"""
        blocks = extract_fenced_blocks(src)
        self.assertEqual(2, len(blocks))
        self.assertEqual("mermaid", blocks[0]["lang"])
        self.assertEqual("dot", blocks[1]["lang"])

    def test_resolve_engine_aliases(self):
        self.assertEqual("mermaid", resolve_engine("network", ""))
        self.assertEqual("graphviz", resolve_engine("dot", ""))
        self.assertEqual("nomnoml", resolve_engine("uml", ""))

    def test_resolve_engine_from_code_shape(self):
        self.assertEqual("graphviz", resolve_engine("", "digraph G { A -> B; }"))
        self.assertEqual("mermaid", resolve_engine("", "flowchart LR\nA-->B"))
        self.assertEqual("nomnoml", resolve_engine("", "[User]-[Order]"))

    def test_subject_fallback_for_generic_diagram(self):
        self.assertEqual("mermaid", resolve_engine("diagram", "", "Network"))
        self.assertEqual("nomnoml", resolve_engine("diagram", "", "Uml"))

    def test_validate_warnings_for_unknown_or_empty(self):
        src = """```unknownlang\nabc\n```\n```mermaid\n\n```"""
        warnings = validate_diagram_blocks(src, subject_id="Network")
        self.assertEqual(2, len(warnings))
        self.assertTrue(any("Unknown diagram language" in w["message"] for w in warnings))
        self.assertTrue(any("empty" in w["message"].lower() for w in warnings))


if __name__ == "__main__":
    unittest.main()
