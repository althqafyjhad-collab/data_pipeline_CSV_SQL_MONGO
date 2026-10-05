"""
display.py - Console preview of DataFrames.
=========================================

Provides a small helper used by every pipeline unless it is run with
the `--quiet` flag.

It prints a readable preview of the data *before* and *after*
processing, so the effect of the cleaning stage is visible directly in
the terminal.
"""

import logging
from typing import Optional

import pandas as pd

# How many rows to print by default.
PREVIEW_ROWS = 5

# Width of the separator lines.
LINE_WIDTH = 60


def print_header(title: str) -> None:
    """Print a title framed by two separator lines."""
    print("\n" + "=" * LINE_WIDTH)
    print(title)
    print("=" * LINE_WIDTH)


def print_stage(stage: str, df: pd.DataFrame) -> None:
    """
    Print one stage: its label, shape and a short preview.

    Parameters
    ----------
    stage:
        Label of the stage, e.g. ``"INPUT (raw)"``.
    df:
        The DataFrame at that stage.
    """
    print(f"\n--- {stage} ---")
    print(f"rows: {len(df)} | columns: {len(df.columns)}")

    if df.empty:
        print("(empty)")
        return

    with pd.option_context(
        "display.max_columns",
        None,
        "display.width",
        LINE_WIDTH,
        "display.max_colwidth",
        24,
    ):
        print(df.head(PREVIEW_ROWS))


def print_dataframe_summary(df: pd.DataFrame, title: str) -> None:
    """Print a compact statistical summary of a DataFrame."""
    print(f"\n--- {title} ---")
    if df.empty:
        print("(empty)")
        return

    with pd.option_context(
        "display.max_columns",
        None,
        "display.width",
        LINE_WIDTH,
    ):
        print(df.describe(include="all").iloc[:, :8])


def log_verbose(
    logger: logging.Logger,
    message: str,
    verbose: bool,
) -> None:
    """Log `message` only when verbose mode is on."""
    if verbose:
        logger.info(message)