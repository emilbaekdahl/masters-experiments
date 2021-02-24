# pykg2vec Grid Search

This folder provides two Python scripts, `create.py` and `parse.py`, that (a) generates files for running grid search experiments with pykg2vec on a Slurm cluster and (b) parsing the output of pykg2vec into CSV files that can be used for analysis.
It also provides an R script for analysing these CSV files.

## Python Scripts

### `create.py`
The `create.py` script generates the relevant files to run a grid search experiment. 
This is done based on a parameter grid (see the `CONFIG` constant) that defines search spaces for batch size, learning rate, etc. 
For each parameter configuration, the script stores the relevant configuration as a JSON file and creates a bash script that invokes pykg2vec with said parameters. 
Furthermore, the scripts generates one or more Slurm batch job files that execute the experiments as a job array.

#### Parameters
* `--model` The models to generate experiments for.
The default value is determined by the `MODELS` constant.
* `--dataset` The datasets that will be used. 
Default is determined by the `DATASETS` constant.
* `--partitions` The number of Slurm batch jobs to generate.
The default is 1.
* `--output` The directory in which the jobs should be placed.

#### Example
```bash
python create.py --model TransE TransH --dataset wn18_rr --partitions 10 --output path/to/folder
```
This generates the directory structure `path/to/folder/{TransE,TransH}/wn18_rr/`.
Each folder will be populated with a number of `{model}_{dataset}_{n}.{sh,json}` files where `n` enumerates the different parameters configurations.
Futhermore, each experiments folder will contain the Slurm job files `{model}_{dataset}_job_{0-9}.sbatch` ready to be queued.

### `parse.py`
The output of pykg2vec can be parsed into CSV files using `parse.py`. 
The CSV file contains one row per validation epcoh (the standard is to evaluate every ten epochs) with the measured metrics (MRR and H@N).
Each row will also contain the relevant parameter configuration as well as model and dataset name.

#### Parameters
* `folder` The location of the output files from pykg2vec.
* `--output` The directory in which to put the parsed CSV file.
The defalut is to put it in `folder`.

#### Example
```bash
python parse.py path/to/exp/TransE/wn18_rr --output analysis/TransE_wn18_rr.csv
```
This reads all `path/to/expt/TransE/wn18_rr/*.out` files, parses them, and write the output CSV to `analysis/TransE_wn18_rr.csv`.

## R Analysis
The `analysis` folder contains an R script for generating relevant plots based on data from the `parse.py` script.

### `analysis.R`
This is the main script used to generate the plots.
The program reads data files that are generated using the `parse.py` script.
These files are assumed to follow the directory structure `{dataset}/{model}.csv`, e.g. `wn/TransE.csv`.

#### Pararmeters
* `input` Path to data generated with `parse.py`. 
* `output` Folder to place the generated plots in.

#### Example
```bash
Rscript analysis.R path/to/data path/to/output
```
This command reads all the data files `path/to/data/{dataset}/{model}.csv` and writes the results to `path/to/output/{dataset}/{model}.pdf`.
