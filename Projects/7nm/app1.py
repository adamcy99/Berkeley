# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import ibmdata
import pandas as pd
import numpy as np
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
pd.set_option('display.max_columns', None)
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table as dt
import plotly.graph_objects as go
import plotly.express as px
from dash.dependencies import Input, Output


######################## SQL Yield Pulls ####################################

daysback = 365
Query = """
SELECT lot_id, wafer_id, family_code, MIN(tw.Last_test_date) AS date, 
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
  AND (UCASE(SUBSTR(tp.parm_Label,20,13)) = '_PERFECTYIELD')
GROUP BY lot_id, wafer_id, family_code
ORDER BY date desc, lot_id, wafer_id
WITH UR;
""".format(daysback)
w_df = ibmdata.isdw.query(Query)
w_df['sail1_0p50to1p05'] = w_df['sail1_0p50to1p05'].astype(float).round(2)
w_df['sail1_0p65to1p05'] = w_df['sail1_0p65to1p05'].astype(float).round(2)
w_df['sail2_0p50to1p05'] = w_df['sail2_0p50to1p05'].astype(float).round(2)
w_df['sail2_0p65to1p05'] = w_df['sail2_0p65to1p05'].astype(float).round(2)
w_df['sail3_0p50to1p05'] = w_df['sail3_0p50to1p05'].astype(float).round(2)
w_df['sail3_0p65to1p05'] = w_df['sail3_0p65to1p05'].astype(float).round(2)
lot_df = w_df.groupby(['lot_id','family_code']).agg({'date':'min','sail1_0p50to1p05':'mean',
                                                     'sail1_0p65to1p05':'mean','sail2_0p50to1p05':'mean',
                                                     'sail2_0p65to1p05':'mean','sail3_0p50to1p05':'mean',
                                                     'sail3_0p65to1p05':'mean'}) \
                                                     .round(2).sort_values('date',ascending=False).reset_index()

Block_df = pd.read_csv('/Users/acyang@us.ibm.com/Downloads/SailBlock7hp.csv')
ScanOut_df = pd.read_csv('/Users/acyang@us.ibm.com/Downloads/SailScanOut7hp.csv')

global lot_wafer_state
lot_wafer_state = 'lot'

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
             children=[
             # This part generates the header
      html.H4(children='7HPP Sail Yield - Lot Level'),
      # This part generates the table
      dt.DataTable(
          id='lot-table-id',
          columns=[{"name":i,"id":i} for i in lot_df.columns],
          data=lot_df.to_dict('records'),
          fixed_rows={'headers':True},
          style_cell={'minWidth': '130px', 'width': '160px', 'maxWidth': '160px'},
          style_table={'height':600},
          style_header={'backgroundColor': 'rgb(230, 230, 230)',
                        'fontWeight': 'bold','textAlign': 'center'},
          filter_action="native",
          sort_action="native",
          sort_mode="multi",
          row_selectable="multi",
          selected_rows=[]
      )]
    ),
    html.Br(),

    # This part generates the interactive components for the graph
    html.Div(children=[
        html.Label('Blocks/ScanOuts Pareto'),
        dcc.RadioItems(
            id='block-so-toggle',
            options=[
                {'label': 'Blocks', 'value': 'blocks'},
                {'label': 'ScanOuts', 'value': 'scanouts'}
            ],
            value='blocks'
        ),
        html.Br(),
        html.Label('Sails Macros to Include'),
        dcc.Checklist(
            id='sail-checklist',
            options=[
                {'label': 'Sail 1', 'value': 'SSL1'},
                {'label': 'Sail 2', 'value': 'SSL2'},
                {'label': 'Sail 3', 'value': 'SSL3'}
            ],
            value=['SSL1', 'SSL2', 'SSL3']
        ),
        html.Label('Plot Yield or Yield Loss'),
        dcc.RadioItems(
            id='yield-yldLoss-toggle',
            options=[
                {'label': 'Yield Loss', 'value': 'yld_loss'},
                {'label': 'Yield', 'value': 'yield'}
            ],
            value='yld_loss'
        ),
        html.Br(),
        html.Label('Number of Paretos:'),
        dcc.Slider(
            id='num-paretos',
            min=10,
            max=100,
            marks={i: '{}'.format(i) if i == 1 else str(i) for i in range(10, 110, 10)},
            value=20,
        )
      ], 
      style={'columnCount': 4, 'margin-left':'auto','margin-right':'auto','width':'60%'}
    ),

    # This Div holds the graph
    html.Div(id='pareto-interactivity-container')
  ]
)

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
      html.H4(children='7HPP Sail Yield - Lot Level'),
      # This part generates the table
      dt.DataTable(
          id='lot-table-id',
          columns=[{"name":i,"id":i} for i in lot_df.columns],
          data=lot_df.to_dict('records'),
          fixed_rows={'headers':True},
          style_cell={'minWidth': '130px', 'width': '160px', 'maxWidth': '160px'},
          style_table={'height':600},
          style_header={'backgroundColor': 'rgb(230, 230, 230)',
                        'fontWeight': 'bold','textAlign': 'center'},
          filter_action="native",
          sort_action="native",
          sort_mode="multi",
          row_selectable="multi",
          selected_rows=[]
      )
    ]
  elif selected_item == 'wafer':
    lot_wafer_state = 'wafer'
    return [
      # This part generates the header
      html.H4(children='7HPP Sail Yield - Wafer Level'),
      # This part generates the table
      dt.DataTable(
          id='wafer-table-id',
          columns=[{"name":i,"id":i} for i in w_df.columns],
          data=w_df.to_dict('records'),
          fixed_rows={'headers':True},
          style_cell={'minWidth': '130px', 'width': '150px', 'maxWidth': '150px'},
          style_table={'height':600},
          style_header={'backgroundColor': 'rgb(230, 230, 230)',
                        'fontWeight': 'bold','textAlign': 'center'},
          filter_action="native",
          sort_action="native",
          sort_mode="multi",
          row_selectable="multi",
          selected_rows=[]
      )
    ]

