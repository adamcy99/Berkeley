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

APP_PREFIX = "pti_rel_vmax_dashboard"
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
    menu="PTIApps:Reliability Vmax",
    path="/pti_apps/rel_vmax",
    description="Reliability Vmax",
    title="Reliability Vmax",
    image='',  # force dash to not look for an image, None doesn't work
)

MO_WEEK_AGG_FUNCTIONS = {
    'wafer_id': lambda x: x.nunique(),
    'num_bad_chips': 'sum',
    '%_bad_chips': 'mean',
    'opdb_vmax': 'mean',
    'rvtp_vmax_18': 'mean',
    'ulvtp_vmax_18': 'mean',
    'slvtn_vmax_18': 'mean',
    'mol54_vmax_18': 'mean',
    'mol60_vmax_18': 'mean',
    'mol_vmax': 'mean',
    'vmaxpfet': 'mean',
    'lvt_pfet_vmax': 'mean'
}

LOT_WAFER_AGG_FUNCTIONS = {
    'test_date': 'min',
    'num_bad_chips': 'sum',
    '%_bad_chips': 'mean',
    'opdb_vmax': 'mean',
    'rvtp_vmax_18': 'mean',
    'ulvtp_vmax_18': 'mean',
    'slvtn_vmax_18': 'mean',
    'mol54_vmax_18': 'mean',
    'mol60_vmax_18': 'mean',
    'mol_vmax': 'mean',
    'vmaxpfet': 'mean',
    'lvt_pfet_vmax': 'mean'
}

def generate_SQL_GroupBy(mydict, parm_label = 'parm_Label', val = 'parmYield', agg = 'AVG'):
    output = ''
    n = len(mydict)
    for i,parm in enumerate(mydict):
        if i == n-1:
            output += f"{agg}(CASE WHEN {parm_label} = '{parm}' THEN {val} ELSE NULL END) AS {parm}"
        else:
            output += f"{agg}(CASE WHEN {parm_label} = '{parm}' THEN {val} ELSE NULL END) AS {parm},\n"
    return output
# ########################## SQL QUERY ##########################################

@cache.memoize(timeout=21600)
def pull_rel_vmax_chip_data(start, end):
    parms = ['MOL_VMAX','RVT_PFET_VMAX','ULVT_PFET_VMAX','VmaxPFET','SLVT_NFET_VMAX','OPDB_VMAX','MOL54','MOL60','LVT_PFET_VMAX']
    cases = generate_SQL_GroupBy(parms, 'parm_label', 'parmvalue')

    QUERY = f"""
    SELECT lotlabel AS lotnumber, family_code, wafer_id, 
        normalized_testx AS chipx, normalized_testy AS chipy, kerf_x, kerf_y,
        radius_center_5, quadrant, MAX(last_testtimestamp) AS timestamp, 
        MAX(DATE(last_testtimestamp)) AS Test_Date, MAX(VARCHAR_FORMAT(last_testtimestamp,'YYYY-MM')) AS Test_Month,
        MAX(VARCHAR_FORMAT(last_testtimestamp,'YYYY-WW')) AS Test_Week, {cases},
        AVG(CASE
            WHEN family_code = 'Q6' AND parm_label = 'RVT_PFET_VMAX' THEN parmvalue + 0.018
            WHEN family_code = 'X2' AND parm_label = 'RVT_PFET_VMAX' THEN parmvalue
            ELSE NULL
        END) AS RVTP_VMAX_18,
        AVG(CASE
            WHEN family_code = 'Q6' AND parm_label = 'ULVT_PFET_VMAX' THEN parmvalue + 0.018
            WHEN family_code = 'X2' AND parm_label = 'ULVT_PFET_VMAX' THEN parmvalue
            ELSE NULL
        END) AS ULVTP_VMAX_18,
        AVG(CASE
            WHEN family_code = 'Q6' AND parm_label = 'SLVT_NFET_VMAX' THEN parmvalue + 0.018
            WHEN family_code = 'X2' AND parm_label = 'SLVT_NFET_VMAX' THEN parmvalue
            ELSE NULL
        END) AS SLVTN_VMAX_18,
        AVG(CASE
            WHEN family_code = 'Q6' AND parm_label = 'MOL54' THEN parmvalue + 0.018
            WHEN family_code = 'X2' AND parm_label = 'MOL54' THEN parmvalue
            ELSE NULL
        END) AS MOL54_VMAX_18,
        AVG(CASE
            WHEN family_code = 'Q6' AND parm_label = 'MOL60' THEN parmvalue + 0.018
            WHEN family_code = 'X2' AND parm_label = 'MOL60' THEN parmvalue
            ELSE NULL
        END) AS MOL60_VMAX_18
    FROM
        DMIW_SYSTEMS.ChipParmFactR cpfr
        INNER JOIN DMIW_SYSTEMS.testparm tp ON cpfr.testparmkey = tp.testparmkey
        INNER JOIN DMIW_SYSTEMS.Geography g ON cpfr.geographyKey = g.geographyKey
        INNER JOIN DMIW_SYSTEMS.testedwafer tw ON cpfr.testedwaferkey = tw.testedwaferkey
    WHERE
        Tech_id = '7HPP' AND tw.Calcdefs = 'WL01R'
        AND DATE(last_testtimestamp) BETWEEN DATE('{start}') and DATE('{end}')
        AND family_code IN ('Q6', 'X2')
    GROUP BY 
        lotlabel,family_code,wafer_id,normalized_testx,normalized_testy,kerf_x, kerf_y,radius_center_5,quadrant
    """

    df = ibmdata.isdw.query(QUERY)
    df = df.drop_duplicates(subset=['wafer_id', 'chipx', 'chipy'], keep='last')
    df['product_schema'] = df['family_code'].apply(lambda x: 'p10dd2' if x == 'Q6' else 'zadd2')
    return df


