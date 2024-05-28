import datetime

from dash import dcc, html, dash_table as dt, Input, Output, callback
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import ibmdata
import numpy as np
from pelib.sandbox import canop
import plotly.express as px
import plotly.graph_objects as go

from .. import cache, register_page

HEADER_BACKGROUND_COLOR = "#343A40"
HEADER_FONT_COLOR = "white"
GOOD_GREEN = "#99FF99"
BAD_RED = "#FF9999"
HIGHLIGHT = "#FFF700"
APP_PREFIX = "pti_inline_func_dashboard"
TABLE_FONT_SIZE = "0.7em"
DAYSBACK = 365

register_page(
    __name__,
    menu="PTIApps:Inline Func",
    path="/pti_apps/inline_func/dashboard",
    description="Inline Dashboard",
    title="Inline Dashboard"
)


# ############## SQL Queries ##################################################################
def generate_query(daysback, family_code):
    if family_code == 'all':
        family_code = "'X2','Q6','Q5','XQ'"
    else:
        family_code = f"'{family_code}'"
    return f"""
    WITH lot_name_cte AS(
        SELECT DISTINCT wafer_id, E.CELL_NAME AS Lot_Name
        FROM DMIW_SYSTEMS.WAFER A,
            DMIW_SYSTEMS.PRODUCT B,
            DMIW_SYSTEMS.EWR_EVENT_FACT C,
            DMIW_SYSTEMS.EWR_EVENT D,
            DMIW_SYSTEMS.EWR_CELL E
        WHERE A.WAFERKEY=C.WAFERKEY
            AND B.PRODUCTKEY=C.PRODUCTKEY
            AND  C.EWR_CELLKEY=E.EWR_CELLKEY
            AND OWNER_USER_ID='hai.zhu@ibm.com'
            AND EWR_NAME IN ('7HPP_Name_P10', '7HPP_Name_zA')
            AND (CELL_ID LIKE '7HPP_Name_P10%' OR CELL_ID LIKE '7HPP_Name_zA%')
            AND E.CELL_NAME NOT IN ('Lot0-1','Lot0-2','uncertain')
            AND B.FAMILY_CODE IN ({family_code})
    ),
    sail_cte AS(
        SELECT LEFT(wafer_id,5) AS lot_id_base, lot_id, wafer_id, family_code, 
          MIN(tw.Last_test_date) AS Sail_date, 1 AS Sail_n,
          AVG(CASE WHEN parm_Label = 'SAIL23_H2_0p50to1p05_PerfectYield' THEN yield ELSE NULL END) AS SAILALL_0p50to1p05,
          AVG(CASE WHEN parm_Label = 'SAIL23_H2_0p65to1p05_PerfectYield' THEN yield ELSE NULL END) AS SAILALL_0p65to1p05,
          AVG(CASE WHEN parm_Label = 'SAIL2_H2_0p50to1p05_PerfectYield' THEN yield ELSE NULL END) AS SAIL2_0p50to1p05,
          AVG(CASE WHEN parm_Label = 'SAIL2_H2_0p65to1p05_PerfectYield' THEN yield ELSE NULL END) AS SAIL2_0p65to1p05,
          AVG(CASE WHEN parm_Label = 'SAIL3_H2_0p50to1p05_PerfectYield' THEN yield ELSE NULL END) AS SAIL3_0p50to1p05,
          AVG(CASE WHEN parm_Label = 'SAIL3_H2_0p65to1p05_PerfectYield' THEN yield ELSE NULL END) AS SAIL3_0p65to1p05
        FROM DMIW_SYSTEMS.PTileWaferFact ptwf
        INNER JOIN DMIW_SYSTEMS.TestParm tp ON ptwf.testparmkey = tp.testparmkey
        INNER JOIN DMIW_SYSTEMS.TestedWafer tw ON ptwf.testedWaferKey = tw.testedWaferKey
        WHERE tw.Last_test_date >= (current date - {daysback} days)
          AND tw.Tech_id = '7HPP'
          AND tw.Level = 'H2'
          AND tw.Calcdefs in ('SSL11', 'SSL21', 'SSL31')
          AND weighted_Mean IS NOT null AND ABS(weighted_Mean) < 1e25
          AND UCASE(tp.parm_Label) LIKE '%_PERFECTYIELD'
          AND FAMILY_CODE IN ({family_code})
        GROUP BY lot_id, wafer_id, family_code
        ORDER BY Sail_date desc, lot_id, wafer_id
    ),
    pele_cte AS(
        SELECT lot_Id, wafer_Id, family_code, MIN(last_Test_Date) AS Pele_date, 1 as Pele_n,
           AVG(CASE WHEN ucase(tp.parm_Label) = 'PELE1_H2_L3_HL_PERFECTYIELD' THEN yield ELSE null END) AS PELE1_L3_Vmax_PY,
           AVG(CASE WHEN ucase(tp.parm_Label) = 'PELE1_H2_L3_NL_PERFECTYIELD' THEN yield ELSE null END) AS PELE1_L3_Vnom_PY,
           AVG(CASE WHEN ucase(tp.parm_Label) = 'PELE1_H2_L3_LL_PERFECTYIELD' THEN yield ELSE null END) AS PELE1_L3_Vmin_PY,
           AVG(CASE WHEN ucase(tp.parm_Label) = 'PELE1_H2_1K_HL_PERFECTYIELD' THEN yield ELSE null END) AS PELE1_1K_Vmax_PY,
           AVG(CASE WHEN ucase(tp.parm_Label) = 'PELE1_H2_1K_NL_PERFECTYIELD' THEN yield ELSE null END) AS PELE1_1K_Vnom_PY,
           AVG(CASE WHEN ucase(tp.parm_Label) = 'PELE1_H2_1K_LL_PERFECTYIELD' THEN yield ELSE null END) AS PELE1_1K_Vmin_PY
        FROM DMIW_SYSTEMS.PTileWaferFact ptwf
        INNER JOIN DMIW_SYSTEMS.TestParm tp ON tp.testParmKey = ptwf.testParmKey 
        INNER JOIN DMIW_SYSTEMS.TestedWafer tw ON tw.testedWaferKey = ptwf.testedWaferKey
        WHERE Last_test_date >= (current date - {daysback} days) AND
            Tech_id = '7HPP' and Level = 'H2' AND tw.Calcdefs IN ('PEL11', 'PEL21', 'PEL31') AND
            weighted_Mean IS NOT null AND abs(weighted_Mean) < 1e25 AND
            (ucase(tp.parm_Label) LIKE 'PELE%_H2_%PERFECTYIELD')
            AND FAMILY_CODE IN ({family_code})
        GROUP BY lot_Id, wafer_Id, family_code
    )
    SELECT ln.lot_name, s.lot_id_base, s.lot_id, s.family_code, Sail_date, Sail_n, s.wafer_id, 
        SAILALL_0p50to1p05, SAILALL_0p65to1p05,
        SAIL2_0p50to1p05, SAIL2_0p65to1p05, SAIL3_0p50to1p05, SAIL3_0p65to1p05,
        Pele_date, Pele_n, s.wafer_id AS wafer_id_2,
        PELE1_L3_Vmax_PY, PELE1_L3_Vnom_PY, PELE1_L3_Vmin_PY,
        PELE1_1K_Vmax_PY, PELE1_1K_Vnom_PY, PELE1_1K_Vmin_PY
    FROM sail_cte s
    FULL OUTER JOIN pele_cte p ON s.wafer_id = p.wafer_id
    LEFT JOIN lot_name_cte ln ON s.wafer_id = ln.wafer_id
    ORDER BY Sail_date desc, s.lot_id, s.wafer_id
    """


