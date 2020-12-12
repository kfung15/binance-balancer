# Name: Kennard Fung
# Project Title: risk_manager.R
# Project Description: Given historical price data, this program creates an optimal portfolio
#                      based on a user's risk preference.

library(PerformanceAnalytics)
library(jsonlite)

# Uncomment and run this first if you don't have a weights.csv file yet
# cryptos_of_interest = as.matrix(c("XLM", "BTC", "XRP", "ENJ"))
# weights = as.matrix(c(0.05,0.05,0.05,0.05))
# cryptos_of_interest = cbind(cryptos_of_interest,weights)
# colnames(cryptos_of_interest) = c("Crypto", "Weight")
# write.csv(cryptos_of_interest,"weights.csv")
# ---------------------------------------------------------

var_pvalue = 0.95
risk_tolerance = 0.10
portfolios_to_create = 100000
crypto_list_size = 4
cryptos_of_interest = c("XLM", "BTC", "XRP", "ENJ")



while (TRUE){
  startTime = as.numeric(as.POSIXct(Sys.time()))
  # First, upload the weights file
  weights = read.csv("weights.csv")
  weights = weights[,2:3]
  confirm_array = c()
  weight_array = c()
  for(x in 1:length(cryptos_of_interest)){
    for(y in 1:nrow(weights)){
      if(cryptos_of_interest[x] == as.character(weights[y,1])) {
        confirm_array = c(confirm_array,as.character(weights[y,1]))
        weight_array = c(weight_array,weights[y,2])
        next
      } 
    }
  }
  
  if(is.na(match(FALSE,(confirm_array == cryptos_of_interest)))){
    # Only continue if both arrays of crypto names match!
    var_list = c()
    for(x in 1:length(cryptos_of_interest)){
      # Upload the cc returns file
      returns = read.csv(paste(cryptos_of_interest[x],"USDT_returns.csv",sep=""))
      returns = returns[,2]
      
      # Collect the VaR for the particular crypto's returns
      var = VaR(returns,p=var_pvalue,method=c("historical"),invert=FALSE)
      var_list = c(var_list,var)
    }
    
    # At this point, you have a set of VaRs
    # If the current risk profile is within +/- 5% of the risk_tolerance, then do nothing.
    risk_profile = var_list * weight_array
    if(abs(sum(var_list * weight_array) - risk_tolerance) > (0.05*(risk_tolerance))){
      # If not, create a million portfolios with asset weights between 5% and 10%
      # Sum the absolute differences in weights for each asset. Keep the portfolio that most closely resembles the existing one 
      # AND is within 5% of the risk_tolerance
      
      best_portfolio_so_far = c()
      lowest_sum_distance = 99999.999
      lowest_risk_difference = 99999.999
      
      for(x in 1:portfolios_to_create){
        print(paste(x, "Risk:", lowest_risk_difference, "Sum Difference:", lowest_sum_distance, sep = " "))
        sample_portfolio = c()
        # Populate the sample portfolio with random weights
        for(y in 1:crypto_list_size){
          sample_portfolio = c(sample_portfolio,runif(1,0.05,0.15))
        }
        
        # Calculate the overall portfolio risk and proceed only if the sum is within +/-5%
        # of the risk_tolerance
        
        if(abs(sum(sample_portfolio * var_list) - risk_tolerance) < (0.05*risk_tolerance)){
          temp_sum_distance = sum(abs(weight_array - sample_portfolio))
          if(temp_sum_distance < lowest_sum_distance & (abs(sum(sample_portfolio * var_list) - risk_tolerance) < lowest_risk_difference)){
            lowest_sum_distance = temp_sum_distance
            lowest_risk_difference = abs(sum(sample_portfolio * var_list) - risk_tolerance)
            best_portfolio_so_far = sample_portfolio
          }
        }
      }
      
      # At this point, you have the best possible portfolio
      # Update the weights file and generate the JSON file
  
      confirm_array = as.data.frame(confirm_array)
      best_portfolio_so_far = as.data.frame(best_portfolio_so_far)
      confirm_array = cbind(confirm_array,best_portfolio_so_far)
      colnames(confirm_array) = c("Crypto", "Weight")
      write.csv(confirm_array,"weights.csv")
      write_json(confirm_array,"weights.json")
      
    } else {
      print("Current weights contain the right amount of risk!")
    }
    
  } else {
    print("Crypto array names do not match!")
  }
  
  # Sleep for a week
  Sys.sleep(604800 - (as.numeric(as.POSIXct(Sys.time())) - startTime))
}










