# humanbytes

A tiny, dependency-free Python library and CLI to parse and format human-readable byte sizes such as `1.5 GiB` or `500 MB`.

It supports both IEC units (KiB, MiB, GiB, ...) using 1024-byte prefixes and SI units (kB, MB, GB, ...) using 1000-byte prefixes.

## Install

No third-party dependencies are required. Just copy `humanbytes.py` into your project, or run it directly:

```bash
python3 humanbytes.py --help
```

## Library usage

```python
import humanbytes as hb

# Format bytes as human-readable strings
hb.format_bytes(1610612736)          # '1.50 GiB'
hb.format_bytes(500000000, unit_system="SI")  # '500.00 MB'
hb.format_bytes(0)                   # '0 B'
hb.format_bytes(-1024)                 # '-1 KiB'

# Parse human-readable strings back to bytes
hb.parse_bytes("1.5 GiB")            # 1610612736
hb.parse_bytes("500 MB")             # 500000000
hb.parse_bytes("-1 kiB")             # -1024
```

## CLI usage

```bash
# Parse a human-readable size
python3 humanbytes.py parse "1.5 GiB"
# 1610612736

# Format a byte count (IEC / base-1024 by default)
python3 humanbytes.py format 1610612736
# 1.50 GiB

# Format using SI / base-1000 units
python3 humanbytes.py format 1500000000 --si
# 1.50 GB

# Adjust precision
python3 humanbytes.py format 1610612736 --precision 0
# 2 GiB
```

## Running tests

```bash
python3 -m unittest test_humanbytes.py
```

## License

MIT
