import csv

def fix_broken_csv(input_file, output_file, expected_cols=17, delimiter=','):
    fixed_rows = []
    bad_rows = []

    with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
        buffer = ""

        for line_num, line in enumerate(f, 1):
            # Strip newline but preserve internal spacing
            line = line.rstrip('\n')

            # Add to buffer
            if buffer:
                buffer += ' ' + line
            else:
                buffer = line

            # Count columns
            cols = buffer.split(delimiter)

            if len(cols) == expected_cols:
                fixed_rows.append(cols)
                buffer = ""  # reset for next row

            elif len(cols) > expected_cols:
                # Something is wrong — too many columns
                bad_rows.append((line_num, buffer))
                buffer = ""

            # else: keep reading (len < expected_cols)

        # Catch leftover buffer
        if buffer:
            bad_rows.append(("EOF", buffer))

    # Write fixed output
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(fixed_rows)

    print(f"✅ Fixed rows written: {len(fixed_rows)}")
    print(f"⚠️ Bad rows found: {len(bad_rows)}")

    return bad_rows
