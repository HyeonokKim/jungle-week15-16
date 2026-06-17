import enum


class ProblemArea(str, enum.Enum):
    reading_comprehension = "reading_comprehension"
    reasoning_argumentation = "reasoning_argumentation"


class ProblemType(str, enum.Enum):
    main_claim = "main_claim"
    detail_matching = "detail_matching"
    inference = "inference"
    structure_analysis = "structure_analysis"
    conditional_reasoning = "conditional_reasoning"
    strengthen_weaken = "strengthen_weaken"
    error_identification = "error_identification"
    principle_application = "principle_application"
    data_interpretation = "data_interpretation"


PROBLEM_TYPES_BY_AREA = {
    ProblemArea.reading_comprehension: {
        ProblemType.main_claim,
        ProblemType.detail_matching,
        ProblemType.inference,
        ProblemType.structure_analysis,
    },
    ProblemArea.reasoning_argumentation: {
        ProblemType.conditional_reasoning,
        ProblemType.strengthen_weaken,
        ProblemType.error_identification,
        ProblemType.principle_application,
        ProblemType.data_interpretation,
    },
}


class ProblemScope(str, enum.Enum):
    all_random = "all_random"
    recent_3y = "recent_3y"
    recent_5y = "recent_5y"
