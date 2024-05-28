setwd("~/Downloads")
getwd()
data <- read.csv("pareto_wafer2.csv")
library(data.table)
library(dplyr)
library(ggplot2)

a <- data[which(data$tym != "20-01" & data$Yield_Bucket == "G15_Baseline"),c(3,6,14,12,17,21,129,130,131)]
a <- data[which(data$tym != "20-01" & data$pareto_bucket == "Baseline"),c(3,6,14,12,17,21,126)]
t.test(LAGRANGE_8_24C~tym, data = a)
t.test(chain_24c~tym, data = a)
t.test(F_0800_Logic_N~tym, data = a)
#write.csv(x = a,file = "~/Downloads/a.csv")

ggplot(a, aes(LAGRANGE_8_24C, fill = tym), bin) + geom_histogram(alpha = 0.5, position = 'identity',binwidth = 0.02)
ggplot(a, aes(chain_24c, fill = tym), bin) + geom_histogram(alpha = 0.5, position = 'identity',binwidth = 0.02)
ggplot(a, aes(F_0800_Logic_N, fill = tym), bin) + geom_histogram(alpha = 0.5, position = 'identity',binwidth = 0.02)

library(Hmisc)
a <- read.csv("a.csv")
a<-a[which(!(a$Lot_ID_Base %in% c('8IQU46006','8IQU50006'))),c(2:length(a))]
t.test.cluster(y = a$LAGRANGE_8_24C, cluster = a$Lot_ID_Base, group = a$tym,conf.int = 0.95)
t.test.cluster(y = a$chain_24c, cluster = a$Lot_ID_Base, group = a$tym,conf.int = 0.95)
t.test.cluster(y = a$F_0800_Logic_N, cluster = a$Lot_ID_Base, group = a$tym,conf.int = 0.95)


b<- a[which(a$tym =="19-12"),]
write.csv(x=b, file="~/Downloads/b.csv")
c<- a[which(a$tym =="20-02"),]
write.csv(x=c, file="~/Downloads/c.csv")