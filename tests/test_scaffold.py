"""Repository scaffold checks for T01 (spec sections 3 and 13)."""

import importlib
import os
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

SECTION_3_DIRS = [
    "docs",
    "apps/web/src/app",
    "apps/web/src/components",
    "apps/web/src/lib",
    "apps/api/app",
    *(
        f"apps/api/app/{module}"
        for module in (
            "tenancy",
            "catalog",
            "packs",
            "mapping",
            "content",
            "validation",
            "compliance",
            "listings",
            "inventory",
            "orders",
            "channels",
            "queue",
        )
    ),
    "apps/api/alembic",
    "apps/api/tests",
    "apps/worker/workflows",
    "apps/worker/activities",
    "packages/connectors",
    *(
        f"packages/connectors/{channel}"
        for channel in ("ebay", "kaufland", "amazon", "otto", "shopify", "testing")
    ),
    "packages/packs",
    "packages/ai/prompts",
    "packages/ai/schemas",
    "packages/ai/evals",
    "infra/terraform",
    "infra/docker",
]

MAKE_TARGETS = ["setup", "dev", "test", "lint", "eval", "e2e", "openapi", "migrate", "seed"]
PLACEHOLDER_TARGETS = ["eval", "e2e", "openapi", "migrate"]
SKIP_DIRS = {".git", ".venv", "node_modules", ".next", ".mypy_cache", ".ruff_cache"}


def make_recipes() -> dict[str, list[str]]:
    recipes: dict[str, list[str]] = {}
    current: str | None = None
    for line in (ROOT / "Makefile").read_text().splitlines():
        if line.startswith("\t") and current is not None:
            recipes[current].append(line.strip())
            continue
        match = re.match(r"^([a-z0-9]+):(?!=)", line)
        current = match.group(1) if match else None
        if current is not None:
            recipes[current] = []
    return recipes


def compose_text() -> str:
    return (ROOT / "docker-compose.yml").read_text()


@pytest.mark.parametrize("path", SECTION_3_DIRS)
def test_section_3_folder_exists(path: str) -> None:
    assert (ROOT / path).is_dir(), f"missing folder from spec section 3: {path}"


@pytest.mark.parametrize("module", ["app", "workflows", "activities", "connectors"])
def test_python_packages_import(module: str) -> None:
    importlib.import_module(module)


def test_makefile_defines_section_13_targets() -> None:
    assert sorted(make_recipes()) == sorted(MAKE_TARGETS)


@pytest.mark.parametrize("target", PLACEHOLDER_TARGETS)
def test_placeholder_targets_fail(target: str) -> None:
    assert "@exit 1" in make_recipes()[target]


def test_seed_target_succeeds() -> None:
    assert not any("exit" in line for line in make_recipes()["seed"])


def test_compose_uses_only_declared_named_volumes() -> None:
    text = compose_text()
    declared = set(re.findall(r"^  ([a-z0-9-]+):\s*$", text.split("\nvolumes:\n", 1)[1], re.M))
    mounts = re.findall(r"^\s+- ([^\s:\"]+):/", text, re.M)
    assert mounts, "expected volume mounts in docker-compose.yml"
    for source in mounts:
        assert source in declared, f"not a declared named volume (bind mount?): {source}"


def test_compose_images_pinned_to_exact_tags() -> None:
    images = re.findall(r"^\s+image:\s*(\S+)", compose_text(), re.M)
    assert len(images) == 6
    for image in images:
        tag = image.rsplit(":", 1)[1] if ":" in image.rsplit("/", 1)[-1] else ""
        assert tag and tag != "latest", f"image not pinned to an exact tag: {image}"
        assert re.search(r"\d+\.\d+", tag), f"tag is not an exact version: {image}"


def test_env_example_lists_every_compose_variable() -> None:
    used = set(re.findall(r"\$\{([A-Z0-9_]+)", compose_text()))
    listed = set(re.findall(r"^([A-Z0-9_]+)=", (ROOT / ".env.example").read_text(), re.M))
    assert used, "expected variables in docker-compose.yml"
    assert used <= listed, f"missing from .env.example: {sorted(used - listed)}"


def test_no_symlinks_in_repository() -> None:
    links = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in dirnames + filenames:
            path = Path(dirpath, name)
            if path.is_symlink():
                links.append(str(path.relative_to(ROOT)))
    assert links == []


def test_gitattributes_forces_lf_and_marks_binaries() -> None:
    lines = (ROOT / ".gitattributes").read_text().splitlines()
    assert "* text=auto eol=lf" in lines
    for pattern in ("*.png", "*.jpg", "*.woff2", "*.ttf"):
        assert f"{pattern} binary" in lines
