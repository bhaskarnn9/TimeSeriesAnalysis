# %% [markdown]
# Stock Prediction

#### This project introduces common techniques to manipulate time series and make predictions.

#### The data is a sample from the historical [US stock prices in the last 5 years](https://intrinio.com/bulk-financial-data-downloads/all). Only the New German Fund (GF) will be considered for analysis. 

#### There roughly 1000 days of recoreded trading for GF.

# %%
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
import statsmodels.tsa.api as smt
from sklearn.metrics import mean_absolute_error
from itertools import product
from tqdm import tqdm_notebook
from statsmodels.graphics.tsaplots import plot_acf

# %%
path = '/usr/local/google/home/bneella/Workspace/Python/TimeSeriesAnalysis/'
data = pd.read_csv(path + 'data/stock_prices_sample.csv')
data.head()
# %%
# Let's take DATE as index col and read the file again
data = pd.read_csv(path + 'data/stock_prices_sample.csv', index_col=['DATE'], parse_dates=['DATE'])
data.head()

# %%
# We are interested in TICKER:GF and TYPE:EOD
# Let's check unique vales in TICKER and TYPE
print(data['TICKER'].value_counts())
print(data['TYPE'].value_counts())

# %%
# As we are interested in TICKER:GF and TYPE:EOD, lets remove others
data = data[data.TICKER != 'GEF']
data = data[data.TYPE != 'Intraday']
data.shape

# %%
print(data['TICKER'].value_counts())
print(data['TYPE'].value_counts())

# %%
# We are interested in data points of open low high and close
drop_cols = ['FIGI', 'TYPE', 'FREQUENCY', 'VOLUME', 'ADJ_OPEN', 'ADJ_HIGH',\
     'ADJ_LOW', 'ADJ_CLOSE', 'ADJ_VOLUME', 'ADJ_FACTOR', 'EX_DIVIDEND', 'SPLIT_RATIO']
data.drop(drop_cols, axis=1, inplace=True)
data.head()
# %% [markdown]
## Exploratory Data Analysis
# %%
sns.set()
sns.set_style('darkgrid')
plt.figure(figsize=(15,8))
plt.plot(data.CLOSE)
plt.title('Closing price of New Germany Fund Inc (GF')
plt.ylabel('Closing Prices')
plt.xlabel('Trading Day')
plt.show()

# %% [markdown]
## Moving Average
# %%
roll_mean = data.CLOSE.rolling(window=5).mean()
roll_mean

# %%
def plot_moving_average(series, window, plot_intervals=False, scale=1.96):

    rolling_mean = series.rolling(window=window).mean()

    # calculate and plot rolliing mean
    plt.figure(figsize=(15,8))
    plt.title('Moving average\nwindow = {}'.format(window))
    plt.plot(rolling_mean, 'g', label='Rolling mean trend')

    # plot CI for smoothed values
    if plot_intervals:
        mae = mean_absolute_error(series[window:], rolling_mean[window:])
        deviation = np.std(series[window:] - rolling_mean[window:])
        lower_bound = rolling_mean - (mae + scale*deviation)
        upper_bound = rolling_mean + (mae + scale*deviation)
        plt.plot(upper_bound, 'r--', label='Upper bound / Lower bound')
        plt.plot(lower_bound, 'r--')

    plt.plot(series[window:], label='Actual values')
    plt.legend(loc='best')
    plt.grid(True)

# %%
# Smooth by the previous 5 days (by week)
plot_moving_average(series=data.CLOSE, window=5)

# %%
# Smooth by the previous 30 days (by month)
plot_moving_average(series=data.CLOSE, window=30)

# %%
# Smooth by previous quarter (90 days)
plot_moving_average(data.CLOSE, 90, plot_intervals=True)

# %% [markdown]
## Exponential smoothing

# %%
def exponential_smoothing(series, alpha):
    result = [series[0]] # since first value is same as series
    for i in range(1, len(series)):
        result.append(alpha * series[i] + (1 - alpha) * result[i-1])
    return result

# %%
def plot_exponential_smoothing(series, alphas):

    plt.figure(figsize=(15,8))
    for alpha in alphas:
        plt.plot(exponential_smoothing(series, alpha), label='Alpha {}'.format(alpha))
    plt.plot(series.values, 'c', label='Actual')
    plt.legend(loc='best')
    plt.axis('tight')
    plt.title('Exponential Smoothing')
    plt.grid(True)
    

# %%
plot_exponential_smoothing(data.CLOSE, [0.05, 0.3])

# %% [markdown]
## Double exponential smoothing

# %%
def double_exponential_smoothing(series, alpha, beta):

    result = [series[0]]
    for n in range(1, len(series)+1):
        if n == 1:
            level, trend = series[0], series[1] - series[0]
        if n >= len(series): # forecasting
            value = result[-1]
        else:
            value = series[n]
        last_level, level = level, alpha * value + (1 - alpha) * (level + trend)
        trend = beta * (level - last_level) + (1 - beta) * trend
        result.append(level + trend)
    return result

# %%
def plot_double_exponential_smoothing(series, alphas, betas):
     
    plt.figure(figsize=(17, 8))
    for alpha in alphas:
        for beta in betas:
            plt.plot(double_exponential_smoothing(series, alpha, beta), label="Alpha {}, beta {}".format(alpha, beta))
    plt.plot(series.values, label = "Actual")
    plt.legend(loc="best")
    plt.axis('tight')
    plt.title("Double Exponential Smoothing")
    plt.grid(True)