@cache.memoize(timeout=21600)
def get_wafer_data(daysback, family_code):
    w_df = ibmdata.isdw.query(generate_query(daysback, family_code))

    canop_yl = canop.yield_loss(daysback)

    w_df = w_df.merge(canop_yl, how='left', on=['lot_id_base', 'wafer_id', 'family_code'])

    w_df = w_df.rename(columns={"wafer_id_2": "wafer_id"})
    w_df["sailall_0p50to1p05"] = w_df["sailall_0p50to1p05"].astype(float).round(2)
    w_df["sailall_0p65to1p05"] = w_df["sailall_0p65to1p05"].astype(float).round(2)
    w_df["sail2_0p50to1p05"] = w_df["sail2_0p50to1p05"].astype(float).round(2)
    w_df["sail2_0p65to1p05"] = w_df["sail2_0p65to1p05"].astype(float).round(2)
    w_df["sail3_0p50to1p05"] = w_df["sail3_0p50to1p05"].astype(float).round(2)
    w_df["sail3_0p65to1p05"] = w_df["sail3_0p65to1p05"].astype(float).round(2)

    w_df["pele1_l3_vmax_py"] = w_df["pele1_l3_vmax_py"].astype(float).round(2)
    w_df["pele1_l3_vnom_py"] = w_df["pele1_l3_vnom_py"].astype(float).round(2)
    w_df["pele1_l3_vmin_py"] = w_df["pele1_l3_vmin_py"].astype(float).round(2)
    w_df["pele1_1k_vmax_py"] = w_df["pele1_1k_vmax_py"].astype(float).round(2)
    w_df["pele1_1k_vnom_py"] = w_df["pele1_1k_vnom_py"].astype(float).round(2)
    w_df["pele1_1k_vmin_py"] = w_df["pele1_1k_vmin_py"].astype(float).round(2)

    #w_df["canop_yieldloss"] = w_df["canop_yieldloss"].astype(float).round(2)

    return w_df.sort_values("sail_date", ascending=False)


