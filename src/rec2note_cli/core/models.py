from typing import List

from pydantic import BaseModel


class VisualAidTimestamp(BaseModel):
    """A moment in the transcript where a visual aid is likely needed."""

    timestamp: str
    reason: str

    def to_dict(self) -> dict:
        return self.model_dump()


class LectureTopic(BaseModel):
    """A topic or section covered in the lecture."""

    topic: str
    details: str

    def to_dict(self) -> dict:
        return self.model_dump()


class KeyTerm(BaseModel):
    """A key term or concept introduced in the lecture."""

    term: str
    definition: str

    def to_dict(self) -> dict:
        return self.model_dump()


class LectureSummary(BaseModel):
    """Structured summary of a lecture transcript."""

    title: str
    overview: str
    key_points: List[str]
    topics: List[LectureTopic]
    key_terms: List[KeyTerm]

    def to_dict(self) -> dict:
        return self.model_dump(mode="json")  # Or just self.model_dump()


class Deadline(BaseModel):
    """A deadline or deliverable mentioned in the lecture."""

    timestamp: str
    description: str
    due_date: str | None
    type: str

    def to_dict(self) -> dict:
        return self.model_dump()


class StudyQuestion(BaseModel):
    """A study question generated from the lecture content."""

    question: str
    type: str
    answer: str
    timestamp_reference: str

    def to_dict(self) -> dict:
        return self.model_dump()


class StudentQA(BaseModel):
    """A genuine student question and the lecturer's answer."""

    question_timestamp: str
    question: str
    answer_timestamp: str
    answer: str

    def to_dict(self) -> dict:
        return self.model_dump()


class LectureNoteResult(BaseModel):
    """Aggregate of all agent outputs for one processed lecture."""

    name: str
    media_path: str
    transcription_path: str | None
    summary: LectureSummary
    deadlines: list[Deadline]
    study_questions: list[StudyQuestion]
    student_qa: list[StudentQA]
    visual_aids: list[VisualAidTimestamp]
