library(tidyverse)
source("src/util.R")

data <- load_all_data(
  c("fb", "wn"),
  c("TransE", "TransH", "TransM", "RotatE"),
  base_path = "data"
)

data %>% 
  group_by(model_name, dataset) %>% 
  select(ends_with("filtered")) %>% 
  summarise_all(max) %>% 
  pivot_longer(ends_with("filtered")) %>% 
  ggplot(aes(x = model_name, y = value, fill = dataset)) +
  geom_col(position = "dodge") +
  facet_wrap(~ name)