@cache.memoize(timeout=21600)
def get_lot_data(daysback, family_code):
    # Lot Level df
    temp_agg_df = get_wafer_data(daysback, family_code)
    temp_agg_df["sail_date"] = temp_agg_df["sail_date"].fillna(datetime.date(9999, 12, 30))
    temp_agg_df["pele_date"] = temp_agg_df["pele_date"].fillna(datetime.date(9999, 12, 30))
    temp_agg_df["lot_name"] = temp_agg_df["lot_name"].fillna("")

    lot_df = (
        temp_agg_df.groupby(["lot_name", "lot_id_base", "lot_id", "family_code"])
        .agg(
            {
                "sail_date": "min",
                "sail_n": "sum",
                "sailall_0p50to1p05": "mean",
                "sailall_0p65to1p05": "mean",
                "sail2_0p50to1p05": "mean",
                "sail2_0p65to1p05": "mean",
                "sail3_0p50to1p05": "mean",
                "sail3_0p65to1p05": "mean",
                "pele_date": "min",
                "pele_n": "sum",
                "pele1_l3_vmax_py": "mean",
                "pele1_l3_vnom_py": "mean",
                "pele1_l3_vmin_py": "mean",
                "pele1_1k_vmax_py": "mean",
                "pele1_1k_vnom_py": "mean",
                "pele1_1k_vmin_py": "mean",
                "num_wafers_with_canop": "sum",
                "pct_wafers_with_canop": "mean",
            }
        )
        .round(2)
        .sort_values("sail_date", ascending=False)
        .reset_index()
    )

    # Add lot_id columns in the middle of the table
    lot_df.insert(12, "lot_id_2", lot_df.lot_id)
    lot_ids = lot_df.lot_id
    lot_df = lot_df.drop(columns=["lot_id"])
    lot_df.insert(5, "lot_id", lot_ids)
    lot_df = lot_df.rename(columns={"lot_id_2": "lot_id", "lot_id_3": "lot_id"})
    lot_df["sail_date"] = lot_df["sail_date"].replace(datetime.date(9999, 12, 30), np.nan)
    lot_df["pele_date"] = lot_df["pele_date"].replace(datetime.date(9999, 12, 30), np.nan)

    return lot_df


