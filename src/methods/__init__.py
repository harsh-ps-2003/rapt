from src.methods.base import COMPONENT_LABELS, SaliencyMethod, SaliencyResult
from src.methods.perturbation import Perturbation
from src.methods.omission import Omission
from src.methods.paraphrase import Paraphrase
from src.methods.hierarchical import HierarchicalAblation
from src.methods.counterfactual import Counterfactual

METHODS: dict[str, type[SaliencyMethod]] = {
    "perturbation": Perturbation,
    "omission": Omission,
    "paraphrase": Paraphrase,
    "hierarchical": HierarchicalAblation,
    "counterfactual": Counterfactual,
}

__all__ = [
    "COMPONENT_LABELS",
    "SaliencyMethod",
    "SaliencyResult",
    "METHODS",
]
