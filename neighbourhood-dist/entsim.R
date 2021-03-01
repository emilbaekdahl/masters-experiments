doc <- 'Compute entity similarities

Usage:
  entsim.R [options] <input> <output>

Options:
  -m, --method=<method>  Similarity measure [default: cosine].
'

library(docopt)

arguments <- docopt(doc)

library(tidyverse)
source("src/util.R")

load_data(arguments$input) %>%
  compute_softmax() %>%
  compute_similarity(method = arguments$method) %>%
  write_csv(arguments$output)