@cache.memoize(timeout=21600)
def get_macro_data(selected_item: str, n: int, daysback: int, family_code: str):
    w_df = get_wafer_data(daysback, family_code)
    w_df["lot_name"] = w_df["lot_name"].fillna("")

    if selected_item == "sail":
        parm_labels = [
            "lot_name",
            "lot_id_base",
            "sail_date",
            "sailall_0p50to1p05",
            "sailall_0p65to1p05",
            "sail2_0p50to1p05",
            "sail2_0p65to1p05",
            "sail3_0p50to1p05",
            "sail3_0p65to1p05",
        ]
        sort_date = "sail_date"
    elif selected_item == "pele":
        parm_labels = [
            "lot_name",
            "lot_id_base",
            "pele_date",
            "pele1_l3_vmax_py",
            "pele1_l3_vnom_py",
            "pele1_l3_vmin_py",
            "pele1_1k_vmax_py",
            "pele1_1k_vnom_py",
            "pele1_1k_vmin_py",
        ]
        sort_date = "pele_date"
    else:
        raise ValueError(f"item {selected_item} is not supported")

    lot_ids = w_df[parm_labels].dropna().sort_values(sort_date, ascending=False).lot_id_base.unique()[0:n]
    w_df_temp = (
        w_df.loc[:, ~w_df.columns.duplicated()]
        .loc[w_df["lot_id_base"].isin(lot_ids)]
        .sort_values(sort_date, ascending=True)
    )
    w_df_temp["xlabel"] = np.where(
        w_df_temp.lot_name == "", w_df_temp.lot_id_base, w_df_temp.lot_id_base + " (" + w_df_temp.lot_name + ")"
    )

    return w_df_temp


############################################## HTML Section ####################################################

