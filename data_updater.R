# Name: Kennard Fung
# Project Title: data_updater.R
# Project Description: Grabs historical crypto data from Binance. Creates data files if they
#                      do not exist.

library(PerformanceAnalytics)
library(httr)

cryptos_of_interest = c("BNB", "BTC", "XLM", "XMR", "XRP", "MANA", "ENJ", "RVN")

while (TRUE) {
  # cd to the folder that contains price information. If none is available, create one and populate
  startTime = as.numeric(as.POSIXct(Sys.time()))
  setwd("/Users/kenfung/github/binance-balancer-R/crypto_data/")
  for(crypto in cryptos_of_interest){
    # We're gonna use USDT instead of BUSD because of the greater amount of data available
    usdt_name_transform = paste(crypto,"USDT_prices.csv",sep="")
    if(!(file.exists(usdt_name_transform))){
      # At this point, the file does not exist for a certain crypto
      print(paste("Weekly data files not available for ", crypto, "USDT, creating now..."),sep="")
      data_fully_extracted = FALSE
      price.mat = matrix(nrow=0,ncol=2)
      earliest_time = as.numeric(as.POSIXct(Sys.time())) * 1000;
      while(data_fully_extracted == FALSE){
        query = list(symbol=paste(crypto,"USDT",sep=""),interval="1w",limit=1000,endTime=ceiling(as.numeric(earliest_time)))
        resp = httr::GET("https://api.binance.com/api/v3/klines",query=query)
        if(http_error(resp) == TRUE){
          # Something went wrong with the request
          print("Something went wrong!")
          next
        }
  
        jsonRespText = content(resp,as="text")
        print(nrow(as.matrix(fromJSON(jsonRespText))))
        if(length(fromJSON(jsonRespText)) > 0){
          temp_price.mat = as.matrix(fromJSON(jsonRespText)[,5])
          temp_price.mat = cbind(as.matrix(fromJSON(jsonRespText)[,1]),temp_price.mat)
          price.mat = rbind(temp_price.mat,price.mat)
        }
        
        if(nrow(as.matrix(fromJSON(jsonRespText))) < 1000){
          print("No more data left!")
          data_fully_extracted = TRUE
        } else {
          print("There is some data still available!")
          earliest_time = as.numeric(as.matrix(fromJSON(jsonRespText))[1,1]) - 86400000
        }
      }
      
      # At this point, you have price.mat which contains the full price data
      # Chop off the last thing, because it hasn't reached the endTime yet
      price.mat = as.matrix(price.mat[1:(nrow(price.mat)-1),])
      price.z = zoo(price.mat,order.by = index(price.mat))
      write.csv(as.data.frame(price.z),paste(crypto,"USDT_prices.csv",sep=""))
      returns.z = diff(log(as.numeric(price.z[,2])))
      write.csv(as.data.frame(returns.z),paste(crypto,"USDT_returns.csv",sep=""))
    } else {
      # Update the csv folder with the latest data point
  
      earliest_time = as.numeric(as.POSIXct(Sys.time())) * 1000;
      query = list(symbol=paste(crypto,"USDT",sep=""),interval="1w",limit=1000,endTime=ceiling(as.numeric(earliest_time)))
      resp = httr::GET("https://api.binance.com/api/v3/klines",query=query)
      
      jsonRespText = content(resp,as="text")
      
      if(http_error(resp) == TRUE){
        # Something went wrong with the request
        print("Something went wrong!")
      }
  
      latest_time = as.numeric(fromJSON(jsonRespText)[nrow(fromJSON(jsonRespText)),1])
      penultimate_time = as.numeric(fromJSON(jsonRespText)[(nrow(fromJSON(jsonRespText)) - 1),1])
      penultimate_price = as.numeric(fromJSON(jsonRespText)[(nrow(fromJSON(jsonRespText)) - 1),5])
      
      # Import the price.csv file
      price.csv = read.csv(paste(crypto,"USDT_prices.csv",sep = ""))
      #Remove the first column
      price.csv = price.csv[,2:3]
  
      # Only update if the week has actually passed. Otherwise you'd just be making a double ending entry.
      if(penultimate_time > price.csv[nrow(price.csv),1]) {
        temp_update = c()
        temp_update = c(temp_update,penultimate_time)
        temp_update = c(temp_update,penultimate_price)
        temp_update = t(as.data.frame(temp_update))
        colnames(temp_update) = colnames(price.csv)
        rownames(temp_update) = as.character(as.numeric(rownames(price.csv[nrow(price.csv),])) + 1)
        price.csv = rbind(price.csv,temp_update)
        
        # Export the price file
        write.csv(price.csv,paste(crypto,"USDT_prices.csv"))
        
        # Import the returns file
        returns.csv = read.csv(paste(crypto,"USDT_returns.csv",sep = ""))
        
        # Get rid of the first column
        returns.csv = returns.csv[,2]
        
        # Add the new cc returns data point
        last_two_points = c()
        last_two_points = c(last_two_points,as.numeric(fromJSON(jsonRespText)[(nrow(fromJSON(jsonRespText)) - 2),5]))
        last_two_points = c(last_two_points,penultimate_price)
        delta = diff(log(last_two_points))
        
        returns.csv = c(returns.csv,delta)
        
        # Export the returns file
        write.csv(returns.csv,paste(crypto,"USDT_returns.csv",sep=""))
        
      } else {
        print("It's not time to update yet!")
      }
      
    }
    
  }
  # Sleep for a week
  Sys.sleep(604800 - (as.numeric(as.POSIXct(Sys.time())) - startTime))
}


