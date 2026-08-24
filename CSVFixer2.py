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

    # Remove only the newline characters for validation.
    record = line.rstrip("\r\n")

    in_quotes = False
    at_field_start = True
    just_closed_quote = False
    column_count = 1

    i = 0

    while i < len(record):
        char = record[i]

        # ---------------------------------------------------------
        # Currently inside a quoted field
        # ---------------------------------------------------------
        if in_quotes:

            if char == QUOTE:

                # Escaped quote: ""
                if i + 1 < len(record) and record[i + 1] == QUOTE:
                    i += 2
                    continue

                # Otherwise this is a closing quote
                in_quotes = False
                just_closed_quote = True
                i += 1
                continue

            i += 1
            continue

        # ---------------------------------------------------------
        # We just closed a quoted field.
        # Only delimiter or end-of-record is allowed next.
        # ---------------------------------------------------------
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

        # ---------------------------------------------------------
        # Outside quotes
        # ---------------------------------------------------------

        if char == DELIMITER:
            column_count += 1
            at_field_start = True
            i += 1
            continue

        if char == QUOTE:

            # A quote is only valid if it begins the field.
            if at_field_start:
                in_quotes = True
                at_field_start = False
                i += 1
                continue

            return False, "Quote found in middle of unquoted field"

        at_field_start = False
        i += 1

    # -------------------------------------------------------------
    # End-of-record checks
    # -------------------------------------------------------------

    if in_quotes:
        return False, "Quoted field was never closed"

    if column_count != expected_columns:
        return False, (
            f"Wrong column count: expected {expected_columns}, "
            f"found {column_count}"
        )

    return True, None


def count_header_columns(header):
    """
    Determine the expected number of columns from the header.
    Assumes the header itself is valid.
    """

    return len(header.rstrip("\r\n").split(DELIMITER))


def process_file(file_path):
    """
    Scan one file and create filename_bad.txt containing:
        - original header
        - original bad records
    """

    bad_file = file_path.with_name(
        f"{file_path.stem}_bad{file_path.suffix}"
    )

    bad_count = 0
    total_records = 0

    print(f"\nChecking: {file_path.name}")

    with file_path.open(
        "r",
        encoding="utf-8",
        errors="replace",
        newline=""
    ) as infile:

        # Read and preserve the header
        header = infile.readline()

        if not header:
            print("  File is empty. Skipping.")
            return

        expected_columns = count_header_columns(header)

        print(f"  Expected columns: {expected_columns:,}")

        with bad_file.open(
            "w",
            encoding="utf-8",
            newline=""
        ) as outfile:

            # Always start with the original header
            outfile.write(header)

            for line_number, line in enumerate(infile, start=2):

                total_records += 1

                valid, reason = validate_record(
                    line,
                    expected_columns
                )

                if not valid:
                    bad_count += 1

                    # Write the ORIGINAL record unchanged
                    outfile.write(line)

                    print(
                        f"  Bad record at line {line_number:,}: "
                        f"{reason}"
                    )

    # No bad records -> remove unnecessary _bad file
    if bad_count == 0:
        bad_file.unlink()

        print(
            f"  Checked {total_records:,} records - "
            f"no bad records found."
        )

    else:
        print(
            f"  Checked {total_records:,} records"
        )
        print(
            f"  Bad records: {bad_count:,}"
        )
        print(
            f"  Output: {bad_file.name}"
        )


def main():

    current_folder = Path(".")

    files = [
        file
        for file in current_folder.glob(FILE_PATTERN)
        if not file.stem.endswith("_bad")
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
