# Project Proposal 1.0



## The Goal:

##### Electricity doesn't always have a fixed carbon cost. Every hour, the grid is fed by a changing mix of power sources: gas plants, nuclear, hydro, wind, solar, imports, and oil. Carbon intensity is the CO2 emitted per unit of electricity delivered, usually in grams of CO2 per kWh. It changes hour to hour because the ratio of sources changes. These changes are caused by outside factors such as changes in weather, power demand and dispatch order. By making a model that can forecast the Carbon intensity days or hours ahead, it allows both the grid and consumers to become proactive rather than reactive, driving down carbon emissions and stabilization costs. This makes it both beneficial for the enviroment, consumers and producers.



## The Data:

##### To have a resonable range on this project I will be limiting this model to only predict the Carbon intensity of New England. I'm choosing New Englang because I live there but also because the region runs a variety of energy sources as it's mostly gas but with steady nuclear as a floor and hydro imports. I'm also choosing New England specifically because most data on energy supply and demand is sorted by balancing authority and New England has their own called ISONE. Additionally, the seasons in New England play a large part in the change of energy sources as during the winter, gas supplies get tight and oil plants run which gives some more variety. 

##### I'm specifically getting the data from the U.S. Energy Information Administration: https://www.eia.gov/electricity/gridmonitor/about. They have a helpful dashboard in which you can download the data from any given time range and choose the hourly or daily data on "Generation by Energy Source" or "Demand by Subregion". They also have their own forecasted model which includes their old forecasted data which could be useful. For weather data I will be using https://open-meteo.com/en/docs/historical-weather-api. which has data for hourly temperature, cloud coverage, windspeed, solar radiation and more. However, since the data is only in coordinate/bounding box format, I plan on averaging all of the values for each New England state to get the values to match with the energy supply and demand of the New England grid.

##### Currently I am planning to use both websites to download the data in xlsx format and use Pandas and NumPy to format it into data the models can work with. However, both websites have API's available which I might utilize. In total I will be using time-based splits for my train and testing data. I currently plan to train on data from 2023-2024 and test on 2025. I'd like to beat the simple baselines: "same hour yesterday" and "same hour last week" to show my model is learning and utilizing the parameters I've given it correctly.

##### I found these other websites while searching for data sources for this project. I don't plan on using them for data but they were helpful in visually understanding the data I am working with and the models I plan to build.
- https://www.gridstatus.io/live/isone
- https://www.weather.gov/wrh/climate?wfo=box&tab=cliplot



## Modeling and Features

##### The main features I plan to use with my models are hour, day of week, holidays, temperature (heating and cooling demand), wind and solar forecasts, the grid operator's own load forecast, and lagged intensity.

##### I plan to use the following model schemas for the data:

| Model Type | Use |
--------      | -------- 
| Clustering: | Run k-means on 24-hour daily intensity curves to find trends in day "types". |
| SVD: | Factor a day x hour matrix to see which few patterns explain most days. |
| Classification: | Predict whether the next hour will be "clean" (below an emissions threshold), comparing trees, Naive Bayes, and SVMs. |
| Neural Network Regression (main model): | Predict carbon intensity directly with linear models. |

##### Since we have not gone over all of these models yet in class, I don't have a full plan for them yet.
