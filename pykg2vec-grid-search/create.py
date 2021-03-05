import argparse
import itertools as it
import json
import pathlib
import string
import typing as tp

MODELS = [
    "TransE",
    "TransH",
    "TransM",
    "RotatE",
    "KG2E",
    "Rescal",
    "DistMult",
    "Complex",
    "SimplE",
    "TuckER",
    "ConvE",
    "ConvKB",
]

DATASETS = ["fb15k_237", "wn18_rr"]

Config = tp.Dict[str, tp.Union[float, bool, str]]

CONFIG: Config = {
    "hidden_size": [100, 500, 1_000],
    "hidden_size_1": [20],
    "batch_size": [100, 1_000, 10_000],
    "learning_rate": [1e-6, 1e-3, 0.1],
    "margin": [0.1, 1, 10],
    "l1_flag": [True, False],
    "cmin": [0.1, 0.3, 0.5],
    "cmax": [1, 3, 5],
    "device": ["cuda"],
    "epochs": [500],
    "sampling": ["bern"],
    "lambda": [0.001, 0.0001, 0.00001],
    "input_dropout": [0.1, 0.2],
    "feature_map_dropout": [0.1, 0.2],
    "hidden_dropout": [0.1, 0.2],
    "num_filters": [10, 50, 100],
}

# Each key in a Config object corresponds to a pykg2vec CLI parameter.
TRANSLATE = {
    "hidden_size": "k",
    "model_name": "mn",
    "dataset": "ds",
    "batch_size": "b",
    "margin": "mg",
    "l1_flag": "l1",
    "ent_hidden_size": "km",
    "rel_hidden_size": "kr",
    "learning_rate": "lr",
    "cmin": "cmin",
    "cmax": "cmax",
    "sampling": "s",
    "device": "device",
    "epochs": "l",
    "lambda": "lmda",
    "hidden_size_1": "k2",
    "input_dropout": "idt",
    "feature_map_dropout": "fmd",
    "hidden_dropout": "hdt",
    "num_filters": "fnum",
}

JOB_TEMPLATE = string.Template(
    """#!/usr/bin/env bash
#SBATCH --array=$start-$end
#SBATCH --job-name ${name}_${partition}
#SBATCH --partition batch
#SBATCH --output ${dir}/${name}_%a.out
#SBATCH --time 21-00:00:00
#SBATCH --qos allgpus
#SBATCH --gres gpu:1
#SBATCH --mem 64G

srun singularity exec --nv pytorch.sif bash ${dir}/${name}_"$$SLURM_ARRAY_TASK_ID".sh
    """
)

SCRIPT_TEMPLATE = string.Template(
    """conda init bash
source /opt/conda/etc/profile.d/conda.sh
conda activate pykg2vec
cd pykg2vec

$command
    """
)


def create_configs(model: str, dataset: str) -> tp.List[Config]:
    config = {**CONFIG, "model_name": [model], "dataset": [dataset]}

    # Only Trans* models differentiate between L1 and L2 regularisation.
    if "Trans" not in model:
        config = {key: value for key, value in config.items() if key != "l1_flag"}

    # The TuckER model uses independent embedding sizes for entities and relations.
    if model == "TuckER":
        config = {
            "ent_hidden_size": config["hidden_size"],
            "rel_hidden_size": config["hidden_size"],
            **{key: value for key, value in config.items() if key != "hidden_size"},
        }

    # Only KG2E uses the cmin and cmax parameters.
    if model != "KG2E":
        config = {
            key: value for key, value in config.items() if key not in ["cmin", "cmax"]
        }

    # Only DistMult, ComplEx, and Simple care about the lambda parameter.
    if model not in ["DistMult", "Complex", "SimplE"]:
        config = {key: value for key, value in config.items() if key != "lambda"}

    if model != "ConvKB":
        config = {key: value for key, value in config.items() if key != "num_filters"}

    if model != "ConvE":
        config = {
            key: value
            for key, value in config.items()
            if key
            not in [
                "hidden_size_1",
                "input_dropout",
                "feature_map_dropout",
                "hidden_dropout",
            ]
        }

    keys, values = zip(*sorted(config.items()))
    return [dict(zip(keys, value)) for value in it.product(*values)]


def create_command(model: str, dataset: str, config: Config) -> str:
    return " ".join(
        ["pykg2vec-train"]
        + [f"-{TRANSLATE[key]} {value}" for key, value in config.items()]
    )


def create_experiment(
    model: str, dataset: str, output: pathlib.Path, partitions: int
) -> None:
    output = output / model / dataset
    output.mkdir(parents=True, exist_ok=True)

    configs = create_configs(model, dataset)

    for n, config in enumerate(configs):
        script = SCRIPT_TEMPLATE.substitute(
            command=create_command(model, dataset, config),
        )

        # Write the script file.
        with open(output / f"{model}_{dataset}_{n}.sh", "w") as file:
            file.write(script)

        # Write the config object to disk for later refference.
        with open(output / f"{model}_{dataset}_{n}.json", "w") as file:
            json.dump(config, file)

    partition_size = len(configs) / float(partitions)

    for partition in range(partitions):
        job = JOB_TEMPLATE.substitute(
            start=round(partition_size * partition),
            end=round(partition_size * (partition + 1)) - 1,
            name=f"{model}_{dataset}",
            dir=output,
            partition=partition,
        )

        # Write the Slurm job file.
        with open(output / f"{model}_{dataset}_job_{partition}.sbatch", "w") as file:
            file.write(job)


def main(
    models: tp.List[str], datasets: tp.List[str], output: str, partitions: int
) -> None:
    output = pathlib.Path(output)

    for model in models:
        for dataset in datasets:
            create_experiment(model, dataset, output, partitions)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", "-m", nargs="+", default=MODELS)
    parser.add_argument("--dataset", "-d", nargs="+", default=DATASETS)
    parser.add_argument("--partitions", "-p", default=1, type=int)
    parser.add_argument("--output", "-o")

    args = parser.parse_args()

    main(
        models=args.model,
        datasets=args.dataset,
        output=args.output,
        partitions=args.partitions,
    )
