"""Tests for the question checks. They don't need Ollama running.

Run from the repo root:  python3 -m unittest discover generator
"""

import unittest

from generate_questions import built_in_questions, is_duplicate, validate


def make(**overrides):
    raw = {
        "question": "What should you do if a chatbot gives you a surprising fact?",
        "correct_answer": "Check it with a trusted source",
        "wrong_answers": ["Believe it straight away", "Share it with everyone", "Print it out", "Ignore the internet"],
        "explanation": "Chatbots can sound confident even when they are wrong, so check important facts.",
    }
    raw.update(overrides)
    return raw


class ValidateTests(unittest.TestCase):
    def test_good_question_becomes_quiz_item_with_answer_in_options(self):
        item = validate(make(), [])
        self.assertEqual(len(item["options"]), 5)
        self.assertIn(item["answer"], item["options"])

    def test_rejects_wrong_number_of_answers(self):
        with self.assertRaisesRegex(ValueError, "expected 4"):
            validate(make(wrong_answers=["a1", "b2", "c3"]), [])

    def test_rejects_duplicate_options(self):
        with self.assertRaisesRegex(ValueError, "not all different"):
            validate(make(wrong_answers=["Check it with a trusted source!", "Print it", "Share it", "Ignore it"]), [])

    def test_rejects_all_of_the_above(self):
        with self.assertRaisesRegex(ValueError, "banned"):
            validate(make(wrong_answers=["All of the above", "Print it", "Share it", "Ignore it"]), [])

    def test_rejects_question_without_question_mark(self):
        with self.assertRaisesRegex(ValueError, "'\\?'"):
            validate(make(question="Pick the safest thing to do with a chatbot fact"), [])

    def test_rejects_near_duplicate_question(self):
        existing = ["What should you do if a chatbot gives you a surprising fact?"]
        with self.assertRaisesRegex(ValueError, "too similar"):
            validate(make(question="What should you do if a chatbot gives you a surprising fact??"), existing)

    def test_rejects_explanation_that_just_names_the_answer(self):
        with self.assertRaisesRegex(ValueError, "correct answer"):
            validate(make(explanation="The correct answer is to check it with a trusted source."), [])

    def test_rejects_missing_explanation(self):
        with self.assertRaisesRegex(ValueError, "explanation"):
            validate(make(explanation=""), [])


class HelperTests(unittest.TestCase):
    def test_is_duplicate_ignores_case_and_punctuation(self):
        self.assertTrue(is_duplicate("WHAT is AI?", ["what is ai"]))
        self.assertFalse(is_duplicate("Where do you meet AI every day?", ["What is a deepfake video?"]))

    def test_reads_the_five_built_in_questions_from_script_js(self):
        self.assertEqual(len(built_in_questions()), 5)


if __name__ == "__main__":
    unittest.main()