########################################################################################################################
# layout
########################################################################################################################
def all_tab():
    return dcc.Tab(
        label="Reliability Vmax Dashboard",
        children=[
            dbc.Row(
                [
                    dbc.Col(
                        dcc.Markdown(f"""\
                        #### 7HPP Reliability Vmax Dashboard
                        
                        Contact: Adam Yang (<acyang@us.ibm.com>)"""
                                     ),
                    ),
                    dbc.Col(
                        [
                            html.Button(
                                "Clear Cache", id=f"{APP_PREFIX}-all-clear-cache-button",
                                #disabled=True,
                                className="btn btn-primary"
                            ),
                            html.Div(id=f"{APP_PREFIX}-all-refresh-prompt"),
                        ],
                        width=3,
                    ),
                ],
                className="mb-3",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Row(dbc.Label("Date Range: ", width="auto"), align="center"),
                            dbc.Row(dcc.DatePickerRange(id=f"{APP_PREFIX}_daterange", start_date=DEFAULT_START_DATE,
                                                        end_date=DEFAULT_END_DATE)),
                        ],
                    ),
                ],
            ),
            html.Div(
                [
                    html.Button("Download Raw Reliability Vmax Data", id=f"{APP_PREFIX}_download_button"),
                    dcc.Download(id=f"{APP_PREFIX}_download_raw_data"),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H5("% chips below cutoff"),
                            dbc.Form(
                                [
                                    dbc.Row(
                                        [
                                            dbc.Label(
                                                "Parameter: ",
                                                html_for=f"{APP_PREFIX}-parameter-input",
                                                width="auto",
                                            ),
                                            dbc.Col(
                                                dcc.Dropdown(
                                                    options=['opdb_vmax', 'rvtp_vmax_18', 'ulvtp_vmax_18',
                                                             'slvtn_vmax_18', 'mol54_vmax_18', 'mol60_vmax_18'],
                                                    value='opdb_vmax',
                                                    id=f"{APP_PREFIX}-parameter-input"
                                                ),
                                            ),
                                        ],
                                    ),
                                    dbc.Row(
                                        [
                                            dbc.Label(
                                                "Cutoff (between 0 and 2): ",
                                                html_for=f"{APP_PREFIX}-int-input",
                                                width="auto",
                                            ),
                                            dbc.Col(
                                                dcc.Input(
                                                    id=f"{APP_PREFIX}-int-input",
                                                    type='number',
                                                    min=0, max=2, step=0.01,
                                                    value=1,
                                                    debounce=True,
                                                    style={'width': '50%'},
                                                ),
                                            ),
                                        ],
                                    ),
                                    dbc.Spinner(
                                        dt.DataTable(
                                            id=f"{APP_PREFIX}-small-table",
                                            columns=[{"name": i, "id": i} for i in ("foo", "bar")],
                                            fixed_rows={"headers": True},
                                            # fixed_columns={'headers': True, 'data': 2},
                                            style_cell={
                                                "minWidth": "80px",
                                                "width": "80px",
                                                "maxWidth": "80px",
                                                "textAlign": "center",
                                                "fontSize": TABLE_FONT_SIZE,
                                            },
                                            style_table={
                                                "minHeight": "140px",
                                                "height": "140px",
                                                "maxHeight": "140px",
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
                                        ),
                                    ),
                                ],
                            ),
                        ],
                        width=3,
                    ),
                    dbc.Col(
                        [
                            html.H5("All Chips Summary (Device)"),
                            dbc.Form(
                                [
                                    dbc.Row(
                                        [
                                            dbc.Label(
                                                "Parameter: ",
                                                html_for=f"{APP_PREFIX}-small_fc_toggle",
                                                width="auto",
                                            ),
                                            dbc.Col(
                                                dcc.RadioItems(
                                                    id=f"{APP_PREFIX}-small-fc-toggle",
                                                    options=[
                                                        {"label": "p10 DD2", "value": "p10dd2"},
                                                        {"label": "zA DD2", "value": "zadd2"},
                                                    ],
                                                    value="p10dd2",
                                                    inputClassName="me-1",
                                                    labelClassName="me-3",
                                                ),
                                            ),
                                        ],
                                    ),
                                    dbc.Spinner(
                                        dt.DataTable(
                                            id=f"{APP_PREFIX}-small-table2",
                                            columns=[{"name": i, "id": i} for i in ("foo", "bar")],
                                            fixed_rows={"headers": True},
                                            # fixed_columns={'headers': True, 'data': 2},
                                            style_cell={
                                                "minWidth": "60px",
                                                "width": "60px",
                                                "maxWidth": "60px",
                                                "textAlign": "center",
                                                "fontSize": TABLE_FONT_SIZE,
                                            },
                                            style_table={
                                                "minHeight": "260px",
                                                "height": "260px",
                                                "maxHeight": "260px",
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
                                        ),
                                    ),
                                ],
                            ),
                        ],
                        width=4,
                    ),
                    dbc.Col(
                        [
                            dbc.Row(
                                [
                                    html.H5("OPDB Vmax Summary"),
                                    dbc.Form(
                                        [
                                            dbc.Spinner(
                                                dt.DataTable(
                                                    id=f"{APP_PREFIX}-small-table3",
                                                    columns=[{"name": i, "id": i} for i in ("foo", "bar")],
                                                    fixed_rows={"headers": True},
                                                    # fixed_columns={'headers': True, 'data': 2},
                                                    style_cell={
                                                        "minWidth": "60px",
                                                        "width": "60px",
                                                        "maxWidth": "60px",
                                                        "textAlign": "center",
                                                        "fontSize": TABLE_FONT_SIZE,
                                                    },
                                                    style_table={
                                                        "minHeight": "160px",
                                                        "height": "160px",
                                                        "maxHeight": "160px",
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
                                                ),
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                            dbc.Row(
                                [
                                    html.H5("Sample Set Wafer Counts by Month"),
                                    dbc.Form(
                                        [
                                            dbc.Spinner(
                                                dt.DataTable(
                                                    id=f"{APP_PREFIX}-small-table4",
                                                    columns=[{"name": i, "id": i} for i in ("foo", "bar")],
                                                    fixed_rows={"headers": True},
                                                    # fixed_columns={'headers': True, 'data': 2},
                                                    style_cell={
                                                        "minWidth": "60px",
                                                        "width": "60px",
                                                        "maxWidth": "60px",
                                                        "textAlign": "center",
                                                        "fontSize": TABLE_FONT_SIZE,
                                                    },
                                                    style_table={
                                                        "minHeight": "160px",
                                                        "height": "160px",
                                                        "maxHeight": "160px",
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
                                                ),
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                        ],
                        width=5,
                    ),
                ],
                className="pretty-container mb-3",
            ),
            dbc.Row(
                dbc.Col(
                    [
                        html.H5("Summarized Reliability Vmax Data"),
                        dbc.Form(
                            dbc.Row(
                                [
                                    dbc.Label(
                                        "Summarize By:",
                                        html_for=f"{APP_PREFIX}-month-lot-toggle",
                                        width="auto",
                                    ),
                                    dbc.Col(
                                        dcc.RadioItems(
                                            id=f"{APP_PREFIX}-month-lot-toggle",
                                            options=[
                                                {"label": "by week", "value": "week"},
                                                {"label": "by month", "value": "month"},
                                                {"label": "by lot id", "value": "lot"},
                                                {"label": "by wafer id", "value": "wafer"},
                                            ],
                                            value="week",
                                            inputClassName="me-1",
                                            labelClassName="me-3",
                                        ), width=4,
                                    ),
                                    dbc.Label(
                                        "Set P10 Threshold:",
                                        html_for=f"{APP_PREFIX}-p10-thresh",
                                        width="auto",
                                    ),
                                    dbc.Col(
                                        [
                                            dcc.Input(
                                                id=f"{APP_PREFIX}-p10-thresh",
                                                type='number',
                                                min=0, max=2, step=0.01,
                                                value=0.9,
                                                debounce=True,
                                                style={'width': '80%'},
                                            ),
                                        ], width=1,
                                    ),
                                    dbc.Label(
                                        "Set zA Threshold:",
                                        html_for=f"{APP_PREFIX}-zA-thresh",
                                        width="auto",
                                    ),
                                    dbc.Col(
                                        [
                                            dcc.Input(
                                                id=f"{APP_PREFIX}-zA-thresh",
                                                type='number',
                                                min=0, max=2, step=0.01,
                                                value=1.05,
                                                debounce=True,
                                                style={'width': '80%'},
                                            ),
                                        ], width=1,
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Button("View Failed Chips", id=f"{APP_PREFIX}-openModal", n_clicks=0),
                                            dbc.Modal(
                                                [
                                                    dbc.ModalHeader(
                                                        dbc.ModalTitle("Chips That Fail Reliabililty Vmax")),
                                                    dbc.ModalBody(
                                                        dbc.Spinner(
                                                            dt.DataTable(
                                                                id=f"{APP_PREFIX}-modal-table",
                                                                columns=[{"name": i, "id": i} for i in ("foo", "bar")],
                                                                fixed_rows={"headers": True},
                                                                # fixed_columns={'headers': True, 'data': 2},
                                                                style_cell={
                                                                    "minWidth": "60px",
                                                                    "width": "110px",
                                                                    "maxWidth": "120px",
                                                                    "textAlign": "center",
                                                                    "fontSize": TABLE_FONT_SIZE,
                                                                },
                                                                style_table={
                                                                    "minHeight": "500px",
                                                                    "height": "500px",
                                                                    "maxHeight": "500px",
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
                                                                export_format="xlsx",
                                                            ),
                                                        ),
                                                    ),
                                                    dbc.ModalFooter(
                                                        dbc.Button(
                                                            "Close",
                                                            id=f"{APP_PREFIX}-close",
                                                            className="ms-auto",
                                                            n_clicks=0
                                                        )
                                                    ),
                                                ],
                                                id=f"{APP_PREFIX}-modal",
                                                size="xl",
                                                is_open=False,
                                            ),
                                        ]
                                    ),
                                ],
                                align="center",
                            )
                        ),
                        dbc.Spinner(
                            dt.DataTable(
                                id=f"{APP_PREFIX}-summary-table",
                                columns=[{"name": i, "id": i} for i in ("foo", "bar")],
                                fixed_rows={"headers": True},
                                # fixed_columns={'headers': True, 'data': 2},
                                style_cell={
                                    "minWidth": "80px",
                                    "width": "130px",
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
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H5("Reliability Vmax CDF Charts"),
                            dbc.Form(
                                dbc.Row(
                                    [
                                        dbc.Label(
                                            "Family Code",
                                            html_for=f"{APP_PREFIX}-CDF-family-code",
                                            width=COL_WIDTH_AUTO,
                                            className="pt-0 pe-0",
                                        ),
                                        dbc.Col(
                                            dcc.RadioItems(
                                                id=f"{APP_PREFIX}-CDF-family-code",
                                                options=[
                                                    {"label": "P10 DD2", "value": "p10dd2"},
                                                    {"label": "zA DD2", "value": "zadd2"},
                                                ],
                                                value="p10dd2",
                                                inputClassName="me-1",
                                                labelClassName="me-3",
                                            ),
                                        ),
                                    ],
                                    align="center",
                                ),
                            ),
                            dbc.Spinner(
                                dcc.Graph(
                                    id=f"{APP_PREFIX}-CDF-Charts-Container",
                                    style={"height": "100%", "width": "100%"},
                                ),
                            ),
                        ],
                    ),
                    dbc.Col(
                        [
                            html.H5("Reliability Vmax Box Charts"),
                            dbc.Form(
                                dbc.Row(
                                    [
                                        dbc.Label(
                                            "Family Code",
                                            html_for=f"{APP_PREFIX}-Box-family-code",
                                            width=COL_WIDTH_AUTO,
                                            className="pt-0 pe-0",
                                        ),
                                        dbc.Col(
                                            dcc.RadioItems(
                                                id=f"{APP_PREFIX}-Box-family-code",
                                                options=[
                                                    {"label": "P10 DD2", "value": "p10dd2"},
                                                    {"label": "zA DD2", "value": "zadd2"},
                                                ],
                                                value="p10dd2",
                                                inputClassName="me-1",
                                                labelClassName="me-3",
                                            ),
                                        ),
                                    ],
                                    align="center",
                                ),
                            ),
                            dbc.Spinner(
                                dcc.Graph(
                                    id=f"{APP_PREFIX}-Box-Charts-Container",
                                    style={"height": "100%", "width": "100%"},
                                ),
                            ),
                        ],
                    ),
                ],
                className="pretty-container mb-3"
            ),
            dbc.Row(
                dbc.Col(
                    [
                        html.H5("Reliability Vmax VT By Month"),
                        dbc.Form(
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            dbc.Label(
                                                "Family Code",
                                                html_for=f"{APP_PREFIX}-VTbyMonth-family-code",
                                                width=COL_WIDTH_AUTO,
                                                className="pt-0 pe-0",
                                            ),
                                            dbc.Col(
                                                dcc.RadioItems(
                                                    id=f"{APP_PREFIX}-VTbyMonth-family-code",
                                                    options=[
                                                        {"label": "P10 DD2", "value": "p10dd2"},
                                                        {"label": "zA DD2", "value": "zadd2"},
                                                    ],
                                                    value="p10dd2",
                                                    inputClassName="me-1",
                                                    labelClassName="me-3",
                                                ),
                                            ),
                                        ],
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Label(
                                                "One Graph/Side by Side",
                                                html_for=f"{APP_PREFIX}-VTbyMonth-toggle",
                                                width=COL_WIDTH_AUTO,
                                                className="pt-0 pe-0",
                                            ),
                                            dbc.Col(
                                                dcc.RadioItems(
                                                    id=f"{APP_PREFIX}-VTbyMonth-toggle",
                                                    options=[
                                                        {"label": "Side by Side", "value": True},
                                                        {"label": "One Graph", "value": False},
                                                    ],
                                                    value=True,
                                                    inputClassName="me-1",
                                                    labelClassName="me-3",
                                                ),
                                            ),
                                        ],
                                    ),
                                ],
                                align="center",
                            ),
                        ),
                        dbc.Spinner(
                            dcc.Graph(
                                id=f"{APP_PREFIX}-VTbyMonth-Charts-Container",
                                style={"height": "100%", "width": "100%"},
                            ),
                        ),
                    ],
                ),
                className="pretty-container mb-3"
            ),
            dbc.Row(
                dbc.Col(
                    [
                        html.H5("Reliability Vmax MOL By Month"),
                        dbc.Form(
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            dbc.Label(
                                                "Family Code",
                                                html_for=f"{APP_PREFIX}-MOLbyMonth-family-code",
                                                width=COL_WIDTH_AUTO,
                                                className="pt-0 pe-0",
                                            ),
                                            dbc.Col(
                                                dcc.RadioItems(
                                                    id=f"{APP_PREFIX}-MOLbyMonth-family-code",
                                                    options=[
                                                        {"label": "P10 DD2", "value": "p10dd2"},
                                                        {"label": "zA DD2", "value": "zadd2"},
                                                    ],
                                                    value="p10dd2",
                                                    inputClassName="me-1",
                                                    labelClassName="me-3",
                                                ),
                                            ),
                                        ],
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Label(
                                                "One Graph/Side by Side",
                                                html_for=f"{APP_PREFIX}-MOLbyMonth-toggle",
                                                width=COL_WIDTH_AUTO,
                                                className="pt-0 pe-0",
                                            ),
                                            dbc.Col(
                                                dcc.RadioItems(
                                                    id=f"{APP_PREFIX}-MOLbyMonth-toggle",
                                                    options=[
                                                        {"label": "Side by Side", "value": True},
                                                        {"label": "One Graph", "value": False},
                                                    ],
                                                    value=True,
                                                    inputClassName="me-1",
                                                    labelClassName="me-3",
                                                ),
                                            ),
                                        ],
                                    ),
                                ],
                                align="center",
                            ),
                        ),
                        dbc.Spinner(
                            dcc.Graph(
                                id=f"{APP_PREFIX}-MOLbyMonth-Charts-Container",
                                style={"height": "100%", "width": "100%"},
                            ),
                        ),
                    ],
                ),
                className="pretty-container mb-3"
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H5("Reliability Vmax OPDB By Month"),
                            dbc.Form(
                                dbc.Row(
                                    [
                                        dbc.Label(
                                            "Family Code",
                                            html_for=f"{APP_PREFIX}-OPDBbyMonth-family-code",
                                            width=COL_WIDTH_AUTO,
                                            className="pt-0 pe-0",
                                        ),
                                        dbc.Col(
                                            dcc.RadioItems(
                                                id=f"{APP_PREFIX}-OPDBbyMonth-family-code",
                                                options=[
                                                    {"label": "P10 DD2", "value": "p10dd2"},
                                                    {"label": "zA DD2", "value": "zadd2"},
                                                ],
                                                value="p10dd2",
                                                inputClassName="me-1",
                                                labelClassName="me-3",
                                            ),
                                        ),
                                    ],
                                    align="center",
                                ),
                            ),
                            dbc.Spinner(
                                dcc.Graph(
                                    id=f"{APP_PREFIX}-OPDBbyMonth-Charts-Container",
                                    style={"height": "100%", "width": "100%"},
                                ),
                            ),
                        ],
                    ),
                    dbc.Col(
                        [
                            html.H5("Reliability Vmax OPDB CDF"),
                            dbc.Spinner(
                                dcc.Graph(
                                    id=f"{APP_PREFIX}-OPDBCDF-Charts-Container",
                                    style={"height": "100%", "width": "100%"},
                                ),
                            ),
                        ],
                    ),
                ],
                className="pretty-container mb-3"
            ),
        ],

    )


