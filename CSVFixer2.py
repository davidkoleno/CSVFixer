from pathlib import Path


DELIMITER = "|"
QUOTE = '"'
FILE_PATTERN = "*.txt"


def validate_record(line, expected_columns):
    """
    Validate pipe-delimited record quote structure.

    Returns:
        (True, None) if valid
        (False, reason) if invalid
    """

    record = line.rstrip("\r\n")

    in_quotes = False
    at_field_start = True
    just_closed_quote = False
    column_count = 1

    i = 0

    while i < len(record):
        char = record[i]

        # Inside a quoted field
        if in_quotes:
            if char == QUOTE:

                # Properly escaped quote: ""
                if i + 1 < len(record) and record[i + 1] == QUOTE:
                    i += 2
                    continue

                # Otherwise this closes the quoted field
                in_quotes = False
                just_closed_quote = True
                i += 1
                continue

            i += 1
            continue

        # Just closed a quoted field
        if just_closed_quote:
            if char == DELIMITER:
                column_count += 1
                at_field_start = True
                just_closed_quote = False
                i += 1
                continue

            return False, (
                f"Unexpected character '{char}' after closing quote"
            )

        # Outside quotes
        if char == DELIMITER:
            column_count += 1
            at_field_start = True
            i += 1
            continue

        if char == QUOTE:

            # Quote is only valid at the beginning of a field
            if at_field_start:
                in_quotes = True
                at_field_start = False
                i += 1
                continue

            return False, "Quote found in middle of unquoted field"

        at_field_start = False
        i += 1

    # End-of-record checks
    if in_quotes:
        return False, "Quoted field was never closed"

    if column_count != expected_columns:
        return False, (
            f"Wrong column count: expected {expected_columns}, "
            f"found {column_count}"
        )

    return True, None


def count_header_columns(header):
    return len(header.rstrip("\r\n").split(DELIMITER))


def process_file(file_path):

    good_file = file_path.with_name(
        f"{file_path.stem}_good{file_path.suffix}"
    )

    bad_file = file_path.with_name(
        f"{file_path.stem}_bad{file_path.suffix}"
    )

    good_count = 0
    bad_count = 0
    total_records = 0

    print(f"\nChecking: {file_path.name}")

    with file_path.open(
        "r",
        encoding="utf-8",
        errors="replace",
        newline=""
    ) as infile:

        header = infile.readline()

        if not header:
            print("  File is empty. Skipping.")
            return

        expected_columns = count_header_columns(header)

        print(f"  Expected columns: {expected_columns:,}")

        with good_file.open(
            "w",
            encoding="utf-8",
            newline=""
        ) as good_output, bad_file.open(
            "w",
            encoding="utf-8",
            newline=""
        ) as bad_output:

            # Put the header in both output files
            good_output.write(header)
            bad_output.write(header)

            for line_number, line in enumerate(infile, start=2):

                total_records += 1

                valid, reason = validate_record(
                    line,
                    expected_columns
                )

                if valid:
                    good_output.write(line)
                    good_count += 1

                else:
                    bad_output.write(line)
                    bad_count += 1

                    print(
                        f"  Bad record at line {line_number:,}: "
                        f"{reason}"
                    )

    # If there were no bad records, remove the unnecessary bad file
    if bad_count == 0:
        bad_file.unlink()

    print(f"  Total records: {total_records:,}")
    print(f"  Good records:  {good_count:,}")
    print(f"  Bad records:   {bad_count:,}")
    print(f"  Good output:   {good_file.name}")

    if bad_count > 0:
        print(f"  Bad output:    {bad_file.name}")


def main():

    current_folder = Path(".")

    files = [
        file
        for file in current_folder.glob(FILE_PATTERN)
        if not file.stem.endswith("_bad")
        and not file.stem.endswith("_good")
    ]

    if not files:
        print("No matching files found.")
        return

    print(f"Found {len(files):,} file(s).")

    for file_path in files:
        process_file(file_path)

    print("\nFinished.")


if __name__ == "__main__":
    main()
