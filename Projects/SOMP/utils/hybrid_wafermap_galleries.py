from typing import List, Iterable, Union
from itertools import cycle
import plotly.express as px
import plotly.graph_objs as go

from dash import dcc, html
from .plots import make_plot_gallery, empty_figure
from .data import verify_columns_in_dataframe

import ibmdata
from ibmdata import DataFrame, pd, np, isdw
from ibmdata.plot.wafermap import WafermapConfig, wafermap

geog = ibmdata.isdw.tables.geography


def hybrid_wafermap_gallery(
    chip_df: DataFrame = DataFrame(),
    subdie_df: DataFrame = DataFrame(),
    join_cols: List[str] = None,
    cols: List[str] = None,
    rows: List[str] = None,
    chunks: List[str] = None,
    max_cols: int = 20,
    max_rows: int = 20,
    max_chunks: int = 20,
    plot_width: int = 500,
    chip_x: str = "x",
    chip_y: str = "y",
    geographykey_col: str = "geographykey",
    chip_color_by_col: str = None,
    chip_discrete: bool = True,
    chip_legend_asc=True,
    chip_cmin: float = None,
    chip_cmax: float = None,
    chip_colorscale=px.colors.colorbrewer.RdYlGn,
    chip_color_map: dict = None,
    chip_tooltip_col: str = None,
    chip_opacity: float = 1.0,
    show_subdie: bool = True,
    subdie_xmin: str = "xmin",
    subdie_xmax: str = "xmax",
    subdie_ymin: str = "ymin",
    subdie_ymax: str = "ymax",
    subdie_as_scatter: bool = True,
    subdie_discrete: bool = True,
    subdie_cmin: float = None,
    subdie_cmax: float = None,
    subdie_colorscale=px.colors.colorbrewer.RdYlGn,
    subdie_border_width: int = 1,
    subdie_marker_size: int = 10,
    subdie_color_by_col: str = None,
    subdie_legend_asc=True,
    subdie_opacity: float = 1.0,
    subdie_label_col: str = "subdie_segment_name",
    subdie_tooltip_col: str = None,
    subdie_color_map: dict = None,
    subdie_symbol_map: dict = None,
    graph_component_id_type: str = None,
    legends_on_all_plots: bool = False,
    show_titles: bool = True,
    style_as_table: bool = False,
    generate_global_legend: bool = True,
    show_continuous_legend: bool = True,
    continuous_legend_title: str = None,
    discrete_legend_title: str = None,
    plot_title_font_size: int = 12,
    color_list: List[str] = px.colors.qualitative.Light24,
    global_title: Union[str, List] = None,
    chunk_title_suffix: str = "",
    chunk_div_class_name: str = "pretty-container mb-5",
    plot_cell_class_name: str = "white-container",
    show_stack_depth_footnote: bool = True,
    show_chip_and_subdie_count: bool = False,
    update_chip_traces: dict = None,
    update_subdie_traces: dict = None,
    update_layout: dict = None,
    update_xaxes: dict = None,
    update_yaxes: dict = None,
    wafersize=300000,
) -> List:
    """
    high level wrapper function to create hybrid (showing chip + chiplet data) wafermap galleries. Returns a list of
    content to be used as 'children' property of a html.Div. One grid of dcc.Graph components will be generated for each
    "chunk." Within each chunk grid, plots will be facetted into rows/cols based on col names given to rows/cols args.

    :param chip_df: DataFrame for chip-level data. Must have all columns listed in
        cols/rows/chunks/join_cols lists and all column names specified by:
        chip_grain_col, chip_x, chip_y, geographykey_col, and chip_color_by_col.
        If chip_discrete == True, each chip rect in a wafermap will be colored based on the first row for each
            chip_x/chip_y position. All other rows for each chip_x/chip_y will be ignored.
        If chip_discrete == False, each chip rect will be colored based on mean of chip_color_by_col for each
        chip_x/chip_y position.
    :param subdie_df: DataFrame for subdie data. Must have all columns in join_cols, and all columns specified by:
        subdie_xmin, subdie_xmax, subdie_ymin, subdie_ymax, subdie_color_by_col, subdie_label_col
    :param join_cols: list of cols used to join chip_df and subdie_df ([tcpkey] should be enough in most cases).
        The set of values in join_cols should be unique to each chip in chip_df.
    :param cols: list of df columns to define columns in gallery
    :param rows: list of df columns to define rows in gallery
    :param chunks: list of df columns to split gallery into "chunks." Each chunk is one grid of plots
    :param max_cols: max number of gallery columns
    :param max_rows: max number of gallery rows
    :param max_chunks: max number of gallery chunks
    :param plot_width: width in px for each plot

    :param chip_x: name of df column containing x coordinate of each chip (wafer_id_xy.str.split('/').str[-2]
    :param chip_y: name of df column containing y coordinate of each chip (wafer_id_xy.str.split('/').str[-1]
    :param geographykey_col: name of geographykey column
    :param chip_color_by_col: df column used to color chip rects
    :param chip_discrete: if True, 1st chip_color_by_col val taken for each chip location, colored with discrete scale
        Else, value of chip_color_by_col is averaged at each chip location and colored using a continuous scale.
    :param chip_legend_asc: if True, chip legend entries sorted in ascending alphabetical order. If False, sorted
        in descending order. If None, legend is unsorted (retains order of input data). Ignored if chip_discrete==False
    :param chip_cmin: min value for continuous chip colorscale (only used if chip_discrete==False)
    :param chip_cmax: max value for continuous chip colorscale (only used if chip_discrete==False)
    :param chip_colorscale: List of colors used for continuous chip colorscale (only used if chip_discrete==False)
    :param chip_color_map: color mapping for chips. keys=values in chip_color_by_col, values=colors
        if not provided, color_list will be used to create colormap applied to all plots
    :param chip_tooltip_col: column in chip_df used to assign custom tooltips to chip rectangles
    :param chip_opacity: opacity of chip rects on scale of 0-1

    :param show_subdie: Should subdie be overlayed. If False, just generates a normal chip-level map
    :param subdie_xmin: name of df column containing xmin of each subdie
    :param subdie_xmax: name of df column containing xmax of each subdie
    :param subdie_ymin: name of df column containing ymin of each subdie
    :param subdie_ymax: name of df column containing ymax of each subdie
    :param subdie_as_scatter: Subdie are rendered as scatter points if True, else rendered as cartoon rectangles
    :param subdie_discrete: If True, individual subdie are plotted. If False, subdie are aggregated by position
        (subdie_color_by_col must be numeric if subdie_discrete is False)
    :param subdie_cmin: lower bound for subdie colorscale (only used if subdie_discrete == False)
    :param subdie_cmax: upper bound for subdie colorscale (only used if subdie_discrete == False)
    :param subdie_colorscale: continuous colorscale for subdie (only used if subdie_discrete == False)
    :param subdie_border_width: border width (in px) for subdie rects or scatter points
    :param subdie_marker_size: marker size for subdie scatter points
    :param subdie_color_by_col: df column used to color subdie
    :param subdie_legend_asc: if True, subdie legend entries sorted in ascending alphabetical order. If False,
        sorted in descending order. If None, legend retains order of input data.
    :param subdie_opacity: opacity of subdie markers on scale of 0-1
    :param subdie_label_col: label in title of subdie hover info. title formated like: "Chip({x}, {y}) - {subdie label}"
    :param subdie_tooltip_col: hover text displayed below subdie tooltip title. value in subdie_color_by_col will be
        displayed here if subdie_tooltip_col is not provided.
    :param subdie_color_map: color mapping for subdie. keys=values in subdie_color_by_col, values=colors
        if not provided, color_list will be used to create subdie colormap applied to all plots
    :param subdie_symbol_map: symbol mapping for subdie. keys=values in subdie_color_by_col, values=plotly symbol names
        if not provided, symbols will be automatically assigned to values in subdie_color_by_col
    :param graph_component_id_type: if provided, will be used as 'type' in each dcc.Graph's component_id
        (this allows pattern matching callbacks to be used)
    :param legends_on_all_plots: If True, every plot in gallery will have its own legend.
    :param show_titles: Display individual plot titles describing value of columns used to assign rows/cols/chunks
    :param style_as_table: Style gallery grids as tables with row/column headers
    :param generate_global_legend: add global legend to top of output Div
    :param show_continuous_legend: should continuous color scale be shown in legend (ignored if chip_discrete==True)
    :param continuous_legend_title: title for continuous legend. defaults to f'mean({chip_color_by_col})' if not
        provided. (Ignored if chip_discrete==True)
    :param discrete_legend_title: title for discrete legend
    :param plot_title_font_size: font size in px for plot titles
    :param color_list: list of colors used to build automatic color maps
    :param global_title: title to display at top of gallery
    :param chunk_title_suffix: text to append to end of each chunk div's title. Useful for displaying additional
        global filters.
    :param chunk_div_class_name: class name for each chunk's div (only used if style_as_table=False)
    :param plot_cell_class_name: class name for each figure (only used if style_as_table=False)
    :param show_stack_depth_footnote: display maximum stack depth as annotation below each wafermap
    :param show_chip_and_subdie_count: display number of chips/subdie in annotation below each wafermap
    :param update_chip_traces: dict of kwargs to pass into fig.update_traces() to modifying chip traces
    :param update_subdie_traces: dict of kwargs to pass into fig.update_traces() to modifying subdie traces
    :param update_layout: dict of kwargs to pass into fig.update_layout() for each plot
    :param update_xaxes: dict of kwargs to pass into fig.update_xaxes() for each plot
    :param update_yaxes: dict of kwargs to pass into fig.update_yaxes() for each plot
    :param wafersize: wafer diameter in um. (300mm -> 300000um)
    :return: list of html.Divs to be used as children property for an output div
    """
    cols, rows, chunks = [[] if i is None else i for i in [cols, rows, chunks]]
    chip_color_map, subdie_color_map, subdie_symbol_map = [
        {} if i is None else i for i in [chip_color_map, subdie_color_map, subdie_symbol_map]
    ]
    join_cols = ["testedchippasskey"] if join_cols is None else join_cols

    _verify_inputs(
        chip_df,
        subdie_df,
        show_subdie,
        cols,
        rows,
        chunks,
        join_cols,
        chip_x,
        chip_y,
        geographykey_col,
        chip_color_by_col,
        chip_tooltip_col,
        subdie_xmin,
        subdie_xmax,
        subdie_ymin,
        subdie_ymax,
        subdie_color_by_col,
        subdie_label_col,
        subdie_tooltip_col,
    )

    if show_subdie and subdie_discrete:
        subdie_vals = [x for x in subdie_df[subdie_color_by_col].unique() if x and not pd.isna(x)]
        subdie_symbol_map = _make_mapping(
            subdie_symbol_map,
            subdie_vals,
            range(53),  # ints from 0-52 are valid plotly symbol identifiers
            sort_asc=subdie_legend_asc,
        )
        subdie_color_map = _make_mapping(subdie_color_map, subdie_vals, color_list, sort_asc=subdie_legend_asc)

    wafermap_kwargs = dict(
        overlay_subdie=show_subdie,
        show_legend=legends_on_all_plots,
        chip_opacity=chip_opacity,
        geographykey_col=geographykey_col,
        chip_x=chip_x,
        chip_y=chip_y,
        chip_color_by_col=chip_color_by_col,
        chip_tooltip_col=chip_tooltip_col,
        join_cols=join_cols,
        subdie_label_column=subdie_label_col,
        subdie_color_by_col=subdie_color_by_col,
        subdie_as_scatter=subdie_as_scatter,
        subdie_discrete=subdie_discrete,
        subdie_cmin=subdie_cmin,
        subdie_cmax=subdie_cmax,
        subdie_tooltip_col=subdie_tooltip_col,
        subdie_color_dict=subdie_color_map,
        subdie_colorscale=subdie_colorscale,
        subdie_opacity=subdie_opacity,
        subdie_symbol_dict=subdie_symbol_map,
        subdie_border_width=subdie_border_width,
        subdie_marker_size=subdie_marker_size,
        show_stack_depth_footnote=show_stack_depth_footnote,
        show_chip_and_subdie_count=show_chip_and_subdie_count,
        update_layout=update_layout,
        update_xaxes=update_xaxes,
        update_yaxes=update_yaxes,
        update_chip_traces=update_chip_traces,
        update_subdie_traces=update_subdie_traces,
        wafer_size_mm=wafersize / 1000,
    )

    if not chip_discrete:
        chip_df[chip_color_by_col] = chip_df[chip_color_by_col].astype(float)
        chip_cmin = chip_cmin or chip_df[chip_color_by_col].min()
        chip_cmax = chip_cmax or chip_df[chip_color_by_col].max()

        wafermap_kwargs["aggregate_chips"] = True
        wafermap_kwargs["chip_continuous_color_scale"] = chip_colorscale
        wafermap_kwargs["chip_cmin"] = chip_cmin
        wafermap_kwargs["chip_cmax"] = chip_cmax

    else:
        chip_vals = [x for x in chip_df[chip_color_by_col].unique() if x and not pd.isna(x)]
        chip_color_map = _make_mapping(chip_color_map, chip_vals, color_list, sort_asc=chip_legend_asc)

        wafermap_kwargs["aggregate_chips"] = False
        wafermap_kwargs["chip_color_dict"] = chip_color_map

    output_content = [html.H3(global_title, style={"text-align": "center"})] if global_title else []
    if generate_global_legend:
        output_content.append(
            _legend_div(
                chip_discrete,
                chip_color_by_col,
                chip_color_map,
                chip_colorscale,
                chip_cmin,
                chip_cmax,
                show_subdie,
                subdie_color_by_col,
                subdie_color_map,
                subdie_marker_size,
                subdie_border_width,
                subdie_discrete,
                subdie_colorscale,
                subdie_cmin,
                subdie_cmax,
                chip_opacity,
                subdie_opacity,
                subdie_symbol_map,
                show_continuous_legend,
                continuous_legend_title,
                discrete_legend_title,
            )
        )

    df = (
        _join_subdie_and_geo_data(
            chip_df,
            subdie_df,
            subdie_xmin,
            subdie_xmax,
            subdie_ymin,
            subdie_ymax,
            join_cols,
            geographykey_col,
            wafersize,
        )
        if show_subdie
        else chip_df
    )

    output_content.append(
        make_plot_gallery(
            df,
            cols,
            rows,
            chunks,
            max_cols=max_cols,
            max_rows=max_rows,
            max_chunks=max_chunks,
            show_plot_titles=show_titles,
            include_headers=style_as_table,
            cell_width=plot_width,
            title_font_size=plot_title_font_size,
            graph_id_type=graph_component_id_type,  # used for pattern matching callbacks
            chunk_title_suffix=chunk_title_suffix,
            chunk_div_class_name=chunk_div_class_name,
            plot_cell_class_name=plot_cell_class_name,
            plot_func=_single_wafermap_plot_func,
            plot_func_args=wafermap_kwargs,
        )
    )

    return output_content


