from src.methods.base import SaliencyMethod, SaliencyResult
from src.methods.perturbation import Perturbation
from src.methods.omission import Omission
from src.methods.paraphrase import Paraphrase

METHODS: dict[str, type[SaliencyMethod]] = {
    "perturbation": Perturbation,
    "omission": Omission,
    "paraphrase": Paraphrase,
}

__all__ = ["SaliencyMethod", "SaliencyResult", "METHODS"]
