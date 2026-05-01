"""Prompt utilities for Mamba-YOLO-World inference.

This module contains only outer-wrapper prompt bookkeeping. It does not change
model architecture, checkpoint loading, or the prompt format passed to
YOLO-World.
"""

import os

from Yolov8.utils1 import update_event_names


BUILTIN_CATEGORIES = ["fire", "smoke"]
DEFAULT_BUSINESS_PROMPTS = [
    "overflow",
    "garbage",
    "garbage bin",
    "bicycle",
    "motorcycle",
]

DISABLED_PROMPTS = {
    "ice on road",
    "icy road",
    "frozen road surface",
    "snow ice on road",
    "smoking",
    "cigarette",
}

# 同义词组：业务上仍然看作一个目标，但模型侧用多个英文 prompt 增强召回。
# key 使用 monitor.py / 前端传入的主 prompt；value 第一个元素必须保持主 prompt 本身，
# 这样画框显示和历史语义都比较直观。
PROMPT_SYNONYM_GROUPS = {
    "fire": [
        "fire",
        "flame",
        "open flame",
        "burning object",
    ],
    "smoke": [
        "smoke",
        "white smoke",
        "black smoke",
        "thick smoke",
    ],
    "garbage on ground": [
        "garbage on ground",
        "garbage pile",
        "trash on ground",
        "garbage bag",
        "overflowing trash bin",
    ],
    "ice on road": [
        "ice on road",
        "icy road",
        "frozen road surface",
        "snow ice on road",
    ],
    "electric scooter": [
        "electric scooter",
        "electric bike",
        "e-bike",
        "electric bicycle",
        "scooter",
    ],
    "vehicle on sidewalk": [
        "vehicle on sidewalk",
        "car on sidewalk",
        "motorcycle on sidewalk",
        "vehicle in restricted area",
    ],
}


def _normalize_prompt(prompt):
    return str(prompt).strip().lower()


def _dedupe_keep_order(items):
    seen = set()
    result = []
    for item in items:
        text = str(item).strip()
        key = text.lower()
        if text and key not in seen:
            seen.add(key)
            result.append(text)
    return result


ENABLE_PROMPT_SYNONYMS = os.environ.get("ENABLE_PROMPT_SYNONYMS", "0") == "1"


def build_prompt_groups(extra_prompts=None):
    """Build grouped prompts in the same business order as legacy categories.

    By default, synonym expansion is disabled to preserve the detector label
    order and inference behavior for enabled Mamba business targets:
        0 fire, 1 smoke, 2 overflow, 3 garbage, 4 garbage bin,
        5 bicycle, 6 motorcycle.

    Ice and smoking are intentionally not included in Mamba defaults. RES_LIST
    keeps their backend slots but reports them as False unless implemented
    elsewhere.

    Set ENABLE_PROMPT_SYNONYMS=1 to expand each business target into multiple
    English prompts and aggregate their labels back to the same business group.
    """
    raw_prompts = BUILTIN_CATEGORIES + DEFAULT_BUSINESS_PROMPTS
    if extra_prompts:
        existing = {_normalize_prompt(prompt) for prompt in raw_prompts}
        for prompt in extra_prompts:
            normalized = _normalize_prompt(prompt)
            if normalized in DISABLED_PROMPTS:
                continue
            if normalized not in existing:
                raw_prompts.append(prompt)
                existing.add(normalized)

    groups = []
    for prompt in raw_prompts:
        if ENABLE_PROMPT_SYNONYMS:
            synonyms = PROMPT_SYNONYM_GROUPS.get(_normalize_prompt(prompt), [prompt])
        else:
            synonyms = [prompt]
        groups.append(_dedupe_keep_order(synonyms))
    return groups


def flatten_prompt_groups(prompt_groups):
    """Flatten grouped prompts to the category list passed into YOLO-World."""
    categories = []
    group_label_ids = []
    for group in prompt_groups:
        label_ids = []
        for prompt in group:
            label_ids.append(len(categories))
            categories.append(prompt)
        group_label_ids.append(label_ids)
    return categories, group_label_ids


def build_categories(extra_prompts=None):
    """Return flattened categories in the order expected by the detector."""
    categories, _ = flatten_prompt_groups(build_prompt_groups(extra_prompts))
    return categories


def build_categories_and_groups(extra_prompts=None):
    """Return flattened categories plus label ids grouped by business target."""
    return flatten_prompt_groups(build_prompt_groups(extra_prompts))


def build_texts(categories):
    """Convert category names to Mamba-YOLO-World text format."""
    return [[cat] for cat in categories] + [[" "]]


def text_signature(texts):
    """Create a stable signature for detecting whether prompts changed."""
    return tuple(tuple(item) for item in texts)


def sync_event_names(categories):
    """Keep drawing utilities aligned with current detector categories."""
    update_event_names(categories)
