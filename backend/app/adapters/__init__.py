from .base import ProspectDataAdapter
from .synthetic import SyntheticFileAdapter
from .idbi_sandbox import IDBISandboxAdapter
from ..config import get_settings


def get_adapter(seed_path: str = "") -> ProspectDataAdapter:
    s = get_settings()
    if s.data_source == "idbi_sandbox":
        return IDBISandboxAdapter()
    return SyntheticFileAdapter(seed_path or s.seed_file)


__all__ = ["ProspectDataAdapter", "SyntheticFileAdapter", "IDBISandboxAdapter", "get_adapter"]