layout = html.Div([dcc.Tabs(id=f"{APP_PREFIX}_tabs", children=[all_tab()])])


########################################################################################################################
# callbacks
########################################################################################################################
# Clear Cache Callback
@callback(
    Output(f"{APP_PREFIX}-all-refresh-prompt", "children"),
    Input(f"{APP_PREFIX}-all-clear-cache-button", "n_clicks"),
)
def update_output(n_clicks):
    if n_clicks is not None:
        cache.delete_memoized(pull_rel_vmax_chip_data)
        return "Cache has been cleared. Please refresh the page."


# Download Raw Data Callback
@callback(
    Output(f"{APP_PREFIX}_download_raw_data", "data"),
    Input(f"{APP_PREFIX}_download_button", "n_clicks"),
    State(f"{APP_PREFIX}_daterange", "start_date"),
    State(f"{APP_PREFIX}_daterange", "end_date"),
    prevent_initial_call=True,
)
def download_raw_data(n_clicks, start_date, end_date):
    df = pull_rel_vmax_chip_data(start_date, end_date)
    return dcc.send_data_frame(df.to_csv, "rel_vmax_raw_data.csv")


# Mini Table Callback
@callback(
    Output(f"{APP_PREFIX}-small-table", "columns"),
    Output(f"{APP_PREFIX}-small-table", "data"),
    Input(f"{APP_PREFIX}-parameter-input", "value"),
    Input(f"{APP_PREFIX}-int-input", "value"),
    Input(f"{APP_PREFIX}_daterange", "start_date"),
    Input(f"{APP_PREFIX}_daterange", "end_date"),
)
def generate_small_table(parm, cutoff, start_date, end_date):
    df = pull_rel_vmax_chip_data(start_date, end_date)
    data = df.groupby('product_schema').apply(lambda x: len(x[x[parm] < cutoff]) / len(x)).reset_index(
        name='{} < {} (%)'.format(parm, str(cutoff)))
    columns = [
        dict(name=data.columns[0], id=data.columns[0]),
        dict(name=data.columns[1], id=data.columns[1], type='numeric', format=dt.FormatTemplate.percentage(4))
    ]
    data_dict = data.fillna("-").to_dict("records")

    return columns, data_dict


