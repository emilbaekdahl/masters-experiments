"""
This scripts parses all pykg2vec .out files in a given folder into a readable CSV format.
"""

import argparse
import json
import os
import pathlib
import re
import typing as tp

import pandas as pd
import tqdm


def parse_line(line: str) -> tp.Dict[str, tp.Union[str, float, bool]]:
    """
    Parse a single line from an ouput file to a list of metric dictionaries.
    """
    if "mr" in line:
        match = re.match(
            r"--(?P<metric>mrr?).*(?P<value>\d\.\d+), (?P<filtered_value>\d\.\d+)",
            line,
        )

        return [
            {
                "metric": match.group("metric"),
                "value": float(match.group("value")),
            },
            {
                "metric": f"{match.group('metric')}_filtered",
                "value": float(match.group("filtered_value")),
            },
        ]
    else:
        match = re.match(r".*(?P<metric>hits\d+).*(?P<value>\d\.\d+)", line)

        metric = match.group("metric")

        if "filtered" in line:
            metric = f"{metric}_filtered"

        return [
            {
                "metric": metric,
                "value": float(match.group("value")),
            }
        ]


def parse_out_file(file_name: pathlib.Path) -> pd.DataFrame:
    """
    Parse an output file to a pandas DataFrame with performance metrics per epoch.
    """
    with open(file_name, "r", encoding="utf-8") as file:
        current_epoch = None
        metrics = []

        for line in file:
            if "Test Results" in line:
                current_epoch = int(
                    re.match(r".*Epoch: (?P<epoch>\d+)", line).group("epoch")
                )

            if re.match("^-+$", line) is not None:
                current_epoch = None

            if current_epoch is None:
                if "Stop the training" in line:
                    break

                continue

            try:
                metrics = metrics + [
                    {**parsed_line, "epoch": current_epoch}
                    for parsed_line in parse_line(line)
                ]
            except AttributeError:
                continue

    dataframe = (
        pd.DataFrame.from_records(metrics)
        .pivot(index="epoch", columns="metric", values="value")
        .reset_index()
    )

    with open(file_name.with_suffix(".json"), "r") as file:
        config = json.load(file)

    for key, value in config.items():
        dataframe[key] = value

    return dataframe


def parse(folder: str, output: str) -> None:
    """
    Parse all output files in a folder and write each to a .csv file.
    """
    folder = pathlib.Path(folder)

    if output is None:
        output = folder / "aggregated.csv"
    else:
        output = pathlib.Path(output)

    out_files = [folder / file for file in os.listdir(folder) if file.endswith(".out")]

    data = pd.concat(
        [
            parse_out_file(file)
            for file in tqdm.tqdm(out_files, desc="Processing file", unit="files")
        ],
        ignore_index=True,
    )

    data.to_csv(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("folder")
    parser.add_argument("--output", "-o")

    args = parser.parse_args()

    parse(folder=args.folder, output=args.output)
