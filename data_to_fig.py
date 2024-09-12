import numpy as np
import pandas as pd
import statsmodels.api as sm
import warnings
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sktime.forecasting.arima import AutoARIMA
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error

warnings.filterwarnings("ignore")

#불러온 데이터프레임의 시계열차트와 파이차트 fig
def time_series_and_pie(data, title):
    rainbow_colors = [
        'rgba(255, 0, 0, 0.8)', #red
        'rgba(255, 127, 0, 0.8)', #orange
        'rgba(255, 187, 20, 0.8)', #yellow
        'rgba(0, 153, 0, 0.8)', #green
        'rgba(0, 0, 255, 0.8)',  #blue
        'rgba(148, 0, 211, 0.8)' #purple
    ]

    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "xy"}, {"type": "pie"}]],
        column_widths=[0.6, 0.4],
    )
    
    delete_datetime_df = data.drop("날짜", axis=1)
    
    for idx, col in enumerate(delete_datetime_df):
        if col == "날짜":
            continue
        fig.add_trace(go.Scatter(
            x=data["날짜"], 
            y=data[col], 
            mode='lines', 
            name=col,
            line=dict(color=rainbow_colors[(idx) % len(rainbow_colors)])  
        ), row=1, col=1)

    df = data.drop('날짜', axis=1).apply(pd.to_numeric, errors='coerce').fillna(0).astype(float)
    df_sum = df.sum()

    pie_colors = rainbow_colors[:len(df_sum)]

    fig.add_trace(go.Pie(
        labels=df_sum.index, 
        values=df_sum.values, 
        sort=False, 
        textinfo='label+percent',
        marker=dict(colors=pie_colors) 
    ), row=1, col=2)

    fig.update_layout(
        title_text=title,
        showlegend=True,
        width=1000,
        height=500,
        template='plotly_white'
    )
    
    return fig

#연령별 시계열 데이터의 상관관계 분석 fig
def age_analytics(data, date_time, col_name, lags):
    """Plots time series graph, ACF, PACF test."""

    ts = pd.to_numeric(data[col_name], errors='coerce').fillna(method='ffill').fillna(method='bfill')
    dates = data[date_time].copy()
    
    fig = make_subplots(
        rows=2, cols=2, 
        specs=[[{"colspan": 2}, None], [{"type": "xy"}, {"type": "xy"}]],
        subplot_titles=(
            f'{col_name} category Time Series', 
            'Autocorrelation', 'Partial Autocorrelation'
        ),
        vertical_spacing=0.2
    )
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=ts,
        mode='lines',
        name='Time Series',
        line=dict(color='rgba(0, 123, 255, 0.8)')  # Blue
    ), row=1, col=1)

    acf_vals, acf_confint = sm.tsa.acf(ts, nlags=lags, alpha=0.05)
    pacf_vals, pacf_confint = sm.tsa.pacf(ts, nlags=lags, alpha=0.05)
    plot_acf_pacf(fig, acf_vals, acf_confint, pacf_vals, pacf_confint)

    fig.update_layout(
        title_text=f'{col_name} category Analysis',
        showlegend=False,
        width=1000,
        height=600,
    )
    
    return fig

#차분된 연령별 시계열 데이터의 상관관계 분석 fig
def diff_age_analytics(data, date_time, col_name, lags, diff):
    ts = pd.to_numeric(data[col_name], errors='coerce').fillna(method='ffill').fillna(method='bfill')
    ts_diff = ts.diff(periods = diff).dropna()
    dates = data[date_time].copy()[1:]
    
    fig = make_subplots(
        rows=2, cols=2, 
        specs=[[{"colspan": 2}, None], [{"type": "xy"}, {"type": "xy"}]],
        subplot_titles=(
            f'{col_name} diff category Time Series', 
            'Autocorrelation', 'Partial Autocorrelation'
        ),
        vertical_spacing=0.2
    )
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=ts_diff,
        mode='lines',
        name='Time Series',
        line=dict(color='rgba(0, 123, 255, 0.8)')  # Blue
    ), row=1, col=1)

    acf_vals, acf_confint = sm.tsa.acf(ts_diff, nlags=lags, alpha=0.05)
    pacf_vals, pacf_confint = sm.tsa.pacf(ts_diff, nlags=lags, alpha=0.05)
    plot_acf_pacf(fig, acf_vals, acf_confint, pacf_vals, pacf_confint)

    fig.update_layout(
        title_text=f'{col_name} diff category Analysis', 
        showlegend=False, 
        width=1000, 
        height=600
    )
    
    return fig