def _join_subdie_and_geo_data(chip_df, subdie_df, xmin, xmax, ymin, ymax, join_cols, geographykey_col, wafersize):
    geo = geog.select(
        geog.c.geographykey,
        geog.c.prodchip_ll_x,
        geog.c.prodchip_ll_y,
        where=[geog.c.geographykey.in_(chip_df.geographykey.unique())],
    ).set_index("geographykey")

    df = chip_df.join(geo, on=geographykey_col, rsuffix="_geo")

    subdie_df["subdie_center_x"] = (subdie_df[xmin] + subdie_df[xmax]) / 2
    subdie_df["subdie_center_y"] = (subdie_df[ymin] + subdie_df[ymax]) / 2

    df = df.join(subdie_df.set_index(join_cols), on=join_cols, rsuffix="_subdie")

    def normalize(ser: ibmdata.Series) -> ibmdata.Series:
        return ser / wafersize + 0.5

    df["norm_subdie_xmin"] = normalize(df.prodchip_ll_x + df[xmin])
    df["norm_subdie_xmax"] = normalize(df.prodchip_ll_x + df[xmax])
    df["norm_subdie_ymin"] = normalize(df.prodchip_ll_y + df[ymin])
    df["norm_subdie_ymax"] = normalize(df.prodchip_ll_y + df[ymax])
    df["norm_subdie_x"] = (df.norm_subdie_xmin + df.norm_subdie_xmax) / 2
    df["norm_subdie_y"] = (df.norm_subdie_ymin + df.norm_subdie_ymax) / 2
    return df


