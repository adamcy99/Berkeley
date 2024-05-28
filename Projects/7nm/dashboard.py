import pandas as pd
import numpy as np

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
pd.set_option('display.max_columns', None)


import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table as dt
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import plotly.express as px

import ibmdata

HEADER_BACKGROUND_COLOR = '#343A40'
HEADER_FONT_COLOR = 'white'
GOOD_GREEN = '#99FF99'
BAD_RED = '#FF9999'

##################################### SQL Yield Pulls ####################################

# Wafer Level df
daysback = 300
Query = """
WITH sail_cte AS(
    SELECT LEFT(wafer_id,5) AS lot_id_base, lot_id, wafer_id, family_code, MIN(tw.Last_test_date) AS Sail_date, 1 AS Sail_n,
      AVG(CASE WHEN parm_Label = 'SAILALL_H2_0p50to1p05_PerfectYield' THEN yield ELSE NULL END) AS SAILALL_0p50to1p05,
      AVG(CASE WHEN parm_Label = 'SAILALL_H2_0p65to1p05_PerfectYield' THEN yield ELSE NULL END) AS SAILALL_0p65to1p05,
      AVG(CASE WHEN parm_Label = 'SAIL1_H2_0p50to1p05_PerfectYield' THEN yield ELSE NULL END) AS SAIL1_0p50to1p05,
      AVG(CASE WHEN parm_Label = 'SAIL1_H2_0p65to1p05_PerfectYield' THEN yield ELSE NULL END) AS SAIL1_0p65to1p05,
      AVG(CASE WHEN parm_Label = 'SAIL2_H2_0p50to1p05_PerfectYield' THEN yield ELSE NULL END) AS SAIL2_0p50to1p05,
      AVG(CASE WHEN parm_Label = 'SAIL2_H2_0p65to1p05_PerfectYield' THEN yield ELSE NULL END) AS SAIL2_0p65to1p05,
      AVG(CASE WHEN parm_Label = 'SAIL3_H2_0p50to1p05_PerfectYield' THEN yield ELSE NULL END) AS SAIL3_0p50to1p05,
      AVG(CASE WHEN parm_Label = 'SAIL3_H2_0p65to1p05_PerfectYield' THEN yield ELSE NULL END) AS SAIL3_0p65to1p05
    FROM DMIW.PTileWaferFact ptwf
    INNER JOIN DMIW_SYSTEMS.TestParm tp ON ptwf.testparmkey = tp.testparmkey
    INNER JOIN DMIW_SYSTEMS.TestedWafer tw ON ptwf.testedWaferKey = tw.testedWaferKey
    WHERE tw.Last_test_date >= (current date - {} days)
      AND tw.Tech_id = '7HPP'
      AND tw.Level = 'H2'
      AND tw.Calcdefs in ('SSL11', 'SSL21', 'SSL31')
      AND weighted_Mean IS NOT null AND ABS(weighted_Mean) < 1e25
      AND UCASE(tp.parm_Label) LIKE '%_PERFECTYIELD'
    GROUP BY lot_id, wafer_id, family_code
    ORDER BY Sail_date desc, lot_id, wafer_id
),
pele_cte AS(
    SELECT lot_Id, wafer_Id, family_code, MIN(last_Test_Date) AS Pele_date, 1 as Pele_n,
        AVG(CASE WHEN ucase(tp.parm_Label) = 'PELEALL_H2_L3_HL_PERFECTYIELD' THEN yield ELSE null END) AS PELE_ALL_L3_Vmax_PY,
        AVG(CASE WHEN ucase(tp.parm_Label) = 'PELEALL_H2_L3_NL_PERFECTYIELD' THEN yield ELSE null END) AS PELE_ALL_L3_Vnom_PY,
        AVG(CASE WHEN ucase(tp.parm_Label) = 'PELEALL_H2_L3_LL_PERFECTYIELD' THEN yield ELSE null END) AS PELE_ALL_L3_Vmin_PY,
        AVG(CASE WHEN ucase(tp.parm_Label) = 'PELE1_H2_L3_HL_PERFECTYIELD' THEN yield ELSE null END) AS PELE1_L3_Vmax_PY,
        AVG(CASE WHEN ucase(tp.parm_Label) = 'PELE1_H2_L3_NL_PERFECTYIELD' THEN yield ELSE null END) AS PELE1_L3_Vnom_PY,
        AVG(CASE WHEN ucase(tp.parm_Label) = 'PELE1_H2_L3_LL_PERFECTYIELD' THEN yield ELSE null END) AS PELE1_L3_Vmin_PY,
        AVG(CASE WHEN ucase(tp.parm_Label) = 'PELE2_H2_L3_HL_PERFECTYIELD' THEN yield ELSE null END) AS PELE2_L3_Vmax_PY,
        AVG(CASE WHEN ucase(tp.parm_Label) = 'PELE2_H2_L3_NL_PERFECTYIELD' THEN yield ELSE null END) AS PELE2_L3_Vnom_PY,
        AVG(CASE WHEN ucase(tp.parm_Label) = 'PELE2_H2_L3_LL_PERFECTYIELD' THEN yield ELSE null END) AS PELE2_L3_Vmin_PY,
        AVG(CASE WHEN ucase(tp.parm_Label) = 'PELE3_H2_L3_HL_PERFECTYIELD' THEN yield ELSE null END) AS PELE3_L3_Vmax_PY,
        AVG(CASE WHEN ucase(tp.parm_Label) = 'PELE3_H2_L3_NL_PERFECTYIELD' THEN yield ELSE null END) AS PELE3_L3_Vnom_PY,
        AVG(CASE WHEN ucase(tp.parm_Label) = 'PELE3_H2_L3_LL_PERFECTYIELD' THEN yield ELSE null END) AS PELE3_L3_Vmin_PY
    FROM DMIW.PTileWaferFact ptwf
    INNER JOIN DMIW_SYSTEMS.TestParm tp ON tp.testParmKey = ptwf.testParmKey 
    INNER JOIN DMIW_SYSTEMS.TestedWafer tw ON tw.testedWaferKey = ptwf.testedWaferKey
    WHERE Last_test_date >= (current date - {} days) AND
        Tech_id = '7HPP' and Level = 'H2' AND tw.Calcdefs IN ('PEL11', 'PEL21', 'PEL31') AND
        weighted_Mean IS NOT null AND abs(weighted_Mean) < 1e25 AND
        (ucase(tp.parm_Label) LIKE 'PELE%_H2_L3_%PERFECTYIELD')
    GROUP BY lot_Id, wafer_Id, family_code
)
SELECT s.lot_id_base, s.lot_id, s.wafer_id, s.family_code, Sail_date, Sail_n, 
    SAILALL_0p50to1p05, SAILALL_0p65to1p05, SAIL1_0p50to1p05, SAIL1_0p65to1p05, 
    SAIL2_0p50to1p05, SAIL2_0p65to1p05, SAIL3_0p50to1p05, SAIL3_0p65to1p05,
    Pele_date, Pele_n, PELE_ALL_L3_Vmax_PY, PELE_ALL_L3_Vnom_PY, PELE_ALL_L3_Vmin_PY,
    PELE1_L3_Vmax_PY, PELE1_L3_Vnom_PY, PELE1_L3_Vmin_PY, PELE2_L3_Vmax_PY, PELE2_L3_Vnom_PY, 
    PELE2_L3_Vmin_PY, PELE3_L3_Vmax_PY, PELE3_L3_Vnom_PY, PELE3_L3_Vmin_PY
FROM sail_cte s
LEFT JOIN pele_cte p ON s.wafer_id = p.wafer_id
ORDER BY Sail_date desc, s.lot_id, s.wafer_id
""".format(daysback,daysback)

