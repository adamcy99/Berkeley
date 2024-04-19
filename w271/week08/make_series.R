###############################################################################
# Live Session 8
# make_series.R
###############################################################################


###############################################################################
# Clean up the workspace before we begin
rm(list = ls())

# Load required libraries
library(astsa)
library(forecast)
library(fpp2)
library(dplyr)
library(Hmisc)
library(ggplot2)

# Set working directory
wd = "~/Documents/Teach/Cal/w271/_2018.03_Fall/live-session-files/week08"
setwd(wd)
###############################################################################

###############################################################################
set.seed(2095)

series1 <- arima.sim(n = 120, list(ar = c(.8, -.7, .5), ma=0))
Mod(polyroot(c(.8, -.7, .5))) # checking residuals

str(series1)
describe(series1)
summary(series1)
head(series1, 10)
tail(series1, 10)
plot.ts(series1)

write.table(series1, file = "series1.csv", row.names=FALSE, col.names=FALSE)

###############################################################################
set.seed(2046)
series2 <- arima.sim(list(order=c(0,0,2), ma=c(0.7, -0.4)), n=120)

str(series2)
describe(series2)
summary(series2)
head(series2, 10)
tail(series2, 10)
plot.ts(series2)

write.table(series2, file = "series2.csv", 
          row.names=FALSE, col.names=FALSE, sep=",")
###############################################################################

###############################################################################
set.seed(1997)
series3 <- arima.sim(list(order=c(2,0,1), ar=c(0.8, -0.4), ma=c(0.7)), n=120)

str(series3)
describe(series3)
summary(series3)
head(series3, 10)
tail(series3, 10)
plot.ts(series3)

write.table(series3, file = "series3.csv", 
            row.names=FALSE, col.names=FALSE, sep=",")
###############################################################################

