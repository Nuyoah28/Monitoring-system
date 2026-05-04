"""Dynamic exports for the trimmed YOLOv13-lite module tree.

Some source files are trimmed to zero bytes, while their Python bytecode remains
available in this directory. The export script restores those bytecode files as
sourceless modules before importing YOLO.
"""

from importlib import import_module


_MODULE_NAMES = ("block", "conv", "head", "transformer", "activation", "utils")
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


def _load_exports() -> None:
    modules = [import_module(f"{__name__}.{module_name}") for module_name in _MODULE_NAMES]
    for export_name in _EXPORT_NAMES:
        for module in modules:
            if hasattr(module, export_name):
                globals()[export_name] = getattr(module, export_name)
                break


_load_exports()

__all__ = tuple(name for name in _EXPORT_NAMES if name in globals())
