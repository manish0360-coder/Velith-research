"""Static process/network policy for the in-stage ``egrid`` package (defence in depth).

Contract §12.3 lists socket, http, urllib, requests, ssl, ftplib, smtplib, subprocess. M-H0 adds
process-creation paths (multiprocessing, concurrent, pty, os.fork/system/popen/spawn*/exec*/
posix_spawn*) because a child process would escape per-process RLIMIT_CPU accounting. The added
entries are a stricter check pending RD class-(b) acceptance; the aggregate CPU guarantee does not
rest on this test (it rests on the host monitor).
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent / "egrid"
DENIED_MODULES = {
    "socket", "http", "urllib", "requests", "ssl", "ftplib", "smtplib", "subprocess",
    "multiprocessing", "concurrent", "pty", "asyncio",
}
DENIED_OS_PREFIXES = ("fork", "system", "popen", "spawn", "exec", "posix_spawn")


def violations(source: str) -> list[str]:
    found = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            found += [a.name for a in node.names if a.name.split(".")[0] in DENIED_MODULES]
        elif isinstance(node, ast.ImportFrom):
            mod = (node.module or "").split(".")[0]
            if mod in DENIED_MODULES:
                found.append(node.module or "")
            if mod == "os":
                found += [f"os.{a.name}" for a in node.names if a.name.startswith(DENIED_OS_PREFIXES)]
        elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "os":
            if node.attr.startswith(DENIED_OS_PREFIXES):
                found.append(f"os.{node.attr}")
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("__import__", "exec", "eval"):
            found.append(node.func.id)
    return found


class TestPolicy(unittest.TestCase):
    def test_package_has_no_denied_imports_or_calls(self) -> None:
        files = sorted(PKG.glob("*.py"))
        self.assertTrue(files)
        bad = {f.name: v for f in files if (v := violations(f.read_text(encoding="utf-8")))}
        self.assertEqual(bad, {})

    def test_scanner_detects_violations(self) -> None:
        src = "import subprocess\nfrom multiprocessing import Pool\nimport os\nos.fork()\nos.execv('x', [])\nfrom os import system\n"
        self.assertEqual(len(violations(src)), 5)


if __name__ == "__main__":
    unittest.main()