def _single_wafermap_plot_func(
    df: DataFrame,
    join_cols: List[str],
    chip_x: str,
    chip_y: str,
    geographykey_col: str,
    overlay_subdie: bool = True,
    chip_color_by_col: str = "",
    aggregate_chips: bool = False,
    chip_continuous_color_scale=px.colors.colorbrewer.RdYlGn,
    chip_tooltip_col=None,
    chip_cmin: float = None,
    chip_cmax: float = None,
    chip_color_dict: dict = None,
    show_legend: bool = False,
    chip_opacity: float = 0.5,
    subdie_as_scatter=True,
    subdie_discrete=True,
    subdie_cmin=None,
    subdie_cmax=None,
    subdie_colorscale=None,
    subdie_color_by_col=None,
    subdie_label_column=None,
    subdie_tooltip_col=None,
    subdie_color_dict: dict = None,
    subdie_symbol_dict: dict = None,
    subdie_opacity=1.0,
    subdie_border_width: float = 1.0,
    subdie_marker_size: int = 10,
    show_stack_depth_footnote: bool = True,
    show_chip_and_subdie_count: bool = False,
    update_layout=None,
    update_xaxes=None,
    update_yaxes=None,
    update_chip_traces=None,
    update_subdie_traces=None,
    wafer_size_mm=300,
):
    subdie_color_dict, subdie_symbol_dict = [{} if i is None else i for i in [subdie_color_dict, subdie_symbol_dict]]
    chip_map = _make_wafermap(
        df.drop_duplicates(join_cols),  # joining subdie_data may have duplicated rows of chip data
        chip_x,
        chip_y,
        geographykey_col,
        color_by_column=chip_color_by_col,
        tooltip_col=chip_tooltip_col,
        agg=aggregate_chips,
        continuous_color_scale=chip_continuous_color_scale,
        global_cmin=chip_cmin,
        global_cmax=chip_cmax,
        color_dict=chip_color_dict,
        legends=show_legend,
        opacity=chip_opacity,
        show_depth=show_stack_depth_footnote,
        show_chip_and_subdie_count=show_chip_and_subdie_count,
        n_subdie=len(df[~df.norm_subdie_x.isna()]) if overlay_subdie else None,
        wafer_size_mm=wafer_size_mm,
    )
    if update_chip_traces:
        chip_map.update_traces(**update_chip_traces)

    if overlay_subdie:
        customdata_cols = [chip_x, chip_y, subdie_tooltip_col or subdie_color_by_col]
        subdie_hovertemplate = "Chip (%{customdata[0]}, %{customdata[1]})"
        if subdie_label_column:
            customdata_cols.append(subdie_label_column)
            subdie_hovertemplate += " - %{customdata[3]}"

        customdata_cols.append("count")
        if subdie_discrete:
            subdie_df = _aggregate_subdie_data(df, chip_x, chip_y, subdie_color_by_col, discrete=True)
            subdie_hovertemplate += (
                f"<br>%{{customdata[2]}} " f"(stack depth=%{{customdata[{len(customdata_cols) - 1}]}})<extra></extra>"
            )
            subdie_traces = [
                _get_subdie_trace(
                    dff,
                    subdie_as_scatter,
                    subdie_hovertemplate,
                    customdata_cols,
                    marker_props=dict(
                        color=subdie_color_dict.get(colorby_val, "grey"),
                        opacity=subdie_opacity,
                        line_color="black" if subdie_as_scatter else "lightGrey",
                        line_width=subdie_border_width if subdie_as_scatter else 0.1,
                        **dict(symbol=subdie_symbol_dict.get(colorby_val, "circle"), size=subdie_marker_size)
                        if subdie_as_scatter
                        else dict(),
                    ),
                )
                for colorby_val, dff in subdie_df.groupby(subdie_color_by_col, dropna=False)
            ]

        else:
            subdie_df = _aggregate_subdie_data(df, chip_x, chip_y, subdie_color_by_col)

            subdie_hovertemplate += (
                f"<br>{subdie_color_by_col}=%{{customdata[2]}}"
                f" (n=%{{customdata[{len(customdata_cols)-1}]}})<extra></extra>"
            )

            if subdie_df.empty:
                subdie_traces = []

            else:
                subdie_traces = [
                    _get_subdie_trace(
                        subdie_df,
                        subdie_as_scatter,
                        subdie_hovertemplate,
                        customdata_cols,
                        marker_props=dict(
                            color=subdie_df[subdie_color_by_col],
                            cmin=subdie_cmin,
                            cmax=subdie_cmax,
                            colorscale=subdie_colorscale,
                            opacity=subdie_opacity,
                            line_color="lightGrey",
                            line_width=0.1,
                        ),
                    )
                ]
        if update_subdie_traces:
            for trace in subdie_traces:
                trace.update(**update_subdie_traces)

        chip_map.add_traces(subdie_traces)

    if update_layout:
        chip_map.update_layout(**update_layout)
    if update_xaxes:
        chip_map.update_xaxes(**update_xaxes)
    if update_yaxes:
        chip_map.update_yaxes(**update_yaxes)

    return chip_map


