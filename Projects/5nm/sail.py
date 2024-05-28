import ibmdata
import pandas as pd
import copy

import plotly.express as px
import plotly.figure_factory as ff
from dash import dcc, html, dash_table as dt, callback
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc

# from apps.inline_func.ay_useful_functions import empty_figure
from .. import cache, LOG, register_page
from ..utils import COL_WIDTH_AUTO, empty_figure

APP_PREFIX = "pti_sail_app"
HEADER_BACKGROUND_COLOR = "#343A40"
HEADER_FONT_COLOR = "white"
GOOD_GREEN = "#99FF99"
BAD_RED = "#FF9999"
color_map = {"SSL1": "tomato", "SSL2": "springgreen", "SSL3": "dodgerblue"}
TABLE_FONT_SIZE = "0.7em"

register_page(
    __name__,
    menu="PTIApps:Sail",
    path="/pti_apps/inline_func/sail",
    description="Sail Dashboard",
    title='Sail Dashboard'
)

########################################################################################################################
# SQL Yield Pulls For Sail Analysis Tab

DAYSBACK = 365
QUERY = f"""
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
        AND EWR_NAME IN ('7HPP_Name_P10')
        AND CELL_ID LIKE '7HPP_Name_P10%'
        AND E.CELL_NAME NOT IN ('Lot0-1','Lot0-2','uncertain')
),
sail_cte AS(
    SELECT --LEFT(wafer_id,5) AS lot_id_base, 
        lot_id, wafer_id, MIN(tw.Last_test_date) AS date,
        AVG(CASE WHEN parm_Label = 'SAILALL_H2_0p50to1p05_PerfectYield' THEN yield ELSE NULL END) AS SAILALL_0p50to1p05,
        AVG(CASE WHEN parm_Label = 'SAILALL_H2_0p65to1p05_PerfectYield' THEN yield ELSE NULL END) AS SAILALL_0p65to1p05,
        AVG(CASE WHEN parm_Label = 'SAIL1_H2_0p50to1p05_PerfectYield' THEN yield ELSE NULL END) AS SAIL1_0p50to1p05,
        AVG(CASE WHEN parm_Label = 'SAIL1_H2_0p65to1p05_PerfectYield' THEN yield ELSE NULL END) AS SAIL1_0p65to1p05,
        AVG(CASE WHEN parm_Label = 'SAIL2_H2_0p50to1p05_PerfectYield' THEN yield ELSE NULL END) AS SAIL2_0p50to1p05,
        AVG(CASE WHEN parm_Label = 'SAIL2_H2_0p65to1p05_PerfectYield' THEN yield ELSE NULL END) AS SAIL2_0p65to1p05,
        AVG(CASE WHEN parm_Label = 'SAIL3_H2_0p50to1p05_PerfectYield' THEN yield ELSE NULL END) AS SAIL3_0p50to1p05,
        AVG(CASE WHEN parm_Label = 'SAIL3_H2_0p65to1p05_PerfectYield' THEN yield ELSE NULL END) AS SAIL3_0p65to1p05
    FROM DMIW_SYSTEMS.PTileWaferFact ptwf
    INNER JOIN DMIW_SYSTEMS.TestParm tp ON ptwf.testparmkey = tp.testparmkey
    INNER JOIN DMIW_SYSTEMS.TestedWafer tw ON ptwf.testedWaferKey = tw.testedWaferKey
    WHERE tw.Last_test_date >= (current date - {DAYSBACK} days)
        AND tw.Tech_id = '7HPP'
        AND tw.Level = 'H2'
        AND tw.Calcdefs in ('SSL11', 'SSL21', 'SSL31')
        AND weighted_Mean IS NOT null AND ABS(weighted_Mean) < 1e25
        AND UCASE(tp.parm_Label) LIKE '%_PERFECTYIELD'
    GROUP BY lot_id, wafer_id, family_code
    ORDER BY date desc, lot_id, wafer_id
)
SELECT ln.Lot_Name, s.*
FROM sail_cte s
LEFT JOIN lot_name_cte ln ON ln.wafer_id = s.wafer_id
ORDER BY date desc, lot_id, wafer_id
"""


@cache.memoize(timeout=21600)
def get_wafer_data():
    w_df = ibmdata.isdw.query(QUERY)
    w_df["sailall_0p50to1p05"] = w_df["sailall_0p50to1p05"].astype(float).round(2)
    w_df["sailall_0p65to1p05"] = w_df["sailall_0p65to1p05"].astype(float).round(2)
    w_df["sail1_0p50to1p05"] = w_df["sail1_0p50to1p05"].astype(float).round(2)
    w_df["sail1_0p65to1p05"] = w_df["sail1_0p65to1p05"].astype(float).round(2)
    w_df["sail2_0p50to1p05"] = w_df["sail2_0p50to1p05"].astype(float).round(2)
    w_df["sail2_0p65to1p05"] = w_df["sail2_0p65to1p05"].astype(float).round(2)
    w_df["sail3_0p50to1p05"] = w_df["sail3_0p50to1p05"].astype(float).round(2)
    w_df["sail3_0p65to1p05"] = w_df["sail3_0p65to1p05"].astype(float).round(2)
    return w_df


@cache.memoize(timeout=21600)
def get_lot_data():
    w_df = get_wafer_data()
    w_df["lot_name"] = w_df["lot_name"].fillna("")
    lot_df = (
        w_df.groupby(["lot_name", "lot_id"])
        .agg(
            {
                "date": "min",
                "sailall_0p50to1p05": "mean",
                "sailall_0p65to1p05": "mean",
                "sail1_0p50to1p05": "mean",
                "sail1_0p65to1p05": "mean",
                "sail2_0p50to1p05": "mean",
                "sail2_0p65to1p05": "mean",
                "sail3_0p50to1p05": "mean",
                "sail3_0p65to1p05": "mean",
            }
        )
        .round(2)
        .sort_values("date", ascending=False)
        .reset_index()
    )
    return lot_df


