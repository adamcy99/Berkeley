from typing import List, Sequence, Union

from ibmdata import np, pd, DataFrame
import plotly.express as px
import plotly.graph_objects as go
from itertools import cycle
from .data import verify_columns_in_dataframe

Scalar = Union[int, float]


def cdf_plot(
    data: DataFrame,
    x: Union[str, Sequence[str]],
    count_col: str = None,
    color: str = None,
    symbol: str = None,
    facet_row: str = None,
    facet_col: str = None,
    normalize: bool = False,
    vline_percentiles: Sequence[Scalar] = (50,),
    vline_dash_specs: Sequence[str] = None,
    mode: str = "lines+markers",
    marker_size: str = 5,
    hover_data: Union[dict, List] = None,
    hover_data_precision: int = 3,
    **px_scatter_kwargs,
) -> go.Figure:

    if isinstance(x, list):
        if facet_col:
            raise ValueError(f"if list of parameters is provided, facet_col must be None")

        data = data.melt(id_vars=[c for c in data.columns if c not in x], value_vars=x)
        facet_col = "variable"
        x = "value"

    _verify_inputs(data, x, count_col, color, symbol, facet_row, facet_col)

    subplot_cols = _unique_cols([facet_row, facet_col])
    gby_cols = _unique_cols([color, symbol])
    if subplot_cols:
        df = data.groupby(subplot_cols).apply(_data_for_subplot, x, gby_cols, normalize, count_col)
    else:
        df = _data_for_subplot(data, x, gby_cols, normalize, count_col)

    x_col = "sigma" if normalize else x
    fig = px.scatter(
        df.sort_values(by="cdf"),
        x=x_col,
        y="cdf",
        color=color,
        symbol=symbol,
        facet_row=facet_row,
        facet_col=facet_col,
        hover_data=_make_hover_data_dict(hover_data, x_col, x, hover_data_precision, normalize),
        **px_scatter_kwargs,
    )

    fig.update_traces(mode=mode, marker_size=marker_size)
    fig.update_yaxes(showticklabels=True, rangemode="tozero")
    if not normalize:
        fig.update_xaxes(matches=None)

    _drop_lines(fig, vline_percentiles, vline_dash_specs)

    return fig


def _verify_inputs(data, x, count_col, color, symbol, facet_row, facet_col):
    cols_to_check = [x, count_col, color, symbol, facet_row, facet_col]
    verify_columns_in_dataframe(data, [c for c in cols_to_check if c])

    should_be_numeric = [x, count_col]
    for arg_name, col in zip(["x", "count_col"], should_be_numeric):
        if col and not pd.api.types.is_numeric_dtype(data[col]):
            try:
                data[col] = pd.to_numeric(data[col])
            except Exception:
                raise ValueError(f"Column: {col} was provided for argument: {arg_name}, but is not numeric!")

    if color:
        data.loc[:, color] = data[color].astype(str)  # prevent continuous colorscale


def _unique_cols(cols):
    return list(set(c for c in cols if c))


def _compute_cdf(df, col, count_col, normalize=False, mean=None, sigma=None):
    cdf = df.copy()
    if count_col:
        cdf = cdf[~cdf[col].isna()].sort_values(by=col)
        cdf["cdf"] = cdf[count_col].cumsum() / cdf[count_col].sum() * 100

    else:
        cdf["cdf"] = cdf[col].rank(pct=True) * 100

    if normalize:
        cdf["sigma"] = (cdf[col] - mean) / sigma
    return cdf


def _compute_mean_and_sd(df, col, count_col):
    if df.empty:
        return 0, 0

    if count_col:
        mean = (df[col] * df[count_col]).sum() / df[count_col].sum()
        n = df[count_col].sum()
        var = ((df[col] ** 2 * df[count_col]).sum() - (df[col] * df[count_col]).sum() ** 2 / n) / (n - 1)
        sd = var ** 0.5
        return mean, sd

    else:
        return df[col].mean(), df[col].std()


def _data_for_subplot(df, col, gby_cols=None, normalize=True, count_col=None):
    mean, sigma = _compute_mean_and_sd(df, col, count_col) if normalize else (None, None)

    if gby_cols:
        return df.groupby(gby_cols).apply(_compute_cdf, col, count_col, normalize, mean, sigma)

    else:
        return _compute_cdf(df, col, count_col, normalize, mean, sigma)


def _drop_lines(fig, percentiles, dashes):
    if not percentiles:
        return

    dash_specs = cycle(dashes) if dashes else cycle(["dot"])
    traces_to_add = []
    for tr in fig.select_traces():
        for cdf, dash in zip(percentiles, dash_specs):
            x0 = np.interp(cdf, tr.y, tr.x)
            traces_to_add.append(
                go.Scatter(
                    x=[x0, x0],
                    y=[0, cdf],
                    line_color=tr.marker.color,
                    line_dash=dash,
                    legendgroup=tr.legendgroup,
                    showlegend=False,
                    hoverinfo="skip",
                    mode="lines",
                    xaxis=tr.xaxis,
                    yaxis=tr.yaxis,
                )
            )
    fig.add_traces(traces_to_add)


def _make_hover_data_dict(user_defined, plot_x_col, x, precision, normalize) -> dict:
    format_str = f":.{precision}f"

    hover_data = {plot_x_col: format_str, "cdf": format_str}
    if normalize:
        hover_data[x] = format_str

    if user_defined:
        if isinstance(user_defined, dict):
            return {**hover_data, **user_defined}
        elif isinstance(user_defined, Sequence):
            return {**hover_data, **{col: True for col in user_defined}}

    return hover_data
