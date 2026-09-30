import csv
import shutil
from pathlib import Path


INPUT_FOLDER = Path(r"C:\Path\To\Input")
OUTPUT_FOLDER = Path(r"C:\Path\To\Output")

DELIMITER = "^"
ENCODING = "cp1252"

# Maximum columns in the generated file itself.
# Leaves room below SQL Server's 1024-column limit
# for columns added by the import program.
MAX_OUTPUT_COLUMNS = 1000

ROW_ID_COLUMN = "ROW_ID"


def get_header(input_file: Path):
    with input_file.open("r", encoding=ENCODING, newline="") as infile:
        clean_lines = (line.replace("\x00", "") for line in infile)

        reader = csv.reader(
            clean_lines,
            delimiter=DELIMITER,
            quotechar='"'
        )

        try:
            return next(reader)
        except StopIteration:
            return None


def split_wide_file(input_file: Path, output_base: Path, header):
    # Reserve one output column for ROW_ID
    source_columns_per_file = MAX_OUTPUT_COLUMNS - 1

    header_chunks = [
        header[i:i + source_columns_per_file]
        for i in range(0, len(header), source_columns_per_file)
    ]

    print(
        f"Splitting: {input_file} "
        f"({len(header):,} columns -> {len(header_chunks)} files)"
    )

    output_files = []
    writers = []

    try:
        for part_number, header_chunk in enumerate(header_chunks, start=1):

            output_file = (
                output_base.parent
                / f"{output_base.stem}_part{part_number}{output_base.suffix}"
            )

            output_file.parent.mkdir(parents=True, exist_ok=True)

            outfile = output_file.open(
                "w",
                encoding=ENCODING,
                newline=""
            )

            writer = csv.writer(
                outfile,
                delimiter=DELIMITER,
                quotechar='"',
                quoting=csv.QUOTE_ALL,
                lineterminator="\n"
            )

            writer.writerow([ROW_ID_COLUMN] + header_chunk)

            output_files.append(outfile)
            writers.append(writer)

        with input_file.open("r", encoding=ENCODING, newline="") as infile:
            clean_lines = (line.replace("\x00", "") for line in infile)

            reader = csv.reader(
                clean_lines,
                delimiter=DELIMITER,
                quotechar='"'
            )

            # Skip original header
            next(reader, None)

            for row_id, row in enumerate(reader, start=1):

                for i, writer in enumerate(writers):
                    start = i * source_columns_per_file
                    end = start + source_columns_per_file

                    writer.writerow(
                        [row_id] + row[start:end]
                    )

                if row_id % 100000 == 0:
                    print(
                        f"  Processed {row_id:,} rows "
                        f"from {input_file.name}"
                    )

    finally:
        for outfile in output_files:
            outfile.close()


def copy_normal_file(input_file: Path, output_file: Path):
    output_file.parent.mkdir(parents=True, exist_ok=True)

    shutil.copy2(input_file, output_file)

    print(f"Copied unchanged: {input_file}")


def process_file(input_file: Path):
    relative_path = input_file.relative_to(INPUT_FOLDER)
    output_file = OUTPUT_FOLDER / relative_path

    header = get_header(input_file)

    if header is None:
        print(f"Skipped empty file: {input_file}")
        return

    column_count = len(header)

    print(f"Checking: {input_file}")
    print(f"  Columns: {column_count:,}")

    # If the source file already fits comfortably below the limit,
    # copy it unchanged.
    if column_count <= MAX_OUTPUT_COLUMNS:
        copy_normal_file(input_file, output_file)

    else:
        split_wide_file(
            input_file,
            output_file,
            header
        )


def main():
    csv_files = list(INPUT_FOLDER.rglob("*.csv"))

    print(f"Found {len(csv_files):,} CSV files.\n")

    for input_file in csv_files:
        process_file(input_file)

    print("\nProcessing complete.")


if __name__ == "__main__":
    main()