# Mini Table 2 Callback
@callback(
    Output(f"{APP_PREFIX}-small-table2", "columns"),
    Output(f"{APP_PREFIX}-small-table2", "data"),
    Input(f"{APP_PREFIX}-small-fc-toggle", "value"),
    Input(f"{APP_PREFIX}_daterange", "start_date"),
    Input(f"{APP_PREFIX}_daterange", "end_date"),
)
def generate_small_table2(fc, start_date, end_date):
    df = pull_rel_vmax_chip_data(start_date, end_date)
    data = df[df['product_schema'] == fc]
    if fc == "p10dd2":
        data = data[['rvtp_vmax_18', 'ulvtp_vmax_18', 'slvtn_vmax_18', 'mol54_vmax_18', 'mol60_vmax_18']].agg(
            ['mean', 'median', 'std']).transpose().reset_index().rename(
            columns={'index': 'device', 'mean': 'mean (V)', 'median': 'median (V)', 'std': 'std (mV)'})
    elif fc == "zadd2":
        data = data[['rvtp_vmax_18', 'ulvtp_vmax_18', 'slvtn_vmax_18', 'mol54_vmax_18', 'mol60_vmax_18',
                   'lvt_pfet_vmax']].agg(
            ['mean', 'median', 'std']).transpose().reset_index().rename(
            columns={'index': 'device', 'mean': 'mean (V)', 'median': 'median (V)', 'std': 'std (mV)'})
    data['std (mV)'] = data['std (mV)'].map(lambda x: x * 1000)
    data = data.round(4)
    columns = [{"name": i, "id": i} for i in data.columns]
    data_dict = data.fillna("-").to_dict("records")

    return columns, data_dict


