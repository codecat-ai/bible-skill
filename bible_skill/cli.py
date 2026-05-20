from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from bible_skill.extract import ExtractedReference, extract_references
from bible_skill.providers import BibleApiClient, FreeUseBibleApiClient, ProviderError
from bible_skill.query import PassageResult, QueryError, query_passage, render_markdown, render_usfm
from bible_skill.release_check import check_release_readiness, render_release_check_text
from bible_skill.search import search_installed
from bible_skill.skill_template import render_skill
from bible_skill.store import Store


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except FileNotFoundError as exc:
        print(f"Missing local translation: {exc}", file=sys.stderr)
        return 2
    except ProviderError as exc:
        print(f"Error: {_format_provider_error(args, exc)}", file=sys.stderr)
        return 2
    except (QueryError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bible-skill")
    parser.add_argument("--data-dir", help="Directory for downloaded translation data.")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--data-dir", default=argparse.SUPPRESS, help="Directory for downloaded translation data.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    translations = subparsers.add_parser("translations", parents=[common], help="List available translations.")
    translations.add_argument("--query", help="Filter by id or name.")
    translations.add_argument("--language", help="Filter by language.")
    translations.add_argument("--json", action="store_true", help="Output JSON.")
    translations.set_defaults(func=_translations)

    download = subparsers.add_parser("download", parents=[common], help="Download a complete translation.")
    download.add_argument("translation_id")
    download.add_argument("--force", action="store_true")
    download.add_argument("--json", action="store_true")
    download.set_defaults(func=_download)

    installed = subparsers.add_parser("installed", parents=[common], help="List installed translations.")
    installed.add_argument("--json", action="store_true")
    installed.set_defaults(func=_installed)

    validate = subparsers.add_parser("validate", parents=[common], help="Validate installed translation cache files.")
    validate.add_argument("translation_ids", nargs="*", help="Translation IDs to validate. Defaults to all installed.")
    validate.add_argument("--json", action="store_true", help="Output JSON.")
    validate.set_defaults(func=_validate)

    cache = subparsers.add_parser("cache", parents=[common], help="Inspect local translation cache data.")
    cache_subparsers = cache.add_subparsers(dest="cache_command", required=True)
    cache_manifest = cache_subparsers.add_parser(
        "manifest", parents=[common], help="Inspect a portable local cache manifest."
    )
    cache_manifest.add_argument("--json", action="store_true", help="Output JSON.")
    cache_manifest.set_defaults(func=_cache_manifest)

    release = subparsers.add_parser("release", help="Inspect source-checkout release readiness.")
    release_subparsers = release.add_subparsers(dest="release_command", required=True)
    release_check = release_subparsers.add_parser(
        "check",
        help="Check source checkout release readiness without publishing.",
        description="Check source checkout release readiness without publishing.",
    )
    release_check.add_argument("--root", default=".", help="Source checkout root to inspect.")
    release_check.add_argument(
        "--dist-dir",
        help="Built artifact directory to inspect. Defaults to ROOT/dist if present.",
    )
    release_check.add_argument("--json", action="store_true", help="Output JSON.")
    release_check.set_defaults(func=_release_check)

    search = subparsers.add_parser("search", parents=[common], help="Search installed translation metadata.")
    search.add_argument("query")
    search.add_argument("--json", action="store_true")
    search.set_defaults(func=_search)

    query = subparsers.add_parser("query", parents=[common], help="Query a local translation.")
    query.add_argument("translation_id")
    query.add_argument("reference")
    query_output = query.add_mutually_exclusive_group()
    query_output.add_argument("--json", action="store_true")
    query_output.add_argument("--markdown", action="store_true", help="Output note-friendly Markdown.")
    query_output.add_argument("--usfm", action="store_true", help="Output minimal USFM-like text.")
    query.add_argument("--attribution", action="store_true", help="Include local translation license/source metadata.")
    query.set_defaults(func=_query)

    compare = subparsers.add_parser("compare", parents=[common], help="Compare a passage across local translations.")
    compare.add_argument("reference")
    compare.add_argument("translation_ids", nargs="+", help="Two or more installed translation IDs to compare.")
    compare_output = compare.add_mutually_exclusive_group()
    compare_output.add_argument("--json", action="store_true")
    compare_output.add_argument("--markdown", action="store_true")
    compare_output.add_argument("--csv", action="store_true")
    compare.add_argument("--attribution", action="store_true", help="Include per-translation license/source metadata.")
    compare.set_defaults(func=_compare)

    live = subparsers.add_parser("live", parents=[common], help="Query bible-api.com without local data.")
    live.add_argument("reference")
    live.add_argument("--translation", default="web")
    live.add_argument("--timeout", default=30.0, type=_positive_float, metavar="SECONDS")
    live.add_argument("--retries", default=0, type=_nonnegative_int, metavar="COUNT")
    live_output = live.add_mutually_exclusive_group()
    live_output.add_argument("--json", action="store_true")
    live_output.add_argument("--markdown", action="store_true")
    live_output.add_argument("--csv", action="store_true")
    live.set_defaults(func=_live)

    skill = subparsers.add_parser("skill", parents=[common], help="Print a Hermes-compatible SKILL.md.")
    skill.set_defaults(func=_skill)

    extract = subparsers.add_parser("extract", help="Extract Bible references from text or a local file.")
    extract_input = extract.add_mutually_exclusive_group(required=True)
    extract_input.add_argument("--text", help="Text to scan for Bible references.")
    extract_input.add_argument("--file", help="Local UTF-8 text or Markdown file to scan.")
    extract_output = extract.add_mutually_exclusive_group()
    extract_output.add_argument("--json", action="store_true", help="Output JSON.")
    extract_output.add_argument("--markdown", action="store_true", help="Output a note-friendly Markdown summary.")
    extract_output.add_argument("--csv", action="store_true", help="Output spreadsheet-friendly CSV rows.")
    extract.set_defaults(func=_extract)
    return parser


def _translations(args: argparse.Namespace) -> int:
    rows = FreeUseBibleApiClient().translations()
    rows = _filter_translations(rows, args.query, args.language)
    if args.json:
        _print_json(rows)
    else:
        for row in rows:
            print(f"{row.get('id', '')}\t{row.get('name', '')}\t{row.get('language', '')}")
    return 0


def _download(args: argparse.Namespace) -> int:
    record = Store(args.data_dir).download(args.translation_id, FreeUseBibleApiClient(), force=args.force)
    if args.json:
        _print_json(record.to_dict())
    else:
        print(f"{record.translation_id}\t{record.name}\t{record.book_count} books\t{record.verse_count} verses")
    return 0


def _installed(args: argparse.Namespace) -> int:
    rows = [record.to_dict() for record in Store(args.data_dir).installed()]
    if args.json:
        _print_json(rows)
    else:
        for row in rows:
            print(
                f"{row['translation_id']}\t{row['name']}\t"
                f"{row['book_count']} books\t{row['chapter_count']} chapters\t{row['verse_count']} verses"
            )
    return 0


def _validate(args: argparse.Namespace) -> int:
    store = Store(args.data_dir)
    translation_ids = list(args.translation_ids) or store.cached_translation_ids()
    results = [store.validate_translation(translation_id) for translation_id in translation_ids]
    if args.json:
        _print_json([result.to_dict() for result in results])
    else:
        for result in results:
            status = "ok" if result.ok else "invalid"
            issue_text = "" if result.ok else "\t" + "; ".join(result.issues)
            print(f"{result.translation_id}\t{status}\t{result.checksum}{issue_text}")
    return 0 if all(result.ok for result in results) else 2


def _cache_manifest(args: argparse.Namespace) -> int:
    manifest = Store(args.data_dir).cache_manifest()
    if args.json:
        _print_json(manifest)
    else:
        print(_render_cache_manifest_text(manifest))
    return 0


def _release_check(args: argparse.Namespace) -> int:
    result = check_release_readiness(args.root, args.dist_dir)
    if args.json:
        _print_json(result)
    else:
        print(render_release_check_text(result))
    return 0 if result["ok"] else 2


def _search(args: argparse.Namespace) -> int:
    rows = [record.to_dict() for record in search_installed(Store(args.data_dir).installed(), args.query)]
    if args.json:
        _print_json(rows)
    else:
        for row in rows:
            print(f"{row['translation_id']}\t{row['name']}\t{row['language']}\t{row['verse_count']} verses")
    return 0


def _query(args: argparse.Namespace) -> int:
    translation = Store(args.data_dir).load_translation(args.translation_id)
    result = query_passage(translation, args.reference)
    if args.json:
        _print_json(result.to_dict(include_attribution=args.attribution))
    elif args.markdown:
        print(render_markdown(result, include_attribution=args.attribution))
    elif args.usfm:
        print(render_usfm(result, include_attribution=args.attribution))
    else:
        print(f"{result.translation_id} {result.normalized_reference}")
        if args.attribution:
            for line in _attribution_lines(result.attribution):
                print(line)
        for verse in result.verses:
            print(f"{verse.reference} {verse.text}")
    return 0


def _compare(args: argparse.Namespace) -> int:
    if len(args.translation_ids) < 2:
        raise QueryError("Compare requires at least two translation IDs.")

    store = Store(args.data_dir)
    results = [
        query_passage(store.load_translation(translation_id), args.reference) for translation_id in args.translation_ids
    ]
    reference = results[0].normalized_reference
    if args.json:
        _print_json(
            {
                "reference": reference,
                "translations": [
                    _compare_result_dict(result, include_attribution=args.attribution) for result in results
                ],
            }
        )
    elif args.markdown:
        print(_render_compare_markdown(reference, results, include_attribution=args.attribution))
    elif args.csv:
        sys.stdout.write(_render_compare_csv(reference, results, include_attribution=args.attribution))
    else:
        print(reference)
        for result in results:
            print(f"[{result.translation_id}] {result.translation_name}")
            if args.attribution:
                for line in _attribution_lines(result.attribution):
                    print(line)
            for verse in result.verses:
                print(f"{verse.reference} {verse.text}")
    return 0


def _live(args: argparse.Namespace) -> int:
    payload = BibleApiClient().passage(args.reference, args.translation, timeout=args.timeout, retries=args.retries)
    if args.json:
        _print_json(payload)
    elif args.markdown:
        print(_render_live_markdown(payload, args.reference))
    elif args.csv:
        sys.stdout.write(_render_live_csv(payload, args.reference))
    else:
        print(payload.get("reference", args.reference))
        print(payload.get("text", "").strip())
    return 0


def _format_provider_error(args: argparse.Namespace, exc: ProviderError) -> str:
    message = str(exc)
    if args.command == "live" and args.retries == 0 and exc.retryable:
        return f"{message}\nHint: transient provider failures may succeed if you retry with `--retries 2`."
    return message


def _positive_float(value: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a positive number of seconds") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive number of seconds")
    return parsed


def _nonnegative_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a non-negative integer") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be a non-negative integer")
    return parsed


