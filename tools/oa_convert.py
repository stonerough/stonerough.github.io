#!/usr/bin/env python3
"""
EZproxy to OpenAthens URL Converter
University of Waikato Library

Reads a plain text or CSV file of URLs (one per line, or first column of CSV),
converts each to an OpenAthens redirector link, and writes a 3-column CSV:
  source_url, converted_url, notes

Usage:
  python3 oa_convert.py input.csv output.csv
  python3 oa_convert.py input.txt output.csv

Options:
  --plain   Convert plain URLs to OpenAthens without EZproxy cleaning
            (default is EZproxy cleaning mode)
"""

import sys
import re
import csv
import argparse
from pathlib import Path
from urllib.parse import unquote, urlparse, parse_qs, urlencode, urlunparse

OA_PREFIX = "https://go.openathens.net/redirector/waikato.ac.nz?url="
EZPROXY_HOST = "ezproxy.waikato.ac.nz"


def to_openathens(url: str) -> str:
    from urllib.parse import quote
    return OA_PREFIX + quote(url, safe="")


def clean_ezproxy_url(raw: str) -> tuple[str, list[str]]:
    """
    Clean an EZproxy URL down to the plain target URL.
    Returns (cleaned_url, notes).
    Raises ValueError with a reason if the URL is unresolvable.
    """
    url = raw.strip()
    notes = []

    # 1. Strip trailing &amp or &amp; (HTML entity bleed, truncated query string)
    if url.endswith("&amp;"):
        url = url[:-5]
        notes.append("Truncated &amp; stripped — query string may be incomplete")
    elif url.endswith("&amp"):
        url = url[:-4]
        notes.append("Truncated &amp stripped — query string may be incomplete")

    # 2. Handle Google redirect wrapper: google.com/url?q=<url>
    if re.match(r"^https?://(?:www\.)?google\.com/url\?", url, re.IGNORECASE):
        q_match = re.search(r"[?&]q=([^&]+)", url)
        if q_match:
            url = unquote(q_match.group(1))
            notes.append("Extracted from Google redirect wrapper")

    # 3. Detect completely broken inputs
    if re.search(r"location\.href", url, re.IGNORECASE) or re.search(r"javascript:", url, re.IGNORECASE):
        raise ValueError("JavaScript fragment — not a real URL")
    if not re.match(r"^https?://", url, re.IGNORECASE):
        raise ValueError("Does not start with http:// or https://")

    # 4. Strip EZproxy login wrapper — up to 2 layers for double-wrapped URLs
    for _ in range(2):
        login_match = re.match(
            r"^https?://ezproxy\.waikato\.ac\.nz/login\?q?url=(.+)$", url, re.IGNORECASE
        )
        if login_match:
            target = login_match.group(1)
            try:
                target = unquote(target)
            except Exception:
                pass
            notes.append("EZproxy login wrapper stripped")
            url = target
        else:
            break

    # 5. Convert proxied hostname: vendor-host.ezproxy.waikato.ac.nz -> vendor.host
    proxy_match = re.match(
        r"^(https?://)((?:[a-z0-9](?:[a-z0-9\-]*[a-z0-9])?\.)*(?:[a-z0-9\-]+))\.ezproxy\.waikato\.ac\.nz(/.*)?$",
        url, re.IGNORECASE
    )
    if proxy_match:
        scheme = proxy_match.group(1)
        proxied_host = proxy_match.group(2)
        rest = proxy_match.group(3) or ""
        real_host = proxied_host.replace("-", ".")
        url = scheme + real_host + rest
        if proxied_host != real_host:
            notes.append(f"Proxied hostname restored: {proxied_host} → {real_host}")

    # 6. Handle bare DOI (e.g. 10.1080/... without https://doi.org/ prefix)
    if re.match(r"^10\.\d{4,}/", url):
        url = "https://doi.org/" + url
        notes.append("Bare DOI — prefixed with https://doi.org/")

    # 7. Final sanity check
    if not re.match(r"^https?://[a-z0-9]", url, re.IGNORECASE):
        raise ValueError("Could not extract a valid URL after processing")

    return url, notes


def convert_line(raw: str, plain_mode: bool = False) -> tuple[str, str, str]:
    """
    Convert a single URL line.
    Returns (source, converted_url_or_empty, notes_or_reason).
    """
    source = raw.strip()
    if not source:
        return ("", "", "")

    if plain_mode:
        if not re.match(r"^https?://", source, re.IGNORECASE):
            return (source, "", "Does not start with http:// or https://")
        return (source, to_openathens(source), "")

    # EZproxy mode
    try:
        cleaned, notes = clean_ezproxy_url(source)
        # Routine proxy host restoration is not surfaced as a warning
        unusual_notes = [n for n in notes if not n.startswith("Proxied hostname restored")
                         and not n == "EZproxy login wrapper stripped"]
        converted = to_openathens(cleaned)
        return (source, converted, "; ".join(unusual_notes))
    except ValueError as e:
        return (source, "", str(e))


def read_input(path: Path) -> list[str]:
    """
    Read URLs from a .txt or .csv file.
    For CSV, extracts the first column, skipping a header row if the first
    line doesn't look like a URL.
    """
    text = path.read_text(encoding="utf-8-sig")  # utf-8-sig handles BOM if present
    lines = text.splitlines()

    if path.suffix.lower() == ".csv" or ("," in (lines[0] if lines else "")):
        # Extract first column
        reader = csv.reader(lines)
        rows = list(reader)
        # Skip header if first cell doesn't look like a URL
        if rows and not re.match(r"^https?://", rows[0][0].strip(), re.IGNORECASE):
            rows = rows[1:]
        return [row[0].strip() for row in rows if row and row[0].strip()]
    else:
        return [l.strip() for l in lines]


def main():
    parser = argparse.ArgumentParser(
        description="Convert EZproxy URLs to OpenAthens redirector links."
    )
    parser.add_argument("input", help="Input file (.txt or .csv)")
    parser.add_argument("output", help="Output CSV file")
    parser.add_argument(
        "--plain",
        action="store_true",
        help="Plain URL mode — wrap URLs in OpenAthens redirector without EZproxy cleaning",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"Error: input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    urls = read_input(input_path)
    if not urls:
        print("Error: no URLs found in input file.", file=sys.stderr)
        sys.exit(1)

    print(f"Processing {len(urls):,} URLs...", flush=True)

    results = [convert_line(u, plain_mode=args.plain) for u in urls]

    n_ok   = sum(1 for _, c, n in results if c and not n)
    n_warn = sum(1 for _, c, n in results if c and n)
    n_skip = sum(1 for _, c, _ in results if not c)

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["source_url", "converted_url", "notes"])
        for source, converted, notes in results:
            writer.writerow([source, converted, notes])

    print(f"\nConversion report")
    print(f"-----------------")
    print(f"Converted cleanly       : {n_ok:>6,}  ({n_ok/len(results)*100:.1f}%)")
    print(f"Converted with warnings : {n_warn:>6,}  ({n_warn/len(results)*100:.1f}%)")
    print(f"  Total converted       : {n_ok+n_warn:>6,}  ({(n_ok+n_warn)/len(results)*100:.1f}%)")
    print(f"Not converted (skipped) : {n_skip:>6,}  ({n_skip/len(results)*100:.1f}%)")
    print(f"  Total processed       : {len(results):>6,}")
    print(f"\nOutput written to: {output_path}")


if __name__ == "__main__":
    main()
