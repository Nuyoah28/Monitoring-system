"""Dynamic exports for the trimmed YOLOv13-lite module tree.

Some source files are trimmed to zero bytes, while their Python bytecode remains
available in this directory. The export script restores those bytecode files as
sourceless modules before importing YOLO.
"""

import sys
from importlib import import_module, util
from importlib.machinery import SourcelessFileLoader
from pathlib import Path


# Load foundational modules first, then dependent composite modules.
# The trimmed sourceless bytecode for `block` imports `conv`, and `head`
# depends on both `conv` and `block`, so order matters here.
_MODULE_NAMES = ("activation", "utils", "conv", "transformer", "block", "head")
_EXPORT_NAMES = (
    "AIFI",
    "C1",
    "C2",
    "C2PSA",
    "C3",
    "C3TR",
    "ELAN1",
    "OBB",
    "PSA",
    "SPP",
    "SPPELAN",
    "SPPF",
    "AConv",
    "ADown",
    "Bottleneck",
    "BottleneckCSP",
    "C2f",
    "C2fAttn",
    "C2fCIB",
    "C2fPSA",
    "C3Ghost",
    "C3k2",
    "C3x",
    "CBFuse",
    "CBLinear",
    "Classify",
    "Concat",
    "Conv",
    "Conv2",
    "DSConv",
    "ConvTranspose",
    "Detect",
    "DWConv",
    "DWConvTranspose2d",
    "Focus",
    "GhostBottleneck",
    "GhostConv",
    "HGBlock",
    "HGStem",
    "ImagePoolingAttn",
    "Index",
    "Pose",
    "RepC3",
    "RepConv",
    "RepNCSPELAN4",
    "RepVGGDW",
    "ResNetLayer",
    "RTDETRDecoder",
    "SCDown",
    "Segment",
    "TorchVision",
    "WorldDetect",
    "v10Detect",
    "A2C2f",
    "HyperACE",
    "DownsampleConv",
    "FullPAD_Tunnel",
    "DSC3k2",
    "EUCB",
)
_MODULE_DIR = Path(__file__).resolve().parent


def _compatible_pyc_candidates(module_name: str) -> list[Path]:
    cache_dir = _MODULE_DIR / "__pycache__"
    cache_tag = getattr(sys.implementation, "cache_tag", "")
    candidates: list[Path] = []

    if cache_tag:
        candidates.append(cache_dir / f"{module_name}.{cache_tag}.pyc")
    candidates.append(_MODULE_DIR / f"{module_name}.pyc")
    if cache_dir.exists():
        candidates.extend(sorted(cache_dir.glob(f"{module_name}.*.pyc")))

    magic = util.MAGIC_NUMBER
    compatible: list[Path] = []
    for candidate in candidates:
        if not candidate.exists() or candidate in compatible:
            continue
        try:
            if candidate.read_bytes()[:4] == magic:
                compatible.append(candidate)
        except OSError:
            continue
    return compatible


def _load_sourceless_module(module_name: str):
    full_name = f"{__name__}.{module_name}"
    for pyc_path in _compatible_pyc_candidates(module_name):
        loader = SourcelessFileLoader(full_name, str(pyc_path))
        spec = util.spec_from_loader(full_name, loader, origin=str(pyc_path))
        if spec is None:
            continue
        module = util.module_from_spec(spec)
        sys.modules[full_name] = module
        loader.exec_module(module)
        return module
    raise ModuleNotFoundError(
        f"No compatible bytecode found for trimmed module '{full_name}'. "
        f"Expected one of: {[str(path) for path in _compatible_pyc_candidates(module_name)]}"
    )


def _import_module_or_sourceless(module_name: str):
    full_name = f"{__name__}.{module_name}"
    empty_stub = _MODULE_DIR / f"{module_name}.py.empty"
    if empty_stub.exists():
        try:
            return import_module(full_name)
        except (ImportError, ModuleNotFoundError):
            sys.modules.pop(full_name, None)
            return _load_sourceless_module(module_name)
    return import_module(full_name)


def _load_exports() -> None:
    modules = [_import_module_or_sourceless(module_name) for module_name in _MODULE_NAMES]
    for export_name in _EXPORT_NAMES:
        for module in modules:
            if hasattr(module, export_name):
                globals()[export_name] = getattr(module, export_name)
                break


_load_exports()

__all__ = tuple(name for name in _EXPORT_NAMES if name in globals())
