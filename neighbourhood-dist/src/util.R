load_data <- function(path) path %>% 
  readr::read_tsv(col_names = c("head", "relation", "tail"))

compute_softmax <- function(data) data %>% 
  dplyr::count(head, relation) %>% 
  tidyr::pivot_wider(names_from = relation, values_from = n, values_fill = 0) %>% 
  tibble::column_to_rownames(var = "head") %>% 
  dplyr::mutate_all(~ exp(.x) / sum(exp(.x)))

compute_similarity <- function(data, ...) data %>% 
  proxy::simil(...) %>% 
  as.matrix() %>% 
  tibble::as_tibble(rownames = NA) 
