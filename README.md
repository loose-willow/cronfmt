# cronfmt

Cron expressions that come from config files, ticket descriptions, or
copy-pasted Stack Overflow answers are rarely written the same way twice:
extra whitespace, zero-padded numbers, mixed-case month names, duplicate
list entries in random order, `7` instead of `0` for Sunday. All of these
mean the same schedule, but they don't look the same, which makes diffs
noisy and equality checks useless.

`cronfmt` takes a cron expression and rewrites it into one canonical
form, so two expressions that describe the same schedule end up as the
same string.

## Usage

```python
from cronfmt import format_cron

format_cron("  09  05   *  *  MoN-FRI ")
# '9 5 * * MON-FRI'

format_cron("5,1,5,3 * * * *")
# '1,3,5 * * * *'

format_cron("*/05 * * * 7")
# '*/5 * * * 0'

format_cron("  @Daily  ")
# '@daily'
```

Malformed input raises `cronfmt.CronFormatError`:

```python
from cronfmt import format_cron, CronFormatError

try:
    format_cron("60 * * * *")
except CronFormatError as exc:
    print(exc)  # value 60 out of range for minute field (expected 0-59)
```

## What it normalizes

- collapses any run of whitespace between fields down to a single space
- strips leading zeros (`09` -> `9`)
- dedupes and sorts comma-separated lists (`5,1,5,3` -> `1,3,5`)
- upper-cases month and weekday names (`mon-fri` -> `MON-FRI`)
- folds day-of-week `7` down to `0` (both mean Sunday)
- normalizes step values (`*/05` -> `*/5`)
- recognizes the `@yearly` / `@monthly` / `@weekly` / `@daily` /
  `@hourly` / `@midnight` / `@reboot` / `@annually` shorthands
- rejects anything with the wrong field count or an out-of-range value

## What it does not do (yet)

- 6-field expressions with a seconds column
- sorting month/weekday names into calendar order when mixed with numbers
- expanding full names (`Monday`) to abbreviations

See the test suite in `tests/test_formatter.py` for the exact set of
inputs and outputs this is checked against.

## Requirements

Python 3.9+, standard library only.

## License

MIT, see `LICENSE`.
