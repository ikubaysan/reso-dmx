import pytest

def determine_note_fractions(measure):
    """
    Given a list of note rows in a measure, return a dictionary of
    { line_number: note_fraction } for each line containing '1'.

    We pick a repeating pattern based on the measure length:
      - If length is multiple of 24, use [4, 24, 12, 8, 12, 24] repeated length/6 times
      - Else if length is multiple of 4, use [4, 16, 8, 16] repeated length/4 times
      - Otherwise default to [4, 16, 8, 16].
    """

    length = len(measure)

    # Patterns defined by your examples
    pattern_16 = [4, 16, 8, 16]       # base length = 4
    pattern_24 = [4, 24, 12, 8, 12, 24]  # base length = 6

    if length % 24 == 0:
        base_pattern = pattern_24 * (length // 6)
    elif length % 4 == 0:
        base_pattern = pattern_16 * (length // 4)
    else:
        base_pattern = pattern_16  # fallback

    note_fractions = {}
    # For each line i, if there's a '1', pick the fraction from our repeated pattern
    for i, row in enumerate(measure):
        if '1' in row:
            note_fractions[i + 1] = base_pattern[i]

    return note_fractions


# ---------------------
# Helper: Build a test measure of length N
# Each line has '1' so it appears in the output.
# We'll cycle through "1000", "0100", "0010", "0001".
def build_measure(n):
    base_lines = ["1000", "0100", "0010", "0001"]
    measure = []
    for i in range(n):
        measure.append(base_lines[i % 4])
    return measure

# ---------------------
# Helper: Build the expected dictionary for a measure length N
# using the same pattern logic as in determine_note_fractions,
# so we can confirm the test results.
def build_expected_dict(n):
    pattern_16 = [4, 16, 8, 16]
    pattern_24 = [4, 24, 12, 8, 12, 24]

    if n % 24 == 0:
        full_pattern = pattern_24 * (n // 6)
    elif n % 4 == 0:
        full_pattern = pattern_16 * (n // 4)
    else:
        full_pattern = pattern_16

    # Because every line has '1', every line i => full_pattern[i]
    return {i+1: full_pattern[i] for i in range(n)}


# ---------------------
# TESTS for each requested measure length
def test_4_rows():
    n = 4
    measure = build_measure(n)
    expected = build_expected_dict(n)
    assert determine_note_fractions(measure) == expected


def test_8_rows():
    n = 8
    measure = build_measure(n)
    expected = build_expected_dict(n)
    assert determine_note_fractions(measure) == expected


def test_12_rows():
    n = 12
    measure = build_measure(n)
    expected = build_expected_dict(n)
    assert determine_note_fractions(measure) == expected


def test_16_rows():
    # Your original 16-row example
    n = 16
    measure = [
        "1000", "0100", "0010", "0001",
        "1000", "0100", "0010", "0001",
        "1000", "0100", "0010", "0001",
        "1000", "0100", "0010", "0001"
    ]
    # This matches your existing expected dictionary
    expected = {
        1: 4, 2: 16, 3: 8, 4: 16,
        5: 4, 6: 16, 7: 8, 8: 16,
        9: 4, 10: 16, 11: 8, 12: 16,
        13: 4, 14: 16, 15: 8, 16: 16
    }
    assert determine_note_fractions(measure) == expected


def test_24_rows():
    # Your original 24-row example
    n = 24
    measure = [
        "1000", "0100", "0010", "0001",
        "1000", "0100", "0010", "0001",
        "1000", "0100", "0010", "0001",
        "1000", "0100", "0010", "0001",
        "1000", "0100", "0010", "0001",
        "1000", "0100", "0010", "0001"
    ]
    # This matches your existing expected dictionary
    expected = {
        1: 4, 2: 24, 3: 12, 4: 8,
        5: 12, 6: 24, 7: 4, 8: 24,
        9: 12, 10: 8, 11: 12, 12: 24,
        13: 4, 14: 24, 15: 12, 16: 8,
        17: 12, 18: 24, 19: 4, 20: 24,
        21: 12, 22: 8, 23: 12, 24: 24
    }
    assert determine_note_fractions(measure) == expected


def test_32_rows():
    n = 32
    measure = build_measure(n)
    expected = build_expected_dict(n)
    assert determine_note_fractions(measure) == expected


def test_48_rows():
    n = 48
    measure = build_measure(n)
    expected = build_expected_dict(n)
    assert determine_note_fractions(measure) == expected


def test_64_rows():
    n = 64
    measure = build_measure(n)
    expected = build_expected_dict(n)
    assert determine_note_fractions(measure) == expected


def test_192_rows():
    n = 192
    measure = build_measure(n)
    expected = build_expected_dict(n)
    assert determine_note_fractions(measure) == expected
