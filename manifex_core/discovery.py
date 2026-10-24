"""Provider-neutral external discovery for MANIFEX.

Discovery is read-only. It produces facts and candidate metadata; it never
imports source or treats popularity as evidence of correctness.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Protocol
from urllib.request import Request, urlopen


class DiscoveryProvider(Protocol):
    def search_repositories(self, query: str, limit: int = 20) -> list[dict[str, Any]]: ...
    def repository(self, full_name: str) -> dict[str, Any]: ...
    def revision(self, full_name: str, branch: str) -> tuple[str, str]: ...
    def tree(self, full_name: str, revision: str) -> list[dict[str, Any]]: ...


class GitHubDiscoveryProvider:
    """Read-only GitHub REST adapter using only the Python standard library."""

    def __init__(self, token: str | None = None, api_base: str = "https://api.github.com"):
        self.token = token
        self.api_base = api_base.rstrip("/")

    def _get(self, path: str) -> Any:
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "MANIFEX/1.0"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        req = Request(self.api_base + path, headers=headers, method="GET")
        with urlopen(req, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))

    def search_repositories(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        from urllib.parse import quote
        data = self._get(f"/search/repositories?q={quote(query)}&per_page={min(max(limit, 1), 100)}")
        return list(data.get("items", []))

    def repository(self, full_name: str) -> dict[str, Any]:
        return dict(self._get(f"/repos/{full_name}"))

    def revision(self, full_name: str, branch: str) -> tuple[str, str]:
        from urllib.parse import quote
        data = self._get(f"/repos/{full_name}/branches/{quote(branch, safe='')}")
        commit = data.get("commit", {})
        sha = str(commit.get("sha") or "")
        tree = str((commit.get("commit") or {}).get("tree", {}).get("sha") or "")
        if not sha or not tree:
            raise ValueError(f"GitHub returned incomplete immutable revision for {full_name}@{branch}")
        return sha, tree

    def tree(self, full_name: str, revision: str) -> list[dict[str, Any]]:
        from urllib.parse import quote
        data = self._get(f"/repos/{full_name}/git/trees/{quote(revision, safe='')}?recursive=1")
        return list(data.get("tree", []))


@dataclass(frozen=True)
class RepositoryInspection:
    repository: str
    revision: str
    tree_hash: str
    files: tuple[str, ...]
    manifests: tuple[str, ...] = ()
    test_paths: tuple[str, ...] = ()
    interfaces: tuple[str, ...] = ()
    license_name: str = "NOT_MEASURED"
    capabilities: tuple[str, ...] = ()
    runtime_indicators: tuple[str, ...] = ()
    evidence_hints: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)


_MANIFESTS = {
    "pyproject.toml", "setup.py", "setup.cfg", "requirements.txt", "package.json",
    "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "go.mod", "Cargo.toml",
    "pom.xml", "build.gradle", "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
}
_CAPABILITY_KEYWORDS = {
    "security": ("security", "auth", "rbac", "threat", "vulnerability", "siem", "osint"),
    "benchmarking": ("benchmark", "eval", "evaluation", "holdout", "grader"),
    "intelligence": ("agent", "reasoning", "intelligence", "knowledge", "research", "memory"),
    "governance": ("governance", "policy", "audit", "approval", "provenance", "compliance"),
    "deployment": ("docker", "kubernetes", "deploy", "helm", "terraform", "workflow"),
    "api": ("api", "fastapi", "flask", "express", "openapi", "graphql", "mcp"),
    "ui": ("dashboard", "frontend", "react", "vite", "web", "ui", "visualization"),
    "testing": ("test", "pytest", "jest", "unittest", "cypress", "playwright"),
}


class RepositoryInspector:
    """Conservative tree inspection. Heuristics are recorded as hints, not proof."""

    def inspect(self, repo: Mapping[str, Any], tree: Iterable[Mapping[str, Any]], *, revision: str, tree_hash: str) -> RepositoryInspection:
        files = tuple(sorted(str(x.get("path", "")) for x in tree if x.get("type") == "blob"))
        names = {p.rsplit("/", 1)[-1].lower() for p in files}
        manifests = tuple(sorted(p for p in files if p.rsplit("/", 1)[-1] in _MANIFESTS))
        tests = tuple(sorted(p for p in files if re.search(r"(^|/)(tests?|__tests__)(/|$)|(^|/)test_[^/]+$", p, re.I)))
        interfaces = tuple(sorted(p for p in files if re.search(r"openapi|swagger|schema|routes?|api|mcp", p, re.I)))
        haystack = " ".join(files).lower() + " " + str(repo.get("description", "")).lower()
        capabilities = tuple(sorted(k for k, words in _CAPABILITY_KEYWORDS.items() if any(w in haystack for w in words)))
        runtime = tuple(sorted(n for n in names if n in {"dockerfile", "docker-compose.yml", "docker-compose.yaml", "package.json", "pyproject.toml", "go.mod", "cargo.toml"}))
        hints = []
        if tests: hints.append("tests-present")
        if repo.get("stargazers_count") is not None: hints.append("popularity-metadata-present")
        license_name = ((repo.get("license") or {}).get("spdx_id") if isinstance(repo.get("license"), dict) else None) or "NOT_MEASURED"
        return RepositoryInspection(
            repository=str(repo.get("full_name") or repo.get("name") or ""),
            revision=revision,
            tree_hash=tree_hash,
            files=files, manifests=manifests, test_paths=tests, interfaces=interfaces,
            license_name=license_name, capabilities=capabilities, runtime_indicators=runtime,
            evidence_hints=tuple(hints), metadata={"stars": repo.get("stargazers_count", 0), "forks": repo.get("forks_count", 0)},
        )


class AssetDiscoveryEngine:
    """Discovers and inspects candidates without acquiring or modifying them."""

    def __init__(self, provider: DiscoveryProvider, inspector: RepositoryInspector | None = None):
        self.provider = provider
        self.inspector = inspector or RepositoryInspector()

    def discover(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        return self.provider.search_repositories(query, limit)

    def inspect_candidate(self, candidate: Mapping[str, Any]) -> RepositoryInspection:
        full_name = str(candidate.get("full_name") or "")
        repo = self.provider.repository(full_name)
        branch = str(repo.get("default_branch") or "")
        commit, tree_hash = self.provider.revision(full_name, branch)
        tree = self.provider.tree(full_name, commit)
        return self.inspector.inspect(repo, tree, revision=commit, tree_hash=tree_hash)
