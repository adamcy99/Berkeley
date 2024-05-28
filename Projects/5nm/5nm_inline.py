import ibmdata
import pandas as pd
import numpy as np

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash import dcc, html, dash_table as dt, Input, Output, callback, State
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import datetime
import colorlover

from .. import cache, LOG, register_page
from ..utils import COL_WIDTH_AUTO, empty_figure

APP_PREFIX = "pti_inline_func_dashboard_5nm"
ALL_FAMILY_CODES = "'M1'"
DEFAULT_DAYS_BACK = 120
DEFAULT_END_DATE = datetime.datetime.today()
DEFAULT_START_DATE = (DEFAULT_END_DATE - datetime.timedelta(days=DEFAULT_DAYS_BACK)).date()
DEFAULT_END_DATE = (DEFAULT_END_DATE + datetime.timedelta(days=1)).date()
HEADER_BACKGROUND_COLOR = "#343A40"
HEADER_FONT_COLOR = "white"
GOOD_GREEN = "#99FF99"
BAD_RED = "#FF9999"
HIGHLIGHT = "#FFF700"
TABLE_FONT_SIZE = "0.7em"

register_page(
    __name__,
    menu="PTIApps:Inline Func 5nm",
    path="/pti_apps/inline_func/5nm_dashboard",
    description="Inline Functional Dashboard for 5HPP",
    title="5HPP Inline Functional Dashboard"
)

########################## Useful Functions ####################################################
def generate_SQL_GroupBy(mydict, parm_label = 'parm_Label', val = 'parmYield', agg = 'AVG'):
    output = ''
    n = len(mydict)
    for i,parm in enumerate(mydict):
        if i == n-1:
            output += f"{agg}(CASE WHEN {parm_label} = '{parm}' THEN {val} ELSE NULL END) AS {mydict[parm]}"
        else:
            output += f"{agg}(CASE WHEN {parm_label} = '{parm}' THEN {val} ELSE NULL END) AS {mydict[parm]},\n"
    parameters = "', '".join(mydict.keys())
    parameters = "'" + parameters + "'"
    return output, parameters

def get_parm_df():
    schema = 'acayng'
    new_qdat_table = 'inline_func_parms'
    return ibmdata.qdat.query(f'select * from {schema}.{new_qdat_table}')

################################### SQL QUERY ##################################################
def wafer_agg_query(family_code, start, end, aggs, param_lst):
    if family_code == 'all':
        family_code = ALL_FAMILY_CODES
    else:
        family_code = f"'{family_code}'"
    return f"""
    SELECT 
        LEFT(wafer_id, 5) AS lot_id_base, lot_Id, wafer_Id, family_Code, 
        DATE(MIN(last_TestTimeStamp)) AS earliest_test_date,
        {aggs}
    FROM 
        DMIW_SYSTEMS.ptilewaferfact ptwf
        INNER JOIN DMIW_SYSTEMS.testparm tp ON ptwf.testparmkey = tp.testparmkey
        INNER JOIN DMIW_SYSTEMS.testedwafer tw ON ptwf.testedwaferkey = tw.testedwaferkey
    WHERE DATE(last_testtimestamp) BETWEEN DATE('{start}') and DATE('{end}')
        AND parm_Label in ({param_lst})
        AND Tech_id = '5HPP'
        AND Level = 'H4'
        AND family_code IN ({family_code})
        AND weighted_mean IS NOT NULL
        AND abs(weighted_mean) < 1e25
    GROUP BY 
        lot_id, LEFT(wafer_id, 5), wafer_Id, family_Code
    ORDER BY
        lot_Id, wafer_Id
"""

@cache.memoize(timeout=21600)
def get_wafer_aggs(family_code, start, end, keys='all', category='all'):
    parm_df = get_parm_df()
    filtered_parm_df = parm_df
    if category != 'all':
        filtered_parm_df = filtered_parm_df[filtered_parm_df['category'].isin(category)]
    if keys != 'all':
        filtered_parm_df = filtered_parm_df[filtered_parm_df['key'].isin(keys)]
    parms_to_pull = filtered_parm_df[['parm','short_name']].set_index('parm').T.to_dict('records')[0]
    aggs, param_lst = generate_SQL_GroupBy(parms_to_pull, val = 'yield')
    df = ibmdata.isdw.query(wafer_agg_query(family_code, start, end, aggs, param_lst))

    return df.sort_values("earliest_test_date", ascending=False)

