from unittest.mock import MagicMock

import pytest

from rec2note_cli.core.models import (
    Deadline,
    KeyTerm,
    LectureSummary,
    LectureTopic,
    StudentQA,
    StudyQuestion,
)
from rec2note_cli.utils.markdown_builder import build_markdown

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_summary() -> LectureSummary:
    return LectureSummary(
        title="Introduction to Neural Networks",
        overview="This lecture introduces the fundamentals of neural networks.",
        key_points=[
            "Neurons are the basic building blocks",
            "Activation functions introduce non-linearity",
            "Backpropagation is used for training",
        ],
        topics=[
            LectureTopic(topic="Perceptrons", details="Single-layer linear classifier"),
            LectureTopic(
                topic="Backpropagation",
                details="Gradient-based weight update algorithm",
            ),
        ],
        key_terms=[
            KeyTerm(
                term="Neuron", definition="A computational unit in a neural network"
            ),
            KeyTerm(term="Gradient Descent", definition="An optimisation algorithm"),
        ],
    )


@pytest.fixture
def mock_student_qa() -> list[StudentQA]:
    return [
        StudentQA(
            question_timestamp="00:12:30",
            question="What is the difference between supervised and unsupervised learning?",
            answer_timestamp="00:12:55",
            answer="Supervised learning uses labelled data; unsupervised does not.",
        ),
        StudentQA(
            question_timestamp="00:25:10",
            question="Can neural networks overfit?",
            answer_timestamp="00:25:40",
            answer="Yes, regularisation techniques such as dropout help prevent this.",
        ),
    ]


@pytest.fixture
def mock_deadlines() -> list[Deadline]:
    return [
        Deadline(
            timestamp="00:45:00",
            description="Assignment 1 – Implement a perceptron",
            due_date="2024-11-15",
            type="Assignment",
        ),
        Deadline(
            timestamp="00:47:20",
            description="Midterm exam",
            due_date=None,
            type="Exam",
        ),
    ]


@pytest.fixture
def mock_study_questions() -> list[StudyQuestion]:
    return [
        StudyQuestion(
            question="Explain the role of activation functions.",
            type="Conceptual",
            answer="They introduce non-linearity, enabling the network to learn complex patterns.",
            timestamp_reference="00:18:00",
        ),
        StudyQuestion(
            question="Describe the steps of the backpropagation algorithm.",
            type="Procedural",
            answer="Forward pass, compute loss, backward pass, update weights.",
            timestamp_reference="00:33:00",
        ),
    ]


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _build_full(
    mock_summary, mock_student_qa, mock_deadlines, mock_study_questions
) -> str:
    return build_markdown(
        note_name="Lecture 01",
        summary=mock_summary,
        student_qa=mock_student_qa,
        deadline=mock_deadlines,
        study_qs=mock_study_questions,
    )


# ---------------------------------------------------------------------------
# Title & Summary section
# ---------------------------------------------------------------------------


class TestTitleAndSummary:
    def test_title_contains_note_name_and_lecture_title(self, mock_summary):
        result = build_markdown("Lecture 01", mock_summary)
        assert "# Lecture 01 - Introduction to Neural Networks" in result

    def test_summary_heading_present(self, mock_summary):
        result = build_markdown("Lecture 01", mock_summary)
        assert "## Summary" in result

    def test_overview_heading_and_content(self, mock_summary):
        result = build_markdown("Lecture 01", mock_summary)
        assert "### Overview" in result
        assert "fundamentals of neural networks" in result

    def test_key_points_heading_present(self, mock_summary):
        result = build_markdown("Lecture 01", mock_summary)
        assert "### Key Points" in result

    def test_all_key_points_rendered(self, mock_summary):
        result = build_markdown("Lecture 01", mock_summary)
        for point in mock_summary.key_points:
            assert f"- {point}" in result

    def test_topics_heading_present(self, mock_summary):
        result = build_markdown("Lecture 01", mock_summary)
        assert "### Topics" in result

    def test_all_topics_rendered(self, mock_summary):
        result = build_markdown("Lecture 01", mock_summary)
        for topic in mock_summary.topics:
            assert topic.topic in result

    def test_key_terms_heading_present(self, mock_summary):
        result = build_markdown("Lecture 01", mock_summary)
        assert "### Key Terms" in result

    def test_all_key_terms_rendered(self, mock_summary):
        result = build_markdown("Lecture 01", mock_summary)
        for key_term in mock_summary.key_terms:
            assert key_term.term in result

    def test_different_note_name_reflected_in_title(self, mock_summary):
        result = build_markdown("CS301 Week 3", mock_summary)
        assert "# CS301 Week 3 - Introduction to Neural Networks" in result


# ---------------------------------------------------------------------------
# Student Questions section
# ---------------------------------------------------------------------------