def _make_wafermap(
    df: DataFrame,
    chip_x: str,
    chip_y: str,
    geographykey_col: str,
    color_by_column: str = None,
    tooltip_col=None,
    agg: bool = False,
    continuous_color_scale=px.colors.colorbrewer.RdYlGn,
    global_cmin=None,
    global_cmax=None,
    color_dict=None,
    legends=False,
    opacity=1.0,
    show_depth=True,
    show_chip_and_subdie_count=False,
    n_subdie=None,
    wafer_size_mm=300,
):
    if df.empty:
        return empty_figure("No Data")

    n_chips = len(df)
    grouped = df.groupby([chip_x, chip_y])  # df has been preprocessed to extract x/y from wafer_id_xy
    if agg:  # "stacked" style wafermap (computing mean at each site)
        df = DataFrame(
            {
                color_by_column: grouped[color_by_column].mean(),
                "stack_depth": grouped.size(),
                "geographykey": grouped[geographykey_col].first(),
            }
        )

        if not tooltip_col:
            df["tooltip"] = (
                f"{color_by_column} = "
                + df[color_by_column].round(2).astype(str)
                + " (n="
                + df["stack_depth"].astype(str)
                + ")"
            )
            df = df.reset_index()

        else:
            df[tooltip_col] = grouped[tooltip_col].first()
            df = df.reset_index()
    else:
        df = grouped.first()
        df["stack_depth"] = grouped.size()
        if not tooltip_col:
            df["base_tooltip"] = f"{color_by_column}= " + df[color_by_column].astype(str)
            df["tooltip"] = df.base_tooltip
            df.loc[df.stack_depth.gt(1), "tooltip"] = (
                "1st " + df.base_tooltip + "<br>(n=" + df.stack_depth.astype(str) + ")"
            )
        df = df.reset_index()

    config = WafermapConfig(
        df,
        geographykey_column=geographykey_col,
        chipx_column=chip_x,
        chipy_column=chip_y,
        color_by_column=color_by_column,
        show_wafer_circle=True,
        tooltip_column=tooltip_col or "tooltip",
        show_legend=bool(legends),
        plot_type="plotly",
        colorscale=continuous_color_scale if agg else None,
        show_axes=False,
        discrete=not agg,
        colordict=None if agg else color_dict,  # used to sync coloring across gallery for discrete coloring
        alpha=opacity,
        wafer_circle_size=wafer_size_mm,
    )

    try:
        fig = wafermap(config)
    except Exception as ex:
        return empty_figure(str(ex))

    fig.update_traces(
        marker_cmin=global_cmin,  # sync color scale across gallery when using continuous coloring
        marker_cmax=global_cmax,
        selector={"type": "bar"},
    )
    if show_depth or show_chip_and_subdie_count:
        footnote = f"max stack depth = {df.stack_depth.max()} <br>" if show_depth else ""
        if show_chip_and_subdie_count:
            footnote += f"{n_chips} chip{'s' if n_chips > 1 else ''}" + f" | {n_subdie} subdie" if n_subdie else ""

        fig.add_annotation(
            text=footnote,
            showarrow=False,
            xanchor="center",
            x=0.5,
            xref="paper",
            yref="y",
            yanchor="top",
            y=0,
            yshift=-5,
        )
    return fig