# %%
plot_double_exponential_smoothing(data.CLOSE, alphas=[0.9, 0.02], betas=[0.9, 0.02])

# %% [markdown]
## Stationarity 

# %%
def tsplot(y, lags=None, figsize=(12, 7), syle='bmh'):
    
    if not isinstance(y, pd.Series):
        y = pd.Series(y)
        
    with plt.style.context(style='bmh'):
        fig = plt.figure(figsize=figsize)
        layout = (2,2)
        ts_ax = plt.subplot2grid(layout, (0,0), colspan=2)
        acf_ax = plt.subplot2grid(layout, (1,0))
        pacf_ax = plt.subplot2grid(layout, (1,1))
        
        y.plot(ax=ts_ax)
        p_value = sm.tsa.stattools.adfuller(y)[1]
        ts_ax.set_title('Time Series Analysis Plots\n Dickey-Fuller: p={0:.5f}'.format(p_value))
        smt.graphics.plot_acf(y, lags=lags, ax=acf_ax)
        smt.graphics.plot_pacf(y, lags=lags, ax=pacf_ax)
        plt.tight_layout()
        
tsplot(data.CLOSE, lags=30)

# %%
data_diff = data.CLOSE - data.CLOSE.shift(1)

tsplot(data_diff[1:], lags=30)

# %% [markdown]
## SARIMA

# %%
#Set initial values and some bounds
ps = range(0, 5)
d = 1
qs = range(0, 5)
Ps = range(0, 5)
D = 1
Qs = range(0, 5)
s = 5

#Create a list with all possible combinations of parameters
parameters = product(ps, qs, Ps, Qs)
parameters_list = list(parameters)
len(parameters_list)

# %%
def optimize_SARIMA(parameters_list, d, D, s):
    """
        Return dataframe with parameters and corresponding AIC
        
        parameters_list - list with (p, q, P, Q) tuples
        d - integration order
        D - seasonal integration order
        s - length of season
    """
    
    results = []
    best_aic = float('inf')
    
    for param in tqdm_notebook(parameters_list):
        try: model = sm.tsa.statespace.SARIMAX(data.CLOSE, order=(param[0], d, param[1]),
                                               seasonal_order=(param[2], D, param[3], s)).fit(disp=-1)
        except:
            continue
            
        aic = model.aic
        
        #Save best model, AIC and parameters
        if aic < best_aic:
            best_model = model
            best_aic = aic
            best_param = param
        results.append([param, model.aic])
        
    result_table = pd.DataFrame(results)
    result_table.columns = ['parameters', 'aic']
    #Sort in ascending order, lower AIC is better
    result_table = result_table.sort_values(by='aic', ascending=True).reset_index(drop=True)
    
    return result_table

result_table = optimize_SARIMA(parameters_list, d, D, s)

# %%
#Set parameters that give the lowest AIC (Akaike Information Criteria)

p, q, P, Q = result_table.parameters[0]

best_model = sm.tsa.statespace.SARIMAX(data.CLOSE, order=(p, d, q),
                                       seasonal_order=(P, D, Q, s)).fit(disp=-1)

print(best_model.summary())

# %%

def mean_absolute_percentage_error(y_true, y_pred):
    return np.mean(np.abs((y_true - y_pred) / y_true)) * 100
    
def plot_SARIMA(series, model, n_steps):
    """
        Plot model vs predicted values
        
        series - dataset with time series
        model - fitted SARIMA model
        n_steps - number of steps to predict in the future
    """
    
    data = series.copy().rename(columns = {'CLOSE': 'actual'})
    data['arima_model'] = model.fittedvalues
    #Make a shift on s+d steps, because these values were unobserved by the model due to the differentiating
    data['arima_model'][:s+d] = np.NaN
    
    #Forecast on n_steps forward
    forecast = model.predict(start=data.shape[0], end=data.shape[0] + n_steps)
    forecast = data.arima_model.append(forecast)
    #Calculate error
    error = mean_absolute_percentage_error(data['actual'][s+d:], data['arima_model'][s+d:])
    
    plt.figure(figsize=(17, 8))
    plt.title('Mean Absolute Percentage Error: {0:.2f}%'.format(error))
    plt.plot(forecast, color='r', label='model')
    plt.axvspan(data.index[-1], forecast.index[-1],alpha=0.5, color='lightgrey')
    plt.plot(data, label='actual')
    plt.legend()
    plt.grid(True);
    
# plot_SARIMA(data, best_model, 5)
print(best_model.predict(start=data.CLOSE.shape[0], end=data.CLOSE.shape[0] + 5))
print(mean_absolute_percentage_error(data.CLOSE[s+d:], best_model.fittedvalues[s+d:]))

# %%
comparison = pd.DataFrame({'actual': [18.93, 19.23, 19.08, 19.17, 19.11, 19.12],
                          'predicted': [18.96, 18.97, 18.96, 18.92, 18.94, 18.92]}, 
                          index = pd.date_range(start='2018-06-05', periods=6,))
comparison.head()

# %%
plt.figure(figsize=(15, 8))
plt.plot(comparison.actual)
plt.plot(comparison.predicted)
plt.title('Predicted closing price of New Germany Fund Inc (GF)')
plt.ylabel('Closing price ($)')
plt.xlabel('Trading day')
plt.legend(loc='best')
plt.grid(False)
plt.show()

# %%