def create_tab(tab_name: str, family_code: str):
    return dcc.Tab(
        label=tab_name,
        children=[
            dbc.Row(
                [
                    dbc.Col(
                        dcc.Markdown(
                            f"""\
                    #### 7HPP Inline Characterization Dashboard

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
                        html.H5("7HPP Inline Functional Yield Trends"),
                        dbc.Form(
                            dbc.Row(
                                [
                                    dbc.Label(
                                        "Macros:",
                                        html_for=f"{APP_PREFIX}-{family_code}-macro-choices",
                                        width="auto",
                                    ),
                                    dbc.Col(
                                        dcc.RadioItems(
                                            id=f"{APP_PREFIX}-{family_code}-macro-choices",
                                            options=[
                                                {"label": "Sail", "value": "sail"},
                                                {"label": "Pele", "value": "pele"},
                                            ],
                                            value="sail",
                                            inputClassName="me-1",
                                            labelClassName="me-3",
                                        ),
                                    ),
                                    dbc.Label(
                                        "Number of Most Recent Lots to Show:",
                                        html_for=f"{APP_PREFIX}-{family_code}-n-lots",
                                        width="auto",
                                    ),
                                    dbc.Col(
                                        dcc.Slider(
                                            id=f"{APP_PREFIX}-{family_code}-n-lots",
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
                            dcc.Graph(id=f"{APP_PREFIX}-{family_code}-macro-graphs"),
                        ),
                    ]
                ),
                className="pretty-container mb-3",
            ),
            dbc.Row(
                dbc.Col(
                    [
                        html.H5("CANOP Trend"),
                        dbc.Form(
                            dbc.Row(
                                [
                                    dbc.Label(
                                        "Macros:",
                                        html_for=f"{APP_PREFIX}-{family_code}-canop-choices",
                                        width="auto",
                                    ),
                                    dbc.Col(
                                        dcc.RadioItems(
                                            id=f"{APP_PREFIX}-{family_code}-canop-choices",
                                            options=[
                                                {"label": "Yield Loss", "value": "canop_yieldloss"},
                                                {"label": "Fail Density", "value": "abc_dbc_bit_count"},
                                            ],
                                            value="canop_yieldloss",
                                            inputClassName="me-1",
                                            labelClassName="me-3",
                                        ),
                                    ),
                                ],
                                align="center",
                            )
                        ),
                        dbc.Spinner(
                            dcc.Graph(id=f"{APP_PREFIX}-{family_code}-canop-graphs"),
                        ),
                    ]
                ),
                className="pretty-container mb-3",
            ),
            dbc.Row(
                dbc.Col(
                    [
                        html.H5("7HPP Inline Functional Yield Table"),
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


################################################## Callbacks ##################################
def dashboard_callbacks(daysback, family_code):
    @callback(
        Output(f"{APP_PREFIX}-{family_code}-refresh-prompt", "children"),
        Input(f"{APP_PREFIX}-{family_code}-clear-cache-button", "n_clicks"),
    )
    def update_output(n_clicks):
        if n_clicks is not None:
            cache.delete_memoized(get_wafer_data)
            cache.delete_memoized(get_lot_data)
            cache.delete_memoized(get_macro_data)
            return "Cache has been cleared. Please refresh the page."


    @callback(
        Output(f"{APP_PREFIX}-{family_code}-macro-graphs", "figure"),
        Input(f"{APP_PREFIX}-{family_code}-macro-choices", "value"),
        Input(f"{APP_PREFIX}-{family_code}-n-lots", "value"),
    )
    def generate_macro_graphs(selected_item: str, n: int):
        if not selected_item:
            raise PreventUpdate()

        if not n:
            raise PreventUpdate()

        w_df_temp = get_macro_data(selected_item, n, daysback, family_code)
        fig = go.Figure()

        if selected_item == "sail":
            g_title = "Sail Yields"
            plot_params = (
                ("sailall_0p50to1p05", "Sail ALL 0.50 to 1.05", "#25572d", True),
                ("sailall_0p65to1p05", "Sail ALL 0.65 to 1.05", "#a62626", True),
                ("sail2_0p50to1p05", "Sail 2 0.50 to 1.05", "#25ba97", "legendonly"),
                ("sail2_0p65to1p05", "Sail 2 0.65 to 1.05", "#ffaf36", "legendonly"),
                ("sail3_0p50to1p05", "Sail 3 0.50 to 1.05", "#0cf00c", "legendonly"),
                ("sail3_0p65to1p05", "Sail 3 0.65 to 1.05", "#e6d70e", "legendonly"),
            )

        elif selected_item == "pele":
            g_title = "Pele Yields"
            plot_params = (
                ("pele1_l3_vmax_py", "Pele1 L3 1.05v", "#25ba97", True),
                ("pele1_l3_vnom_py", "Pele1 L3 0.75v", "#FF4136", True),
                ("pele1_l3_vmin_py", "Pele1 L3 0.655v", "#0e6fe6", True),
                ("pele1_1k_vmax_py", "Pele1 1K 1.05v", "#0cf00c", "legendonly"),
                ("pele1_1k_vnom_py", "Pele1 1K 0.75v", "#ffaf36", "legendonly"),
                ("pele1_1k_vmin_py", "Pele1 1K 0.655v", "#0edbe6", "legendonly"),
            )

        else:
            raise ValueError(f"unknown selection '{selected_item}'")

        for param in plot_params:
            fig.add_trace(
                go.Box(
                    y=w_df_temp[param[0]],
                    x=w_df_temp.xlabel,
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
            data = get_lot_data(daysback, family_code)
            style_cell_conditional = [
                {"if": {"column_id": "lot_name"}, "width": "90px"},
                {"if": {"column_id": "lot_id_base"}, "width": "110px"},
                {"if": {"column_id": "lot_id"}, "width": "110px"},
                {"if": {"column_id": "family_code"}, "width": "110px"},
                {"if": {"column_id": "sail_date"}, "width": "100px"},
                {"if": {"column_id": "sail_n"}, "width": "80px"},
                {"if": {"column_id": "pele_date"}, "width": "100px"},
                {"if": {"column_id": "pele_n"}, "width": "80px"},
            ]
            conditional_highlight = [
                {"if": {"column_id": "lot_id"}, "backgroundColor": HIGHLIGHT},
                {
                    "if": {
                        "filter_query": "{num_wafers_with_canop} > 0",
                        "column_id": "num_wafers_with_canop",
                    },
                    "backgroundColor": BAD_RED,
                },
                {
                    "if": {
                        "filter_query": "{pct_wafers_with_canop} > 0",
                        "column_id": "pct_wafers_with_canop",
                    },
                    "backgroundColor": BAD_RED,
                }
            ]
            conditional_ignore = ["sail_n", "pele_n", "num_wafers_with_canop", "pct_wafers_with_canop"]
        elif selected_item == "wafer":
            data = get_wafer_data(daysback, family_code)
            data = data.drop(columns=['date', 'num_wafers_with_canop', 'pct_wafers_with_canop'])
            style_cell_conditional = [
                {"if": {"column_id": "lot_name"}, "width": "90px"},
                {"if": {"column_id": "lot_id_base"}, "width": "110px"},
                {"if": {"column_id": "lot_id"}, "width": "110px"},
                {"if": {"column_id": "wafer_id"}, "width": "110px"},
                {"if": {"column_id": "family_code"}, "width": "110px"},
                {"if": {"column_id": "sail_date"}, "width": "100px"},
                {"if": {"column_id": "pele_date"}, "width": "100px"},
            ]
            conditional_highlight = [
                {"if": {"column_id": "wafer_id"}, "backgroundColor": HIGHLIGHT},
                {
                    "if": {
                        "filter_query": "{abc_dbc_bit_count} > 0",
                        "column_id": "abc_dbc_bit_count",
                    },
                    "backgroundColor": BAD_RED,
                },
                {
                    "if": {
                        "filter_query": "{canop_yieldloss} > 0",
                        "column_id": "canop_yieldloss",
                    },
                    "backgroundColor": BAD_RED,
                }
            ]
            conditional_ignore = ["abc_dbc_bit_count", "canop_yieldloss", "sail_n", "pele_n"]
        else:
            raise ValueError(f"unknown selection '{selected_item}'")

        style_data_conditional = (
            [
                {"if": {"filter_query": f"{{{col}}} >= {value}", "column_id": col}, "backgroundColor": GOOD_GREEN}
                for (col, value) in data.drop(columns=conditional_ignore).quantile(0.75, numeric_only=True).items()
            ]
            + [
                {"if": {"filter_query": f"{{{col}}} <= {value}", "column_id": col}, "backgroundColor": BAD_RED}
                for (col, value) in data.drop(columns=conditional_ignore).quantile(0.25, numeric_only=True).items()
            ]
            + conditional_highlight
        )

        if selected_item == "wafer":
            data = data.drop(columns=["sail_n", "pele_n"])

        columns = [{"name": i, "id": i} for i in data.columns]
        data_dict = data.fillna("-").to_dict("records")

        return columns, data_dict, style_data_conditional, style_cell_conditional

    # callback for CANOP graph
    @callback(
        Output(f"{APP_PREFIX}-{family_code}-canop-graphs", "figure"),
        Input(f"{APP_PREFIX}-{family_code}-canop-choices", "value"),
    )
    def generate_macro_graphs(selected_item: str):
        if not selected_item:
            raise PreventUpdate()

        data = get_wafer_data(daysback, family_code)

        data.sort_values(['date','lot_id_base'],inplace=True)
        xorder = data['lot_id_base'].unique()

        fig = px.strip(data,x='lot_id_base',y=selected_item,color='family_code')
        fig.update_xaxes(categoryorder='array', categoryarray=xorder)
        return fig


layout = html.Div(
    dcc.Tabs(
        id=f"{APP_PREFIX}_tabs",
        children=[
            create_tab("All 7HPP Products (2SAIL+1Pele)", "all"),
            create_tab("P10 DD2 Only", "Q6"),
            create_tab("zA DD2 Only", "X2")
        ]
    )
)
dashboard_callbacks(DAYSBACK, 'all')
dashboard_callbacks(DAYSBACK, 'Q6')
dashboard_callbacks(DAYSBACK, 'X2')