@cache.memoize(timeout=21600)
def get_block_data(corner="vnom"):
    if corner == "vmin":
        CORNER = "_H2_0P50V_BLOCK"
    elif corner == "vnom":
        CORNER = "_H2_0P75V_BLOCK"
    elif corner == "vmax":
        CORNER = "_H2_1P05V_BLOCK"
    else:
        return None

    block_query = f"""
    SELECT lot_id, wafer_id, tw.testProgramName AS step,
        tw.testProgramName||RIGHT(parm_Label,8) AS label, yield, 100 - yield AS yld_loss
    FROM DMIW_SYSTEMS.PTileWaferFact ptwf
    INNER JOIN DMIW_SYSTEMS.TestParm tp ON ptwf.testparmkey = tp.testparmkey
    INNER JOIN DMIW_SYSTEMS.TestedWafer tw ON ptwf.testedWaferKey = tw.testedWaferKey
    WHERE tw.Last_test_date >= (current date - {DAYSBACK} days)
        AND tw.Tech_id = '7HPP'
        AND tw.Level = 'H2'
        AND tw.Calcdefs in ('SSL11', 'SSL21', 'SSL31')
        AND weighted_Mean IS NOT null AND ABS(weighted_Mean) < 1e25
        AND (UCASE(SUBSTR(tp.parm_Label,6,15)) = '{CORNER}')
        AND SUBSTR(tp.parm_Label,5,1) = RIGHT(tw.testProgramName,1)
    """
    block_df = ibmdata.isdw.query(block_query)
    block_df["yield"] = block_df["yield"].astype(float).round(2)
    block_df["yld_loss"] = block_df["yld_loss"].astype(float).round(2)
    return block_df


@cache.memoize(timeout=21600)
def get_so_data(corner="vnom"):
    if corner == "vmin":
        CORNER = "SSCANLATCH0P50VFM"
    elif corner == "vnom":
        CORNER = "SSCANLATCH0P75VFM"
    elif corner == "vmax":
        CORNER = "SSCANLATCH1P05VFM"
    else:
        return None

    so_query = f"""
    SELECT lot_id, wafer_id, tw.testProgramName AS step,
        CASE WHEN LENGTH(parm_Label) = 37 THEN tw.testProgramName||RIGHT(parm_Label,11) ELSE tw.testProgramName||RIGHT(parm_Label,12) END AS label,
        yield, 100 - yield AS yld_loss
    FROM DMIW_SYSTEMS.PTileWaferFact ptwf
    INNER JOIN DMIW_SYSTEMS.TestParm tp ON ptwf.testparmkey = tp.testparmkey
    INNER JOIN DMIW_SYSTEMS.TestedWafer tw ON ptwf.testedWaferKey = tw.testedWaferKey
    WHERE tw.Last_test_date >= (current date - {DAYSBACK} days)
        AND tw.Tech_id = '7HPP'
        AND tw.Level = 'H2'
        AND tw.Calcdefs in ('SSL11', 'SSL21', 'SSL31')
        AND weighted_Mean IS NOT null AND ABS(weighted_Mean) < 1e25
        AND (UCASE(SUBSTR(tp.parm_Label,10,17)) = '{CORNER}')
        AND SUBSTR(tp.parm_Label,5,1) = RIGHT(tw.testProgramName,1)
    """
    scan_out_df = ibmdata.isdw.query(so_query)
    scan_out_df["yield"] = scan_out_df["yield"].astype(float).round(2)
    scan_out_df["yld_loss"] = scan_out_df["yld_loss"].astype(float).round(2)
    return scan_out_df


########################################################################################################################
# SQL Yield Pulls For Ghost Fin Tab