w_df = ibmdata.isdw.query(Query)
w_df['sailall_0p50to1p05'] = w_df['sailall_0p50to1p05'].astype(float).round(2)
w_df['sailall_0p65to1p05'] = w_df['sailall_0p65to1p05'].astype(float).round(2)
w_df['sail1_0p50to1p05'] = w_df['sail1_0p50to1p05'].astype(float).round(2)
w_df['sail1_0p65to1p05'] = w_df['sail1_0p65to1p05'].astype(float).round(2)
w_df['sail2_0p50to1p05'] = w_df['sail2_0p50to1p05'].astype(float).round(2)
w_df['sail2_0p65to1p05'] = w_df['sail2_0p65to1p05'].astype(float).round(2)
w_df['sail3_0p50to1p05'] = w_df['sail3_0p50to1p05'].astype(float).round(2)
w_df['sail3_0p65to1p05'] = w_df['sail3_0p65to1p05'].astype(float).round(2)

w_df['pele_all_l3_vmax_py'] = w_df['pele_all_l3_vmax_py'].astype(float).round(2)
w_df['pele_all_l3_vnom_py'] = w_df['pele_all_l3_vnom_py'].astype(float).round(2)
w_df['pele_all_l3_vmin_py'] = w_df['pele_all_l3_vmin_py'].astype(float).round(2)