# Mini Table 3 Callback
@callback(
    Output(f"{APP_PREFIX}-small-table3", "columns"),
    Output(f"{APP_PREFIX}-small-table3", "data"),
    Input(f"{APP_PREFIX}_daterange", "start_date"),
    Input(f"{APP_PREFIX}_daterange", "end_date"),
)
def generate_small_table3(start_date, end_date):
    df = pull_rel_vmax_chip_data(start_date, end_date)
    data = df.groupby('product_schema').agg({'opdb_vmax': ['mean', 'median', 'std']}).reset_index().rename(
        columns={'mean': 'mean (V)', 'median': 'median (V)', 'std': 'std (mV)'})
    data.columns = data.columns.droplevel()
    data['std (mV)'] = data['std (mV)'].map(lambda x: x * 1000)
    data = data.round(4)
    columns = [{"name": i, "id": i} for i in data.columns]
    data_dict = data.fillna("-").to_dict("records")

    return columns, data_dict


# Mini table 4 Callback
@callback(
    Output(f"{APP_PREFIX}-small-table4", "columns"),
    Output(f"{APP_PREFIX}-small-table4", "data"),
    Input(f"{APP_PREFIX}_daterange", "start_date"),
    Input(f"{APP_PREFIX}_daterange", "end_date"),
)
def generate_small_table4(start_date, end_date):
    df = pull_rel_vmax_chip_data(start_date, end_date)
    data = pd.pivot_table(df, values='wafer_id', index='product_schema', columns='test_month',
                          aggfunc=lambda x: x.nunique())
    data.columns.name = None
    data['total'] = data.sum(axis=1)
    data = data.reset_index().rename(columns={'product_schema': 'family_code'})
    columns = [{"name": i, "id": i} for i in data.columns]
    data_dict = data.fillna("-").to_dict("records")

    return columns, data_dict


