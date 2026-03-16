"""
Shared utilities for multi-agent workflows.
"""

from pathlib import Path


def load_instructions(path) -> dict[str, str]:
    """Load agent instructions from a .txt file with [agent_name] sections."""
    sections: dict[str, str] = {}
    current: str | None = None
    lines: list[str] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.startswith("[") and line.endswith("]"):
            if current is not None:
                sections[current] = "\n".join(lines).strip()
            current = line[1:-1]
            lines = []
        else:
            lines.append(line)
    if current is not None:
        sections[current] = "\n".join(lines).strip()
    return sections