w_df['pele1_l3_vmax_py'] = w_df['pele1_l3_vmax_py'].astype(float).round(2)
w_df['pele1_l3_vnom_py'] = w_df['pele1_l3_vnom_py'].astype(float).round(2)
w_df['pele1_l3_vmin_py'] = w_df['pele1_l3_vmin_py'].astype(float).round(2)

w_df['pele2_l3_vmax_py'] = w_df['pele2_l3_vmax_py'].astype(float).round(2)
w_df['pele2_l3_vnom_py'] = w_df['pele2_l3_vnom_py'].astype(float).round(2)
w_df['pele2_l3_vmin_py'] = w_df['pele2_l3_vmin_py'].astype(float).round(2)

w_df['pele3_l3_vmax_py'] = w_df['pele3_l3_vmax_py'].astype(float).round(2)
w_df['pele3_l3_vnom_py'] = w_df['pele3_l3_vnom_py'].astype(float).round(2)
w_df['pele3_l3_vmin_py'] = w_df['pele3_l3_vmin_py'].astype(float).round(2)

# Lot Level df
lot_df = w_df.groupby(['lot_id_base','lot_id','family_code']).agg({'sail_date':'min','sail_n':'sum', 
                                                     'sailall_0p50to1p05':'mean','sailall_0p65to1p05':'mean',
                                                     'sail1_0p50to1p05':'mean', 'sail1_0p65to1p05':'mean',
                                                     'sail2_0p50to1p05':'mean', 'sail2_0p65to1p05':'mean',
                                                     'sail3_0p50to1p05':'mean', 'sail3_0p65to1p05':'mean',
                                                     'pele_date':'min', 'pele_n':'sum','pele_all_l3_vmax_py':'mean',
                                                     'pele_all_l3_vnom_py':'mean','pele_all_l3_vmin_py':'mean',
                                                     'pele1_l3_vmax_py':'mean','pele1_l3_vnom_py':'mean',
                                                     'pele1_l3_vmin_py':'mean','pele2_l3_vmax_py':'mean',
                                                     'pele2_l3_vnom_py':'mean','pele2_l3_vmin_py':'mean',
                                                     'pele3_l3_vmax_py':'mean','pele3_l3_vnom_py':'mean',
                                                     'pele3_l3_vmin_py':'mean'}) \
                                                     .round(2).sort_values('sail_date',ascending=False).reset_index()

################################ This part of the code generates yield tables ########################
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div(children=[
	  # This part generates the interactive components for the table
    html.Div(children=[
		html.Label('Lot/Wafer Level'),
        dcc.RadioItems(
            id='lot-wafer-toggle',
            options=[
                {'label': 'Lot', 'value': 'lot'},
                {'label': 'Wafer', 'value': 'wafer'}
            ],
            value='lot'
        )
      ], 
      style={'margin-left':'auto','margin-right':'auto','width':'90%'}
    ),
    # This Div holds the table
    html.Div(id='datatable-interactivity-container',
             style={'margin-left':'auto','margin-right':'auto','width':'90%'},
    )
])

