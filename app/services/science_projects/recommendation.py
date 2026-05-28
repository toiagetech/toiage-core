"""Project recommendation logic — generates better project suggestions based on grade, topic, difficulty, and budget."""

from dataclasses import dataclass, field


@dataclass
class ProjectRecommendation:
    """A recommended project specification."""
    grade: int
    subject: str
    topic: str
    difficulty: str
    budget: str
    recommended_project_type: str = ""
    reasoning: str = ""
    material_complexity_score: int = 0  # 1-5
    estimated_budget_rs: float = 0.0
    estimated_time_minutes: int = 0
    alternative_topics: list[str] = field(default_factory=list)


class ProjectRecommender:
    """Recommends science projects based on grade, topic, difficulty, and budget constraints."""

    # Budget ranges by grade (min_rs, max_rs)
    BUDGET_RANGES = {
        "low": (0, 200),
        "medium": (200, 500),
        "high": (500, 2000),
    }

    # Topic categories that work well for certain difficulties
    TOPIC_DIFFICULTY_MAP = {
        "easy": [
            "water cycle", "plant growth", "magnetic compass", "static electricity",
            "seed germination", "sink or float", "homemade thermometer",
            "paper bridge", "wind vane", "rain gauge",
        ],
        "medium": [
            "solar still", "electromagnet", "volcano model", "water filtration",
            "human respiratory system model", "electric circuit", "solar oven",
            "periscope", "hydraulic lift", "pH indicator",
        ],
        "hard": [
            "rainwater harvesting system", "solar tracker", "biogas model",
            "automatic street light", "water purification system", "windmill generator",
            "heart model", "greenhouse effect model", "robotic arm", "earthquake alarm",
        ],
    }

    def recommend(
        self,
        grade: int,
        topic: str,
        difficulty: str,
        budget: str,
    ) -> ProjectRecommendation:
        """Generate a project recommendation based on inputs."""
        budget_range = self.BUDGET_RANGES.get(budget, (0, 500))
        recommended_type = self._get_recommended_type(topic, difficulty)
        material_score = self._get_material_complexity(difficulty)
        estimated_time = self._get_estimated_time(grade, difficulty)

        alt_topics = self._get_alternative_topics(topic, difficulty)

        reasoning = (
            f"For Class {grade} studying '{topic}', a {difficulty} difficulty project "
            f"within ₹{budget_range[0]}-₹{budget_range[1]} budget is recommended. "
            f"This project type ({recommended_type}) uses commonly available materials "
            f"and can be completed in approximately {estimated_time} minutes."
        )

        return ProjectRecommendation(
            grade=grade,
            subject="Science",
            topic=topic,
            difficulty=difficulty,
            budget=budget,
            recommended_project_type=recommended_type,
            reasoning=reasoning,
            material_complexity_score=material_score,
            estimated_budget_rs=sum(budget_range) / 2,
            estimated_time_minutes=estimated_time,
            alternative_topics=alt_topics,
        )

    def score_projects(self, criteria: dict) -> list[dict]:
        """Rank multiple project options based on criteria."""
        grade = criteria.get("grade", 7)
        budget = criteria.get("budget", "medium")
        difficulty = criteria.get("difficulty", "medium")

        options = []
        for diff_level in ["easy", "medium", "hard"]:
            if diff_level == difficulty or True:  # Include all for comparison
                rec = self.recommend(
                    grade=grade,
                    topic=criteria.get("topic", "general"),
                    difficulty=diff_level,
                    budget=budget,
                )
                options.append({
                    "difficulty": diff_level,
                    "recommended_type": rec.recommended_project_type,
                    "material_complexity": rec.material_complexity_score,
                    "estimated_time": rec.estimated_time_minutes,
                    "estimated_budget": rec.estimated_budget_rs,
                    "reasoning": rec.reasoning,
                })

        return sorted(options, key=lambda x: x["material_complexity"])

    def _get_recommended_type(self, topic: str, difficulty: str) -> str:
        """Map topic to recommended project type."""
        topic_lower = topic.lower()

        if any(word in topic_lower for word in ["water", "rain", "filter", "conservation"]):
            return "Working Model / Demonstration"
        elif any(word in topic_lower for word in ["electric", "circuit", "magnet", "motor"]):
            return "Working Electrical Model"
        elif any(word in topic_lower for word in ["solar", "energy", "renewable", "wind"]):
            return "Renewable Energy Model"
        elif any(word in topic_lower for word in ["plant", "seed", "grow", "photosynthesis"]):
            return "Botanical Experiment"
        elif any(word in topic_lower for word in ["human", "body", "heart", "respiratory"]):
            return "Biological Model"
        elif any(word in topic_lower for word in ["robot", "machine", "lever", "pulley"]):
            return "Mechanical Model"
        else:
            return "Science Demonstration Model"

    def _get_material_complexity(self, difficulty: str) -> int:
        """Get material complexity score (1-5)."""
        return {"easy": 1, "medium": 3, "hard": 5}.get(difficulty, 3)

    def _get_estimated_time(self, grade: int, difficulty: str) -> int:
        """Get estimated build time in minutes."""
        base = {6: 60, 7: 90, 8: 120}.get(grade, 90)
        difficulty_mult = {"easy": 1, "medium": 1.5, "hard": 2}.get(difficulty, 1.5)
        return int(base * difficulty_mult)

    def _get_alternative_topics(self, topic: str, difficulty: str) -> list[str]:
        """Get alternative topics similar to the given topic."""
        topic_lower = topic.lower()
        alt = []

        if any(word in topic_lower for word in ["water", "rain"]):
            alt = ["Water Filtration", "Solar Still", "Rain Gauge"]
        elif any(word in topic_lower for word in ["solar", "sun"]):
            alt = ["Solar Oven", "Solar Water Heater", "Solar Powered Fan"]
        elif any(word in topic_lower for word in ["electric", "circuit"]):
            alt = ["Simple Electric Motor", "Electromagnet", "LED Circuit"]
        elif any(word in topic_lower for word in ["plant", "seed"]):
            alt = ["Seed Germination in Different Conditions", "Hydroponics", "Plant Light Experiment"]
        elif any(word in topic_lower for word in ["magnet"]):
            alt = ["Magnetic Compass", "Electromagnet", "Magnetic Levitation"]
        else:
            alt = self.TOPIC_DIFFICULTY_MAP.get(difficulty, [])[:3]

        return [t for t in alt if t.lower() != topic_lower][:3]


# Singleton instance
project_recommender = ProjectRecommender()