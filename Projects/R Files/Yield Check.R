setwd("~/Downloads")
getwd()
data <- read.csv("data.csv")
library(data.table)
library(dplyr)
library(ggplot2)
library(aod)

#dt <- data %>% select(Wafer_Id, Yield, RTA1001.EWR.Split.Cell) %>% group_by(Wafer_Id, RTA1001.EWR.Split.Cell) %>% summarise(Yield = mean(Yield))


t.test(Yield~FEV, data = data)
#t.test(fin_res_metric2~FEV, data = data)
#t.test(Yield~CIP30K_V1_V2_3lots.EWR.Split.Cell, data = data)
#t.test(Yield~RMGWCMPPass1P2OPPW.EWR.Split.Cell, data = dt)
#t.test(Yield~RTA1001.EWR.Split.Cell, data = dt)
#t.test(Yield~DiboraneSplit, data = data)
#t.test(Yield~CumN30Prod, data = data)
#t.test(Yield~N30_PEPISplit, data = data)
sd(data$Yield[data$N30_PEPISplit=="00-POR_CO07"])
sd(data$Yield[data$N30_PEPISplit=="01-N30_CO07"])

#data2 <- data[data$Zone_Er == "D" | data$Zone_Er == "E",]
#dt2 <- data2 %>% select(Wafer_Id, Yield, RMGWCMPPass1P2OPPW.EWR.Split.Cell) %>% group_by(Wafer_Id, RMGWCMPPass1P2OPPW.EWR.Split.Cell) %>% summarise(Yield = mean(Yield))
#t.test(Yield~RMGWCMPPass1P2OPPW.EWR.Split.Cell, data = dt2)




# ----------------------- T.test over many parms --------------------#

#sink(file='myoutput.txt')
df <- data.frame(matrix(ncol = 6, nrow = 0))
colnames(df) <- c("parm", "pvalue", "mean1","mean0", "n1", "n0")

for (i in c(4:29)){
  a <- na.omit(data[which(data$predict == 1),][names(data)[i]])
  b <- na.omit(data[which(data$predict == 0),][names(data)[i]])
  fcn <- t.test(a,b)
  if (fcn$p.value < 0.051){
    df <- rbind(df, data.frame("parm"=names(data)[i],"pvalue"=fcn$p.value,"mean1"=fcn$estimate[1],"mean0"=fcn$estimate[2],"n1"=nrow(a),"n2"=nrow(b)))
    print(names(data)[i])
    cat("predict = 1, n = ",nrow(a))
    cat("\npredict = 0, n = ",nrow(b))
    print(fcn)
  }
}
#sink()

# Logistic regression over these parms
mylogit <- glm(predict ~ MEACDRIEMDL5FNP.1.G01.P01DieSiteValue + MEACDRIEMDL5FNP.1.G01.P02DieSiteValue 
               + MEACDRIEMDL5FNP.1.G01.P11DieSiteValue + MEACDRIEMDL5FNP.1.G01.P12DieSiteValue
               + MEACDRIEMDL5FNP.1.G01.P13DieSiteValue + MEACDRIEMDL5FNP.1.G01.P14DieSiteValue
               + MEACDRIEMDL5FNP.1.G01.P15DieSiteValue + MEACDRIEMDL5FNP.1.G01.P16DieSiteValue
               + MEACDRIEMDL5FNP.1.G01.P17DieSiteValue + MEACDRIEMDL5FNP.1.G01.P18DieSiteValue
               + MEACDRIEMDL5FNP.1.G01.P19DieSiteValue
               , data = data, family = "binomial")

mylogit <- glm(predict ~ MEACDRIEMDL5FNP.1.G01.P11DieSiteValue + MEACDRIEMDL5FNP.1.G01.P12DieSiteValue
               + MEACDRIEMDL5FNP.1.G01.P13DieSiteValue + MEACDRIEMDL5FNP.1.G01.P14DieSiteValue
               + MEACDRIEMDL5FNP.1.G01.P15DieSiteValue + MEACDRIEMDL5FNP.1.G01.P16DieSiteValue
               + MEACDRIEMDL5FNP.1.G01.P17DieSiteValue + MEACDRIEMDL5FNP.1.G01.P18DieSiteValue
               + MEACDRIEMDL5FNP.1.G01.P19DieSiteValue
               , data = data, family = "binomial")

mylogit <- glm(predict ~ MEACDRIEMDL5FNP.1.G01.P01DieSiteValue + MEACDRIEMDL5FNP.1.G01.P02DieSiteValue 
               + MEACDRIEMDL5FNP.1.G01.P14DieSiteValue + MEACDRIEMDL5FNP.1.G01.P16DieSiteValue
               , data = data, family = "binomial")
summary(mylogit)
#--------------------------------------------------------------------#

