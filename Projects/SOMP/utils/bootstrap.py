from typing import List

from dash import html
import dash_bootstrap_components as dbc

#from .. import LOG

COL_WIDTH_AUTO = "sm-auto"
COL_WIDTH_EXPAND = 0


def row(
    *args,
    widths: List[int] = None,
    center_vertically: bool = False,
    css_classes: str = "",
    rowid: str = "",
    hidden: bool = False,
    row_style: dict = None,
    col_style: dict = None,
    no_margin: bool = False,
    no_column_gutters: bool = False,
    align_bottom: bool = False,
) -> html.Div:
    """
    helper function to generate a bootstrap row.
    """
    if widths is None:
        widths = [0] * len(args)
    elif len(widths) != len(args):
        LOG.warning(f"got {len(args)} column(s) but {len(widths)} width(s): {widths}")
        while len(widths) < len(args):
            widths.append(0)

    columns = []
    for coldata, colwidth in zip(args, widths):
        columns.append(
            html.Div(children=[coldata], className=f"col{'' if colwidth == 0 else '-%s' % colwidth}", style=col_style)
        )

    return html.Div(
        columns,
        className=(
            "row "
            + ("" if no_margin else "my-3 ")
            + ("align-items-center " if center_vertically else "")
            + ("align-items-end " if align_bottom else "")
            + ("g-0 " if no_column_gutters else "")
            + css_classes
        ),
        style=row_style,
        id=rowid,  # id can't be None
        hidden=hidden,
    )


def card(body, title: str = None, image: str = None, image_height: str = None):
    """
    helper function to generate a bootstrap card

    https://getbootstrap.com/docs/4.3/components/card/
    """
    content = []
    if image:
        style = dict()
        if image_height:
            style["height"] = image_height
        content.append(html.Img(src=image, className="card-img-top", style=style))

    if title:
        content.append(html.Div(title, className="card-header"))

    content.append(html.Div(body, className="card-body"))

    return html.Div(content, className="card")


def card_deck(*args):
    """
    helper function to generate a bootstrap card deck layout

    arguments should be tuples of the form (title, content).  ex:

    (None, 'a message') -- card with no title that displays a message
    ('Hello', html.Div('a message')) -- card titled Hello containing a div structure

    https://getbootstrap.com/docs/4.3/components/card/#card-decks
    """
    cards = []
    for (card_title, card_data) in args:
        cards.append(card(card_data, card_title))
    return html.Div(cards, className="card-deck")


def linked_card(href: str, image: str, text: str, err: bool = False):
    return html.A(
        href=href,
        className="card",
        # style={'min-width': '250px', 'max-width': '300px', 'max-height': '300px'},
        style={"min-width": "200px", "max-width": "200px", "max-height": "250px", "padding-right": "0"},
        children=[
            html.Img(src=image, className="card-img-top",
                     style={"height": "24px", "width": "24px"} if err else {"height": "180px"}),
            html.Div([html.Div(text, style={"text-align": "center"})], className="card-body"),
        ],
    )


def labelled_form_group(
    label_text: str,
    component: object,
    component_in_spinner: bool = True,
    inline: bool = True,
    label_class_name: str = "me-2",
    form_group_class_name: str = "me-4",
    component_col_width: int = 0,
) -> dbc.Row:
    """
    helper function for labeling components within a dbc.Form.
    Returns a dbc.Row containing a dbc.Label and the supplied component optionally wrapped in a dbc.Spinner
    """
    return dbc.Row(
        [
            dbc.Label(label_text, className=label_class_name, width="auto" if inline else None),
            dbc.Col(
                dbc.Spinner(component, size="sm") if component_in_spinner else component,
                width=component_col_width if component_col_width > 0 else None,
            ),
        ],
        className=form_group_class_name,
    )


def dbc_bool_switch(
    component_id: str,
    label_text: str,
    className: str = "me-5",
    is_on: bool = False,
    persistence: bool = True,
    persistence_type: str = "local",
) -> dbc.Checklist:
    """
    Use the "switch" style of dbc.Checklist to act as a boolean switch (looks nicer than a daq.BooleanSwitch)
    'value' property will be [True] if switch is on, else []
    """
    return dbc.Checklist(
        options=[{"label": label_text, "value": True}],
        value=[True] if is_on else [],
        id=component_id,
        switch=True,
        className=className,
        persistence=persistence,
        persistence_type=persistence_type,
    )
