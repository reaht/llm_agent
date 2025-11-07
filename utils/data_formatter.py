# utils/data_formatter.py
"""
Data Formatter — prepares sensor data batches for LLM summarization.
Adds dynamic context culling to fit within a character budget.
"""

def format_sensor_batch(batch, max_chars=1024):
    """
    Formats a list of sensor readings into a compact, LLM-readable table.
    - Keeps only one header line for all entries
    - Uses '|' as delimiter (pipe table style)
    - Removes redundant whitespace and JSON clutter
    - Dynamically truncates rows to fit within max_chars
    """

    if not batch:
        return "(no data)"

    # Flatten and unify keys across all samples
    all_keys = set()
    for entry in batch:
        if isinstance(entry, dict):
            for k, v in _flatten(entry).items():
                all_keys.add(k)
    all_keys = sorted(all_keys)

    # Build header
    header = "|".join(all_keys)

    # Build each row
    rows = []
    for entry in batch:
        flat = _flatten(entry)
        row = "|".join(str(flat.get(k, "")) for k in all_keys)
        rows.append(row)

    # Start full text
    table = header + "\n" + "\n".join(rows)

    # ✅ Keep newlines; just strip extra spaces per line
    table = "\n".join(line.strip() for line in table.splitlines() if line.strip())
    table = table.replace(" |", "|").replace("| ", "|")

    # If too long, trim rows dynamically around center
    if len(table) > max_chars:
        table = _cull_rows(table, header, rows, max_chars)

    return table


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def _flatten(d, parent_key="", sep="."):
    """Flattens nested dicts like {'a': {'b': 1}} → {'a.b': 1}"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def _cull_rows(table, header, rows, max_chars):
    """
    Dynamically removes rows from the middle outward to fit within max_chars.
    Keeps temporal start/end structure to preserve sequence comprehension.
    """
    header_len = len(header) + 1  # + newline
    remaining_budget = max_chars - header_len
    if remaining_budget <= 0:
        return header

    culled = rows.copy()
    while True:
        text = header + "\n" + "\n".join(culled)
        if len(text) <= max_chars or len(culled) <= 2:
            return text

        # Remove rows from the middle outward (center → quarter points → etc.)
        idx = len(culled) // 2
        del culled[idx]


# ---------------------------------------------------------------------
# Example use
# ---------------------------------------------------------------------
if __name__ == "__main__":
    batch = [
        {"time": 1, "temp": 22.1, "hum": 53.3},
        {"time": 2, "temp": 22.2, "hum": 53.2},
        {"time": 3, "temp": 22.3, "hum": 53.1},
    ]
    print(format_sensor_batch(batch, max_chars=100))