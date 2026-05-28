"""Schemas for teacher assistant assessment generation endpoints."""

from pydantic import BaseModel, Field


class MCQOption(BaseModel):
    """Options for a multiple-choice question."""
    A: str = Field(..., description="Option A")
    B: str = Field(..., description="Option B")
    C: str = Field(..., description="Option C")
    D: str = Field(..., description="Option D")


class MCQQuestion(BaseModel):
    """A single multiple-choice question."""
    question_number: int = Field(..., description="Question number", examples=[1])
    question_text: str = Field(..., description="Question text")
    options: MCQOption = Field(..., description="Answer options")
    correct_answer: str = Field(..., description="Correct option letter", examples=["A"])
    difficulty: str = Field(..., description="Difficulty level", examples=["easy", "medium", "hard"])
    cognitive_level: str = Field(..., description="Cognitive level", examples=["recall", "understanding", "application"])
    explanation: str = Field(..., description="Explanation of the correct answer")


class MCQSection(BaseModel):
    """A section of multiple-choice questions."""
    section_name: str = Field(..., description="Section name", examples=["Section A - Multiple Choice Questions"])
    section_type: str = Field(default="mcq", description="Section type")
    marks_per_question: int = Field(default=1, description="Marks per question")
    total_section_marks: int = Field(default=0, description="Total marks for this section")
    instructions: str = Field(default="Choose the correct option.", description="Section instructions")
    questions: list[MCQQuestion] = Field(default_factory=list, description="List of questions")


class FillBlankQuestion(BaseModel):
    """A fill-in-the-blank question."""
    question_number: int = Field(..., description="Question number")
    question_text: str = Field(..., description="Question text with blank", examples=["The _____ is the largest organ of the human body."])
    answer: str = Field(..., description="Correct answer", examples=["skin"])


class ShortAnswerQuestion(BaseModel):
    """A short-answer question."""
    question_number: int = Field(..., description="Question number")
    question_text: str = Field(..., description="Question text")
    marks: int = Field(..., description="Marks for this question", examples=[2, 3])
    difficulty: str = Field(..., description="Difficulty level")
    cognitive_level: str = Field(..., description="Cognitive level")
    expected_key_points: list[str] = Field(default_factory=list, description="Key points for evaluation")
    model_answer: str = Field(..., description="Complete model answer")


class LongAnswerQuestion(BaseModel):
    """A long-answer question with optional sub-parts."""
    question_number: int = Field(..., description="Question number")
    question_text: str = Field(..., description="Main question text")
    sub_parts: list[dict] = Field(default_factory=list, description="Sub-parts if any")
    total_marks: int = Field(..., description="Total marks for this question", examples=[5])
    difficulty: str = Field(..., description="Difficulty level")
    cognitive_level: str = Field(..., description="Cognitive level")
    expected_key_points: list[str] = Field(default_factory=list, description="Key points for evaluation")
    model_answer: str = Field(..., description="Complete model answer")


class Question(BaseModel):
    """A generic question (for exam papers)."""
    question_number: int = Field(..., description="Question number")
    question_text: str = Field(..., description="Question text")
    options: MCQOption | None = Field(default=None, description="Options for MCQ")
    correct_answer: str | None = Field(default=None, description="Correct answer")
    marks: int = Field(default=1, description="Marks for this question")
    difficulty: str = Field(default="medium", description="Difficulty level")
    cognitive_level: str = Field(default="recall", description="Cognitive level")
    chapter: str = Field(default="", description="Chapter name")
    model_explanation: str | None = Field(default=None, description="Explanation")


class ExamSection(BaseModel):
    """A section of an exam paper."""
    section_name: str = Field(..., description="Section name")
    marks_per_question: int = Field(..., description="Marks per question")
    total_section_marks: int = Field(..., description="Total marks for this section")
    instructions: str = Field(..., description="Section instructions")
    questions: list[Question] = Field(default_factory=list, description="Questions in this section")