def _skill(args: argparse.Namespace) -> int:
    store = Store(args.data_dir)
    print(render_skill(str(store.data_dir)))
    return 0


def _extract(args: argparse.Namespace) -> int:
    if args.file:
        try:
            text = Path(args.file).read_text(encoding="utf-8")
        except FileNotFoundError as exc:
            raise OSError(f"Input file not found: {args.file}") from exc
    else:
        text = args.text

    rows = extract_references(text)
    if args.json:
        _print_json([row.to_dict() for row in rows])
    elif args.markdown:
        print(_render_extract_markdown(text, rows))
    elif args.csv:
        sys.stdout.write(_render_extract_csv(text, rows))
    else:
        for row in rows:
            print(row.normalized_reference)
    return 0


def _filter_translations(rows: list[dict[str, Any]], query: str | None, language: str | None) -> list[dict[str, Any]]:
    filtered = rows
    if query:
        needle = query.casefold()
        filtered = [
            row
            for row in filtered
            if needle in str(row.get("id", "")).casefold() or needle in str(row.get("name", "")).casefold()
        ]
    if language:
        lang = language.casefold()
        filtered = [row for row in filtered if str(row.get("language", "")).casefold() == lang]
    return filtered


def _compare_result_dict(result: PassageResult, *, include_attribution: bool = False) -> dict[str, Any]:
    payload = {
        "translation_id": result.translation_id,
        "translation_name": result.translation_name,
        "verses": [verse.__dict__ for verse in result.verses],
    }
    if include_attribution and result.attribution:
        payload["attribution"] = result.attribution
    return payload