def _get_subdie_trace(data, as_scatter, hovertemplate, customdata_cols, marker_props: dict = None):
    if as_scatter:
        trace_constructor = go.Scatter
        trace_kwargs = dict(x=data["norm_subdie_x"], y=data["norm_subdie_y"], mode="markers")
    else:
        trace_constructor = go.Bar
        trace_kwargs = dict(
            x=data.norm_subdie_x,
            y=data.norm_subdie_ymax - data.norm_subdie_ymin,
            width=data.norm_subdie_xmax - data.norm_subdie_xmin,
            base=data.norm_subdie_ymin,
        )

    return trace_constructor(
        customdata=data[customdata_cols], hovertemplate=hovertemplate, marker=marker_props or dict(), **trace_kwargs
    )


def _aggregate_subdie_data(df, chip_x, chip_y, subdie_color_by_col, discrete=False):
    dff = df[
        ~df.norm_subdie_xmin.isna()
        & ~df.norm_subdie_xmax.isna()
        & ~df.norm_subdie_ymin.isna()
        & ~df.norm_subdie_ymax.isna()
    ]
    if dff.empty:
        return dff

    gby_cols = [chip_x, chip_y, "norm_subdie_xmin", "norm_subdie_xmax", "norm_subdie_ymin", "norm_subdie_ymax"]
    # 2022-01-07 (KTP) Previously only the "last" scatter point was drawn for a given coordinate.
    # Adding subdie color by col ensures that ALL scatter points are drawn
    if discrete:
        gby_cols.append(subdie_color_by_col)
    gr = dff.groupby(gby_cols)
    dff = (
        gr.first()
        if discrete
        else gr.agg(
            {
                subdie_color_by_col: "mean",
                **{c: "first" for c in dff.columns if c not in gby_cols + [subdie_color_by_col]},
            }
        )
    )
    dff["count"] = gr.size()
    return dff.reset_index()