#ACF, PACF 그래프
def plot_acf_pacf(fig, acf_vals, acf_confint, pacf_vals, pacf_confint):
    fig.add_trace(go.Bar(
        x=np.arange(len(acf_vals)),
        y=acf_vals,
        name='ACF',
        marker_color='rgba(0, 123, 255, 0.8)' # Blue
    ), row=2, col=1)
    add_conf_interval(fig, acf_vals, acf_confint, row=2, col=1)

    fig.add_trace(go.Bar(
        x=np.arange(len(pacf_vals)),
        y=pacf_vals,
        name='PACF',
        marker_color='rgba(255, 107, 107, 0.8)'  # Red
    ), row=2, col=2)
    add_conf_interval(fig, pacf_vals, pacf_confint, row=2, col=2)

#신뢰구간 시각화
def add_conf_interval(fig, vals, confint, row, col):
    lower_bound = confint[:, 0] - vals
    upper_bound = confint[:, 1] - vals

    fig.add_trace(go.Scatter(x=np.arange(len(vals)), y=lower_bound, mode='lines', line=dict(color='rgba(0,0,0,0)'), showlegend=False), row=row, col=col)
    fig.add_trace(go.Scatter(x=np.arange(len(vals)), y=upper_bound, mode='lines', fill='tonexty', fillcolor='rgba(0,100,80,0.2)', line=dict(color='rgba(0,100,80,0.5)'), showlegend=False), row=row, col=col)

#AutoARIMA 모델을 이용한 연령대별 구매예측 fig
def age_purchase_predict(data, date_time, col_name):
    """Performs forecasting using ARIMA and plots the results."""

    # Prepare time series data
    ts = pd.to_numeric(data[col_name], errors='coerce').fillna(method='ffill').fillna(method='bfill')
    dates = data[date_time].copy()

    # Split data into train and test
    test_len = int(len(ts) * 0.2)
    train, test = ts.iloc[:-test_len], ts.iloc[-test_len:]

    # Fit ARIMA model
    forecaster = AutoARIMA(start_p=1, start_q=1, d=1, max_p=5, max_q=5, suppress_warnings=False)
    forecaster.fit(train)

    # Forecast and calculate intervals
    fh = list(range(1, len(test) + 1))
    forecast = forecaster.predict(fh=fh)
    forecast_int = forecaster.predict_interval(fh=fh, coverage=0.95)

    # Calculate metrics
    mae = np.round(mean_absolute_error(test, forecast), 2)
    mape = np.round(mean_absolute_percentage_error(test, forecast), 2)

    # Create traces for plot
    train_dates = dates[:-test_len]
    test_dates = dates[-test_len:]
    fig = go.Figure()

    fig.add_trace(go.Scatter(x=train_dates, y=train.values, mode='lines', name='Train', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=test_dates, y=test.values, mode='lines', name='Test', line=dict(color='green')))
    fig.add_trace(go.Scatter(x=test_dates, y=forecast, mode='lines', name='Forecast', line=dict(color='red')))

    lower_bound = forecast_int[col_name][0.95]["lower"]
    upper_bound = forecast_int[col_name][0.95]["upper"]

    fig.add_trace(go.Scatter(x=test_dates, y=lower_bound, mode='lines', fill=None, name='Forecast Interval', line=dict(color='gray', width=0)))
    fig.add_trace(go.Scatter(x=test_dates, y=upper_bound, mode='lines', fill='tonexty', name='Forecast Interval', line=dict(color='gray', width=0), fillcolor='rgba(0, 100, 80, 0.2)'))

    # Update layout
    fig.update_layout(
        title=f'MAE: {mae}, MAPE: {mape}',
        xaxis_title='Date',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )

    return fig
