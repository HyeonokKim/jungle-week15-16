import enum


class ProblemArea(str, enum.Enum):
    reading_comprehension = "reading_comprehension"
    reasoning_argumentation = "reasoning_argumentation"


class ProblemScope(str, enum.Enum):
    all_random = "all_random"
    recent_3y = "recent_3y"
    recent_5y = "recent_5y"