def _render_compare_markdown(
    reference: str, results: Sequence[PassageResult], *, include_attribution: bool = False
) -> str:
    lines = [f"# {_markdown_text(reference)}"]
    for result in results:
        lines.extend(
            [
                "",
                f"## {_markdown_text(result.translation_id)} — {_markdown_text(result.translation_name)}",
                "",
            ]
        )
        if include_attribution:
            lines.extend(f"> {_markdown_text(line)}" for line in _attribution_lines(result.attribution))
            if result.attribution:
                lines.append("")
        for verse in result.verses:
            lines.append(f"- **{_markdown_text(verse.reference)}** {_markdown_text(verse.text)}")
    return "\n".join(lines)


def _render_live_markdown(payload: dict[str, Any], requested_reference: str) -> str:
    body = _live_payload_body(payload)
    reference = str(body.get("reference") or requested_reference)
    lines = [f"# {_markdown_text(reference)}", ""]
    verses = _live_usable_verses(body)
    if verses:
        for verse in verses:
            verse_reference = _live_verse_reference(verse)
            lines.append(f"- **{_markdown_text(verse_reference)}** {_markdown_text(_live_text(verse))}")
    else:
        lines.append(f"- **{_markdown_text(reference)}** {_markdown_text(_live_text(body))}")
    return "\n".join(lines)


