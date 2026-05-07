"""Search and filter env keys across vault files."""

import re
from dataclasses import dataclass, field
from typing import List, Optional

from envault.vault import parse_env, unlock


@dataclass
class SearchResult:
    key: str
    value: str
    masked: bool = False


@dataclass
class FileSearchResult:
    vault_path: str
    matches: List[SearchResult] = field(default_factory=list)

    def has_matches(self) -> bool:
        return len(self.matches) > 0


def search_vault(
    vault_path: str,
    key: str,
    pattern: Optional[str] = None,
    mask_values: bool = True,
) -> FileSearchResult:
    """Search a vault file for keys matching a name or pattern.

    Args:
        vault_path: Path to the encrypted .vault file.
        key: Encryption key used to unlock the vault.
        pattern: Optional regex pattern to match against env key names.
        mask_values: If True, mask values in results (default True).

    Returns:
        FileSearchResult with all matching entries.
    """
    plaintext = unlock(vault_path, key)
    env = parse_env(plaintext)

    results: List[SearchResult] = []
    compiled = re.compile(pattern, re.IGNORECASE) if pattern else None

    for k, v in env.items():
        if compiled is not None:
            if not compiled.search(k):
                continue
        masked_value = "***" if mask_values else v
        results.append(SearchResult(key=k, value=masked_value, masked=mask_values))

    return FileSearchResult(vault_path=vault_path, matches=results)


def search_multiple_vaults(
    vault_paths: List[str],
    key: str,
    pattern: Optional[str] = None,
    mask_values: bool = True,
) -> List[FileSearchResult]:
    """Search across multiple vault files."""
    results = []
    for path in vault_paths:
        try:
            result = search_vault(path, key, pattern=pattern, mask_values=mask_values)
            results.append(result)
        except Exception as exc:
            results.append(
                FileSearchResult(
                    vault_path=path,
                    matches=[SearchResult(key="__error__", value=str(exc))],
                )
            )
    return results


def format_search_results(results: List[FileSearchResult]) -> str:
    """Format search results for display."""
    lines = []
    for file_result in results:
        lines.append(f"[{file_result.vault_path}]")
        if not file_result.has_matches():
            lines.append("  (no matches)")
        else:
            for match in file_result.matches:
                indicator = "[masked]" if match.masked else ""
                lines.append(f"  {match.key} = {match.value} {indicator}".rstrip())
        lines.append("")
    return "\n".join(lines).rstrip()