# This callback toggles between lot and wafer level datatables
@app.callback(
    Output('datatable-interactivity-container', 'children'),
    [Input('lot-wafer-toggle', 'value')]
)
def toggle_lotwafer(selected_item):
  global lot_wafer_state
  if selected_item == 'lot':
    lot_wafer_state = 'lot'
    return [
      # This part generates the header
      html.H4(children='7HPP Inline Yields - Lot Level'),
      # This part generates the table
      dt.DataTable(
          id='table-id',
          columns=[{"name":i,"id":i} for i in lot_df.columns],
          data=lot_df.fillna('-').to_dict('records'),
          fixed_rows={'headers':True},
          #fixed_columns={'headers': True, 'data': 2},
          style_cell={'minWidth': '130px', 'width': '160px', 'maxWidth': '160px'},
          style_table={'minHeight': '600px', 'height': '600px', 'maxHeight': '600px',
            		   'minWidth': '100%', 'width': '100%', 'maxWidth': '100%'},
          style_header={'backgroundColor': HEADER_BACKGROUND_COLOR, 'color':HEADER_FONT_COLOR,
                        'fontWeight': 'bold','textAlign': 'center'},
          filter_action="native",
          sort_action="native",
          sort_mode="multi",
          row_selectable="multi",
          selected_rows=[],
          style_data_conditional=([
          	{
          		'if': {'filter_query':'{{{}}} >= {}'.format(col, value), 'column_id':col},
          		'backgroundColor': GOOD_GREEN
          	} for (col, value) in lot_df.drop(columns=['sail_n','pele_n']).quantile(0.9).iteritems()
          ]+
          [
          	{
          		'if': {'filter_query':'{{{}}} <= {}'.format(col, value), 'column_id':col},
          		'backgroundColor': BAD_RED
          	} for (col, value) in lot_df.drop(columns=['sail_n','pele_n']).quantile(0.25).iteritems()
          ])
      )
    ]
  elif selected_item == 'wafer':
    lot_wafer_state = 'wafer'
    return [
      # This part generates the header
      html.H4(children='7HPP Inline Yields - Wafer Level'),
      # This part generates the table
      dt.DataTable(
          id='table-id',
          columns=[{"name":i,"id":i} for i in w_df.columns],
          data=w_df.drop(columns=['sail_n','pele_n']).fillna('-').to_dict('records'),
          fixed_rows={'headers':True},
          fixed_columns={'headers': True, 'data': 3},
          style_cell={'minWidth': '130px', 'width': '150px', 'maxWidth': '150px'},
          style_table={'minHeight': '600px', 'height': '600px', 'maxHeight': '600px',
            		   'minWidth': '100%', 'width': '100%', 'maxWidth': '100%'},
          style_header={'backgroundColor': HEADER_BACKGROUND_COLOR, 'color':HEADER_FONT_COLOR,
                        'fontWeight': 'bold','textAlign': 'center'},
          filter_action="native",
          sort_action="native",
          sort_mode="multi",
          row_selectable="multi",
          selected_rows=[],
          style_data_conditional=([
          	{
          		'if': {'filter_query':'{{{}}} >= {}'.format(col, value), 'column_id':col},
          		'backgroundColor': GOOD_GREEN
          	} for (col, value) in w_df.drop(columns=['sail_n','pele_n']).quantile(0.9).iteritems()
          ]+
          [
          	{
          		'if': {'filter_query':'{{{}}} <= {}'.format(col, value), 'column_id':col},
          		'backgroundColor': BAD_RED
          	} for (col, value) in w_df.drop(columns=['sail_n','pele_n']).quantile(0.25).iteritems()
          ])
      )
    ]


if __name__ == '__main__':
    app.run_server(debug=True)






