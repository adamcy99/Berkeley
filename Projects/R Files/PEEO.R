setwd("~/Downloads")
getwd()
data <- read.csv("data.csv")
library(data.table)
library(dplyr)
library(ggplot2)

y = data$SAIL_DELTA_VMIN
y = data$LAGRANGE_8_24C
x1 = data$gate_expansion
x2 = data$HVT_RON
x3 = data$LVT_CGON
x4 = data$QT_SICONI_BHF_GRP_SHORT
x5 = data$QT_BHF_EG_GRP_SHORT
x6 = data$QT_EG_GRP_SHORTSHORT
  
fit <- lm(y ~ x1 + x2 + x3 + x4 + x5)
summary(fit) # show results
plot(fit)