# Generate Summary Table Callback
@callback(
    Output(f"{APP_PREFIX}-summary-table", "columns"),
    Output(f"{APP_PREFIX}-summary-table", "data"),
    Output(f"{APP_PREFIX}-summary-table", "style_data_conditional"),
    Output(f"{APP_PREFIX}-summary-table", "style_cell_conditional"),
    Input(f"{APP_PREFIX}-month-lot-toggle", "value"),
    Input(f"{APP_PREFIX}-p10-thresh", "value"),
    Input(f"{APP_PREFIX}-zA-thresh", "value"),
    Input(f"{APP_PREFIX}_daterange", "start_date"),
    Input(f"{APP_PREFIX}_daterange", "end_date"),
)
def generate_summary_table(selected_item: str, p10_thresh, zA_thresh, start_date, end_date):
    if not selected_item:
        raise PreventUpdate()
    data = pull_rel_vmax_chip_data(start_date, end_date)
    data['num_bad_chips'] = data.apply(lambda x: 1 if (x.product_schema == 'p10dd2' and x.opdb_vmax < p10_thresh) or
                                                      (x.product_schema == 'zadd2' and x.opdb_vmax < zA_thresh) else 0,
                                       axis=1)
    data['%_bad_chips'] = data.apply(lambda x: 1 if (x.product_schema == 'p10dd2' and x.opdb_vmax < p10_thresh) or
                                                    (x.product_schema == 'zadd2' and x.opdb_vmax < zA_thresh)
                                                    else 0, axis=1)
    style_cell_conditional = [
        {"if": {"column_id": "product_schema"}, "width": "120px"},
        {"if": {"column_id": "num_wafers"}, "width": "110px"},
        {"if": {"column_id": "num_bad_chips"}, "width": "110px"},
        {"if": {"column_id": "%_bad_chips"}, "width": "110px"},
        {"if": {"column_id": "test_month"}, "width": "110px"},
        {"if": {"column_id": "test_week"}, "width": "110px"},
        {"if": {"column_id": "test_date"}, "width": "110px"},
        {"if": {"column_id": "lotnumber"}, "width": "110px"},
        {"if": {"column_id": "wafer_id"}, "width": "110px"},
    ]

    if selected_item == "month":
        conditional_highlight = [{"if": {"column_id": "test_month"}, "backgroundColor": 'LemonChiffon'}]
    elif selected_item == 'week':
        conditional_highlight = [{"if": {"column_id": "test_week"}, "backgroundColor": 'LemonChiffon'}]
    elif selected_item == "lot":
        conditional_highlight = [{"if": {"column_id": "lotnumber"}, "backgroundColor": 'LemonChiffon'}]
    elif selected_item == "wafer":
        conditional_highlight = [{"if": {"column_id": "wafer_id"}, "backgroundColor": 'LemonChiffon'}]
    else:
        raise ValueError(f"unknown selection '{selected_item}'")

    if selected_item == "month":
        data = data.groupby(['product_schema', 'test_month']).agg(MO_WEEK_AGG_FUNCTIONS).reset_index().rename(
            columns={'wafer_id': 'num_wafers'}).sort_values(by='test_month', ascending=False)
    elif selected_item == "week":
        data = data.groupby(['product_schema', 'test_week']).agg(MO_WEEK_AGG_FUNCTIONS).reset_index().rename(
            columns={'wafer_id': 'num_wafers'}).sort_values(by='test_week', ascending=False)
    elif selected_item == 'lot':
        data = data.groupby(['product_schema', 'lotnumber']).agg(LOT_WAFER_AGG_FUNCTIONS).reset_index() \
            .sort_values(by='test_date', ascending=False)
    elif selected_item == 'wafer':
        data = data.groupby(['product_schema', 'lotnumber', 'wafer_id']).agg(LOT_WAFER_AGG_FUNCTIONS).reset_index() \
            .sort_values(by='test_date', ascending=False)

    round_cols = [i for i in data.columns if i != '%_bad_chips']
    data[round_cols] = data[round_cols].round(4)
    # conditional color formatting
    n_bins = 8
    bounds = [i * (1.0 / n_bins) for i in range(n_bins + 1)]
    cols = ['%_bad_chips']
    df_numeric_columns = data[cols]
    df_max = df_numeric_columns.max().max()
    df_min = df_numeric_columns.min().min()
    ranges = [
        ((df_max - df_min) * i) + df_min
        for i in bounds
    ]
    styles = []
    for i in range(1, len(bounds)):
        min_bound = ranges[i - 1]
        max_bound = ranges[i]
        backgroundColor = colorlover.scales[str(n_bins)]['seq']['Reds'][i - 1]
        color = 'white' if i > len(bounds) / 2. else 'inherit'
        for column in df_numeric_columns:
            styles.append({
                'if': {
                    'filter_query': (
                            '{{{column}}} >= {min_bound}' +
                            (' && {{{column}}} < {max_bound}' if (i < len(bounds) - 1) else '')
                    ).format(column=column, min_bound=min_bound, max_bound=max_bound),
                    'column_id': column
                },
                'backgroundColor': backgroundColor,
                'color': color
            })

    style_data_conditional = (
            [
                {
                    "if": {
                        "filter_query": "{product_schema} = p10dd2",
                        "column_id": "product_schema",
                    },
                    "backgroundColor": 'lavender',
                }
            ] +
            [
                {
                    "if": {
                        "filter_query": "{product_schema} = zadd2",
                        "column_id": "product_schema",
                    },
                    "backgroundColor": 'LightCyan',
                }
            ] +
            conditional_highlight +
            styles
    )
    columns = [
        {"name": i, "id": i}
        if i != '%_bad_chips' else
        {"name": i, "id": i, "type": "numeric", "format": dt.FormatTemplate.percentage(4)}
        for i in data.columns
    ]
    data_dict = data.fillna(np.NAN).to_dict("records")

    return columns, data_dict, style_data_conditional, style_cell_conditional


# CDF Graph Callback
@callback(
    Output(f"{APP_PREFIX}-CDF-Charts-Container", "figure"),
    # Output(f"{APP_PREFIX}-CDF-Charts-Container", "style"),
    Input(f"{APP_PREFIX}-CDF-family-code", "value"),
    Input(f"{APP_PREFIX}_daterange", "start_date"),
    Input(f"{APP_PREFIX}_daterange", "end_date"),
)
def plot_rel_cdf(family_code, start_date, end_date):
    df = pull_rel_vmax_chip_data(start_date, end_date)
    df = df[df['product_schema'] == family_code]
    if family_code == 'p10dd2':
        fig = px.ecdf(df, x=[
            'rvtp_vmax_18', 'ulvtp_vmax_18', 'slvtn_vmax_18', 'mol54_vmax_18', 'mol60_vmax_18'
        ])  # , marginal='histogram')
    elif family_code == 'zadd2':
        fig = px.ecdf(df, x=[
            'rvtp_vmax_18', 'ulvtp_vmax_18', 'slvtn_vmax_18', 'lvt_pfet_vmax', 'mol54_vmax_18', 'mol60_vmax_18'
        ])
    else:
        fig = empty_figure("unknown product")
    fig.update_xaxes(range=[1, 1.5])
    fig.update_layout(yaxis={'dtick': 0.1})
    return fig