class AnswerKey(BaseModel):
    """Answer key for an exam."""
    section_a_answers: list[str] = Field(default_factory=list, description="MCQ answers")
    section_b_key_points: list[str] = Field(default_factory=list, description="Key points for short answers")
    section_c_model_answers: list[str] = Field(default_factory=list, description="Model answers for long answers")


class ExamBlueprint(BaseModel):
    """Exam blueprint showing marks distribution."""
    chapter_wise_marks: dict[str, int] = Field(default_factory=dict, description="Marks per chapter")
    difficulty_breakdown: dict[str, str] = Field(default_factory=dict, description="Difficulty percentage breakdown")
    cognitive_breakdown: dict[str, str] = Field(default_factory=dict, description="Cognitive level percentage breakdown")


class MCQGenerateRequest(BaseModel):
    """Request to generate MCQs."""
    grade: int = Field(..., description="CBSE class grade", examples=[6])
    subject: str = Field(..., description="Subject name", examples=["Science"])
    chapter: str = Field(..., description="Chapter name", examples=["Water"])
    topic: str = Field(..., description="Topic", examples=["Water Conservation"])
    question_count: int = Field(default=10, description="Number of questions", examples=[10])
    difficulty: str = Field(default="medium", description="Difficulty level")
    provider: str = Field(default="mock", description="LLM provider")


class ShortAnswerGenerateRequest(BaseModel):
    """Request to generate short-answer questions."""
    grade: int = Field(..., description="CBSE class grade")
    subject: str = Field(..., description="Subject name")
    chapter: str = Field(..., description="Chapter name")
    topic: str = Field(..., description="Topic")
    question_count: int = Field(default=5, description="Number of questions")
    difficulty: str = Field(default="medium")
    marks_per_question: int = Field(default=2, description="Marks per question", examples=[2, 3])
    provider: str = Field(default="mock")


class LongAnswerGenerateRequest(BaseModel):
    """Request to generate long-answer questions."""
    grade: int = Field(..., description="CBSE class grade")
    subject: str = Field(..., description="Subject name")
    chapter: str = Field(..., description="Chapter name")
    topic: str = Field(..., description="Topic")
    question_count: int = Field(default=3, description="Number of questions")
    difficulty: str = Field(default="medium")
    marks_per_question: int = Field(default=5, description="Marks per question", examples=[5])
    provider: str = Field(default="mock")


class QuestionSpecItem(BaseModel):
    """Specification for a single question type in a custom assessment."""
    type: str = Field(..., description="Question type: mcq, short_answer, or long_answer", examples=["mcq", "short_answer", "long_answer"])
    count: int = Field(..., description="Number of questions of this type", examples=[5])
    marks_per_question: int = Field(..., description="Marks per question", examples=[1, 2, 3, 5])
    difficulty: str = Field(default="medium", description="Difficulty for this section")
    cognitive_levels: list[str] | None = Field(default=None, description="Cognitive levels to cover")


class CustomAssessmentGenerateRequest(BaseModel):
    """Request to generate a custom assessment with teacher-specified question types."""
    grade: int = Field(..., description="CBSE class grade", examples=[6])
    subject: str = Field(..., description="Subject name", examples=["Science"])
    chapter: str = Field(..., description="Chapter name", examples=["Water"])
    topic: str = Field(..., description="Topic", examples=["Water Conservation"])
    question_specs: list[QuestionSpecItem] = Field(..., description="List of question type specifications")
    difficulty: str = Field(default="medium")
    provider: str = Field(default="mock")


class WorksheetGenerateRequest(BaseModel):
    """Request to generate a worksheet."""
    grade: int = Field(..., description="CBSE class grade")
    subject: str = Field(..., description="Subject name")
    chapter: str = Field(..., description="Chapter name")
    topic: str = Field(..., description="Topic")
    total_marks: int = Field(default=30, description="Total marks for the worksheet")
    difficulty: str = Field(default="medium")
    provider: str = Field(default="mock")