######################### This Part of the code deals with interactive graphs ######################
# This callback works with the pareto graph
if lot_wafer_state == 'lot':
  @app.callback(
    Output('pareto-interactivity-container','children'),
    [Input('lot-wafer-toggle','value'),
    Input('block-so-toggle','value'),
    Input('yield-yldLoss-toggle','value'),
    Input('num-paretos','value'),
    Input('sail-checklist','value'),
    Input('lot-table-id','derived_virtual_data'),
    Input('lot-table-id','derived_virtual_selected_rows')]
  )
  def plot_pareto(lot_wafer,block_so,yld_loss,n,sail,data_rows,data_indices):
    # This logic deals with toggling between yield and yld_loss
    if yld_loss == 'yld_loss':
      yparm = 'yld_loss'
      asc = False
    else:
      yparm = 'yield'
      asc = True

    # Chose between Block or ScanOut pareto graph
    if block_so == 'blocks':
      df = Block_df
    elif block_so == 'scanouts':
      df = ScanOut_df

    df['yield'] = df['yield'].astype(float)
    df['yld_loss'] = df['yld_loss'].astype(float)

    # Choose between lot level or wafer level pareto
    if lot_wafer == 'lot':
      if data_indices is None:
        lots = []
      else:
        tempdf = lot_df if data_rows is None else pd.DataFrame(data_rows) 
        lots = [tempdf['lot_id'][i] for i in data_indices]
      if not lots:
        inclusiontxt = 'all lots'
        pass
      else:
        df = df[df['lot_id'].isin(lots)]
        if len(lots) > 3:
          inclusiontxt = 'lots: '+', '.join(lots[0:3])+'...'
        else:
          inclusiontxt = 'lots: '+', '.join(lots)
      num = '{} distinct lots'.format(df['lot_id'].nunique())
    elif lot_wafer == 'wafer':
      if data_indices is None:
        wafers = []
      else:
        tempdf = w_df if data_rows is None else pd.DataFrame(data_rows)
        wafers = [tempdf['wafer_id'][i] for i in data_indices]
      if not wafers:
        inclusiontxt = 'all lots'
        pass
      else:
        df = df[df['wafer_id'].isin(wafers)]
        if len(wafers) > 3:
          inclusiontxt = 'wafers: '+', '.join(wafers[0:3])+'...'
        else:
          inclusiontxt = 'wafers: '+', '.join(wafers)
      num = '{} distinct wafers'.format(df['wafer_id'].nunique())

    # This part of the code deals with which Sail to include in the Pareto
    df = df[df['step'].isin(sail)]
    sailtxt = ' with Calcdefs '+', '.join(sail)
      
    # This part of the code deals with plotting the pareto     
    df_agg = df.groupby(['label','step']).mean().sort_values(yparm,ascending=asc).reset_index()[0:n]
      
    fig = px.bar(df_agg, x='label', y=yparm,
            hover_data=['label', yparm],
            color = 'step',
            labels={'label':'Label',yparm:yparm+' (%)'})
    fig.update_layout(title_text='Sail '+yparm+' pareto for '+inclusiontxt+sailtxt+' ('+num+')')
    fig.update_layout(xaxis_categoryorder = 'total descending')
    return[dcc.Graph(id='pareto-graph',figure=fig)]

