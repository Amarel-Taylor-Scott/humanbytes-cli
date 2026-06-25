#!/usr/bin/env python3
"""Tests for humanbytes."""

import decimal
import math
import unittest

import humanbytes as hb


class ParseBytesTest(unittest.TestCase):
    def test_plain_integers(self):
        self.assertEqual(hb.parse_bytes("0"), 0)
        self.assertEqual(hb.parse_bytes("42"), 42)
        self.assertEqual(hb.parse_bytes("-7"), -7)
        self.assertEqual(hb.parse_bytes("+123"), 123)

    def test_bytes_unit(self):
        self.assertEqual(hb.parse_bytes("0 B"), 0)
        self.assertEqual(hb.parse_bytes("100 b"), 100)

    def test_iec_units(self):
        self.assertEqual(hb.parse_bytes("1 KiB"), 1024)
        self.assertEqual(hb.parse_bytes("1 MiB"), 1024 ** 2)
        self.assertEqual(hb.parse_bytes("1 GiB"), 1024 ** 3)
        self.assertEqual(hb.parse_bytes("1 TiB"), 1024 ** 4)
        self.assertEqual(hb.parse_bytes("1 PiB"), 1024 ** 5)
        self.assertEqual(hb.parse_bytes("1 EiB"), 1024 ** 6)

    def test_si_units(self):
        self.assertEqual(hb.parse_bytes("1 kB"), 1000)
        self.assertEqual(hb.parse_bytes("1 MB"), 1000 ** 2)
        self.assertEqual(hb.parse_bytes("1 GB"), 1000 ** 3)
        self.assertEqual(hb.parse_bytes("1 TB"), 1000 ** 4)
        self.assertEqual(hb.parse_bytes("1 PB"), 1000 ** 5)
        self.assertEqual(hb.parse_bytes("1 EB"), 1000 ** 6)

    def test_fractional(self):
        self.assertEqual(hb.parse_bytes("1.5 GiB"), 1610612736)
        self.assertEqual(hb.parse_bytes("0.5 KiB"), 512)
        self.assertEqual(hb.parse_bytes("2.5 MB"), 2_500_000)

    def test_negative(self):
        self.assertEqual(hb.parse_bytes("-1 KiB"), -1024)
        self.assertEqual(hb.parse_bytes("-1.5 GiB"), -1610612736)

    def test_whitespace_and_case(self):
        self.assertEqual(hb.parse_bytes("  1.5  GiB  "), 1610612736)
        self.assertEqual(hb.parse_bytes("1.5gib"), 1610612736)
        self.assertEqual(hb.parse_bytes("1.5GB"), 1_500_000_000)
        self.assertEqual(hb.parse_bytes("1.5 kb"), 1500)

    def test_invalid(self):
        with self.assertRaises(ValueError):
            hb.parse_bytes("")
        with self.assertRaises(ValueError):
            hb.parse_bytes("abc")
        with self.assertRaises(ValueError):
            hb.parse_bytes("1.5 XB")
        with self.assertRaises(ValueError):
            hb.parse_bytes("1.5")


class FormatBytesTest(unittest.TestCase):
    def test_zero(self):
        self.assertEqual(hb.format_bytes(0), "0 B")
        self.assertEqual(hb.format_bytes(0, unit_system="SI"), "0 B")

    def test_negative(self):
        self.assertEqual(hb.format_bytes(-1024), "-1.00 KiB")
        self.assertEqual(hb.format_bytes(-1610612736), "-1.50 GiB")

    def test_iec(self):
        self.assertEqual(hb.format_bytes(1024), "1.00 KiB")
        self.assertEqual(hb.format_bytes(1024 ** 2), "1.00 MiB")
        self.assertEqual(hb.format_bytes(1610612736), "1.50 GiB")
        self.assertEqual(hb.format_bytes(1024 ** 3 - 1), "1024.00 MiB")

    def test_si(self):
        self.assertEqual(hb.format_bytes(1000, unit_system="SI"), "1.00 kB")
        self.assertEqual(hb.format_bytes(1_500_000_000, unit_system="SI"), "1.50 GB")
        self.assertEqual(hb.format_bytes(999, unit_system="SI"), "999 B")

    def test_precision(self):
        self.assertEqual(hb.format_bytes(1610612736, precision=0), "2 GiB")
        self.assertEqual(hb.format_bytes(1610612736, precision=4), "1.5000 GiB")

    def test_min_unit_index(self):
        self.assertEqual(hb.format_bytes(512, min_unit_index=1), "0.50 KiB")
        self.assertEqual(hb.format_bytes(1024, min_unit_index=1), "1.00 KiB")

    def test_invalid(self):
        with self.assertRaises(TypeError):
            hb.format_bytes("abc")
        with self.assertRaises(ValueError):
            hb.format_bytes(100, precision=-1)


class RoundTripTest(unittest.TestCase):
    def _assert_round_trip(self, n: int, **kwargs):
        formatted = hb.format_bytes(n, **kwargs)
        parsed = hb.parse_bytes(formatted)
        self.assertEqual(parsed, n, f"round-trip failed for {n}: {formatted!r}")

    def test_round_trip_powers_of_two(self):
        for exp in range(0, 40):
            self._assert_round_trip(2 ** exp)
            self._assert_round_trip(-(2 ** exp))

    def test_round_trip_arbitrary(self):
        # Values that are exact multiples of the chosen unit round-trip cleanly.
        for n in (0, 1, 42, 999, 1024, 1024 ** 2, 1610612736):
            self._assert_round_trip(n)
            self._assert_round_trip(-n)

    def test_round_trip_si(self):
        for n in (0, 1000, 1500000, 2500000000, 10 ** 12):
            self._assert_round_trip(n, unit_system="SI")
            self._assert_round_trip(-n, unit_system="SI")


class CliTest(unittest.TestCase):
    def test_parse_command(self):
        self.assertEqual(hb.main(["parse", "1.5 GiB"]), 0)

    def test_format_command(self):
        self.assertEqual(hb.main(["format", "1610612736"]), 0)

    def test_format_si(self):
        self.assertEqual(hb.main(["format", "1500000000", "--si"]), 0)


if __name__ == "__main__":
    unittest.main()
