"""The LLM response schema for M1 (versioned with the prompt) and the shared field lists.

The response shape is flatter than contract.Recipe: provenance, IDs, offsets and passage
metadata are added by the pipeline, never by the model.
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict

from contract import models as C

CATEGORICAL_FIELDS = ["recipeType", "part", "freshOrDried", "heat", "filtered", "process", "form"]
SET_FIELDS = ["solvent"]
TEXT_FIELDS = ["plantNameAsWritten", "heatText", "durationText", "indicationAsWritten"]
EVIDENCE_FIELDS = CATEGORICAL_FIELDS + SET_FIELDS  # enum fields needing a supporting quote
ALL_FIELDS = CATEGORICAL_FIELDS + SET_FIELDS + TEXT_FIELDS + ["ingredients"]
HEADING_ALLOWED = ["plantNameAsWritten", "ingredients"]

ENUMS: dict[str, type[Enum]] = {
    "recipeType": C.RecipeType,
    "part": C.Part,
    "freshOrDried": C.FreshOrDried,
    "heat": C.Heat,
    "filtered": C.Filtered,
    "process": C.Process,
    "form": C.Form,
    "solvent": C.Solvent,
    "role": C.IngredientRole,
    "kind": C.IngredientKind,
}


def values(enum: type[Enum]) -> list[str]:
    return [e.value for e in enum]


def _enum(name: str) -> dict:
    return {"type": "string", "enum": values(ENUMS[name])}


def response_schema() -> dict:
    """Strict JSON schema for output_config.format (all objects closed, all keys required)."""
    ingredient = {
        "type": "object",
        "properties": {
            "plantNameAsWritten": {"type": "string"},
            "part": _enum("part"),
            "role": _enum("role"),
            "kind": _enum("kind"),
        },
        "required": ["plantNameAsWritten", "part", "role", "kind"],
        "additionalProperties": False,
    }
    evidence = {
        "type": "object",
        "properties": {"field": {"type": "string", "enum": EVIDENCE_FIELDS}, "quote": {"type": "string"}},
        "required": ["field", "quote"],
        "additionalProperties": False,
    }
    confidence = {
        "type": "object",
        "properties": {"field": {"type": "string", "enum": ALL_FIELDS}, "confidence": {"type": "number"}},
        "required": ["field", "confidence"],
        "additionalProperties": False,
    }
    recipe_props = {
        "recipeQuote": {"type": "string"},
        "recipeType": _enum("recipeType"),
        "ingredients": {"type": "array", "items": ingredient},
        "plantNameAsWritten": {"type": "string"},
        "part": _enum("part"),
        "freshOrDried": _enum("freshOrDried"),
        "solvent": {"type": "array", "items": _enum("solvent")},
        "heat": _enum("heat"),
        "heatText": {"type": "string"},
        "durationText": {"type": "string"},
        "filtered": _enum("filtered"),
        "process": _enum("process"),
        "form": _enum("form"),
        "indicationAsWritten": {"type": "string"},
        "evidence": {"type": "array", "items": evidence},
        "quotesFromHeading": {"type": "array", "items": {"type": "string", "enum": HEADING_ALLOWED}},
        "fieldConfidence": {"type": "array", "items": confidence},
    }
    recipe = {
        "type": "object",
        "properties": recipe_props,
        "required": list(recipe_props),
        "additionalProperties": False,
    }
    return {
        "type": "object",
        "properties": {"recipes": {"type": "array", "items": recipe}},
        "required": ["recipes"],
        "additionalProperties": False,
    }


# Pydantic mirror used to parse/validate the JSON returned by the model.

class _M(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=True)


class LLMIngredient(_M):
    plantNameAsWritten: str
    part: C.Part
    role: C.IngredientRole
    kind: C.IngredientKind


class LLMEvidence(_M):
    field: str
    quote: str


class LLMConfidence(_M):
    field: str
    confidence: float


class LLMRecipe(_M):
    recipeQuote: str
    recipeType: C.RecipeType
    ingredients: list[LLMIngredient]
    plantNameAsWritten: str
    part: C.Part
    freshOrDried: C.FreshOrDried
    solvent: list[C.Solvent]
    heat: C.Heat
    heatText: str
    durationText: str
    filtered: C.Filtered
    process: C.Process
    form: C.Form
    indicationAsWritten: str
    evidence: list[LLMEvidence]
    quotesFromHeading: list[str]
    fieldConfidence: list[LLMConfidence]


class LLMResponse(_M):
    recipes: list[LLMRecipe]
