import unittest

from cronfmt import CronFormatError, format_cron

# (input, expected_output) - the awkward-but-valid cases people actually paste in
OK_CASES = [
    ("* * * * *", "* * * * *"),
    ("  0   12   *  *   *  ", "0 12 * * *"),
    ("0\t12\t*\t*\t*", "0 12 * * *"),
    ("09 05 01 01 0", "9 5 1 1 0"),
    ("5,1,5,3 * * * *", "1,3,5 * * * *"),
    ("*/05 * * * *", "*/5 * * * *"),
    ("10-20/05 * * * *", "10-20/5 * * * *"),
    ("* * * * mon-fri", "* * * * MON-FRI"),
    ("* * * * MoN,FRI", "* * * * FRI,MON"),
    ("* * * jan,DEC *", "* * * DEC,JAN *"),
    ("* * * * 7", "* * * * 0"),
    ("* * * * 0,7", "* * * * 0"),
    ("  @Daily  ", "@daily"),
    ("@WEEKLY", "@weekly"),
    ("0 0 12 * * *", "0 0 12 * * *"),
    ("  30   0   12   *  *  *  ", "30 0 12 * * *"),
    ("05 0 12 * * MoN-FRI", "5 0 12 * * MON-FRI"),
    ("*/05 * * * * *", "*/5 * * * * *"),
    ("00 00 00 1 1 0", "0 0 0 1 1 0"),
]

# (input, fragment expected somewhere in the raised error message)
ERROR_CASES = [
    ("* * *", "expected 5 fields"),
    ("60 * * * *", "out of range"),
    ("* 24 * * *", "out of range"),
    ("*/0 * * * *", "invalid step"),
    ("*/abc * * * *", "invalid step"),
    ("* * * * fortnight", "invalid value"),
    ("@fortnightly", "unrecognized macro"),
    ("", "empty cron expression"),
    ("   ", "empty cron expression"),
    ("* * , * *", "empty value"),
    ("60 * * * * *", "out of range"),
    ("* * * * * * *", "expected 5 fields"),
]


class FormatCronTests(unittest.TestCase):
    def test_normalizes_known_inputs(self):
        for raw, expected in OK_CASES:
            with self.subTest(raw=raw):
                self.assertEqual(format_cron(raw), expected)

    def test_rejects_bad_inputs(self):
        for raw, fragment in ERROR_CASES:
            with self.subTest(raw=raw):
                with self.assertRaises(CronFormatError) as ctx:
                    format_cron(raw)
                self.assertIn(fragment, str(ctx.exception))

    def test_is_idempotent(self):
        # normalizing an already-normalized expression should be a no-op
        for raw, expected in OK_CASES:
            with self.subTest(raw=raw):
                self.assertEqual(format_cron(expected), expected)

    def test_non_string_input_raises(self):
        with self.assertRaises(CronFormatError):
            format_cron(None)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