def _make_mapping(maybe_full_mapping: dict, vals: List, color_list: Iterable, sort_asc):
    """make a complete mapping from each value in vals to a color (or other str). Start with any specified mappings
    in maybe_full_mapping, then add mappings for any missing values.
    Ex: want to generate mapping for userlabel -> color where 'GOOD' is always colored green.
        Can do this like: _make_mapping({'GOOD': 'green'}, df.userlabel.unique(), px.colors.qualitative.Plotly)
    """
    vals = vals if sort_asc is None else sorted(vals, reverse=not sort_asc)
    colors_in_mapping = maybe_full_mapping.values() if maybe_full_mapping else []
    zipped = zip(vals, cycle([c for c in color_list if c not in colors_in_mapping]))
    if maybe_full_mapping:
        return {val: maybe_full_mapping.get(val, color) for val, color in zipped}
    else:
        return {val: color for val, color in zipped}


def _verify_inputs(
    chip_df,
    subdie_df,
    show_subdie,
    cols,
    rows,
    chunks,
    join_cols,
    chip_x,
    chip_y,
    geographykey_col,
    chip_color_by_col,
    chip_tooltip_col,
    subdie_xmin,
    subdie_xmax,
    subdie_ymin,
    subdie_ymax,
    subdie_color_by_col,
    subdie_label_col,
    subdie_tooltip_col,
):

    # make sure dfs aren't empty
    if chip_df.empty:
        raise ValueError("hybrid_wafermap_gallery received empty chip_df")
    if show_subdie and subdie_df.empty:
        raise ValueError(f"hybrid wafermap gallery received empty subdie_df")

    # verify that no required columns/column lists are None / empty lists / empty strings
    chip_required = [chip_x, chip_y, geographykey_col, chip_color_by_col, join_cols]
    chip_names = ["chip_x", "chip_y", "geographykey_col", "chip_color_by_col", "join_cols"]
    for c, name in zip(chip_required, chip_names):
        if not c:
            raise ValueError(f"{name} is required but was not provided (received value: {c})")

    if show_subdie:
        subdie_required = [subdie_xmin, subdie_xmax, subdie_ymin, subdie_ymax, subdie_color_by_col]
        subdie_names = ["subdie_xmin", "subdie_xmax", "subdie_ymin", "subdie_ymax", "subdie_color_by_col"]
        for c, name in zip(subdie_required, subdie_names):
            if not c:
                raise ValueError(
                    f"{name} is required when show_subdie=True, but was not provided (received value: {c})"
                )

    # verify provided cols are in corresponding dfs:
    chip_cols_to_check = [chip_x, chip_y, geographykey_col, chip_color_by_col, chip_tooltip_col]
    for col_list in [cols, rows, chunks, join_cols]:
        if col_list:
            chip_cols_to_check.extend([col_list] if isinstance(col_list, str) else col_list)

    verify_columns_in_dataframe(chip_df, [c for c in chip_cols_to_check if c])
    if show_subdie:
        subdie_cols_to_check = [
            subdie_xmin,
            subdie_xmax,
            subdie_ymin,
            subdie_ymax,
            subdie_color_by_col,
            subdie_label_col,
            subdie_tooltip_col,
        ]
        subdie_cols_to_check.extend(join_cols)
        verify_columns_in_dataframe(subdie_df, [c for c in subdie_cols_to_check if c])

    # check for duplicated chip rows
    if chip_df.duplicated(join_cols).any():
        raise ValueError(
            f"chip_df has multiple rows with same values in join_cols. Values in join_cols must be unique"
            f" to each chip."
        )


