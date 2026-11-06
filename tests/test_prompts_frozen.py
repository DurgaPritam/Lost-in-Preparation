"""Prompt versions are frozen once used: nothing may write into prompts/ (decision 2026-11-06).

- the contract generator writes only under contract/schemas/ and refuses a path in prompts/;
- every file of every used prompt version keeps its pinned sha256, and no file is added to a version folder;
- the recorded promptVersion digests still rebuild from the committed files and the in-code response schema.
"""
import hashlib
import json

import pytest

from lip import contract_gen
from lip.paths import ROOT

PINNED = {
    "prompts/m1_extract/v1/fewshot.json": "55c1d53dca374fe468694557897a886f02ce5eaad8fd35ead112949107555a2f",
    "prompts/m1_extract/v1/guidelines.md": "8b708d2b2f1e820340091b541ebd54ae21303ab550d2652030f030025d61844f",
    "prompts/m1_extract/v1/response.schema.json": "8be8df9660493c2aabad25c396c263b378cf3ba4c0d1ae67cf9fa66cdabeb498",
    "prompts/m1_extract/v1/system.md": "b1db840cb49454a733069edb3c89de99b9a1b4a17ed9bbc760c3922ad94b46fd",
    "prompts/m1_extract/v2/fewshot.json": "ee3ae69441dbcd1762c1b81c488792fd1199b475d8d43882611d6c027b36d1d4",
    "prompts/m1_extract/v2/guidelines.md": "e841c35ffaad6c360cf96f7973cd42fa843a721f4f3f392947f52e8a95dce0e2",
    "prompts/m1_extract/v2/retry.md": "235c80d0c34ae1a61439a1d1cec2601e2bfa77d80abb25cfbe1b869374f29047",
    "prompts/m1_extract/v2/system.md": "e47dc35b8a39f6670936b3b61ad8786b55ef84860831df7d6702e56f266208ee",
    "prompts/m1_extract/v3/fewshot.json": "ee3ae69441dbcd1762c1b81c488792fd1199b475d8d43882611d6c027b36d1d4",
    "prompts/m1_extract/v3/guidelines.md": "e841c35ffaad6c360cf96f7973cd42fa843a721f4f3f392947f52e8a95dce0e2",
    "prompts/m1_extract/v3/retry.md": "235c80d0c34ae1a61439a1d1cec2601e2bfa77d80abb25cfbe1b869374f29047",
    "prompts/m1_extract/v3/system.md": "1a9a03f667e6190f0ef321f469b2a760927662d1e90c00772335a1b0c68102b9",
    "prompts/m5_methods/v1/retry.md": "41d2916afa60f60dcf02b154ba943790fafa19c79a83c73d97aff09ab73ac69b",
    "prompts/m5_methods/v1/system.md": "fac7eb5097f8d368258bb4e9f426b666cb3df6cf3455b4f8d510b01f1d9bc46e",
}
# promptVersion recorded in provenance: v1/v2 in the committed Groq caches, v3 on all approved M1 records.
RECORDED = {"v1": "m1_extract/v1:8aadfda9ef", "v2": "m1_extract/v2:36e5019562", "v3": "m1_extract/v3:13ca4093ec"}


def _prompt_files():
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted((ROOT / "prompts").glob("*/v*/*")) if p.is_file()}


def test_prompt_versions_unchanged_and_nothing_added():
    assert _prompt_files() == PINNED


def test_contract_generator_never_writes_into_prompts():
    before = _prompt_files()
    written = contract_gen.write()
    assert written and all(w.startswith("contract/schemas/") for w in written)
    assert _prompt_files() == before


def test_contract_generator_refuses_a_prompts_path():
    with pytest.raises(PermissionError):
        contract_gen._target(ROOT / "prompts" / "m1_extract" / "v3" / "response.schema.json")
    with pytest.raises(PermissionError):
        contract_gen._target(ROOT / "contract" / "schemas" / ".." / ".." / "prompts" / "x.json")


def test_recorded_prompt_versions_rebuild():
    from lip.m1.extract import source_titles
    from lip.m1.prompt import build
    for v, recorded in RECORDED.items():
        assert build(source_titles(), v).version == recorded


def test_v1_schema_file_is_the_schema_every_version_used():
    from lip.m1.schema import response_schema
    assert json.loads((ROOT / "prompts/m1_extract/v1/response.schema.json").read_text()) == response_schema()