@cache.memoize(timeout=21600)
def get_lot_aggs(family_code, start, end, keys='all', category='all'):
    temp_agg_df = get_wafer_aggs(family_code, start, end, keys, category)
    temp_agg_df["earliest_test_date"] = temp_agg_df["earliest_test_date"].fillna(datetime.date(9999, 12, 30))

    groupby_ignore = ["lot_id_base", "lot_id", "family_code", "wafer_id"]
    groupby_dict = {c: 'mean' for c in temp_agg_df.columns if c not in groupby_ignore}
    groupby_dict.update({'earliest_test_date': 'min'})

    lot_df = (
        temp_agg_df.groupby(["lot_id_base", "lot_id", "family_code"])
        .agg(groupby_dict)
        .round(2)
        .sort_values("earliest_test_date", ascending=False)
        .reset_index()
    )
    lot_df["earliest_test_date"] = lot_df["earliest_test_date"].replace(datetime.date(9999, 12, 30), np.nan)

    return lot_df


################################### HTML Section ###############################################
def create_tab(tab_name: str, family_code: str):
    return dcc.Tab(
        label=tab_name,
        children=[
            dbc.Row(
                [
                    dbc.Col(
                        dcc.Markdown(
                            f"""\
                    #### 5HPP Inline Characterization Dashboard

                    Contact: Adam Yang (<acyang@us.ibm.com>)
                    """
                        ),
                    ),
                    dbc.Col(
                        [
                            html.Button(
                                "Clear Cache", id=f"{APP_PREFIX}-{family_code}-clear-cache-button",
                                #disabled=True,
                                className="btn btn-primary"
                            ),
                            html.Div(id=f"{APP_PREFIX}-{family_code}-refresh-prompt"),
                        ],
                        width=3,
                    ),
                ],
                className="mb-3",
            ),
            dbc.Row(
                dbc.Col(
                    [
                        html.H5("5HPP Inline Functional Yield Trends"),
                        dbc.Form(
                            dbc.Row(
                                [
                                    # dbc.Label(
                                    #     "Macros:",
                                    #     html_for=f"{APP_PREFIX}-{family_code}-sail-choices",
                                    #     width="auto",
                                    # ),
                                    # dbc.Col(
                                    #     dcc.RadioItems(
                                    #         id=f"{APP_PREFIX}-{family_code}-macro-choices",
                                    #         options=[
                                    #             {"label": "Sail", "value": "sail"},
                                    #             {"label": "Pele", "value": "pele"},
                                    #         ],
                                    #         value="sail",
                                    #         inputClassName="me-1",
                                    #         labelClassName="me-3",
                                    #     ),
                                    # ),
                                    dbc.Label(
                                        "Number of Most Recent Lots to Show:",
                                        html_for=f"{APP_PREFIX}-{family_code}-sail-n-lots",
                                        width="auto",
                                    ),
                                    dbc.Col(
                                        dcc.Slider(
                                            id=f"{APP_PREFIX}-{family_code}-sail-n-lots",
                                            min=10,
                                            max=50,
                                            marks={i: "{}".format(i) if i == 1 else str(i) for i in range(10, 60, 10)},
                                            value=20,
                                        ),
                                    ),
                                ],
                                align="center",
                            )
                        ),
                        dbc.Spinner(
                            dcc.Graph(id=f"{APP_PREFIX}-{family_code}-sail-graphs"),
                        ),
                    ]
                ),
                className="pretty-container mb-3",
            ),
            dbc.Row(
                dbc.Col(
                    [
                        html.H5("5HPP Inline Functional Yield Trends"),
                        dbc.Form(
                            dbc.Row(
                                [
                                    dbc.Label(
                                        "Aggregate/Drill Down:",
                                        html_for=f"{APP_PREFIX}-{family_code}-pele-choices",
                                        width="auto",
                                    ),
                                    dbc.Col(
                                        dcc.RadioItems(
                                            id=f"{APP_PREFIX}-{family_code}-pele-choices",
                                            options=[
                                                {"label": "Aggregate", "value": "agg"},
                                                {"label": "Drill Down", "value": "base"},
                                            ],
                                            value="agg",
                                            inputClassName="me-1",
                                            labelClassName="me-3",
                                        ),
                                    ),
                                    dbc.Label(
                                        "Number of Most Recent Lots to Show:",
                                        html_for=f"{APP_PREFIX}-{family_code}-pele-n-lots",
                                        width="auto",
                                    ),
                                    dbc.Col(
                                        dcc.Slider(
                                            id=f"{APP_PREFIX}-{family_code}-pele-n-lots",
                                            min=10,
                                            max=50,
                                            marks={i: "{}".format(i) if i == 1 else str(i) for i in range(10, 60, 10)},
                                            value=20,
                                        ),
                                    ),
                                ],
                                align="center",
                            )
                        ),
                        dbc.Spinner(
                            dcc.Graph(id=f"{APP_PREFIX}-{family_code}-pele-graphs"),
                        ),
                    ]
                ),
                className="pretty-container mb-3",
            ),
            # dbc.Row(
            #     dbc.Col(
            #         [
            #             html.H5("CANOP Trend"),
            #             dbc.Form(
            #                 dbc.Row(
            #                     [
            #                         dbc.Label(
            #                             "Macros:",
            #                             html_for=f"{APP_PREFIX}-{family_code}-canop-choices",
            #                             width="auto",
            #                         ),
            #                         dbc.Col(
            #                             dcc.RadioItems(
            #                                 id=f"{APP_PREFIX}-{family_code}-canop-choices",
            #                                 options=[
            #                                     {"label": "Yield Loss", "value": "canop_yieldloss"},
            #                                     {"label": "Fail Density", "value": "abc_dbc_bit_count"},
            #                                 ],
            #                                 value="canop_yieldloss",
            #                                 inputClassName="me-1",
            #                                 labelClassName="me-3",
            #                             ),
            #                         ),
            #                     ],
            #                     align="center",
            #                 )
            #             ),
            #             dbc.Spinner(
            #                 dcc.Graph(id=f"{APP_PREFIX}-{family_code}-canop-graphs"),
            #             ),
            #         ]
            #     ),
            #     className="pretty-container mb-3",
            # ),
            dbc.Row(
                dbc.Col(
                    [
                        html.H5("5HPP Inline Functional Yield Table"),
                        dbc.Form(
                            dbc.Row(
                                [
                                    dbc.Label(
                                        "Level:",
                                        html_for=f"{APP_PREFIX}-{family_code}-level-choices",
                                        width="auto",
                                        className="pt-0 pe-0",
                                    ),
                                    dbc.Col(
                                        dcc.RadioItems(
                                            id=f"{APP_PREFIX}-{family_code}-level-choices",
                                            options=[
                                                {"label": "lot", "value": "lot"},
                                                {"label": "wafer", "value": "wafer"},
                                            ],
                                            value="lot",
                                            inputClassName="me-1",
                                            labelClassName="me-3",
                                        ),
                                    ),
                                ],
                                align="center",
                            )
                        ),
                        dbc.Spinner(
                            dt.DataTable(
                                id=f"{APP_PREFIX}-{family_code}-stats-table",
                                columns=[{"name": i, "id": i} for i in ("foo", "bar")],
                                fixed_rows={"headers": True},
                                # fixed_columns={'headers': True, 'data': 2},
                                style_cell={
                                    "minWidth": "80px",
                                    "width": "160px",
                                    "maxWidth": "160px",
                                    "textAlign": "center",
                                    "fontSize": TABLE_FONT_SIZE,
                                },
                                style_table={
                                    "minHeight": "600px",
                                    "height": "600px",
                                    "maxHeight": "600px",
                                    "minWidth": "100%",
                                    "width": "100%",
                                    "maxWidth": "100%",
                                    "overflowX": "scroll",
                                    "overflowY": "scroll",
                                },
                                style_header={
                                    "backgroundColor": HEADER_BACKGROUND_COLOR,
                                    "color": HEADER_FONT_COLOR,
                                    "fontWeight": "bold",
                                    "textAlign": "center",
                                    "fontSize": TABLE_FONT_SIZE,
                                },
                                filter_action="native",
                                sort_action="native",
                                sort_mode="multi",
                                row_selectable="multi",
                                export_format="xlsx",
                                selected_rows=[],
                            )
                        ),
                    ]
                ),
                className="pretty-container mb-3",
            ),

        ],
    )