# Box Chart Callback
@callback(
    Output(f"{APP_PREFIX}-Box-Charts-Container", "figure"),
    # Output(f"{APP_PREFIX}-Box-Charts-Container", "style"),
    Input(f"{APP_PREFIX}-Box-family-code", "value"),
    Input(f"{APP_PREFIX}_daterange", "start_date"),
    Input(f"{APP_PREFIX}_daterange", "end_date"),
)
def plot_rel_box(family_code, start_date, end_date):
    df = pull_rel_vmax_chip_data(start_date, end_date)
    df = df[df['product_schema'] == family_code]

    if family_code == 'p10dd2':
        fig = px.box(df, y=['rvtp_vmax_18', 'ulvtp_vmax_18', 'slvtn_vmax_18', 'mol54_vmax_18', 'mol60_vmax_18'])
    elif family_code == 'zadd2':
        fig = px.box(df, y=[
            'rvtp_vmax_18', 'ulvtp_vmax_18', 'slvtn_vmax_18', 'lvt_pfet_vmax', 'mol54_vmax_18', 'mol60_vmax_18'
        ])
    else:
        fig = empty_figure("unknown product")
    return fig


# By Month Callback VT parameters
@callback(
    Output(f"{APP_PREFIX}-VTbyMonth-Charts-Container", "figure"),
    # Output(f"{APP_PREFIX}-VTbyMonth-Charts-Container", "style"),
    Input(f"{APP_PREFIX}-VTbyMonth-family-code", "value"),
    Input(f"{APP_PREFIX}-VTbyMonth-toggle", "value"),
    Input(f"{APP_PREFIX}_daterange", "start_date"),
    Input(f"{APP_PREFIX}_daterange", "end_date"),
)
def plot_vt_by_month(family_code, subplots, start_date, end_date):
    df = pull_rel_vmax_chip_data(start_date, end_date)
    df = df[df['product_schema'] == family_code]
    xval = 'test_month'

    if family_code == 'p10dd2':
        yvals = ['rvtp_vmax_18', 'ulvtp_vmax_18', 'slvtn_vmax_18']
    elif family_code == 'zadd2':
        yvals = ['rvtp_vmax_18', 'ulvtp_vmax_18', 'slvtn_vmax_18', 'lvt_pfet_vmax']
    else:
        yvals = []

    xylabels = ['Month', 'Vmax']
    if subplots:
        n = len(yvals)
        fig = make_subplots(rows=1, cols=n, subplot_titles=(yvals))
        for i, yval in enumerate(yvals):
            fig.add_trace(go.Box(y=df[yval], x=df[xval], name=yval), row=1, col=i + 1)
            fig.update_xaxes(title_text=xylabels[0], tickformat="%b %Y", row=1, col=i + 1)

        fig.update_layout(yaxis_title=xylabels[1])
    else:
        fig = go.Figure()
        for yval in yvals:
            fig.add_trace(go.Box(y=df[yval], x=df[xval], name=yval))

        fig.update_layout(
            yaxis_title=xylabels[1],
            xaxis_title=xylabels[0],
            boxmode='group',  # group together boxes of the different traces for each value of x
            xaxis=dict(tickformat="%b %Y"),
        )

    fig.update_xaxes(tickangle=45)
    return fig


# By month callback MOL parameters
@callback(
    Output(f"{APP_PREFIX}-MOLbyMonth-Charts-Container", "figure"),
    # Output(f"{APP_PREFIX}-VTbyMonth-Charts-Container", "style"),
    Input(f"{APP_PREFIX}-MOLbyMonth-family-code", "value"),
    Input(f"{APP_PREFIX}-MOLbyMonth-toggle", "value"),
    Input(f"{APP_PREFIX}_daterange", "start_date"),
    Input(f"{APP_PREFIX}_daterange", "end_date"),
)
def plot_mol_by_month(family_code, subplots, start_date, end_date):
    df = pull_rel_vmax_chip_data(start_date, end_date)
    df = df[df['product_schema'] == family_code]
    xval = 'test_month'
    yvals = ['mol54_vmax_18', 'mol60_vmax_18']
    xylabels = ['Month', 'Vmax']
    if subplots:
        n = len(yvals)
        fig = make_subplots(rows=1, cols=n, subplot_titles=(yvals))
        for i, yval in enumerate(yvals):
            fig.add_trace(go.Box(y=df[yval], x=df[xval], name=yval), row=1, col=i + 1)
            fig.update_xaxes(title_text=xylabels[0], tickformat="%b %Y", row=1, col=i + 1)

        fig.update_layout(
            yaxis_title=xylabels[1],
        )
    else:
        fig = go.Figure()
        for yval in yvals:
            fig.add_trace(go.Box(y=df[yval], x=df[xval], name=yval))

        fig.update_layout(
            yaxis_title=xylabels[1],
            xaxis_title=xylabels[0],
            boxmode='group',  # group together boxes of the different traces for each value of x
            xaxis=dict(tickformat="%b %Y"),
        )

    fig.update_xaxes(tickangle=45)
    return fig


# By Month Callback OPDB parameter
@callback(
    Output(f"{APP_PREFIX}-OPDBbyMonth-Charts-Container", "figure"),
    # Output(f"{APP_PREFIX}-OPDBbyMonth-Charts-Container", "style"),
    Input(f"{APP_PREFIX}-OPDBbyMonth-family-code", "value"),
    Input(f"{APP_PREFIX}_daterange", "start_date"),
    Input(f"{APP_PREFIX}_daterange", "end_date"),
)
def plot_opdb(family_code, start_date, end_date):
    df = pull_rel_vmax_chip_data(start_date, end_date)
    df = df[df['product_schema'] == family_code]
    xval = 'test_month'
    yvals = ['opdb_vmax']
    xylabels = ['Month', 'Vmax']
    fig = go.Figure()
    for yval in yvals:
        fig.add_trace(go.Box(y=df[yval], x=df[xval], name=yval))

    fig.update_layout(
        yaxis_title=xylabels[1],
        xaxis_title=xylabels[0],
        boxmode='group',  # group together boxes of the different traces for each value of x
        xaxis=dict(tickformat="%b %Y"),
    )
    fig.update_xaxes(tickangle=45)
    return fig


