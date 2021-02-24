#' Loads a single data frame.
#' 
#' @param dataset Name of the dataset to load.
#' @param model Name of the model to load.
#' @param base_path Root of the data folder.
#' 
#' @returns Data frame.
#' @export
#' 
#' @example 
#' load_data("wn", "TransE", base_path = "path/to/data")
load_data <- function(dataset, model, base_path = "data") 
  str_c(base_path, dataset, model, sep = "/") %>% 
  str_c(".csv") %>%
  readr::read_csv() %>% 
  select(-device, -sampling, -epochs)

#' Loads multiple data frames and combines them into one ready for analysis.
#'
#' @param datasets Vector of dataset names.
#' @param models Vector of model names.
#' 
#' @returns Data frame.
#' @export
#' 
#' @examples 
#' load_all_data(c("wn", "fb"), c("TransE", TransH"), base_path = "path/to/data")
load_all_data <- function(datasets, models, ...) 
  tidyr::expand_grid(dataset = datasets, model = models) %>% 
  purrr::pmap(load_data, ...) %>% 
  dplyr::bind_rows()