################################### Callbacks ##################################################
def dashboard_callbacks(family_code, start, end):
    @callback(
        Output(f"{APP_PREFIX}-{family_code}-refresh-prompt", "children"),
        Input(f"{APP_PREFIX}-{family_code}-clear-cache-button", "n_clicks"),
    )
    def update_output(n_clicks):
        if n_clicks is not None:
            cache.delete_memoized(get_wafer_aggs)
            cache.delete_memoized(get_lot_aggs)
            #cache.delete_memoized(get_macro_data)
            return "Cache has been cleared. Please refresh the page."
    @callback(
        Output(f"{APP_PREFIX}-{family_code}-sail-graphs", "figure"),
        Input(f"{APP_PREFIX}-{family_code}-sail-n-lots", "value"),
    )
    def plot_sail_graphs(n: int):
        w_df = get_wafer_aggs(family_code, DEFAULT_START_DATE, DEFAULT_END_DATE, keys = 'all', category = 'all')

        fig = go.Figure()

        g_title = "Sail Aggregate Yields"
        plot_params = (
            ("sailall_vmin", "Sail ALL 0.50 to 1.05", "#53cf4e", True),
            ("sailall_vnom", "Sail ALL 0.65 to 1.05", "#25572d", True),
            ("sail1_vmin", "Sail 1 0.50 to 1.05", "#b53024", "legendonly"),
            ("sail1_vnom", "Sail 1 0.65 to 1.05", "#e06234", "legendonly"),
            ("sail2_vmin", "Sail 2 0.50 to 1.05", "#242bbd", "legendonly"),
            ("sail2_vnom", "Sail 2 0.65 to 1.05", "#3667b5", "legendonly"),
        )
        parm_labels = [
                "lot_id_base",
                "earliest_test_date",
                "sailall_vmin",
                "sailall_vnom",
                "sail1_vmin",
                "sail1_vnom",
                "sail2_vmin",
                "sail2_vnom",
            ]
        lot_ids = w_df[parm_labels].dropna().sort_values("earliest_test_date", ascending=False).lot_id_base.unique()[0:n]
        w_df_temp = (
            w_df.loc[:, ~w_df.columns.duplicated()]
            .loc[w_df["lot_id_base"].isin(lot_ids)]
            .sort_values("earliest_test_date", ascending=True)
        )

        for param in plot_params:
            fig.add_trace(
                go.Box(
                    y=w_df_temp[param[0]],
                    x=w_df_temp.lot_id_base,
                    name=param[1],
                    marker=dict(color=param[2]),
                    boxpoints="all",
                    visible=param[3],
                    text=w_df_temp.wafer_id,
                    hovertemplate="<b>%{text}</b>" + "<br>%{y:.2f}%",
                )
            )

        fig.update_layout(
            title=g_title,
            yaxis_title="Yield (%)",
            boxmode="group",  # group together boxes of the different traces for each value of x
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        return fig
    @callback(
        Output(f"{APP_PREFIX}-{family_code}-pele-graphs", "figure"),
        Input(f"{APP_PREFIX}-{family_code}-pele-choices", "value"),
        Input(f"{APP_PREFIX}-{family_code}-pele-n-lots", "value"),
    )
    def plot_pele_graphs(selected_item: str, n: int):
        if not selected_item:
            raise PreventUpdate()

        if not n:
            raise PreventUpdate()

        w_df = get_wafer_aggs(family_code, DEFAULT_START_DATE, DEFAULT_END_DATE, keys = 'all', category = 'all')

        fig = go.Figure()

        if selected_item == "agg":
            g_title = "Pele Aggregate Yields"
            plot_params = (
                ("peleall_1k_vmin", "PeleALL 1K 0.655 to 1.05", "#53cf4e", True),
                ("peleall_1k_vnom", "PeleALL 1K 0.75 to 1.05", "#25572d", True),
                ("peleall_m032_vmin", "PeleAll M032 0.655 to 1.05", "#b53024", True),
                ("peleall_m032_vnom", "PeleAll M032 0.75 to 1.05", "#e06234", True),
                ("peleall_m026vwb_vmin", "PeleAll M026VWB 0.655 to 1.05", "#242bbd", True),
                ("peleall_m026vwb_vnom", "PeleAll M026VWB 0.75 to 1.05", "#3667b5", True),
                ("peleall_m026vf6_vmin", "PeleAll M026VF6 0.655 to 1.05", "#42c0d4", "legendonly"),
                ("peleall_m026vf6_vnom", "PeleAll M026VF6 0.75 to 1.05", "#298391", "legendonly"),
                ("peleall_m026nbe_vmin", "PeleAll M026NBE 0.655 to 1.05", "#a06ce6", "legendonly"),
                ("peleall_m026nbe_vnom", "PeleAll M026NBE 0.75 to 1.05", "#6232a1", "legendonly"),
            )

        elif selected_item == "base":
            g_title = "Pele Yields"
            plot_params = (
                ("pele1_1k_vmin", "Pele1 1K 0.655 to 1.05", "#53cf4e", "legendonly"),
                ("pele1_1k_vnom", "Pele1 1K 0.75 to 1.05", "#25572d", True),
                ("pele2_1k_vmin", "Pele2 1K 0.655 to 1.05", "#b53024", "legendonly"),
                ("pele2_1k_vnom", "Pele2 1K 0.75 to 1.05", "#e06234", True),
                ("pele1_m032_vmin", "Pele1 M032 0.655 to 1.05", "#242bbd", "legendonly"),
                ("pele1_m032_vnom", "Pele1 M032 0.75 to 1.05", "#3667b5", True),
                ("pele2_m032_vmin", "Pele2 M032 0.655 to 1.05", "#42c0d4", "legendonly"),
                ("pele2_m032_vnom", "Pele2 M032 0.75 to 1.05", "#298391", True),
                ("pele1_m026vwb_vmin", "Pele1 M026VWB 0.655 to 1.05", "#a06ce6", "legendonly"),
                ("pele1_m026vwb_vnom", "Pele1 M026VWB 0.75 to 1.05", "#6232a1", True),
                ("pele2_m026vwb_vmin", "Pele2 M026VWB 0.655 to 1.05", "#f5cf45", "legendonly"),
                ("pele2_m026vwb_vnom", "Pele2 M026VWB 0.75 to 1.05", "#e8a70e", True),
                ("pele1_m026vf6_vmin", "Pele1 M026VF6 0.655 to 1.05", "#f090ed", "legendonly"),
                ("pele1_m026vf6_vnom", "Pele1 M026VF6 0.75 to 1.05", "#d121cc", "legendonly"),
                ("pele2_m026vf6_vmin", "Pele2 M026VF6 0.655 to 1.05", "#eda17b", "legendonly"),
                ("pele2_m026vf6_vnom", "Pele2 M026VF6 0.75 to 1.05", "#ed621c", "legendonly"),
                ("pele1_m026nbe_vmin", "Pele1 M026NBE 0.655 to 1.05", "#bced1c", "legendonly"),
                ("pele1_m026nbe_vnom", "Pele1 M026NBE 0.75 to 1.05", "#86e31b", "legendonly"),
                ("pele2_m026nbe_vmin", "Pele2 M026NBE 0.655 to 1.05", "#e884b6", "legendonly"),
                ("pele2_m026nbe_vnom", "Pele2 M026NBE 0.75 to 1.05", "#e01078", "legendonly"),
            )
        parm_labels = [
                "lot_id_base",
                "earliest_test_date",
                "peleall_1k_vnom",
                "peleall_1k_vmin",
                "peleall_m032_vnom",
                "peleall_m032_vmin",
                "peleall_m026vwb_vnom",
                "peleall_m026vwb_vmin",
                "peleall_m026vf6_vnom",
                "peleall_m026vf6_vmin",
                "peleall_m026nbe_vnom",
                "peleall_m026nbe_vmin",
            ]
        lot_ids = w_df[parm_labels].dropna().sort_values("earliest_test_date", ascending=False).lot_id_base.unique()[0:n]
        w_df_temp = (
            w_df.loc[:, ~w_df.columns.duplicated()]
            .loc[w_df["lot_id_base"].isin(lot_ids)]
            .sort_values("earliest_test_date", ascending=True)
        )

        for param in plot_params:
            fig.add_trace(
                go.Box(
                    y=w_df_temp[param[0]],
                    x=w_df_temp.lot_id_base,
                    name=param[1],
                    marker=dict(color=param[2]),
                    boxpoints="all",
                    visible=param[3],
                    text=w_df_temp.wafer_id,
                    hovertemplate="<b>%{text}</b>" + "<br>%{y:.2f}%",
                )
            )

        fig.update_layout(
            title=g_title,
            yaxis_title="Yield (%)",
            boxmode="group",  # group together boxes of the different traces for each value of x
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        return fig
    @callback(
        Output(f"{APP_PREFIX}-{family_code}-stats-table", "columns"),
        Output(f"{APP_PREFIX}-{family_code}-stats-table", "data"),
        Output(f"{APP_PREFIX}-{family_code}-stats-table", "style_data_conditional"),
        Output(f"{APP_PREFIX}-{family_code}-stats-table", "style_cell_conditional"),
        Input(f"{APP_PREFIX}-{family_code}-level-choices", "value"),
    )
    def toggle_lotwafer_table(selected_item: str):
        if not selected_item:
            raise PreventUpdate()

        if selected_item == "lot":
            data = get_lot_aggs(family_code, start, end, ['L1'])
            style_cell_conditional = [
                {"if": {"column_id": "lot_id_base"}, "width": "110px"},
                {"if": {"column_id": "lot_id"}, "width": "110px"},
                {"if": {"column_id": "family_code"}, "width": "110px"},
                {"if": {"column_id": "earliest_test_date"}, "width": "120px"},
                #{"if": {"column_id": "sail_n"}, "width": "80px"},
                #{"if": {"column_id": "pele_n"}, "width": "80px"},
            ]
            conditional_highlight = [
            #     {"if": {"column_id": "lot_id"}, "backgroundColor": HIGHLIGHT},
            #     {
            #         "if": {
            #             "filter_query": "{num_wafers_with_canop} > 0",
            #             "column_id": "num_wafers_with_canop",
            #         },
            #         "backgroundColor": BAD_RED,
            #     },
            #     {
            #         "if": {
            #             "filter_query": "{pct_wafers_with_canop} > 0",
            #             "column_id": "pct_wafers_with_canop",
            #         },
            #         "backgroundColor": BAD_RED,
            #     }
            ]
            conditional_ignore = [] #["sail_n", "pele_n", "num_wafers_with_canop", "pct_wafers_with_canop"]
        elif selected_item == "wafer":
            data = get_wafer_aggs(family_code, start, end, ['L1'])
            style_cell_conditional = [
                {"if": {"column_id": "lot_id_base"}, "width": "110px"},
                {"if": {"column_id": "lot_id"}, "width": "110px"},
                {"if": {"column_id": "wafer_id"}, "width": "110px"},
                {"if": {"column_id": "family_code"}, "width": "110px"},
                {"if": {"column_id": "earliest_test_date"}, "width": "120px"},
            ]
            conditional_highlight = [
            #     {"if": {"column_id": "wafer_id"}, "backgroundColor": HIGHLIGHT},
            #     {
            #         "if": {
            #             "filter_query": "{abc_dbc_bit_count} > 0",
            #             "column_id": "abc_dbc_bit_count",
            #         },
            #         "backgroundColor": BAD_RED,
            #     },
            #     {
            #         "if": {
            #             "filter_query": "{canop_yieldloss} > 0",
            #             "column_id": "canop_yieldloss",
            #         },
            #         "backgroundColor": BAD_RED,
            #     }
            ]
            conditional_ignore = [] #["abc_dbc_bit_count", "canop_yieldloss", "sail_n", "pele_n"]
        else:
            raise ValueError(f"unknown selection '{selected_item}'")

        style_data_conditional = (
            [
                {"if": {"filter_query": f"{{{col}}} >= {97}", "column_id": col}, "backgroundColor": GOOD_GREEN}
                for (col, value) in data.drop(columns=conditional_ignore).quantile(0.90, numeric_only=True).items()
            ]
            + [
                {"if": {"filter_query": f"{{{col}}} <= {90}", "column_id": col}, "backgroundColor": BAD_RED}
                for (col, value) in data.drop(columns=conditional_ignore).quantile(0.10, numeric_only=True).items()
            ]
            + conditional_highlight
        )

        # if selected_item == "wafer":
        #     data = data.drop(columns=["sail_n", "pele_n"])

        columns = [{"name": i, "id": i} for i in data.columns]
        data_dict = data.fillna("-").to_dict("records")

        return columns, data_dict, style_data_conditional, style_cell_conditional
################################## Generate Dashboard ##########################################
layout = html.Div(
    dcc.Tabs(
        id=f"{APP_PREFIX}_tabs",
        children=[
            #create_tab("All 7HPP Products (2SAIL+1Pele)", "all"),
            create_tab("zMetis DD1 Only", "M1"),
            #create_tab("zA DD2 Only", "X2")
        ]
    )
)
#dashboard_callbacks(DAYSBACK, 'all')
dashboard_callbacks('M1', DEFAULT_START_DATE, DEFAULT_END_DATE)
#dashboard_callbacks(DAYSBACK, 'X2')