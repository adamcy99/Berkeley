import plotly.graph_objects as go

def empty_figure(text):
  """This function returns an empty figure with your choice of text"""
  text = str(text)
  fig = go.Figure()
  fig.update_layout(
    annotations=[
      dict(
        text=text,
        xref="paper",
        yref="paper",
        showarrow=False,
        font={"size": 28}
        )
      ])
  return fig