# CDF Callback OPDB
@callback(
    Output(f"{APP_PREFIX}-OPDBCDF-Charts-Container", "figure"),
    # Output(f"{APP_PREFIX}-OPDBCDF-Charts-Container", "style"),
    Input(f"{APP_PREFIX}_daterange", "start_date"),
    Input(f"{APP_PREFIX}_daterange", "end_date"),
)
def plot_opdb_cdf(start_date, end_date):
    df = pull_rel_vmax_chip_data(start_date, end_date)
    fig = px.ecdf(df, x='opdb_vmax', color='product_schema')  # , marginal='histogram')
    fig.update_xaxes(range=[1.05, 1.10])
    fig.update_layout(yaxis={'dtick': 0.1})
    return fig


# Open Modal Callback (View failed chips)
@callback(
    Output(f"{APP_PREFIX}-modal", "is_open"),
    [Input(f"{APP_PREFIX}-openModal", "n_clicks"),
     Input(f"{APP_PREFIX}-close", "n_clicks")],
    [State(f"{APP_PREFIX}-modal", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


@callback(
    Output(f"{APP_PREFIX}-modal-table", "columns"),
    Output(f"{APP_PREFIX}-modal-table", "data"),
    Output(f"{APP_PREFIX}-modal-table", "style_data_conditional"),
    Output(f"{APP_PREFIX}-modal-table", "style_cell_conditional"),
    Input(f"{APP_PREFIX}-month-lot-toggle", "value"),
    Input(f"{APP_PREFIX}-p10-thresh", "value"),
    Input(f"{APP_PREFIX}-zA-thresh", "value"),
    Input(f"{APP_PREFIX}_daterange", "start_date"),
    Input(f"{APP_PREFIX}_daterange", "end_date"),
    Input(f"{APP_PREFIX}-summary-table", "derived_virtual_data"),
    Input(f"{APP_PREFIX}-summary-table", "derived_virtual_selected_rows"),
)
def failed_chips_table(selected_item: str, p10_thresh, zA_thresh, start_date, end_date, table_rows, table_indices):
    if not selected_item:
        raise PreventUpdate()

    data = pull_rel_vmax_chip_data(start_date, end_date)
    data['num_bad_chips'] = data.apply(
        lambda x: 1 if (x.product_schema == 'p10dd2' and x.opdb_vmax < p10_thresh) or (x.product_schema == 'zadd2' and x.opdb_vmax < zA_thresh) else 0,
        axis=1
    )
    data = data[data['num_bad_chips'] == 1]
    selection_df = pd.DataFrame(table_rows)
    if table_indices:
        if selected_item == 'week':
            chips = [selection_df["test_week"][i] for i in table_indices]
            fc = [selection_df["product_schema"][i] for i in table_indices]
            data = data[data["test_week"].isin(chips)]
            data = data[data["product_schema"].isin(fc)]
        elif selected_item == 'month':
            chips = [selection_df["test_month"][i] for i in table_indices]
            fc = [selection_df["product_schema"][i] for i in table_indices]
            data = data[data["test_month"].isin(chips)]
            data = data[data["product_schema"].isin(fc)]
        elif selected_item == 'lot':
            chips = [selection_df["lotnumber"][i] for i in table_indices]
            data = data[data["lotnumber"].isin(chips)]
        elif selected_item == 'wafer':
            chips = [selection_df["wafer_id"][i] for i in table_indices]
            data = data[data["wafer_id"].isin(chips)]
        else:
            LOG.error(f"item {selected_item} is unsupported")
            raise PreventUpdate

    data = data[[
        'product_schema', 'lotnumber', 'wafer_id', 'chipx', 'chipy', 'test_date', 'opdb_vmax', 'rvtp_vmax_18',
        'ulvtp_vmax_18', 'slvtn_vmax_18', 'mol54_vmax_18', 'mol60_vmax_18', 'mol_vmax', 'vmaxpfet',
        'lvt_pfet_vmax'
    ]].sort_values(by='test_date', ascending=False).round(4)

    style_cell_conditional = (
        [
            {"if": {"column_id": "product_schema"}, "width": "120px"},
            {"if": {"column_id": "test_date"}, "width": "80px"},
            {"if": {"column_id": "lotnumber"}, "width": "110px"},
            {"if": {"column_id": "wafer_id"}, "width": "80px"},
            {"if": {"column_id": "chipx"}, "width": "60px"},
            {"if": {"column_id": "chipy"}, "width": "60px"},
        ]
    )
    style_data_conditional = (
            [
                {
                    "if": {
                        "filter_query": "{product_schema} = p10dd2",
                        "column_id": "product_schema",
                    },
                    "backgroundColor": 'lavender',
                }
            ] +
            [
                {
                    "if": {
                        "filter_query": "{product_schema} = zadd2",
                        "column_id": "product_schema",
                    },
                    "backgroundColor": 'LightCyan',
                }
            ] +
            [
                {
                    "if": {
                        "column_id": ["lotnumber", "wafer_id", "chipx", "chipy"],
                    },
                    "backgroundColor": 'LemonChiffon',
                }
            ] +
            [
                {
                    "if": {
                        "filter_query": f"{{product_schema}} = zadd2 && {{{col}}} < {str(zA_thresh)}",
                        "column_id": col,
                    },
                    "backgroundColor": 'LightSalmon'
                }
                for col in data.drop(columns=[
                    'product_schema', 'lotnumber', 'wafer_id', 'chipx', 'chipy', 'test_date'
                ]).columns
            ] +
            [
                {
                    "if": {
                        "filter_query": f"{{product_schema}} = p10dd2 && {{{col}}} < {str(p10_thresh)}",
                        "column_id": col,
                    },
                    "backgroundColor": 'Salmon'
                }
                for col in data.drop(columns=[
                    'product_schema', 'lotnumber', 'wafer_id', 'chipx', 'chipy', 'test_date'
                ]).columns
            ]
    )
    columns = [{"name": i, "id": i} for i in data.columns]
    data_dict = data.fillna(np.NAN).to_dict("records")

    return columns, data_dict, style_data_conditional, style_cell_conditional
