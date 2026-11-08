#!/usr/bin/env python3
"""Download the Markdown links in public_list.md into res/<link name>.txt."""

import argparse
from collections import Counter
import re
import sys
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
LINK = re.compile(r"\[([^\]]+)\]\((https?://[^\s)]+)\)")


def normalize(name: str, content: str) -> str:
    lines = content.splitlines()
    if name in ["AntiAD","HaGeZiPro"]:
        lines = [line for line in lines if not line.startswith("#")]
    elif name == "AdRules":
        lines = [line.removeprefix("domain:") for line in lines]
    return "\n".join(lines) + ("\n" if lines else "")


def merge_lists(destination: Path, produce_duplicates: bool = False) -> None:
    """Merge source .txt files; report each domain occurring more than once."""
    merged = destination / "merged.txt"
    duplicates = destination / "duplicates.txt"
    counts = Counter()
    sources = sorted(
        path for path in destination.glob("*.txt")
        if path not in {merged, duplicates}
    )
    if not sources:
        raise ValueError(f"No downloaded lists found in {destination}")
    for path in sources:
        with path.open(encoding="utf-8") as source:
            counts.update(domain for line in source if (domain := line.strip()))

    def write_domains(path: Path, domains) -> None:
        temporary = path.with_suffix(".txt.tmp")
        temporary.write_text(
            "".join(f"{domain}\n" for domain in sorted(domains)), encoding="utf-8"
        )
        temporary.replace(path)

    write_domains(merged, counts)
    print(f"Saved {merged}: {len(counts)} unique domains")
    if produce_duplicates:
        repeated = [domain for domain, count in counts.items() if count > 1]
        write_domains(duplicates, repeated)
        print(f"Saved {duplicates}: {len(repeated)} duplicated domains")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--duplicates", action="store_true",
        help="also write sorted duplicated domains to res/duplicates.txt",
    )
    parser.add_argument(
        "--merge-only", action="store_true",
        help="merge existing downloads without downloading again",
    )
    args = parser.parse_args()
    destination = ROOT / "res"
    destination.mkdir(parents=True, exist_ok=True)
    if args.merge_only:
        merge_lists(destination, args.duplicates)
        return 0

    links = LINK.findall((ROOT / "public_list.md").read_text(encoding="utf-8"))
    if not links:
        print("No HTTP(S) Markdown links found in public_list.md.", file=sys.stderr)
        return 1

    failed = False
    for name, url in links:
        if name in {".", ".."} or any(char in name for char in '/\\\x00'):
            print(f"Invalid filename: {name!r}", file=sys.stderr)
            failed = True
            continue
        path = destination / f"{name}.txt"
        temporary = path.with_suffix(".txt.tmp")
        try:
            request = Request(url)
            with urlopen(request, timeout=60) as response:
                content = response.read().decode("utf-8-sig")
            temporary.write_text(normalize(name, content), encoding="utf-8")
            temporary.replace(path)
            print(f"Saved {path.relative_to(ROOT)}")
        except (OSError, URLError, UnicodeError) as error:
            temporary.unlink(missing_ok=True)
            print(f"Failed to download {name}: {error}", file=sys.stderr)
            failed = True
    if not failed:
        merge_lists(destination, args.duplicates)
    return int(failed)


if __name__ == "__main__":
    sys.exit(main())
