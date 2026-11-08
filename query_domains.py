#!/usr/bin/env python3
"""Check a domain or a file of domains against one or more target lists."""

import argparse
from pathlib import Path


def read_domains(path: Path) -> set[str]:
    """Read one domain per line, ignoring blank lines and # comments."""
    with path.open(encoding="utf-8-sig") as source:
        return {
            line.strip().lower()
            for line in source
            if line.strip() and not line.lstrip().startswith("#")
        }


def query_domains(domain_or_file: str | Path, target_file: str | Path) -> dict[str, bool]:
    """Return exact membership for each input domain (case insensitive)."""
    input_path = Path(domain_or_file)
    if input_path.is_file():
        domains = read_domains(input_path)
    elif isinstance(domain_or_file, Path):
        raise FileNotFoundError(f"Input file does not exist: {input_path}")
    else:
        domain = domain_or_file.strip().lower()
        if not domain:
            raise ValueError("Input domain must not be empty")
        domains = {domain}
    target = read_domains(Path(target_file))
    return {domain: domain in target for domain in sorted(domains)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="a single domain or a file with one domain per line")
    parser.add_argument("targets", nargs="+", type=Path, help="target blocklist file(s)")
    parser.add_argument(
        "--file", action="store_true", help="require the input to be an existing file"
    )
    parser.add_argument(
        "--missing-only", action="store_true",
        help="print only domains missing from every target, one per line",
    )
    args = parser.parse_args()
    try:
        source = Path(args.input) if args.file else args.input
        results = [query_domains(source, target) for target in args.targets]
    except (OSError, UnicodeError, ValueError) as error:
        parser.exit(1, f"Error: {error}\n")

    if args.missing_only:
        for domain in results[0]:
            if not any(result[domain] for result in results):
                print(domain)
        return 0

    print("\t".join(["domain", *(str(target) for target in args.targets)]))
    for domain in results[0]:
        print("\t".join([domain, *("included" if result[domain] else "missing" for result in results)]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