GF_QUERY = f"""
WITH cte AS(
    (SELECT lot_Id, wafer_Id, family_Code, tw.Calcdefs AS Sail, tw.Last_test_date AS date,
        unitcell_X - 1 AS retx, unitcell_Y AS rety,
        --(unitcell_X - 1)||'_'||unitcell_Y AS retXY,
        CASE WHEN LENGTH(parm_Label) = 37 THEN tw.testProgramName||'_0p75'||RIGHT(parm_Label,11) 
             ELSE tw.testProgramName||'_0p75'||RIGHT(parm_Label,12) END AS label,
        parmYield as yield
    FROM DMIW_SYSTEMS.ChipParmFactR cpfr
        JOIN DMIW_SYSTEMS.TestParm tp ON tp.testParmKey = cpfr.testParmKey
        JOIN DMIW_SYSTEMS.Geography g ON g.geographyKey = cpfr.geographyKey
        JOIN DMIW_SYSTEMS.TestedWafer tw ON tw.testedWaferKey = cpfr.testedWaferKey
    WHERE Last_test_date >= (current date - {DAYSBACK} days)
        AND Tech_id = '7HPP' AND Level = 'H2' AND tw.Calcdefs IN ('SSL21', 'SSL31')
        AND cpfr.parmValue IS NOT null AND ABS(parmValue) < 1e25 
        AND (UCASE(SUBSTR(tp.parm_Label,10,17)) = 'SSCANLATCH0P75VFM')
        AND ((unitcell_X - 1) || '_' || unitcell_Y NOT IN (
            '-2_-1','1_8','2_9','2_10','3_10','4_11','5_11','6_11','7_11','9_10','10_9','11_8',
            '1_4','2_3','3_2','4_1','5_1','7_1','9_2','10_3','11_4')
        )
        AND parmYield < 100
        AND family_Code = 'Q5'
        --AND wafer_id = 'AZ6B5-19'
    ORDER BY lot_Id, wafer_Id, parm_Label)

    UNION ALL

    (SELECT lot_Id, wafer_Id, family_Code, tw.Calcdefs AS Sail, tw.Last_test_date AS date,
        unitcell_X AS retx, unitcell_Y AS rety,
        CASE WHEN LENGTH(parm_Label) = 37 THEN tw.testProgramName||'_0p75'||RIGHT(parm_Label,11) 
             ELSE tw.testProgramName||'_0p75'||RIGHT(parm_Label,12) END AS label,
        parmYield as yield
    FROM DMIW_SYSTEMS.ChipParmFactR cpfr
        JOIN DMIW_SYSTEMS.TestParm tp ON tp.testParmKey = cpfr.testParmKey
        JOIN DMIW_SYSTEMS.Geography g ON g.geographyKey = cpfr.geographyKey
        JOIN DMIW_SYSTEMS.TestedWafer tw ON tw.testedWaferKey = cpfr.testedWaferKey
    WHERE Last_test_date >= (current date - {DAYSBACK} days)
        AND Tech_id = '7HPP' AND Level = 'H2' AND tw.Calcdefs IN ('SSL21', 'SSL31')
        AND cpfr.parmValue IS NOT null AND ABS(parmValue) < 1e25 
        AND (UCASE(SUBSTR(tp.parm_Label,10,17)) = 'SSCANLATCH0P75VFM')
        AND ((unitcell_X) || '_' || unitcell_Y NOT IN (
            '1_7','2_9','3_10','4_11','5_11','6_12','7_12','9_11','10_11','11_10','12_8','12_5',
            '11_3','10_2','9_2','6_1','5_2','4_2','3_3','2_4')
        )
        AND parmYield < 100
        AND family_Code = 'Q6'
        --AND wafer_id = 'AZA2K-07'
    ORDER BY lot_Id, wafer_Id, parm_Label)
)
SELECT lot_id, wafer_id, family_Code, MIN(date) AS sail_date, retx, rety,
    SUM(
        CASE 
            WHEN Sail = 'SSL21' AND RIGHT(label,10) IN ('block6_so0','block6_so5','block7_so0','block7_so5') THEN 1
            WHEN Sail = 'SSL21' AND SUBSTR(label,11,7) IN ('block22','block24','block25') THEN 1
            WHEN Sail = 'SSL21' AND (RIGHT(label,10) NOT IN ('block6_so0','block6_so5','block7_so0','block7_so5')
                 OR SUBSTR(label,11,7) NOT IN ('block22','block24','block25')) THEN -0.3
            ELSE 0 END
        ) AS SSL2_GF_metric,
    SUM(
        CASE 
            WHEN Sail = 'SSL31' AND RIGHT(label,10) IN ('block6_so0','block6_so5','block7_so0','block7_so5') THEN 1
            WHEN Sail = 'SSL31' AND SUBSTR(label,11,7) IN ('block22','block24','block25') THEN 1
            WHEN Sail = 'SSL31' AND (RIGHT(label,10) NOT IN ('block6_so0','block6_so5','block7_so0','block7_so5') 
                 OR SUBSTR(label,11,7) NOT IN ('block22','block24','block25')) THEN -0.3
            ELSE 0 END
        ) AS SSL3_GF_metric
FROM cte
GROUP BY lot_id, wafer_id, family_code, retx, rety
ORDER BY MIN(date) DESC, lot_id, cte.wafer_id
"""


@cache.memoize(timeout=21600)
def ghost_fin_chip():
    df = ibmdata.isdw.query(GF_QUERY)
    df["ssl2_gf_metric"] = df["ssl2_gf_metric"].astype(float).round(2)
    df["ssl3_gf_metric"] = df["ssl3_gf_metric"].astype(float).round(2)
    df["GF_metric"] = df["ssl2_gf_metric"] + df["ssl3_gf_metric"]
    df["GF_metric"] = df["GF_metric"].round(2)
    df["Ghost_Fin"] = df["GF_metric"].apply(lambda x: 1 if x > 1 else 0)
    df = fill_zeros(df)
    return df


@cache.memoize(timeout=21600)
def ghost_fin_wafer():
    df = ghost_fin_chip()
    agg_df = (
        df.groupby(["lot_id", "wafer_id", "family_code"]).agg({"sail_date": "min", "Ghost_Fin": "sum"}).reset_index()
    )
    q5_df = agg_df[agg_df["family_code"] == "Q5"]
    q5_df["Ghost_Fin_YieldLoss"] = q5_df["Ghost_Fin"].apply(lambda x: 100 * x / 75).round(2)
    q6_df = agg_df[agg_df["family_code"] == "Q6"]
    q6_df["Ghost_Fin_YieldLoss"] = q6_df["Ghost_Fin"].apply(lambda x: 100 * x / 80).round(2)
    agg_df = pd.concat([q6_df, q5_df])
    agg_df = agg_df.rename(columns={"Ghost_Fin": "Ghost_Fin_ChipCount"})
    agg_df = agg_df.sort_values("sail_date", ascending=False).reset_index(drop=True)
    return agg_df


