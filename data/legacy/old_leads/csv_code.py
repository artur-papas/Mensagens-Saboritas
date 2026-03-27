import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mensagens_saboritas.data.csv_tools import aggregate_csvs, subtract_csv


def default_paths() -> tuple[Path, Path]:
    script_dir = Path(__file__).resolve().parent
    source_dir = script_dir
    output_file = ROOT / "data" / "generated" / "LEADS_agregated.csv"
    return source_dir, output_file


def parse_args(argv: list[str]) -> argparse.Namespace:
    src_default, out_default = default_paths()
    parser = argparse.ArgumentParser(
        description=(
            "Aggregate all CSV files in 'old_leads' (no headers, single column) "
            "into a single LEADS_agregated.csv."
        )
    )
    parser.add_argument("--source", type=Path, default=src_default)
    parser.add_argument("--output", type=Path, default=out_default)
    parser.add_argument("--pattern", type=str, default="*.csv")
    parser.add_argument("--include-empty", action="store_true")
    parser.add_argument("--no-dedupe", dest="dedupe", action="store_false")
    parser.set_defaults(dedupe=True)
    parser.add_argument("--subtract", action="store_true")
    parser.add_argument("--base", type=Path, default=(ROOT / "data" / "generated" / "LEADS_agregated.csv"))
    parser.add_argument("--exclude", type=Path, default=(ROOT / "data" / "reference" / "LEADS TOTAL.csv"))
    parser.add_argument("--subtract-output", type=Path, default=(ROOT / "data" / "generated" / "leads_subtracted.csv"))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])

    if args.subtract:
        summary = subtract_csv(
            base_file=args.base,
            exclude_file=args.exclude,
            output_file=args.subtract_output,
            include_empty=args.include_empty,
            dedupe_output=True,
        )
        print("Subtraction complete.")
        print(f"Output: {summary['output']}")
        print(
            f"Written: {summary['written']} | "
            f"Excluded: {summary['skipped_excluded']} | "
            f"Skipped empty: {summary['skipped_empty']}"
        )
        return 0

    summary = aggregate_csvs(
        source_dir=args.source,
        output_file=args.output,
        include_empty=args.include_empty,
        dedupe=args.dedupe,
        pattern=args.pattern,
    )
    print("Aggregation complete.")
    print(f"Output: {summary['output']}")
    print(f"Total lines written: {summary['total_lines_written']}")
    if summary["deduped"]:
        print(f"Duplicate lines skipped: {summary['deduped']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
