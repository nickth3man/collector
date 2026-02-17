"""Copy each AGENTS.md to a CLAUDE.md in the same directory."""

from __future__ import annotations

import shutil
from pathlib import Path


def copy_agents_to_claude(root: Path) -> None:
    for agents_file in root.rglob("AGENTS.md"):
        claude_file = agents_file.parent / "CLAUDE.md"
        shutil.copy2(agents_file, claude_file)
        print(f"Copied {agents_file.relative_to(root)} -> {claude_file.relative_to(root)}")


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parent.parent
    copy_agents_to_claude(repo_root)
    print("Done.")
