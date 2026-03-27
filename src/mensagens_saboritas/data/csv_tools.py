from __future__ import annotations

from pathlib import Path


def aggregate_csvs(
    source_dir: Path,
    output_file: Path,
    include_empty: bool = False,
    dedupe: bool = False,
    pattern: str = "*.csv",
) -> dict:
    if not source_dir.is_dir():
        raise FileNotFoundError(f"Source directory not found: {source_dir}")

    output_file.parent.mkdir(parents=True, exist_ok=True)
    files = sorted([path for path in source_dir.glob(pattern) if path.is_file()])
    files = [path for path in files if path.resolve() != output_file.resolve()]

    if not files:
        return {
            "files": [],
            "total_lines_written": 0,
            "skipped_empty": 0,
            "deduped": 0,
            "output": str(output_file),
        }

    total_written = 0
    total_skipped_empty = 0
    total_deduped = 0
    per_file_counts: dict[str, dict[str, int]] = {}
    seen = set() if dedupe else None

    with output_file.open("w", encoding="utf-8", newline="\n") as out_fp:
        for csv_path in files:
            written_this = 0
            skipped_empty_this = 0
            deduped_this = 0

            with csv_path.open("r", encoding="utf-8-sig", errors="ignore") as in_fp:
                for raw_line in in_fp:
                    line = raw_line.strip()
                    if not include_empty and line == "":
                        skipped_empty_this += 1
                        continue
                    if seen is not None:
                        if line in seen:
                            deduped_this += 1
                            continue
                        seen.add(line)
                    out_fp.write(line + "\n")
                    written_this += 1

            per_file_counts[csv_path.name] = {
                "written": written_this,
                "skipped_empty": skipped_empty_this,
                "deduped": deduped_this,
            }
            total_written += written_this
            total_skipped_empty += skipped_empty_this
            total_deduped += deduped_this

    return {
        "files": per_file_counts,
        "total_lines_written": total_written,
        "skipped_empty": total_skipped_empty,
        "deduped": total_deduped,
        "output": str(output_file),
    }


def subtract_csv(
    base_file: Path,
    exclude_file: Path,
    output_file: Path,
    include_empty: bool = False,
    dedupe_output: bool = True,
) -> dict:
    if not base_file.is_file():
        raise FileNotFoundError(f"Base file not found: {base_file}")
    if not exclude_file.is_file():
        raise FileNotFoundError(f"Exclude file not found: {exclude_file}")

    output_file.parent.mkdir(parents=True, exist_ok=True)

    exclude_set = set()
    excluded_empty = 0
    with exclude_file.open("r", encoding="utf-8-sig", errors="ignore") as ex_fp:
        for raw in ex_fp:
            line = raw.strip()
            if not include_empty and line == "":
                excluded_empty += 1
                continue
            exclude_set.add(line)

    written = 0
    skipped_empty = 0
    skipped_excluded = 0
    skipped_dupe_out = 0
    seen_out = set() if dedupe_output else None

    with base_file.open("r", encoding="utf-8-sig", errors="ignore") as base_fp, output_file.open(
        "w",
        encoding="utf-8",
        newline="\n",
    ) as out_fp:
        for raw in base_fp:
            line = raw.strip()
            if not include_empty and line == "":
                skipped_empty += 1
                continue
            if line in exclude_set:
                skipped_excluded += 1
                continue
            if seen_out is not None:
                if line in seen_out:
                    skipped_dupe_out += 1
                    continue
                seen_out.add(line)
            out_fp.write(line + "\n")
            written += 1

    return {
        "output": str(output_file),
        "written": written,
        "skipped_empty": skipped_empty,
        "skipped_excluded": skipped_excluded,
        "skipped_dupe_out": skipped_dupe_out,
        "exclude_size": len(exclude_set),
        "excluded_empty_in_exclude_file": excluded_empty,
    }