def _make_continuous_legend(color_scale, cmin, cmax, legend_title: str = "", width=None) -> html.Div:
    """plotly has no way to make a horizontal colorbar... but a heatmap trace can be made to look the same"""

    xs = np.linspace(cmin, cmax, 255)
    fig = go.Figure(
        data=dict(
            type="heatmap",
            x=xs,
            y=np.ones_like(xs),
            z=xs,
            colorscale=color_scale,
            zmin=cmin,
            zmax=cmax,
            showscale=False,
        ),
        layout=dict(
            height=50,
            width=width,
            margin_t=0,
            margin_b=25,
            autosize=False,
            margin_l=0,
            margin_r=0,
            yaxis=dict(showticklabels=False),
        ),
    )

    return html.Div(
        [
            html.Label(legend_title, className="font-weight-bold me-2 align-text-bottom"),
            dcc.Graph(figure=fig, config={"displayModeBar": False, "staticPlot": True}),
        ],
        className="row justify-content-center mx-auto",
    )


def _make_legend(
    chip_color_map: dict = None,
    subdie_color_map: dict = None,
    subdie_symbol_map: dict = None,
    marker_size=12,
    border_width=1,
    in_div=True,
    chip_opacity=1.0,
    subdie_opacity=1.0,
    title="",
):
    """create a global legend using a plotly figure"""
    chip_color_map, subdie_color_map, subdie_symbol_map = [
        {} if i is None else i for i in [chip_color_map, subdie_color_map, subdie_symbol_map]
    ]
    fig = go.Figure()
    if chip_color_map:
        for value, color in chip_color_map.items():
            fig.add_bar(
                x=[None], y=[None], name=value, showlegend=True, marker_color=color, marker_opacity=chip_opacity
            )
    if subdie_color_map:
        for value, color in subdie_color_map.items():
            fig.add_scatter(
                mode="markers",
                marker_symbol=subdie_symbol_map.get(value, "circle"),
                marker_size=marker_size,
                x=[None],
                y=[None],
                name=value,
                showlegend=True,
                marker_color=color,
                marker_line_width=border_width,
                marker_line_color="black",
                marker_opacity=subdie_opacity,
            )

    # for small number of legend items, want a short plot. Legend will overflow with scroll for large number
    plot_height = 50 if len(chip_color_map or []) + len(subdie_color_map or []) < 15 else 150
    fig.update_layout(
        legend_orientation="h",
        legend_x=0.5,
        legend_y=1,
        legend_xanchor="center",
        legend_title=title or None,
        height=plot_height,
        autosize=True,
        legend_itemclick=False,
        legend_itemdoubleclick=False,
        margin_t=0,
        margin_b=0,
        dragmode=False,
    )
    ax_opts = dict(showgrid=False, zeroline=False, showticklabels=False)
    fig.update_yaxes(**ax_opts)
    fig.update_xaxes(**ax_opts)
    graph = dcc.Graph(figure=fig, config=dict(displayModeBar=False))

    return html.Div(graph) if in_div else graph


