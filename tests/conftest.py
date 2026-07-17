"""Shared pytest fixtures for the bami-content-fabric tests."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent  # repository root


@pytest.fixture(scope="session")
def root() -> Path:
    return ROOT


@pytest.fixture(scope="session")
def template_path(root) -> Path:
    return root / "templates" / "bami" / "template.pptx"


@pytest.fixture(scope="session")
def tokens_path(root) -> Path:
    return root / "templates" / "bami" / "design_tokens.yaml"


@pytest.fixture(scope="session")
def sample_deck(root) -> Path:
    return root / "clients" / "_sample" / "deck.json"
@pytest.fixture(scope="session")
def kvi_template_path(root) -> Path:
    return root / "templates" / "kvi" / "template.pptx"

@pytest.fixture(scope="session")
def kvi_tokens_path(root) -> Path:
    return root / "templates" / "kvi" / "design_tokens.yaml"

@pytest.fixture(scope="session")
def sample_deck(root) -> Path:
    return root / "clients" / "_sample" / "deck.json"

@pytest.fixture(scope="session")
def sample_deck(root) -> Path:
    return root / "clients" / "_sample" / "deck.json"


@pytest.fixture()
def tmp_out(tmp_path) -> Path:
    return tmp_path / "out.pptx"
