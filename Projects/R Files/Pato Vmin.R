setwd("~/Downloads")
getwd()
data <- read.csv("patoVminDelta.csv")

y <- data$pato1_delta
x1 <- data$Pato1.H2.CH_LL1_G10AX01_FailCount
x2 <- data$Pato1.H2.CH_LL1_G10AX02_FailCount
x3 <- data$Pato1.H2.CH_LL1_G10AX03_FailCount
x4 <- data$Pato1.H2.CH_LL1_G10AX04_FailCount
x5 <- data$Pato1.H2.CH_LL1_G10AX05_FailCount
x6 <- data$Pato1.H2.CH_LL1_G10AX06_FailCount
x7 <- data$Pato1.H2.CH_LL1_G10AX07_FailCount
x8 <- data$Pato1.H2.CH_LL1_G10AX08_FailCount
x9 <- data$Pato1.H2.CH_LL1_G10AX09_FailCount
x10 <- data$Pato1.H2.CH_LL1_G10AX10_FailCount
x11 <- data$Pato1.H2.CH_LL1_G10AX11_FailCount
x12 <- data$Pato1.H2.CH_LL1_G10AX12_FailCount
x13 <- data$Pato1.H2.CH_LL1_G10AX13_FailCount
x14 <- data$Pato1.H2.CH_LL1_G10AX14_FailCount
x15 <- data$Pato1.H2.CH_LL1_G10AX15_FailCount
x16 <- data$Pato1.H2.CH_LL1_G10AX16_FailCount
x17 <- data$Pato1.H2.CH_LL1_G10AX17_FailCount

fit <- lm(y~x1+x2+x3+x4+x5+x6+x7+x8+x9+x10+x11+x12+x13+x14+x15+x16)
summary(fit) # show results
plot(fit)