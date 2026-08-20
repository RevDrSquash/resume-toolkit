import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "lint_resume.py"
SPEC = importlib.util.spec_from_file_location("lint_resume", MODULE_PATH)
lint_resume = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(lint_resume)


class JdPhraseEchoTests(unittest.TestCase):
    def test_does_not_match_across_resume_lines(self):
        resume = (
            "Built scalable distributed systems\n"
            "Using Python across production services"
        )
        jd = "Built scalable distributed systems using Python across production services."

        self.assertEqual(lint_resume.lint_jd_phrase_echo(resume, jd), [])

    def test_does_not_match_across_jd_lines(self):
        resume = (
            "Built scalable distributed systems using Python across "
            "production services"
        )
        jd = (
            "Built scalable distributed systems\n"
            "Using Python across production services"
        )

        self.assertEqual(lint_resume.lint_jd_phrase_echo(resume, jd), [])

    def test_matches_within_one_logical_line(self):
        phrase = (
            "Built scalable distributed systems using Python across "
            "production services"
        )

        findings = lint_resume.lint_jd_phrase_echo(phrase, phrase)

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].line_number, 1)
        self.assertEqual(findings[0].rule.name, "jd-phrase-echo")

    def test_markdown_skills_mask_preserves_following_line_numbers(self):
        raw = (
            "# Summary\n"
            "Original summary\n"
            "\n"
            "## Skills\n"
            "Python, Kubernetes, AWS\n"
            "\n"
            "## Experience\n"
            "Built systems that process ten million events every day\n"
        )
        body = lint_resume._body_text_excluding_skills(raw, ".md", raw)

        findings = lint_resume.lint_jd_phrase_echo(
            body,
            "Built systems that process ten million events every day",
        )

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].line_number, 8)
        self.assertNotIn("Python", body)
        self.assertEqual(body.count("\n"), raw.count("\n"))

    def test_html_skills_mask_preserves_visible_line_numbers(self):
        raw = """
<section><h2>Summary</h2><p>Original summary</p></section>
<section><h2>Skills</h2><p>Python, Kubernetes, AWS</p></section>
<section><h2>Experience</h2>
<ul><li>Built systems that process ten million events every day</li></ul>
</section>
"""
        full_text = lint_resume.html_to_text(raw)
        body = lint_resume._body_text_excluding_skills(raw, ".html", full_text)
        expected_line = full_text.splitlines().index(
            "Built systems that process ten million events every day"
        ) + 1

        findings = lint_resume.lint_jd_phrase_echo(
            body,
            "Built systems that process ten million events every day",
        )

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].line_number, expected_line)
        self.assertNotIn("Python", body)
        self.assertEqual(body.count("\n"), full_text.count("\n"))


if __name__ == "__main__":
    unittest.main()