def _render_extract_markdown(text: str, rows: Sequence[ExtractedReference]) -> str:
    lines = ["# Extracted Bible references", ""]
    if not rows:
        lines.append("No Bible references found.")
        return "\n".join(lines)

    for row in rows:
        context = _extract_source_context(text, row.start, row.end)
        if context:
            lines.append(f"- **{_markdown_text(row.normalized_reference)}** {_markdown_text(context)}")
        else:
            lines.append(f"- **{_markdown_text(row.normalized_reference)}**")
    return "\n".join(lines)


def _extract_source_context(text: str, start: int, end: int) -> str:
    line_start = text.rfind("\n", 0, start) + 1
    line_end = text.find("\n", end)
    if line_end == -1:
        line_end = len(text)
    return text[line_start:line_end].strip()


def _render_extract_csv(text: str, rows: Sequence[ExtractedReference]) -> str:
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(["reference", "book", "chapter", "start_verse", "end_verse", "start", "end", "context"])
    for row in rows:
        writer.writerow(
            [
                row.normalized_reference,
                row.book_name,
                row.start_chapter,
                row.start_verse or "",
                row.end_verse or "",
                row.start,
                row.end,
                _extract_source_context(text, row.start, row.end),
            ]
        )
    return output.getvalue()


def _render_cache_manifest_text(manifest: dict[str, Any]) -> str:
    lines = [f"Cache manifest for {manifest['data_dir']}"]
    translations = manifest["translations"]
    if not translations:
        lines.append("No cached translations found.")
        return "\n".join(lines)
    for row in translations:
        status = "ok" if row["validation_ok"] else "invalid"
        detail = row["checksum"] if row["validation_ok"] else "; ".join(row["issues"])
        lines.append(f"{row['id']}\t{status}\t{row['relative_path']}\t{detail}")
    return "\n".join(lines)


def _render_live_csv(payload: dict[str, Any], requested_reference: str) -> str:
    body = _live_payload_body(payload)
    reference = str(body.get("reference") or requested_reference)
    translation = str(body.get("translation_id") or body.get("translation") or "")
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(["reference", "translation", "verse_reference", "text"])

    usable_verses = _live_usable_verses(body)
    if usable_verses:
        for verse in usable_verses:
            writer.writerow([reference, translation, _live_verse_reference(verse), _live_text(verse)])
    else:
        writer.writerow([reference, translation, reference, _live_text(body)])
    return output.getvalue()


def _live_payload_body(payload: dict[str, Any]) -> dict[str, Any]:
    data = payload.get("data")
    return data if isinstance(data, dict) else payload


def _live_usable_verses(payload: dict[str, Any]) -> list[dict[str, Any]]:
    verses = payload.get("verses") or payload.get("passages")
    return [verse for verse in verses if isinstance(verse, dict)] if isinstance(verses, list) else []


def _live_verse_reference(verse: dict[str, Any]) -> str:
    reference = verse.get("reference")
    if reference:
        return str(reference)
    book_name = verse.get("book_name") or verse.get("book")
    chapter = verse.get("chapter")
    verse_number = verse.get("verse")
    if book_name and chapter and verse_number:
        return f"{book_name} {chapter}:{verse_number}"
    return ""


def _live_text(value: Any) -> str:
    if isinstance(value, dict):
        for key in ("text", "content", "verse_text"):
            if key in value:
                return _live_text(value[key])
        return ""
    if isinstance(value, list):
        return " ".join(part for part in (_live_text(item).strip() for item in value) if part)
    return str(value)


def _render_compare_csv(reference: str, results: Sequence[PassageResult], *, include_attribution: bool = False) -> str:
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    if include_attribution:
        writer.writerow(
            ["reference", "translation_id", "translation_name", "license_url", "source_url", "verse_reference", "text"]
        )
    else:
        writer.writerow(["reference", "translation_id", "translation_name", "verse_reference", "text"])
    for result in results:
        for verse in result.verses:
            if include_attribution:
                writer.writerow(
                    [
                        reference,
                        result.translation_id,
                        result.translation_name,
                        result.attribution.get("license_url", ""),
                        result.attribution.get("source_url", ""),
                        verse.reference,
                        verse.text,
                    ]
                )
            else:
                writer.writerow(
                    [reference, result.translation_id, result.translation_name, verse.reference, verse.text]
                )
    return output.getvalue()


def _attribution_lines(attribution: dict[str, str]) -> list[str]:
    labels = {
        "license_url": "License",
        "source_url": "Source",
    }
    return [f"{labels[key]}: {attribution[key]}" for key in ("license_url", "source_url") if key in attribution]


def _markdown_text(value: str) -> str:
    text = " ".join(str(value).split())
    escaped = text.replace("\\", "\\\\")
    for char in ("`", "*", "_", "[", "]", "#", "|", "<", ">"):
        escaped = escaped.replace(char, f"\\{char}")
    return escaped.replace("- ", "\\- ")


def _print_json(payload: Any) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    raise SystemExit(main())
