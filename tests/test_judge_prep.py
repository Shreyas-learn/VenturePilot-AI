import unittest

from frontend.judge_prep import build_judge_prep


class JudgePrepTests(unittest.TestCase):
    def test_uses_report_text_as_talking_points(self):
        questions = build_judge_prep(
            {"Problem Statement": "Clinics lose time coordinating patient follow-up."}
        )

        self.assertEqual(len(questions), 5)
        self.assertEqual(
            questions[0].talking_points,
            (("Problem Statement", "Clinics lose time coordinating patient follow-up."),),
        )
        self.assertIn("Target Customers", questions[0].missing_sections)

    def test_truncates_long_report_sections(self):
        questions = build_judge_prep({"Revenue Model": "revenue " * 150})

        excerpt = questions[2].talking_points[0][1]
        self.assertLessEqual(len(excerpt), 420)
        self.assertTrue(excerpt.endswith("..."))


if __name__ == "__main__":
    unittest.main()