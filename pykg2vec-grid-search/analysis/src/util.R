#' Loads a single data frame.
#'
#' @param dataset Name of the dataset to load.
#' @param model Name of the model to load.
#' @param base_path Root of the data folder.
#'
#' @return Data frame.
#' @export
#'
#' @examples
#' load_data("wn", "TransE", base_path = "path/to/data")
load_data <- function(dataset, model, base_path = "data")
  stringr::str_c(base_path, dataset, model, sep = "/") %>%
  stringr::str_c(".csv") %>%
  readr::read_csv() %>%
  dplyr::select(-device, -sampling, -epochs)

#' Loads multiple data frames and combines them into one ready for analysis.
#'
#' @param datasets Vector of dataset names.
#' @param models Vector of model names.
#'
#' @return Data frame.
#' @export
#'
#' @examples
#' load_all_data(c("wn", "fb"), c("TransE", TransH"), base_path = "path/to/data")
load_all_data <- function(datasets, models, ...)
  tidyr::expand_grid(datasets, models) %>%
  purrr::pmap(load_data, ...) %>%
  dplyr::bind_rows()
