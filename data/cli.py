import argparse
import os.path
import pathlib
import shutil
import zipfile

import pandas as pd
import requests as rq
import tqdm


def download_file(url, dest_folder):
    if not isinstance(dest_folder, pathlib.Path):
        dest_folder = pathlib.Path(dest_folder)

    dest_folder.mkdir(parents=True, exist_ok=True)

    file_name = os.path.basename(url)
    dest = dest_folder / file_name

    if dest.exists():
        return dest

    response = rq.get(url, stream=True)

    file_size = int(response.headers["Content-Length"])

    with open(dest, "wb") as file, tqdm.tqdm(
        desc="Downloading",
        unit="B",
        unit_scale=True,
        unit_divisor=1024,
        total=file_size,
    ) as pbar:
        for chunk in response.iter_content(chunk_size=1024):
            write_size = file.write(chunk)
            pbar.update(write_size)

    return dest


def unzip_file(path):
    if not isinstance(path, pathlib.Path):
        path = pathlib.Path(path)

    with zipfile.ZipFile(path, "r") as zip_file:
        for file in tqdm.tqdm(zip_file.namelist(), desc="Unzipping"):
            zip_file.extract(file, path.parent)

    return path.with_suffix("")


def download_fb(dest, keep):
    zip_path = download_file("https://data.deepai.org/FB15K-237.2.zip", dest)

    unzip_file(zip_path)

    for file_name in tqdm.tqdm(
        ["train.txt", "valid.txt", "test.txt"], desc="Cleaning up"
    ):
        source = dest / "Release" / file_name
        target = (dest / file_name).with_suffix(".csv")

        pd.read_csv(
            source, sep="\t", usecols=[0, 1, 2], names=["head", "relation", "tail"]
        ).to_csv(target, index=False)

        source.unlink()

    if not keep:
        zip_path.unlink()

    shutil.rmtree(dest / "Release")


def download_wn(dest, keep):
    zip_path = download_file(
        "https://graphs.telecom-paristech.fr/data/torchkge/kgs/WN18RR.zip", dest
    )

    unzipped_folder = unzip_file(zip_path)

    for file_name in tqdm.tqdm(os.listdir(unzipped_folder), desc="Cleaning up"):
        source = unzipped_folder / file_name
        target = (dest / file_name).with_suffix(".csv")

        pd.read_csv(source, sep="\t", names=["head", "relation", "tail"]).to_csv(
            target, index=False
        )

        source.unlink()

    if not keep:
        zip_path.unlink()

    shutil.rmtree(unzipped_folder)


def download_dataset(dataset, dest, keep):
    if not isinstance(dest, pathlib.Path):
        dest = pathlib.Path(dest)

    if dataset == "wn":
        download_fn = download_wn
    elif dataset == "fb":
        download_fn = download_fb
    else:
        raise ValueError(f"dataset '{dataset}'' not recognised")

    download_fn(dest, keep)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset")
    parser.add_argument("--output", "-o")
    parser.add_argument("--keep", "-k", action="store_true")

    args = parser.parse_args()

    download_dataset(
        dataset=args.dataset, dest=args.output or args.dataset, keep=args.keep
    )
