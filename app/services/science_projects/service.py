"""Science Project generation service — core engine for generating curriculum-aligned science projects."""

from app.schemas.science_project import (
    MaterialItem,
    BuildStep,
    ScienceProjectGenerateRequest,
    ScienceProjectResponse,
)
from app.services.education_engine import fetch_project_context, _format_context_for_prompt
from app.services.orchestration.pipeline_runner import orchestrator
from app.utils.logger import get_logger

logger = get_logger("app.science_projects")

# Grade-to-age-range mapping for CBSE
GRADE_AGE_MAP = {
    6: "11-12 years",
    7: "12-13 years",
    8: "13-14 years",
}

# Valid difficulty levels
VALID_DIFFICULTIES = {"easy", "medium", "hard"}
VALID_BUDGETS = {"low", "medium", "high"}


def _validate_request(body: ScienceProjectGenerateRequest) -> None:
    """Validate the generate request parameters."""
    if body.grade not in GRADE_AGE_MAP:
        raise ValueError(f"Unsupported grade: {body.grade}. Supported grades: {list(GRADE_AGE_MAP.keys())}")
    if body.difficulty not in VALID_DIFFICULTIES:
        raise ValueError(f"Invalid difficulty: {body.difficulty}. Must be one of: {VALID_DIFFICULTIES}")
    if body.budget not in VALID_BUDGETS:
        raise ValueError(f"Invalid budget: {body.budget}. Must be one of: {VALID_BUDGETS}")