@cache.memoize(timeout=21600)
def ghost_fin_lot():
    df = ghost_fin_wafer()
    agg_df = (
        df.groupby(["lot_id", "family_code"])
        .agg({"sail_date": "min", "Ghost_Fin_ChipCount": "mean", "Ghost_Fin_YieldLoss": "mean"})
        .reset_index()
    )
    agg_df = agg_df.rename(
        columns={"Ghost_Fin_ChipCount": "Avg_Ghost_Fin_ChipCount", "Ghost_Fin_YieldLoss": "Avg_Ghost_Fin_YieldLoss"}
    )
    agg_df["Avg_Ghost_Fin_ChipCount"] = agg_df["Avg_Ghost_Fin_ChipCount"].astype(float).round(2)
    agg_df["Avg_Ghost_Fin_YieldLoss"] = agg_df["Avg_Ghost_Fin_YieldLoss"].astype(float).round(2)
    agg_df = agg_df.sort_values("sail_date", ascending=False).reset_index(drop=True)
    return agg_df


#################################################################################################
# layout
#################################################################################################
def sail_tab():
    return dcc.Tab(
        label="Sail Analysis",
        children=[
            dbc.Row(
                [
                    dbc.Col(
                        dcc.Markdown(
                            f"""\
                #### 7HPP Sail Dashboard

                Contact: Adam Yang (<acyang@us.ibm.com>)
                """
                        ),
                    ),
                    dbc.Col(
                        [
                            html.Button(
                                "Clear Cache", id=f"{APP_PREFIX}-clear-cache-button", className="btn btn-primary"
                            ),
                            html.Div(id=f"{APP_PREFIX}-refresh-prompt"),
                        ],
                        width=3,
                    ),
                ],
                className="mb-3",
            ),
            dbc.Row(
                dbc.Col(
                    [
                        html.H5("7HPP SAIL Yield Table"),
                        dbc.Form(
                            dbc.Row(
                                [
                                    dbc.Label(
                                        "Level:",
                                        html_for=f"{APP_PREFIX}-level-choices",
                                        width=COL_WIDTH_AUTO,
                                        className="pt-0 pe-0",
                                    ),
                                    dbc.Col(
                                        dcc.RadioItems(
                                            id=f"{APP_PREFIX}-level-choices",
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
                                id=f"{APP_PREFIX}-stats-table",
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
                                selected_rows=[],
                            )
                        ),
                    ]
                ),
                className="pretty-container mb-3",
            ),
            dbc.Row(
                dbc.Col(
                    [
                        html.H5("Sail Block and ScanOut Pareto"),
                        dbc.Form(
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            dbc.Label(
                                                "Voltage Corner:",
                                                html_for=f"{APP_PREFIX}-voltage-corner",
                                                width=COL_WIDTH_AUTO,
                                                className="pt-0 ps-0",
                                            ),
                                            dcc.RadioItems(
                                                id=f"{APP_PREFIX}-voltage-corner",
                                                options=[
                                                    {"label": "0.50v", "value": "vmin"},
                                                    {"label": "0.75v", "value": "vnom"},
                                                ],
                                                value="vnom",
                                                labelStyle={"display": "block"},
                                                inputClassName="me-1",
                                                labelClassName="me-3",
                                            ),
                                        ]
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Label(
                                                "Blocks/ScanOuts:",
                                                html_for=f"{APP_PREFIX}-block-so-toggle",
                                                width=COL_WIDTH_AUTO,
                                                className="pt-0 ps-0",
                                            ),
                                            dcc.RadioItems(
                                                id=f"{APP_PREFIX}-block-so-toggle",
                                                options=[
                                                    {"label": "Blocks", "value": "blocks"},
                                                    {"label": "ScanOuts", "value": "scanouts"},
                                                ],
                                                value="blocks",
                                                labelStyle={"display": "block"},
                                                inputClassName="me-1",
                                                labelClassName="me-3",
                                            ),
                                        ]
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Label(
                                                "Sail Macros to Include:",
                                                html_for=f"{APP_PREFIX}-sail-checklist",
                                                width=COL_WIDTH_AUTO,
                                                className="pt-0 ps-0",
                                            ),
                                            dcc.Checklist(
                                                id=f"{APP_PREFIX}-sail-checklist",
                                                options=[
                                                    {"label": "Sail 1", "value": "SSL1"},
                                                    {"label": "Sail 2", "value": "SSL2"},
                                                    {"label": "Sail 3", "value": "SSL3"},
                                                ],
                                                value=["SSL1", "SSL2", "SSL3"],
                                                labelStyle={"display": "block"},
                                                inputClassName="me-1",
                                                labelClassName="me-3",
                                            ),
                                        ]
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Label(
                                                "Plot Yield or Yield Loss:",
                                                html_for=f"{APP_PREFIX}-yield-yldLoss-toggle",
                                                width=COL_WIDTH_AUTO,
                                                className="pt-0 ps-0",
                                            ),
                                            dcc.RadioItems(
                                                id=f"{APP_PREFIX}-yield-yldLoss-toggle",
                                                options=[
                                                    {"label": "Yield Loss", "value": "yld_loss"},
                                                    {"label": "Yield", "value": "yield"},
                                                ],
                                                value="yld_loss",
                                                labelStyle={"display": "block"},
                                                inputClassName="me-1",
                                                labelClassName="me-3",
                                            ),
                                        ]
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Label(
                                                "Graph Width:",
                                                html_for=f"{APP_PREFIX}-graph-width",
                                                width=COL_WIDTH_AUTO,
                                                className="pt-0 ps-0",
                                            ),
                                            dcc.RadioItems(
                                                id=f"{APP_PREFIX}-graph-width",
                                                options=[
                                                    {"label": "Wide", "value": "wide"},
                                                    {"label": "Narrow", "value": "narrow"},
                                                ],
                                                value="wide",
                                                labelStyle={"display": "block"},
                                                inputClassName="me-1",
                                                labelClassName="me-3",
                                            ),
                                        ]
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Label(
                                                "Number of Paretos:",
                                                html_for=f"{APP_PREFIX}-num-paretos",
                                                width=COL_WIDTH_AUTO,
                                                className="pt-0 ps-0",
                                            ),
                                            dcc.Slider(
                                                id=f"{APP_PREFIX}-num-paretos",
                                                min=10,
                                                max=100,
                                                marks={
                                                    i: "{}".format(i) if i == 1 else str(i) for i in range(10, 110, 10)
                                                },
                                                value=20,
                                            ),
                                        ],
                                        width=4,
                                    ),
                                ],
                                align="center",
                            )
                        ),
                        dbc.Spinner(
                            dcc.Graph(
                                id=f"{APP_PREFIX}-pareto-interactivity-container",
                                style={"height": "100%", "width": "100%"},
                            )
                        ),
                    ]
                ),
                className="pretty-container mb-3",
            ),
        ],
    )


