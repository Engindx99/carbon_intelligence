"""Every copy of the plant's geometry is the one source's.

geometry/plant_geometry.yaml holds each dimension once (single-source
rule, user decision 13-14 Oct 2026). The SolidWorks macros hold copies
in generated Const blocks, the equipment documents in generated
tables (tools/gen_geometry.py); none may be stale or
edited by hand, and none of the generated names may be written again
outside its block.
"""

import re
import unittest

from geometry import plant_geometry as pg
from tests.twin_harness import REPO_ROOT
from tools import gen_geometry as gen


class TheGeneratedBlocksAreCurrentTest(unittest.TestCase):

    def test_no_block_is_stale(self):
        """python3 tools/gen_geometry.py --check"""
        self.assertEqual(gen.run(check=True), [])

    def test_a_generated_name_is_written_only_in_its_block(self):
        g = pg.load()
        for name, build in gen.TARGETS.items():
            text = (gen.MACROS / name).read_text(encoding="latin-1")
            i, j = text.index(gen.BEGIN), text.index(gen.END)
            outside = text[:i] + text[j:]
            for const in build(g):
                with self.subTest(macro=name, const=const.name):
                    self.assertIsNone(
                        re.search(rf"^\s*Const\s+{const.name}\b", outside, re.M | re.I)
                    )

    def test_the_source_values_are_written_as_given(self):
        """The CFD domains are rebuilt bit for bit: what the source
        gives goes into the macros unrounded."""
        g = pg.load()
        for build in gen.TARGETS.values():
            for const in build(g):
                if const.kind == "Double" and not const.derived:
                    with self.subTest(const=const.name):
                        text = const.line().split("=", 1)[1].split("'")[0].strip()
                        self.assertEqual(float(text.rstrip("#")), float(const.value))


if __name__ == "__main__":
    unittest.main()