class ScienceProjectService:
    """Core service for generating curriculum-aligned science projects."""

    async def generate_project(self, body: ScienceProjectGenerateRequest) -> ScienceProjectResponse:
        """Generate a complete science project with materials, steps, and explanation."""
        _validate_request(body)

        age_range = GRADE_AGE_MAP[body.grade]

        # Fetch educational context from engine
        context_data = await fetch_project_context(
            grade=body.grade,
            topic=body.topic,
            subject=body.subject,
        )
        context_prompt = _format_context_for_prompt(context_data, context_type="project")
        logger.info("Education context fetched", extra={"counts": context_data.get("counts", {})})

        common_vars = {
            "grade": str(body.grade),
            "subject": body.subject,
            "topic": body.topic,
            "difficulty": body.difficulty,
            "budget": body.budget,
            "age_range": age_range,
            "educational_context": context_prompt,
        }

        # Step 1: Generate project idea
        logger.info("Generating science project idea", extra={"topic": body.topic, "grade": body.grade})
        project_raw = await orchestrator.execute_with_retry(
            category="science_projects",
            prompt_name="generate",
            variables=common_vars,
            provider=body.provider,
            max_tokens=1024,
            context=f"Generate a science project for Class {body.grade} on {body.topic}",
            age_group=age_range,
        )
        project_data = orchestrator.cleanup_response(project_raw)

        # Step 2: Generate materials list
        logger.info("Generating materials list for project", extra={"title": project_data.get("project_title", "")})
        project_title = project_data.get("project_title", f"Project on {body.topic}")
        materials_vars = {
            "project_title": project_title,
            "subject": body.subject,
            "grade": str(body.grade),
            "topic": body.topic,
            "difficulty": body.difficulty,
        }
        materials_raw = await orchestrator.execute_with_retry(
            category="science_projects",
            prompt_name="materials",
            variables=materials_vars,
            provider=body.provider,
            max_tokens=1024,
            context=f"Generate materials list for {project_title}",
            age_group=age_range,
        )
        materials_data = orchestrator.cleanup_response(materials_raw, expected_fields=["materials"])

        # Step 3: Generate build steps
        logger.info("Generating build steps", extra={"project": project_title})
        materials_summary = ", ".join(
            m.get("item", "") for m in materials_data.get("materials", [])
        ) or "common household items"
        steps_vars = {
            "project_title": project_title,
            "materials_summary": materials_summary,
            "grade": str(body.grade),
            "age_range": age_range,
        }
        steps_raw = await orchestrator.execute_with_retry(
            category="science_projects",
            prompt_name="build_steps",
            variables=steps_vars,
            provider=body.provider,
            max_tokens=1536,
            context=f"Generate build instructions for {project_title}",
            age_group=age_range,
        )
        steps_data = orchestrator.cleanup_response(steps_raw, expected_fields=["steps"])

        # Step 4: Generate explanation
        logger.info("Generating explanation", extra={"project": project_title})
        explanation_vars = {
            "project_title": project_title,
            "subject": body.subject,
            "topic": body.topic,
            "grade": str(body.grade),
        }
        explanation_raw = await orchestrator.execute_with_retry(
            category="science_projects",
            prompt_name="explanation",
            variables=explanation_vars,
            provider=body.provider,
            max_tokens=1024,
            context=f"Explain science behind {project_title}",
            age_group=age_range,
        )
        explanation_data = orchestrator.cleanup_response(explanation_raw)

        # Step 5: Generate difficulty assessment
        logger.info("Generating difficulty assessment", extra={"project": project_title})
        steps_summary = f"{steps_data.get('total_steps', 0)} steps"
        difficulty_vars = {
            "project_title": project_title,
            "topic": body.topic,
            "materials_summary": materials_summary,
            "steps_summary": steps_summary,
            "grade": str(body.grade),
        }
        difficulty_raw = await orchestrator.execute_with_retry(
            category="science_projects",
            prompt_name="difficulty",
            variables=difficulty_vars,
            provider=body.provider,
            max_tokens=1024,
            context=f"Assess difficulty of {project_title}",
            age_group=age_range,
        )
        difficulty_data = orchestrator.cleanup_response(difficulty_raw)

        # Assemble final response
        return self._assemble_response(
            project_data=project_data,
            materials_data=materials_data,
            steps_data=steps_data,
            explanation_data=explanation_data,
            difficulty_data=difficulty_data,
            body=body,
        )

    def _assemble_response(
        self,
        project_data: dict,
        materials_data: dict,
        steps_data: dict,
        explanation_data: dict,
        difficulty_data: dict,
        body: ScienceProjectGenerateRequest,
    ) -> ScienceProjectResponse:
        """Assemble data from multiple LLM calls into a single response."""
        materials_list = []
        for m in materials_data.get("materials", []):
            materials_list.append(
                MaterialItem(
                    item=m.get("item", ""),
                    quantity=str(m.get("quantity", "1")),
                    unit=m.get("unit", "pieces"),
                    estimated_cost_rs=float(m.get("estimated_cost_rs", 0)),
                    source=m.get("source", ""),
                    notes=m.get("notes"),
                )
            )

        steps_list = []
        for s in steps_data.get("steps", []):
            steps_list.append(
                BuildStep(
                    step_number=s.get("step_number", 1),
                    title=s.get("title", ""),
                    description=s.get("description", ""),
                    estimated_time_minutes=s.get("estimated_time_minutes", 15),
                    materials_needed=s.get("materials_needed", []),
                    safety_note=s.get("safety_note"),
                )
            )

        return ScienceProjectResponse(
            project_title=project_data.get("project_title", f"Project on {body.topic}"),
            subject=body.subject,
            grade=body.grade,
            topic=body.topic,
            difficulty=body.difficulty,
            estimated_build_time=project_data.get("estimated_build_time", "2-3 hours"),
            estimated_cost=project_data.get("estimated_cost", "₹150-₹300"),
            short_description=project_data.get("short_description", ""),
            learning_objectives=project_data.get("learning_objectives", []),
            curriculum_alignment=project_data.get("curriculum_alignment", ""),
            materials=materials_list,
            total_estimated_cost_rs=float(materials_data.get("total_estimated_cost_rs", 0)),
            safety_items_required=materials_data.get("safety_items_required", []),
            alternative_materials=materials_data.get("alternative_materials", []),
            total_steps=steps_data.get("total_steps", len(steps_list)),
            steps=steps_list,
            precautions=steps_data.get("precautions", []),
            adult_supervision_required=steps_data.get("adult_supervision_required", True),
            tips_for_success=steps_data.get("tips_for_success", []),
            scientific_principle=explanation_data.get("scientific_principle", ""),
            simple_explanation=explanation_data.get("simple_explanation", ""),
            how_project_demonstrates=explanation_data.get("how_project_demonstrates", ""),
            real_world_applications=explanation_data.get("real_world_applications", []),
            simple_analogy=explanation_data.get("simple_analogy", ""),
            overall_difficulty=difficulty_data.get("overall_difficulty", body.difficulty),
            provider=body.provider,
        )


# Singleton instance
science_project_service = ScienceProjectService()