def _legend_div(
    chip_discrete,
    chip_color_by_col,
    chip_color_map,
    chip_colorscale,
    chip_cmin,
    chip_cmax,
    show_subdie,
    subdie_color_by_col,
    subdie_color_map,
    subdie_marker_size,
    subdie_border_width,
    subdie_discrete,
    subdie_colorscale,
    subdie_cmin,
    subdie_cmax,
    chip_opacity,
    subdie_opacity,
    subdie_symbol_map,
    show_continuous_legend,
    continuous_legend_title,
    discrete_legend_title,
):
    legend_content = []
    if show_continuous_legend:
        if not chip_discrete:
            if continuous_legend_title is None:
                continuous_legend_title = f"mean({chip_color_by_col}):"
            legend_content = [_make_continuous_legend(chip_colorscale, chip_cmin, chip_cmax, continuous_legend_title)]
        if show_subdie and not subdie_discrete:
            legend_content = [
                _make_continuous_legend(subdie_colorscale, subdie_cmin, subdie_cmax, f"mean({subdie_color_by_col}):")
            ]

    if chip_discrete or (show_subdie and subdie_discrete):
        if discrete_legend_title is None:
            # depending on inputs, should set title to one of:
            # ["{chip_color_by_col}:", "{chip_color_by_col}/{subdie_color_by_col}:", "{subdie_color_by_col}:"]
            title_content = [chip_color_by_col] if chip_discrete else []
            if show_subdie and subdie_discrete:
                title_content.append(subdie_color_by_col)
            discrete_legend_title = f"<b>{'/'.join(title_content)}:</b>"

        legend_content.append(
            _make_legend(
                chip_color_map,
                subdie_color_map,
                subdie_symbol_map,
                marker_size=subdie_marker_size,
                border_width=subdie_border_width,
                chip_opacity=chip_opacity,
                subdie_opacity=subdie_opacity,
                title=discrete_legend_title,
            )
        )

    return html.Div(legend_content) if legend_content else None
