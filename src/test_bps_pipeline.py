# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026  Nestor Wheelock.  Licensed under the GNU GPL v3 or later.
"""Unit tests for bps_pipeline parsers.  Run:  python3 -m unittest -v"""
import unittest
import bps_pipeline as bp

CONSOLIDATE = ("306994 – BPS26-0279 – Request submitted by Michael Meehan to "
               "consolidate lots 22 and 23 located at the property at 3316 Illinois Ave., "
               "in C. B. 1528.")
SUBDIVIDE = ("306686 – BPS26-0028 – Request submitted by Starke Inc., to divide the "
             "existing lot into 6 new parcels at 2740 Ellendale Ave., in C.B 4789.")
BOUNDARY = ("306542 – BPS25-0464 – Request by Second Patch, LLC for a boundary "
            "adjustment reducing the rear of 1919 Hereford St., in C. B. 4081.")
SPECIAL_EVENT = ("306983 – BPS26-0196 – Beer Mile North American Classic will take "
                 "place on July 11 from 2 pm to 11 pm on Manchester Avenue.")

class TestClassify(unittest.TestCase):
    def test_consolidation(self):
        r = bp.classify(CONSOLIDATE)
        self.assertIsNotNone(r)
        self.assertEqual(r["item_no"], "306994")
        self.assertEqual(r["bps_no"], "BPS26-0279")
        self.assertEqual(r["type"], "consolidation")
        self.assertEqual(r["applicant"], "Michael Meehan")
        self.assertEqual(r["city_block"], "1528")
        self.assertIn("3316 Illinois Ave", r["address"])

    def test_subdivision(self):
        r = bp.classify(SUBDIVIDE)
        self.assertEqual(r["type"], "subdivision")
        self.assertEqual(r["bps_no"], "BPS26-0028")
        self.assertEqual(r["applicant"], "Starke Inc.")
        self.assertEqual(r["city_block"], "4789")

    def test_boundary_adjustment(self):
        r = bp.classify(BOUNDARY)
        self.assertEqual(r["type"], "boundary adjustment")
        self.assertEqual(r["applicant"], "Second Patch, LLC")
        self.assertEqual(r["city_block"], "4081")

    def test_non_parcel_returns_none(self):
        self.assertIsNone(bp.classify(SPECIAL_EVENT))

    def test_missing_case_number_returns_none(self):
        self.assertIsNone(bp.classify("306999 – consolidate two lots somewhere."))

class TestHelpers(unittest.TestCase):
    def test_date_from_filename(self):
        self.assertEqual(bp.date_from_filename("x/BPS-Minutes-June-9-2026-Approved.txt"),
                         "2026-06-09")
        self.assertEqual(bp.date_from_filename("BPS-Minutes-September-29-2026-Preliminary.txt"),
                         "2026-09-29")

    def test_version_from_filename(self):
        self.assertEqual(bp.version_from_filename("BPS-Minutes-June-9-2026-Approved.txt"),
                         "Approved")
        self.assertEqual(bp.version_from_filename("BPS-Minutes-Sep-29-2026-Preliminary.txt"),
                         "Preliminary")

    def test_iter_item_blocks_splits_two(self):
        text = CONSOLIDATE + "\n\n" + SUBDIVIDE
        blocks = list(bp.iter_item_blocks(text))
        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0][0], "306994")
        self.assertEqual(blocks[1][0], "306686")

    def test_tuesdays_2026_count(self):
        # 2026 has 52 Tuesdays
        self.assertEqual(sum(1 for _ in bp.tuesdays(2026)), 52)

if __name__ == "__main__":
    unittest.main(verbosity=2)
