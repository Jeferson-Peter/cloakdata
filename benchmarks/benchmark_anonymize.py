"""Measure CloakData in fresh processes using synthetic inputs."""

import argparse
import hashlib
import hmac
import json
import platform
import statistics
import subprocess
import sys
from time import perf_counter

import polars as pl
from loguru import logger

from cloakdata import anonymize, get_all_methods

SIZES = (10_000, 100_000, 1_000_000)
SALT = "benchmark-public-salt"
KEY = bytes(32)  # Public benchmark fixture.
THRESHOLD = 30
TRUNCATE_LENGTH = 8
MASK = {"method": "full_mask", "params": {"match_length": True}}
CHAIN = [{"method": "truncate", "params": {"length": TRUNCATE_LENGTH}}, MASK]
CASES = {
    "mask": ("id", MASK),
    "generalize": ("age", "generalize_age"),
    "hash": ("id", {"method": "hash_value", "params": {"salt": SALT}}),
    "hmac": ("id", {"method": "hmac_value", "params": {"key": KEY}}),
    "conditional": (
        "id",
        {"method": "full_mask", "condition": {"col": "age", "op": ">=", "value": THRESHOLD}},
    ),
    "chain": ("id", CHAIN),
}


def peak_rss_mib() -> float:
    if sys.platform == "win32":
        import ctypes  # noqa: PLC0415
        from ctypes import wintypes  # noqa: PLC0415

        class Counters(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD),
                ("page_faults", wintypes.DWORD),
                ("peak_working_set", ctypes.c_size_t),
                ("remaining", ctypes.c_size_t * 7),
            ]

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.GetCurrentProcess.restype = wintypes.HANDLE
        get_memory = kernel.K32GetProcessMemoryInfo
        get_memory.argtypes = (wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD)
        get_memory.restype = wintypes.BOOL
        info = Counters()
        info.cb = ctypes.sizeof(info)
        if not get_memory(kernel.GetCurrentProcess(), ctypes.byref(info), info.cb):
            raise ctypes.WinError(ctypes.get_last_error())
        return info.peak_working_set / 1024**2

    import resource  # noqa: PLC0415

    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return peak / (1024**2 if sys.platform == "darwin" else 1024)


def expected_row(case: str, index: int) -> tuple[str, str | int]:
    """Compute the expected result without the library or Polars transforms."""
    identifier, age = f"ça-{index}@example.test", index % 100
    match case:
        case "mask":
            return "*" * len(identifier), age
        case "generalize":
            lower = age // 10 * 10
            return identifier, f"{lower}-{lower + 9}"
        case "hash":
            return hashlib.sha256(f"{SALT}{identifier}".encode()).hexdigest(), age
        case "hmac":
            return hmac.digest(KEY, identifier.encode(), "sha256").hex(), age
        case "conditional":
            return ("*****" if age >= THRESHOLD else identifier), age
        case "chain":
            return "*" * min(len(identifier), TRUNCATE_LENGTH), age
        case _:
            raise ValueError(f"Unknown benchmark case {case}")


def measure(case: str, rows: int, reference_chain: bool) -> None:
    logger.disable("cloakdata")
    index = pl.int_range(rows, eager=True)
    frame = pl.DataFrame(
        {"id": "ça-" + index.cast(pl.String) + "@example.test", "age": index % 100}
    )
    column, rule = CASES[case]
    start = perf_counter()
    if case == "chain" and reference_chain:
        result = frame
        for stage in CHAIN:
            result = anonymize(result, {"columns": {column: stage}})
    else:
        result = anonymize(frame, {"columns": {column: rule}})
    elapsed = perf_counter() - start
    memory = peak_rss_mib()
    if result.height != rows or result.columns != frame.columns:
        raise AssertionError(f"{case}: incorrect result shape or columns")
    for index, actual in enumerate(result.iter_rows()):
        if actual != expected_row(case, index):
            raise AssertionError(f"{case}: incorrect output at row {index}")
    print(json.dumps([elapsed * 1000, memory]))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument(
        "--reference-chain",
        action="store_true",
        help="Use two separate calls for a baseline that does not compose rule lists",
    )
    parser.add_argument("--worker", nargs=2, metavar=("CASE", "ROWS"))
    args = parser.parse_args()
    if args.worker:
        case, rows = args.worker
        measure(case, int(rows), args.reference_chain)
        return
    if args.repeats < 1:
        parser.error("--repeats must be positive")

    print(f"Python {platform.python_version()}, Polars {pl.__version__}, {platform.platform()}")
    processor = platform.processor() or platform.machine()
    print(f"CPU: {processor}, Polars threads: {pl.thread_pool_size()}")
    print("Chain:", "two separate calls" if args.reference_chain else "one rule list")
    print("| Case | Rows | Median ms | Peak MiB |")
    print("| --- | ---: | ---: | ---: |")
    for case in CASES:
        if case == "hmac" and "hmac_value" not in get_all_methods():
            continue
        for rows in SIZES:
            command = [sys.executable, __file__, "--worker", case, str(rows)]
            if args.reference_chain:
                command.append("--reference-chain")
            samples = [
                json.loads(subprocess.check_output(command, text=True)) for _ in range(args.repeats)
            ]
            times, peaks = zip(*samples, strict=True)
            print(f"| {case} | {rows:,} | {statistics.median(times):.2f} | {max(peaks):.2f} |")


if __name__ == "__main__":
    main()
