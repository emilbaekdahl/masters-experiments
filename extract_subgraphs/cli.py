import argparse
import functools as ft
import multiprocessing as mp
import typing as tp

import pandas as pd


def subgraph_for_entity(data: pd.DataFrame, entity: str, size: int = 2) -> pd.DataFrame:
    # Find triples where entity is either head or tail; that is outgoing and
    # ingoing edges from entity.
    index = data[(data["head"] == entity) | (data["tail"] == entity)].index

    for layer in range(size - 1):
        current_data = data.iloc[index]

        tails = current_data["tail"]
        heads = current_data["head"]

        triples = data[data["head"].isin(tails) | data["tail"].isin(heads)]

        index = index.union(triples.index)

    return data.iloc[index]


def subgraph_for_pair(
    data: pd.DataFrame, head: str, tail: str, **kwargs
) -> pd.DataFrame:
    head_subgraph = subgraph_for_entity(data, head, **kwargs)
    tail_subgraph = subgraph_for_entity(data, tail, **kwargs)
    index = head_subgraph.index.intersection(tail_subgraph.index)

    return data.iloc[index]


def smallest_subgraph_for_pair(
    data: pd.DataFrame, head: str, tail: str, min_size: int = 2, max_size: int = 5
) -> pd.DataFrame:
    for size in range(min_size, max_size + 1):
        subgraph = subgraph_for_pair(data, head, tail, size=size)

        if len(subgraph) > 0:
            break

    return subgraph


def process_pair(
    data: pd.DataFrame, head: str, tail: str, min_size: int, max_size: int
) -> pd.DataFrame:
    subgraph = smallest_subgraph_for_pair(
        data, head, tail, min_size=min_size, max_size=max_size
    )

    return pd.DataFrame({"head": head, "tail": tail, "index": subgraph.index})


def subgraphs(path: str, min_size=2, max_size=4) -> pd.DataFrame:
    data = pd.read_csv(
        path, sep="\t", usecols=[0, 1, 2], names=["head", "relation", "tail"]
    )

    pairs = data[["head", "tail"]].drop_duplicates()

    print(f"Dataset has {len(pairs)} unique head-tail pairs.")

    with mp.Pool() as pool:
        results = pool.starmap(
            process_pair,
            [
                (data, head, tail, min_size, max_size)
                for head, tail in pairs.itertuples(index=False)
            ],
        )

    return pd.concat(results, ignore_index=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("output")
    parser.add_argument("--min-size", type=int, default=2)
    parser.add_argument("--max-size", type=int, default=4)

    args = parser.parse_args()

    graphs = subgraphs(
        path=args.input,
        min_size=args.min_size,
        max_size=args.max_size,
    )

    graphs.to_csv(args.output, index=False)