class TestStudentQA:
    def test_student_questions_section_present_when_provided(
        self, mock_summary, mock_student_qa
    ):
        result = build_markdown("Lecture 01", mock_summary, student_qa=mock_student_qa)
        assert "## Student Questions" in result

    def test_student_questions_section_absent_when_empty(self, mock_summary):
        result = build_markdown("Lecture 01", mock_summary, student_qa=[])
        assert "## Student Questions" not in result

    def test_all_questions_rendered(self, mock_summary, mock_student_qa):
        result = build_markdown("Lecture 01", mock_summary, student_qa=mock_student_qa)
        for qa in mock_student_qa:
            assert qa.question in result

    def test_all_answers_rendered(self, mock_summary, mock_student_qa):
        result = build_markdown("Lecture 01", mock_summary, student_qa=mock_student_qa)
        for qa in mock_student_qa:
            assert qa.answer in result

    def test_question_answer_format(self, mock_summary, mock_student_qa):
        result = build_markdown("Lecture 01", mock_summary, student_qa=mock_student_qa)
        assert "- Q:" in result
        assert "- A:" in result


# ---------------------------------------------------------------------------
# Deadline section
# ---------------------------------------------------------------------------


class TestDeadline:
    def test_deadline_section_present_when_provided(self, mock_summary, mock_deadlines):
        result = build_markdown("Lecture 01", mock_summary, deadline=mock_deadlines)
        assert "## Deadline" in result

    def test_deadline_section_absent_when_empty(self, mock_summary):
        result = build_markdown("Lecture 01", mock_summary, deadline=[])
        assert "## Deadline" not in result

    def test_deadline_with_due_date_rendered(self, mock_summary, mock_deadlines):
        result = build_markdown("Lecture 01", mock_summary, deadline=mock_deadlines)
        assert "2024-11-15" in result

    def test_deadline_without_due_date_shows_na(self, mock_summary, mock_deadlines):
        result = build_markdown("Lecture 01", mock_summary, deadline=mock_deadlines)
        assert "N/A" in result

    def test_deadline_type_and_description_rendered(self, mock_summary, mock_deadlines):
        result = build_markdown("Lecture 01", mock_summary, deadline=mock_deadlines)
        for item in mock_deadlines:
            assert item.type in result
            assert item.description in result

    def test_deadline_timestamp_rendered(self, mock_summary, mock_deadlines):
        result = build_markdown("Lecture 01", mock_summary, deadline=mock_deadlines)
        for item in mock_deadlines:
            assert item.timestamp in result


# ---------------------------------------------------------------------------
# Study Questions section
# ---------------------------------------------------------------------------


class TestStudyQuestions:
    def test_study_questions_section_present_when_provided(
        self, mock_summary, mock_study_questions
    ):
        result = build_markdown(
            "Lecture 01", mock_summary, study_qs=mock_study_questions
        )
        assert "## Study Questions" in result

    def test_study_questions_section_absent_when_empty(self, mock_summary):
        result = build_markdown("Lecture 01", mock_summary, study_qs=[])
        assert "## Study Questions" not in result

    def test_all_study_questions_rendered(self, mock_summary, mock_study_questions):
        result = build_markdown(
            "Lecture 01", mock_summary, study_qs=mock_study_questions
        )
        for sq in mock_study_questions:
            assert sq.question in result

    def test_all_study_answers_rendered(self, mock_summary, mock_study_questions):
        result = build_markdown(
            "Lecture 01", mock_summary, study_qs=mock_study_questions
        )
        for sq in mock_study_questions:
            assert sq.answer in result

    def test_study_question_type_and_timestamp_rendered(
        self, mock_summary, mock_study_questions
    ):
        result = build_markdown(
            "Lecture 01", mock_summary, study_qs=mock_study_questions
        )
        for sq in mock_study_questions:
            assert sq.type in result
            assert sq.timestamp_reference in result


# ---------------------------------------------------------------------------
# Full output / integration-style
# ---------------------------------------------------------------------------


class TestFullOutput:
    def test_full_markdown_returns_string(
        self, mock_summary, mock_student_qa, mock_deadlines, mock_study_questions
    ):
        result = _build_full(
            mock_summary, mock_student_qa, mock_deadlines, mock_study_questions
        )
        assert isinstance(result, str)

    def test_full_markdown_section_order(
        self, mock_summary, mock_student_qa, mock_deadlines, mock_study_questions
    ):
        result = _build_full(
            mock_summary, mock_student_qa, mock_deadlines, mock_study_questions
        )
        summary_pos = result.index("## Summary")
        student_qa_pos = result.index("## Student Questions")
        deadline_pos = result.index("## Deadline")
        study_qs_pos = result.index("## Study Questions")

        assert summary_pos < student_qa_pos < deadline_pos < study_qs_pos

    def test_empty_optional_sections_omitted(self, mock_summary):
        result = build_markdown("Lecture 01", mock_summary)
        assert "## Student Questions" not in result
        assert "## Deadline" not in result
        assert "## Study Questions" not in result

    def test_mock_summary_object_attributes_are_called(self):
        """Verify the builder reads the expected attributes via a MagicMock."""
        mock = MagicMock(spec=LectureSummary)
        mock.title = "Mocked Title"
        mock.overview = "Mocked overview text."
        mock.key_points = ["Point A"]
        mock.topics = [MagicMock(topic="Topic A", details="Details A")]
        mock.key_terms = [MagicMock(term="Term A", definition="Definition A")]

        result = build_markdown("Mock Lecture", mock)

        assert "Mocked Title" in result
        assert "Mocked overview text." in result
        assert "Point A" in result
        # Note: build_markdown renders topics/key_terms via str(obj), not .topic/.term,
        # so MagicMock stringification won't expose the field values here.
        # Topic and key-term field access is covered by TestTitleAndSummary with real models.
