from rec2note_cli.core.models import (
    Deadline,
    LectureSummary,
    StudentQA,
    StudyQuestion,
)


def build_markdown(
    note_name: str,
    summary: LectureSummary,
    student_qa: list[StudentQA] = [],
    deadline: list[Deadline] = [],
    study_qs: list[StudyQuestion] = [],
):
    """
    Build markdown from lecture note result
    """
    markdown = f"# {note_name} - {summary.title}\n\n"

    # Summary
    markdown += "## Summary\n\n"
    markdown += f"### Overview\n > [!NOTE] Overview\n > {summary.overview}\n\n"
    markdown += "### Key Points\n"
    for key_point in summary.key_points:
        markdown += f"- {key_point}\n"
    markdown += "### Topics\n"
    for topic in summary.topics:
        markdown += f"- **{topic.topic}** {topic.details}\n"
    markdown += "### Key Terms\n"
    for key_term in summary.key_terms:
        markdown += f"- **{key_term.term}** {key_term.definition}\n"

    # Student Questions
    if student_qa:
        markdown += "## Student Questions\n"
        for question in student_qa:
            markdown += f"> Q: ({question.question_timestamp}) {question.question}\n"
            markdown += f"- A: {question.answer}\n\n"
    # Deadline
    if deadline:
        markdown += "## Deadline\n"
        for deadline_item in deadline:
            markdown += f"- ({deadline_item.timestamp}) [{deadline_item.type}] {deadline_item.description} ({deadline_item.due_date if deadline_item.due_date else 'N/A'})\n"

    # Study Questions
    if study_qs:
        markdown += "## Study Questions\n\n"
        for study_question in study_qs:
            markdown += f"> Q: ({study_question.timestamp_reference}) [{study_question.type}] {study_question.question}\n"
            markdown += f"- A: {study_question.answer}\n\n"

    return markdown


if __name__ == "__main__":
    pass