class ExamPaperGenerateRequest(BaseModel):
    """Request to generate an exam paper."""
    grade: int = Field(..., description="CBSE class grade")
    subject: str = Field(..., description="Subject name")
    chapters: str = Field(..., description="Chapters to cover (comma-separated)")
    total_marks: int = Field(default=80, description="Total marks")
    duration_minutes: int = Field(default=180, description="Exam duration in minutes")
    easy_pct: int = Field(default=30, description="Easy questions percentage")
    medium_pct: int = Field(default=50, description="Medium questions percentage")
    hard_pct: int = Field(default=20, description="Hard questions percentage")
    mcq_count: int = Field(default=10, description="Number of MCQs (1 mark each)")
    vsa_count: int = Field(default=5, description="Number of very short answer (2 marks each)")
    sa_count: int = Field(default=5, description="Number of short answer (3 marks each)")
    la_count: int = Field(default=3, description="Number of long answer (5 marks each)")
    provider: str = Field(default="mock")


class MCQGenerateResponse(BaseModel):
    """Response for MCQ generation."""
    subject: str = Field(..., description="Subject name")
    grade: int = Field(..., description="CBSE class grade")
    chapter: str = Field(..., description="Chapter name")
    topic: str = Field(..., description="Topic")
    questions: list[MCQQuestion] = Field(default_factory=list, description="Generated questions")
    total_marks: int = Field(..., description="Total marks")
    time_recommended_minutes: str = Field(..., description="Recommended time")


class ShortAnswerGenerateResponse(BaseModel):
    """Response for short-answer question generation."""
    subject: str = Field(..., description="Subject name")
    grade: int = Field(..., description="CBSE class grade")
    chapter: str = Field(..., description="Chapter name")
    topic: str = Field(..., description="Topic")
    questions: list[ShortAnswerQuestion] = Field(default_factory=list, description="Generated questions")
    total_marks: int = Field(..., description="Total marks")
    time_recommended_minutes: str = Field(..., description="Recommended time")


class LongAnswerGenerateResponse(BaseModel):
    """Response for long-answer question generation."""
    subject: str = Field(..., description="Subject name")
    grade: int = Field(..., description="CBSE class grade")
    chapter: str = Field(..., description="Chapter name")
    topic: str = Field(..., description="Topic")
    questions: list[LongAnswerQuestion] = Field(default_factory=list, description="Generated questions")
    total_marks: int = Field(..., description="Total marks")
    time_recommended_minutes: str = Field(..., description="Recommended time")


class CustomAssessmentResponse(BaseModel):
    """Response for custom assessment generation."""
    subject: str = Field(..., description="Subject name")
    grade: int = Field(..., description="CBSE class grade")
    chapter: str = Field(..., description="Chapter name")
    topic: str = Field(..., description="Topic")
    total_marks: int = Field(..., description="Total marks")
    sections: list[ExamSection] = Field(default_factory=list, description="Assessment sections")
    total_time_minutes: str = Field(..., description="Recommended time")
    instructions: list[str] = Field(default_factory=list, description="General instructions")


class ExamPaperGenerateResponse(BaseModel):
    """Response for exam paper generation."""
    subject: str = Field(..., description="Subject name")
    grade: int = Field(..., description="CBSE class grade")
    exam_title: str = Field(..., description="Exam title")
    total_marks: int = Field(..., description="Total marks")
    duration_minutes: int = Field(..., description="Exam duration")
    general_instructions: list[str] = Field(default_factory=list, description="General instructions")
    sections: list[ExamSection] = Field(default_factory=list, description="Exam sections")
    answer_key: AnswerKey | None = Field(default=None, description="Answer key")
    blueprint: ExamBlueprint | None = Field(default=None, description="Exam blueprint")