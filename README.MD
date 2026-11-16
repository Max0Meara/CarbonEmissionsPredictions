# Project Proposal 1.4

## Intro

### The Goal:

##### Electricity doesn't always have a fixed carbon cost. Every hour, the grid is fed by a changing mix of power sources: gas plants, nuclear, hydro, wind, solar, imports, and oil. Carbon intensity is the CO2 emitted per unit of electricity delivered, usually in grams of CO2 per kWh. It changes hour to hour because the ratio of sources changes. These changes are caused by outside factors such as changes in weather, power demand and dispatch order. By making a model that can forecast the Carbon intensity a day ahead, it allows both the grid and consumers to become proactive rather than reactive, driving down carbon emissions and stabilization costs. This makes it both beneficial for the enviroment, consumers and producers.

**Primary goal:** At noon each day, predict New England's carbon intensity for each of the 24 hours of the next day, using only information available at forecast time, and try to beat baselines on on held-out 2025 data.

**Secondary goals:**
- Cluster the data to see if we can group "types" of days.
- Classify whether each hour of the next day will be "clean" (below an emissions threshold).
- Measure the practical value of the forecast (if a flexible load is scheduled in the forecast's cleanest window, how much CO2 is saved compared with a fixed schedule, and how close does it get to perfect)?

### The Data:

 To have a resonable range on this project I will be limiting this model to only predict the Carbon intensity of New England. I'm choosing New Englang because I live there but also because the region runs a variety of energy sources as it's mostly gas but with steady nuclear as a floor and hydro imports. I'm also choosing New England specifically because most data on energy supply and demand is sorted by balancing authority and New England has their own called ISONE. Additionally, the seasons in New England play a large part in the change of energy sources as during the winter, gas supplies get tight and oil plants run which gives some more variety. 

 I'm specifically getting the data from the U.S. Energy Information Administration: https://www.eia.gov/electricity/gridmonitor/about. They have a helpful dashboard in which you can download the data from any given time range and choose the hourly or daily data on "Generation by Energy Source" or "Demand by Subregion". They also have their own forecasted model which includes their old forecasted data which could be useful. For weather data I will be using https://open-meteo.com/en/docs/historical-weather-api. which has data for hourly temperature, cloud coverage, windspeed, solar radiation and more. However, since the data is only in coordinate/bounding box format, I plan on averaging all of the values for each New England state to get the values to match with the energy supply and demand of the New England grid.

Currently I am planning to use both websites to download the data in xlsx format and use Pandas and NumPy to format it into data the models can work with. However, both websites have API's available which I might utilize. In total I will be using time-based splits for my train and testing data. I currently plan to train on data from 2023-2024 and test on 2025. I'd like to beat the simple baselines: "same hour yesterday" and "same hour last week" to show my model is learning and utilizing the parameters I've given it correctly.

 I found these other websites while searching for data sources for this project. I don't plan on using them for data but they were helpful in visually understanding the data I am working with and the models I plan to build.
- https://www.gridstatus.io/live/isone
- https://www.weather.gov/wrh/climate?wfo=box&tab=cliplot


### Modeling and Features

##### The main features I plan to use with my models are hour, day of week, holidays, temperature (heating and cooling demand), wind and solar forecasts, the grid operator's own load forecast, and lagged intensity.

##### I plan to use the following model schemas and timeline:

| Task | Use | Timeline |
|-------- | -------- | -------- |
| Data Collection and Proposal | Fit data for models | Week 1|
| Clustering: | Run k-means on 24-hour daily intensity curves to find trends in day "types". | Week 2 |
| SVD: | Factor a day x hour matrix to see which few patterns explain most days. | Week 3-4 (in time for check in) |
| Classification: | Predict whether the next hour will be "clean" (below an emissions threshold), comparing trees, Naive Bayes, and SVMs. | Week 5 |
| Neural Network Regression (main model): | Predict carbon intensity directly with linear models. | Week 6-7 |
| Neural Network Evaluation | Finalize model accuracy and output | Week 8-9 (in time for check in) |ß
| Final Write Up and Visualizations | Complete project | Week 10 |

## October Check In

### Building Dataset

#### Weather Data

Fetching the weather data involved making API calls to open-meteo from ranges 2023-01-01 to 2025-12-31 and using the latitude and longitude values for Connecticut (Hartford), Northeast MA (Boston), West/Central MA (Worcester), Southeast MA (Brockton), Maine (Portland), New Hampshire (Manchester), Rhode Island (Providence), and Vermont (Burlington) to aquire data temperature_2m, wind_speed_100m , shortwave_radiation and cloud_cover for each every hour. These were all compiles into their own respective csv files.

#### EIA Data

Fetching the EIA Data involved fetching the data in chunks due to their free limit of at most 5000 pages at a time. Matching the weather data, I got hourly data on eia_fuel_type, eia_region, eia_subregion and eia_interchange for each region in the time period from 2023-01-01 to 2025-12-31. Each of these sub data sets had their own information which had to be combined using the process below

#### Combining Weather and EIA Data

Building the final processed dataset involved combining the weather data with each of the chunks from the EIA datasets. Since the data for the model is indexed by the date and time I choose to take a weighted average of the weather. Each EIA subregion is matched to its weather city by keyword. Every hour, each zone’s share of total demand becomes its weight, so Boston counts for more than Burlington. This produces ne_temperature_2m, ne_wind_speed_100m, ne_shortwave_radiation, and ne_cloud_cover. The EIA fuel type, demand, demand forecast and net values data is for the ISNE alone so no weighted averages are needed. The carbon intensity is calculated by: Σ(generation × emission factor) ÷ total generation as it's weighted by how much each fuel generated that hour.

After combining the datasets, we are left with the following columns:

| Name | Value |
|-------- | -------- |
| period_utc | The hour this row covers, in UTC (6-7 pm EDT) |
| gen_NG | Natural gas generation in MWh that hour |
| gen_NUC | Nuclear generation |
| gen_SUN | Solar generation |
| gen_WAT | Hydro inside New England generation |
| gen_OTH | Other: wood, trash-to-energy, etc |
| gen_PS | Pumped storage hydro (negative when pumping) |
| gen_BAT | Battery storage, discharging (negative when charging) |
| gen_WND | Wind generation |
| gen_OIL | Oil generation |
| gen_SNB | Solar with integrated battery storage |
| gen_COL | Coal |
| net_generation | Total generation inside New England (sum the gen variables) |
| demand | How much electricity New England actually used (per sub region but we sum it) |
| demand_forecast | ISO-NEs day-ahead prediction of demand |
| net_interchange | Net flow with neighbors (Negative = importing) |
| carbon_intensity | gCO2 per kWh generated this hour |
| ne_temperature_2m | Demand weighted New England temperature (Celcius) [a temperature metric adjusted so that regions or weather stations with higher energy consumption or higher population get more weight than sparsely populated or low-energy areas] |
| ne_wind_speed_100m | Wind at 100 m height (km/h) |
| ne_shortwave_radiation | Sunlight reaching the ground (W/m2) |
| ne_cloud_cover | Percent of sky covered |

### Figures


#### Heat Map

![Heat Map](figures/k=6_figures/heatmap.png)

This heat map shows every hour of the three years. Date on the x-axis, hour of day (UTC) on the y-axis, color = intensity. I specifically choose a heat map because it shows two time scales, daily and seasonal, in one image, which a line plot can't do for 26,000 points.

- Here we can see that the stripes are vertical so whole days are clean or dirty together, so day-to-day variation matters the most.

- Bright yellow spikes around Feb 2023, Jan 2025 and Dec 2025 reach about 500 g/kWh. This was unexpected but I later did more research to find that: 

    - Carbon intensity measures emissions per kWh instead of total emissions. This means the day being clean or dirty comes down to what share of each hour’s power comes from fossil fuels. This is most likely caused by 4 things happening:

    1. Summer demand gets filled with gas. New England uses the most electricity in summer, because of air conditioning. Nuclear (about 3.3 GW) and in-region hydro produce roughly the same amount regardless of demand, so when demand rises, gas plants cover almost all of the extra. Nuclear’s share shrinks, gas’s share grows, and intensity rises. These gas plants are also often ran with Carosine in high demand to help get the plants running faster but cause more Carbon intensity.

    2. Winter heating mostly isn’t electric. Most New England homes heat with oil or gas furnaces, so electricity demand in winter rises less than in summer. ISONE is still a summer-peaking grid, which is why winter isn’t as dirty as you might expect.

    3. Spring has more zero carbon supply. Snowmelt raises hydro output from roughly March through May, and wind is usually stronger in winter and spring than in summer. Combined with the low demand of the shoulder seasons, that makes spring the cleanest stretch.

    4. Winter has a few outliers. On extremely cold days, natural gas pipelines prioritize home heating, gas plants run short of fuel, and oil plants come on. 

- Spring is darker (cleaner); summer and fall are greener (dirtier)


#### Choosing K

![Elbow](figures/k=6_figures/elbow.png)

This graph shows inertia (within-cluster squared error) and silhouette score (how well clusters separate) for k = 2 to 10. This was computed on the full 24-dimensional data.

For the rest of the figures I will be choosing k = 6 given its near the pleateu of the graph.


#### PCA Kmeans 

![clusters](figures/k=6_figures/clusters_pca.png)

This graph shows each day plotted by its PC1 score (overall level, 87%) and PC2 score (daytime vs. night contrast, 7%), colored by cluster, with the projected cluster centers marked. I did this by running PCA on the data and then running Kmeans with k = 6. Each dot is one day kept as 24 separate numbers, one carbon intensity value per hour (intensity (gCO₂/kWh) = Σ (generation of each fuel × that fuel’s emission factor) ÷ total generation). PCA then collapses the 24 numbers into 2 coordinates in 2D.

- We can see that types 2, 0, 3, 4, and 1 are adjacent vertical bands along PC1 with no gaps between them, so k = 6 slices a continuum more finely rather than finding separate groups.

- Type 5’s points are spread across PC1 ≈ 620–1120, and its center falls in empty space between them. It’s a catch-all for extreme days, not a tight group.


#### Day Types by Month

![clusters](figures/k=6_figures/day_types_month.png)

This graph shows how many days of each cluster fall in each calendar month, pooled across 2023–2025. Each bar totals about 90 days.

- We can see that the clean types (0 and 2) dominate January–May. Type 2, the cleanest, is concentrated in February–May.

- July has no clean days at all, only types 1, 3, and 4.

- The extreme type (5) appears only in December–February, which fits the winter outlier hypothesis.

- October has an unexpectedly large number of type 1 days (second-dirtiest) without any AC demand to explain it. A possible cause is fall nuclear refueling outages.


#### Daily carbon-intensity profiles

![clusters](figures/k=6_figures/day_types.png)

This graph plots the average 24-hour curve for each cluster, with the number of days in each.

- We can see that the five clusters are roughly parallel bands of overall level, from about 170 to 335 g/kWh.

- Type 2 is the exception: it has the deepest midday dip (about noon–2 pm local), so it’s the first cluster that differs in shape, likely because of spring solar.

- Type 5 (6 days, about 415–450 g/kWh) isolates the spike days, so they no longer inflate the averages of the normal clusters.


#### PCA loadings

![clusters](figures/k=6_figures/day_types.png)

This graph shows the weight (loading) each principal component puts on each hour. A day's PC score is a weighted sum of its centered hourly values, using these loadings as the weights.

- We can see that PC1 (87%) is flat at about 0.2 for every hour so it measures the overall daily level.

- PC2 (7%) is negative at night and positive during the day so it measures how a day's daytime-vs-night contrast differs from the average day's.

