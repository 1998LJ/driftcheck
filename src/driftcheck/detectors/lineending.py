"""Line ending drift detection: missing CRLF-safe .gitattributes or CRLF line endings."""
from __future__ import annotations
import fnmatch
import re
from pathlib import Path

EOL_ATTR_RE = re.compile(r'^\s*\*?\s*text\s*=\s*auto', re.MULTILINE)
EOL_LINE_RE = re.compile(r'^\s*\*.*eol\s*=\s*lf', re.MULTILINE)

SKIP_DIRS = frozenset({
    "node_modules", "vendor", ".git", "build", "dist", "__pycache__",
    ".venv", "venv", ".tox", ".eggs", "htmlcov", ".next", ".nuxt",
    "out", "target", "bower_components", ".cache", ".gradle", ".m2",
})

SOURCE_EXTENSIONS = frozenset({
    ".py", ".js", ".ts", ".rs", ".go", ".java", ".sh",
})


def find_lineending_drift(root: Path) -> list[dict]:
    """Detect missing CRLF-safe .gitattributes or CRLF files violating LF policy.

    A repo that ships text source but lacks `* text=auto eol=lf` in
    .gitattributes can check out with CRLF working-tree bytes on Windows
    (core.autocrlf=true) while the index stores LF -- silently breaking
    byte-exact checks. Returns a drift if .gitattributes is absent or does
    not normalize line endings.

    When .gitattributes specifies LF line endings, this also detects any source
    files containing CRLF line endings that violate the repository policy.

    Only fires when the repo has source files (to avoid noise on empty dirs).
    """
    # Check if repo has any source files that would need line ending normalization
    source_patterns = [
        "*.py", "*.js", "*.ts", "*.tsx", "*.jsx", "*.rs", "*.go", "*.java",
        "*.kt", "*.kts", "*.c", "*.cpp", "*.h", "*.hpp", "*.rb", "*.php",
        "*.cs", "*.fs", "*.swift", "*.m", "*.mm", "*.scala", "*.clj",
        "*.sh", "*.bash", "*.zsh", "*.fish", "*.ps1", "*.bat", "*.cmd",
        "*.xml", "*.json", "*.yaml", "*.yml", "*.toml", "*.ini", "*.cfg",
        "*.conf", "*.config", "*.properties", "*.gradle", "*.sbt",
        "Makefile", "Dockerfile", "*.md", "*.rst", "*.txt",
    ]
    has_source = False
    for pattern in source_patterns:
        if list(root.glob(pattern)):
            has_source = True
            break
    if not has_source:
        # Check common subdirectories
        for subdir in ["src", "lib", "app", "test", "tests", "scripts", "bin", "pkg", "cmd"]:
            subpath = root / subdir
            if subpath.exists():
                for pattern in source_patterns:
                    if list(subpath.glob(pattern)):
                        has_source = True
                        break
            if has_source:
                break

    if not has_source:
        return []  # Empty repo or no source files — skip lineending check

    ga = root / ".gitattributes"
    if not ga.exists():
        return [{
            "file": ".gitattributes",
            "kind": "lineending",
            "detail": "missing .gitattributes with `* text=auto eol=lf`",
        }]
    text = ga.read_text(encoding="utf-8", errors="replace")
    if not (EOL_ATTR_RE.search(text) and EOL_LINE_RE.search(text)):
        return [{
            "file": ".gitattributes",
            "kind": "lineending",
            "detail": ".gitattributes does not set `* text=auto eol=lf`",
        }]

    # Extract CRLF override patterns from .gitattributes (e.g. *.bat text eol=crlf)
    crlf_patterns: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "eol=crlf" in line:
            parts = line.split()
            if parts:
                crlf_patterns.append(parts[0])

    drifts: list[dict] = []
    for fpath in root.rglob("*"):
        try:
            rel_parts = fpath.relative_to(root).parts
        except ValueError:
            continue
        if any(part in SKIP_DIRS for part in rel_parts[:-1]):
            continue
        if not fpath.is_file():
            continue
        if fpath.suffix not in SOURCE_EXTENSIONS:
            continue

        rel_path = str(fpath.relative_to(root))
        rel_posix = fpath.relative_to(root).as_posix()

        # Respect .gitattributes override if pattern specifies eol=crlf
        if any(
            fnmatch.fnmatch(rel_posix, pat) or fnmatch.fnmatch(fpath.name, pat)
            for pat in crlf_patterns
        ):
            continue

        try:
            data = fpath.read_bytes()
            if b"\r\n" in data:
                drifts.append({
                    "file": rel_path,
                    "kind": "lineending",
                    "type": "lineending_drift",
                    "expected": "LF",
                    "found": "CRLF",
                    "detail": "file has CRLF line endings but .gitattributes specifies LF",
                })
        except OSError:
            continue

    return drifts