def ghostfin_tab():
    return dcc.Tab(
        label="Ghost Fin",
        children=[
            dbc.Row(
                [
                    dbc.Col(
                        dcc.Markdown(
                            f"""\
                #### 7HPP Ghost Fin Metric

                Contact: Adam Yang (<acyang@us.ibm.com>)
                """
                        ),
                    ),
                    # dbc.Col(
                    #     [
                    #     html.Button('Clear Cache', id=f"{APP_PREFIX}-clear-cache-button", className="btn btn-primary"),
                    #     html.Div(id=f"{APP_PREFIX}-refresh-prompt")
                    #     ],
                    #     width=3
                    # )
                ],
                className="mb-3",
            ),
            dbc.Row(
                dbc.Col(
                    [
                        html.H5("7HPP Ghost Fin Table"),
                        dbc.Form(
                            dbc.Row(
                                [
                                    dbc.Label(
                                        "Level:",
                                        html_for=f"{APP_PREFIX}-gf-level-choices",
                                        width=COL_WIDTH_AUTO,
                                        className="pt-0 pe-0",
                                    ),
                                    dbc.Col(
                                        dcc.RadioItems(
                                            id=f"{APP_PREFIX}-gf-level-choices",
                                            options=[
                                                {"label": "wafer", "value": "wafer"},
                                                {"label": "lot", "value": "lot"},
                                                {"label": "chip", "value": "chip"},
                                            ],
                                            value="wafer",
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
                                id=f"{APP_PREFIX}-gf-table",
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
                                selected_rows=[],
                                export_format="xlsx",
                            )
                        ),
                        dbc.Spinner(
                            dcc.Graph(
                                id=f"{APP_PREFIX}-gf-wafer-map",
                                style={"height": "100%", "width": "100%"},
                            )
                        ),
                    ]
                ),
                className="pretty-container mb-3",
            ),
        ],
    )


layout = html.Div([dcc.Tabs(id=f"{APP_PREFIX}_tabs", children=[sail_tab(), ghostfin_tab()])])


########################################################################################################################
# callbacks
########################################################################################################################
# Clear Cache Callback
@callback(Output(f"{APP_PREFIX}-refresh-prompt", "children"), Input(f"{APP_PREFIX}-clear-cache-button", "n_clicks"))
def update_output(n_clicks):
    if n_clicks is not None:
        cache.clear()
        return "Cache has been cleared. Please refresh the page."


@callback(
    Output(f"{APP_PREFIX}-stats-table", "columns"),
    Output(f"{APP_PREFIX}-stats-table", "data"),
    Output(f"{APP_PREFIX}-stats-table", "style_data_conditional"),
    Output(f"{APP_PREFIX}-stats-table", "style_cell_conditional"),
    Input(f"{APP_PREFIX}-level-choices", "value"),
)
def toggle_lotwafer_table(selected_item: str):
    if not selected_item:
        raise PreventUpdate()

    if selected_item == "lot":
        data = get_lot_data()
        style_cell_conditional = [
            {"if": {"column_id": "lot_name"}, "width": "90px"},
            {"if": {"column_id": "lot_id_base"}, "width": "110px"},
            {"if": {"column_id": "lot_id"}, "width": "110px"},
            {"if": {"column_id": "family_code"}, "width": "110px"},
            {"if": {"column_id": "date"}, "width": "100px"},
        ]
    elif selected_item == "wafer":
        data = get_wafer_data()
        style_cell_conditional = [
            {"if": {"column_id": "lot_name"}, "width": "90px"},
            {"if": {"column_id": "lot_id_base"}, "width": "110px"},
            {"if": {"column_id": "lot_id"}, "width": "110px"},
            {"if": {"column_id": "wafer_id"}, "width": "110px"},
            {"if": {"column_id": "family_code"}, "width": "110px"},
            {"if": {"column_id": "date"}, "width": "100px"},
        ]
    else:
        raise ValueError(f"unknown selection '{selected_item}'")

    style_data_conditional = [
                                 {"if": {"filter_query": "{{{}}} >= {}".format(col, value), "column_id": col},
                                  "backgroundColor": GOOD_GREEN}
                                 for (col, value) in data.quantile(0.9, numeric_only=True).items()
                             ] + [
                                 {"if": {"filter_query": "{{{}}} <= {}".format(col, value), "column_id": col},
                                  "backgroundColor": BAD_RED}
                                 for (col, value) in data.quantile(0.25, numeric_only=True).items()
                             ]

    columns = [{"name": i, "id": i} for i in data.columns]
    data_dict = data.fillna("-").to_dict("records")
    return columns, data_dict, style_data_conditional, style_cell_conditional


########################################################################################################################
# This Part of the code deals with the pareto graph
@callback(
    Output(f"{APP_PREFIX}-pareto-interactivity-container", "figure"),
    Output(f"{APP_PREFIX}-pareto-interactivity-container", "style"),
    Input(f"{APP_PREFIX}-level-choices", "value"),
    Input(f"{APP_PREFIX}-graph-width", "value"),
    Input(f"{APP_PREFIX}-voltage-corner", "value"),
    Input(f"{APP_PREFIX}-block-so-toggle", "value"),
    Input(f"{APP_PREFIX}-yield-yldLoss-toggle", "value"),
    Input(f"{APP_PREFIX}-num-paretos", "value"),
    Input(f"{APP_PREFIX}-sail-checklist", "value"),
    Input(f"{APP_PREFIX}-stats-table", "derived_virtual_data"),
    Input(f"{APP_PREFIX}-stats-table", "derived_virtual_selected_rows"),
)
def plot_pareto(lot_wafer, width, voltage_corner, block_so, yld_loss, n, sail, table_rows, table_indices):
    # This logic deals with toggling between yield and yld_loss
    if width == "wide":
        graph_width = {"height": "100%", "width": "100%"}
    elif width == "narrow":
        graph_width = {"height": "100%", "width": "50%"}

    if yld_loss == "yld_loss":
        yparm = "yld_loss"
        asc = False
    else:
        yparm = "yield"
        asc = True

    # Chose between Block or ScanOut pareto graph
    if block_so == "blocks":
        df = get_block_data(corner=voltage_corner)
    elif block_so == "scanouts":
        df = get_so_data(corner=voltage_corner)
    else:
        raise ValueError(f"block {block_so} unsupported")

    df["yield"] = df["yield"].astype(float)
    df["yld_loss"] = df["yld_loss"].astype(float)

    # Convert selected row indices to lot ids and wafer ids
    if lot_wafer == "lot":
        if table_indices is None:
            lots = []
        else:
            tempdf = lot_df if table_rows is None else pd.DataFrame(table_rows)
            lots = [tempdf["lot_id"][i] for i in table_indices]
    elif lot_wafer == "wafer":
        if table_indices is None:
            wafers = []
        else:
            tempdf = w_df if table_rows is None else pd.DataFrame(table_rows)
            wafers = [tempdf["wafer_id"][i] for i in table_indices]

    # Choose between lot level or wafer level pareto
    if lot_wafer == "lot":
        if not lots:
            inclusiontxt = "all lots"
            pass
        else:
            df = df[df["lot_id"].isin(lots)]
            if len(lots) > 3:
                inclusiontxt = "lots: " + ", ".join(lots[0:3]) + "..."
            else:
                inclusiontxt = "lots: " + ", ".join(lots)
        num = "{} distinct wafers".format(df["wafer_id"].nunique())

    elif lot_wafer == "wafer":
        if not wafers:
            inclusiontxt = "all lots"
            pass
        else:
            df = df[df["wafer_id"].isin(wafers)]  # TODO THis is broken for some reason
            if len(wafers) > 3:
                inclusiontxt = "wafers: " + ", ".join(wafers[0:3]) + "..."
            else:
                inclusiontxt = "wafers: " + ", ".join(wafers)
        num = "{} distinct wafers".format(df["wafer_id"].nunique())

    # This part of the code deals with which Sail to include in the Pareto
    df = df[df["step"].isin(sail)]
    sailtxt = " with Calcdefs " + ", ".join(sail)

    # This part of the code deals with plotting the pareto
    df_agg = df.groupby(["label", "step"]).mean(numeric_only=True).sort_values(yparm, ascending=asc).reset_index()[0:n]

    # Just in case there is an empty dataset
    if df_agg is None or df_agg.shape[0] < 1:
        fig = empty_figure("There is currently no Block/Scanout data available for this selection")
        return fig, graph_width

    else:
        fig = px.bar(
            df_agg,
            x="label",
            y=yparm,
            hover_data=["label", yparm],
            color="step",
            color_discrete_map=color_map,
            labels={"label": "Label", yparm: yparm + " (%)"},
        )
        fig.update_layout(title_text="Sail " + yparm + " pareto for " + inclusiontxt + sailtxt + " (" + num + ")")
        fig.update_layout(xaxis_categoryorder="total descending")
        return fig, graph_width


########################################################################################################################
# This Part Deals with the Ghost Fin Callbacks
def fill_zeros(df):
    data = {
        "lot_id": [],
        "wafer_id": [],
        "family_code": [],
        "sail_date": [],
        "retx": [],
        "rety": [],
    }
    temp_df = df.groupby(["lot_id", "wafer_id", "family_code"])["sail_date"].min().reset_index()
    for row in temp_df.drop_duplicates().iterrows():
        if row[1][2] == "Q5":
            data["lot_id"].extend([row[1][0] for i in range(75)])
            data["wafer_id"].extend([row[1][1] for i in range(75)])
            data["family_code"].extend([row[1][2] for i in range(75)])
            data["sail_date"].extend([row[1][3] for i in range(75)])
            data["retx"].extend(
                [
                    1,
                    1,
                    1,
                    2,
                    2,
                    2,
                    2,
                    2,
                    3,
                    3,
                    3,
                    3,
                    3,
                    3,
                    3,
                    4,
                    4,
                    4,
                    4,
                    4,
                    4,
                    4,
                    4,
                    4,
                    5,
                    5,
                    5,
                    5,
                    5,
                    5,
                    5,
                    5,
                    5,
                    6,
                    6,
                    6,
                    6,
                    6,
                    6,
                    6,
                    6,
                    6,
                    7,
                    7,
                    7,
                    7,
                    7,
                    7,
                    7,
                    7,
                    7,
                    8,
                    8,
                    8,
                    8,
                    8,
                    8,
                    8,
                    8,
                    8,
                    9,
                    9,
                    9,
                    9,
                    9,
                    9,
                    9,
                    10,
                    10,
                    10,
                    10,
                    10,
                    11,
                    11,
                    11,
                ]
            )
            data["rety"].extend(
                [
                    5,
                    6,
                    7,
                    4,
                    5,
                    6,
                    7,
                    8,
                    3,
                    4,
                    5,
                    6,
                    7,
                    8,
                    9,
                    2,
                    3,
                    4,
                    5,
                    6,
                    7,
                    8,
                    9,
                    10,
                    2,
                    3,
                    4,
                    5,
                    6,
                    7,
                    8,
                    9,
                    10,
                    2,
                    3,
                    4,
                    5,
                    6,
                    7,
                    8,
                    9,
                    10,
                    2,
                    3,
                    4,
                    5,
                    6,
                    7,
                    8,
                    9,
                    10,
                    2,
                    3,
                    4,
                    5,
                    6,
                    7,
                    8,
                    9,
                    10,
                    3,
                    4,
                    5,
                    6,
                    7,
                    8,
                    9,
                    4,
                    5,
                    6,
                    7,
                    8,
                    5,
                    6,
                    7,
                ]
            )
        elif row[1][2] == "Q6":
            data["lot_id"].extend([row[1][0] for i in range(80)])
            data["wafer_id"].extend([row[1][1] for i in range(80)])
            data["family_code"].extend([row[1][2] for i in range(80)])
            data["sail_date"].extend([row[1][3] for i in range(80)])
            data["retx"].extend(
                [
                    2,
                    2,
                    2,
                    2,
                    3,
                    3,
                    3,
                    3,
                    3,
                    3,
                    4,
                    4,
                    4,
                    4,
                    4,
                    4,
                    4,
                    4,
                    5,
                    5,
                    5,
                    5,
                    5,
                    5,
                    5,
                    5,
                    6,
                    6,
                    6,
                    6,
                    6,
                    6,
                    6,
                    6,
                    6,
                    6,
                    7,
                    7,
                    7,
                    7,
                    7,
                    7,
                    7,
                    7,
                    7,
                    7,
                    8,
                    8,
                    8,
                    8,
                    8,
                    8,
                    8,
                    8,
                    8,
                    8,
                    9,
                    9,
                    9,
                    9,
                    9,
                    9,
                    9,
                    9,
                    10,
                    10,
                    10,
                    10,
                    10,
                    10,
                    10,
                    10,
                    11,
                    11,
                    11,
                    11,
                    11,
                    11,
                    12,
                    12,
                ]
            )
            data["rety"].extend(
                [
                    5,
                    6,
                    7,
                    8,
                    4,
                    5,
                    6,
                    7,
                    8,
                    9,
                    3,
                    4,
                    5,
                    6,
                    7,
                    8,
                    9,
                    10,
                    3,
                    4,
                    5,
                    6,
                    7,
                    8,
                    9,
                    10,
                    2,
                    3,
                    4,
                    5,
                    6,
                    7,
                    8,
                    9,
                    10,
                    11,
                    2,
                    3,
                    4,
                    5,
                    6,
                    7,
                    8,
                    9,
                    10,
                    11,
                    2,
                    3,
                    4,
                    5,
                    6,
                    7,
                    8,
                    9,
                    10,
                    11,
                    3,
                    4,
                    5,
                    6,
                    7,
                    8,
                    9,
                    10,
                    3,
                    4,
                    5,
                    6,
                    7,
                    8,
                    9,
                    10,
                    4,
                    5,
                    6,
                    7,
                    8,
                    9,
                    6,
                    7,
                ]
            )
    filler_df = pd.DataFrame(data)
    output_df = filler_df.merge(df, how="left", on=["lot_id", "wafer_id", "family_code", "retx", "rety"]).fillna(0)
    output_df["sail_date"] = [
        output_df.iloc[i]["sail_date_x"] if output_df.iloc[i]["sail_date_y"] == 0 else output_df.iloc[i]["sail_date_y"]
        for i in range(len(output_df))
    ]
    output_df = output_df.drop(columns=["sail_date_x", "sail_date_y"])
    return output_df


@callback(
    Output(f"{APP_PREFIX}-gf-table", "columns"),
    Output(f"{APP_PREFIX}-gf-table", "data"),
    Output(f"{APP_PREFIX}-gf-table", "style_cell_conditional"),
    Input(f"{APP_PREFIX}-gf-level-choices", "value"),
)
def gf_toggle_table(selected_item: str):
    if not selected_item:
        raise PreventUpdate()

    if selected_item == "wafer":
        data = ghost_fin_wafer()
        style_cell_conditional = [
            {"if": {"column_id": "lot_id"}, "width": "110px"},
            {"if": {"column_id": "wafer_id"}, "width": "110px"},
            {"if": {"column_id": "sail_date"}, "width": "110px"},
            {"if": {"column_id": "family_code"}, "width": "60px"},
            {"if": {"column_id": "Ghost_Fin_ChipCount"}, "width": "150px"},
            {"if": {"column_id": "Ghost_Fin_YieldLoss"}, "width": "150px"},
        ]
    elif selected_item == "lot":
        data = ghost_fin_lot()
        style_cell_conditional = [
            {"if": {"column_id": "lot_id"}, "width": "110px"},
            {"if": {"column_id": "wafer_id"}, "width": "110px"},
            {"if": {"column_id": "sail_date"}, "width": "110px"},
            {"if": {"column_id": "family_code"}, "width": "60px"},
            {"if": {"column_id": "Avg_Ghost_Fin_ChipCount"}, "width": "150px"},
            {"if": {"column_id": "Avg_Ghost_Fin_YieldLoss"}, "width": "150px"},
        ]
    elif selected_item == "chip":
        data = ghost_fin_chip()
        style_cell_conditional = [
            {"if": {"column_id": "lot_id"}, "width": "110px"},
            {"if": {"column_id": "wafer_id"}, "width": "110px"},
            {"if": {"column_id": "sail_date"}, "width": "110px"},
            {"if": {"column_id": "retx"}, "width": "50px"},
            {"if": {"column_id": "rety"}, "width": "50px"},
            {"if": {"column_id": "family_code"}, "width": "60px"},
            {"if": {"column_id": "ssl1_gf_metric"}, "width": "110px"},
            {"if": {"column_id": "ssl2_gf_metric"}, "width": "110px"},
            {"if": {"column_id": "ssl3_gf_metric"}, "width": "110px"},
            {"if": {"column_id": "GF_metric"}, "width": "110px"},
            {"if": {"column_id": "Ghost_Fin"}, "width": "90px"},
        ]
    else:
        raise ValueError(f"unknown selection '{selected_item}'")

    columns = [{"name": i, "id": i} for i in data.columns]
    data_dict = data.fillna("-").to_dict("records")
    return columns, data_dict, style_cell_conditional


########################################################################################################################
# Functions and callback for Ghost Fin wafer maps


def create_z(df, x_col, y_col, z_col):
    # create an empty annotations container
    if len(df["family_code"].unique()) == 1:
        if df["family_code"].unique() == "Q5":
            annotations = [
                ["", "", "", 0, 0, 0, 0, 0, "", "", ""],
                ["", "", 0, 0, 0, 0, 0, 0, 0, "", ""],
                ["", 0, 0, 0, 0, 0, 0, 0, 0, 0, ""],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                ["", 0, 0, 0, 0, 0, 0, 0, 0, 0, ""],
                ["", "", 0, 0, 0, 0, 0, 0, 0, "", ""],
                ["", "", "", 0, 0, 0, 0, 0, "", "", ""],
            ]
            # Fill the annotations container
            for i in range(df.shape[0]):
                x = int(df.iloc[i][x_col] - 1)
                y = int(df.iloc[i][y_col] - 2)
                annotations[y][x] = df.iloc[i][z_col].round(2)
        elif df["family_code"].unique() == "Q6":
            annotations = [
                ["", "", "", "", 0, 0, 0, "", "", "", ""],
                ["", "", 0, 0, 0, 0, 0, 0, 0, "", ""],
                ["", 0, 0, 0, 0, 0, 0, 0, 0, 0, ""],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, ""],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, ""],
                ["", 0, 0, 0, 0, 0, 0, 0, 0, 0, ""],
                ["", "", 0, 0, 0, 0, 0, 0, 0, "", ""],
                ["", "", "", "", 0, 0, 0, "", "", "", ""],
            ]
            # Fill the annotations container
            for i in range(df.shape[0]):
                x = int(df.iloc[i][x_col] - 2)
                y = int(df.iloc[i][y_col] - 2)
                annotations[y][x] = df.iloc[i][z_col].round(2)
        else:
            return False, False
    else:
        return False, False

    # Replace '' with a value to plot with
    z = copy.deepcopy(annotations)
    for y, row in enumerate(z):
        for x, value in enumerate(row):
            if z[y][x] == "":
                if min(df[z_col]) <= 0:
                    z[y][x] = min(df[z_col]) - 1
                else:
                    z[y][x] = -1

    return z, annotations


def plot_heatmap(df, x_col, y_col, z_col):
    z, annotation = create_z(df, x_col=x_col, y_col=y_col, z_col=z_col)
    if not z:
        return {}
    else:
        if df.family_code.unique() == "Q5":
            y = [i for i in range(2, 11)]
        elif df.family_code.unique() == "Q6":
            y = [i for i in range(2, 12)]
        else:
            raise ValueError(f"unsupported family code {df.family_code.unique()}")

        fig = ff.create_annotated_heatmap(
            z=z,
            y=y,
            x=[i for i in range(1, 12)],
            annotation_text=annotation,
            colorscale=[(0.00, "white"), (0.01, "rgb(255,247,236)"), (1.00, "rgb(127, 0, 0)")],
        )
        fig.update_layout(xaxis_title="retx", yaxis_title="rety", width=680, height=600, autosize=False)
        fig.update_xaxes(side="bottom")
        return fig


@callback(
    Output(f"{APP_PREFIX}-gf-wafer-map", "figure"),
    Input(f"{APP_PREFIX}-gf-level-choices", "value"),
    Input(f"{APP_PREFIX}-gf-table", "derived_virtual_data"),
    Input(f"{APP_PREFIX}-gf-table", "derived_virtual_selected_rows"),
)
def plot_gf_maps(selected_item, table_rows, table_indices):
    if not table_indices:
        raise PreventUpdate

    df = ghost_fin_chip()
    selection_df = pd.DataFrame(table_rows)
    if selected_item == "wafer":
        wafers = [selection_df["wafer_id"][i] for i in table_indices]
        wafer_df = df[df["wafer_id"].isin(wafers)]
        wafer_df = wafer_df.groupby(["retx", "rety", "family_code"]).mean(numeric_only=True).reset_index()
        fig = plot_heatmap(wafer_df, "retx", "rety", "GF_metric")
    elif selected_item == "lot":
        lots = [selection_df["lot_id"][i] for i in table_indices]
        lot_df = df[df["lot_id"].isin(lots)]
        lot_df = lot_df.groupby(["retx", "rety", "family_code"]).mean(numeric_only=True).reset_index()
        fig = plot_heatmap(lot_df, "retx", "rety", "GF_metric")
    else:
        LOG.error(f"item {selected_item} is unsupported")
        raise PreventUpdate

    return fig