if lot_wafer_state == 'wafer':
  @app.callback(
      Output('pareto-interactivity-container','children'),
      [Input('lot-wafer-toggle','value'),
      Input('block-so-toggle','value'),
      Input('yield-yldLoss-toggle','value'),
      Input('num-paretos','value'),
      Input('sail-checklist','value'),
      Input('wafer-table-id','derived_virtual_data'),
      Input('wafer-table-id','derived_virtual_selected_rows')]
  )
  def plot_pareto(lot_wafer,block_so,yld_loss,n,sail,data_rows,data_indices):
    # This logic deals with toggling between yield and yld_loss
    if yld_loss == 'yld_loss':
      yparm = 'yld_loss'
      asc = False
    else:
      yparm = 'yield'
      asc = True

    # Chose between Block or ScanOut pareto graph
    if block_so == 'blocks':
      df = Block_df
    elif block_so == 'scanouts':
      df = ScanOut_df

    df['yield'] = df['yield'].astype(float)
    df['yld_loss'] = df['yld_loss'].astype(float)

    # Choose between lot level or wafer level pareto
    if lot_wafer == 'lot':
      if data_indices is None:
        lots = []
      else:
        tempdf = lot_df if data_rows is None else pd.DataFrame(data_rows) 
        lots = [tempdf['lot_id'][i] for i in data_indices]
      if not lots:
        inclusiontxt = 'all lots'
        pass
      else:
        df = df[df['lot_id'].isin(lots)]
        if len(lots) > 3:
          inclusiontxt = 'lots: '+', '.join(lots[0:3])+'...'
        else:
          inclusiontxt = 'lots: '+', '.join(lots)
      num = '{} distinct lots'.format(df['lot_id'].nunique())
    elif lot_wafer == 'wafer':
      if data_indices is None:
        wafers = []
      else:
        tempdf = w_df if data_rows is None else pd.DataFrame(data_rows)
        wafers = [tempdf['wafer_id'][i] for i in data_indices]
      if not wafers:
        inclusiontxt = 'all lots'
        pass
      else:
        df = df[df['wafer_id'].isin(wafers)]
        if len(wafers) > 3:
          inclusiontxt = 'wafers: '+', '.join(wafers[0:3])+'...'
        else:
          inclusiontxt = 'wafers: '+', '.join(wafers)
      num = '{} distinct wafers'.format(df['wafer_id'].nunique())

    # This part of the code deals with which Sail to include in the Pareto
    df = df[df['step'].isin(sail)]
    sailtxt = ' with Calcdefs '+', '.join(sail)
      
    # This part of the code deals with plotting the pareto     
    df_agg = df.groupby(['label','step']).mean().sort_values(yparm,ascending=asc).reset_index()[0:n]
      
    fig = px.bar(df_agg, x='label', y=yparm,
            hover_data=['label', yparm],
            color = 'step',
            labels={'label':'Label',yparm:yparm+' (%)'})
    fig.update_layout(title_text='Sail '+yparm+' pareto for '+inclusiontxt+sailtxt+' ('+num+')')
    fig.update_layout(xaxis_categoryorder = 'total descending')
    return[dcc.Graph(id='pareto-graph',figure=fig)]

if __name__ == '__main__':
    app.run_server(debug=True)