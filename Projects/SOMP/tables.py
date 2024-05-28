"""
Copied from dash-peapps/apps/utils/tables.py
Helper functions for working with dash_table tables
"""
from typing import Dict, List
from itertools import cycle

from dash import html
from dash.dash_table import DataTable
import dash_bootstrap_components as dbc
from pandas import DataFrame

HEADER_BACKGROUND_COLOR = "#343A40"
HEADER_FONT_COLOR = "white"
HEADER_FONT_SIZE = "0.7em"
TABLE_FONT = "Roboto"
TABLE_FONT_SIZE = "0.7em"
TABLE_HEIGHT = "450px"

ROW_SELECTION_SINGLE = "single"
ROW_SELECTION_MULTI = "multi"

DEFAULT_PAGE_SIZE = 10


def make_data_table(
    table_id: str,
    columns: List[Dict] = None,
    data: DataFrame = None,
    in_loading: bool = False,
    height: str = TABLE_HEIGHT,
    row_selection: str = None,
    row_deletable: bool = False,
    color_rows: bool = True,
    filter_action: str = "native",
    filter_query: str = "",
    sort_action: str = "native",
    sort_mode: str = 'multi',
    sort_by: List[Dict] = [],
    page_action: str = "native",
    page_current: int = 0,
    page_size: int = DEFAULT_PAGE_SIZE,
    editable: bool = False,
    className: str = None,
    style_data_conditional: list = None,
    column_selection: str = None,
    fixed_header: bool = False,
    table_font: str = TABLE_FONT,
    table_font_size: str = TABLE_FONT_SIZE,
    header_font_size: str = HEADER_FONT_SIZE,
    fill_width: bool = True,
    export_format: str = None,
    merge_duplicate_headers: bool = False,
    css: List[dict] = None,
) -> html.Div:
    """
    returns a Dash DataTable optionally wrapped in a loading component.

    2020-03-09 fixed_header is still broken in dash_table, column widths are set based on data only
    """
    _style_data_conditional = []
    if color_rows:
        _style_data_conditional.append({"if": {"row_index": "odd"}, "backgroundColor": "rgb(248, 248, 248)"})
    if style_data_conditional:
        _style_data_conditional.extend(style_data_conditional)

    table = DataTable(
        id=table_id,
        columns=columns or [],
        data=[] if data is None else data.to_dict("records"),
        fixed_rows={"headers": fixed_header, "data": 0},
        editable=editable,
        filter_action=filter_action,
        filter_query="",
        sort_action=sort_action,
        sort_mode="multi",
        sort_by=[],
        page_current=0,
        page_size=page_size,
        page_action=page_action,
        row_selectable=row_selection,
        row_deletable=row_deletable,
        column_selectable=column_selection,
        fill_width=fill_width,
        export_format=export_format,
        merge_duplicate_headers=merge_duplicate_headers,
        style_table={"maxHeight": height, "overflowX": "scroll", "overflowY": "scroll"},
        style_header={
            "backgroundColor": HEADER_BACKGROUND_COLOR,
            "color": HEADER_FONT_COLOR,
            # 'fontWeight': 'bold',
            "fontFamily": table_font,
            "fontSize": header_font_size,
        },
        style_cell={
            "fontFamily": table_font,
            "fontSize": table_font_size,
            "textAlign": "left",
        },
        style_data_conditional=_style_data_conditional,
        css=css or [],
    )
    return html.Div(
        dbc.Spinner(table) if in_loading else table,
        className=className,
        style=dict(height=height),
    )


def make_column(
    name: str,
    id: str = None,
    clearable: bool = False,
    deletable: bool = False,
    editable: bool = False,
    hideable: bool = False,
    renamable: bool = False,
    selectable: bool = False,
    format: str = None,
    presentation: str = "input",
    on_change: str = None,
    sort_as_null: bool = False,
    validation: str = None,
    type: str = None,
):
    """
    returns a DataTable column definition.  See https://dash.plot.ly/datatable/reference for help on what each
    parameter means.
    """
    col = dict(
        name=name,
        id=id or name,
        clearable=clearable,
        deletable=deletable,
        editable=editable,
        hideable=hideable,
        renamable=renamable,
        selectable=selectable,
        presentation=presentation,
    )
    if format:
        col["format"] = format
    if on_change:
        col["on_change"] = on_change
    if sort_as_null:
        col["sort_as_null"] = sort_as_null
    if validation:
        col["validation"] = validation
    if type:
        col["type"] = type
    return col


def make_columns(
    data: DataFrame,
    clearable: bool = False,
    deletable: bool = False,
    editable: bool = False,
    hideable: bool = False,
    renamable: bool = False,
    selectable: bool = False,
    format: str = None,
    presentation: str = "input",
    on_change: str = None,
    sort_as_null: bool = False,
    validation: str = None,
    type: str = None,
    ignore: List[str] = None
):
    """
    returns a DataTable column list for all columns in a DataFrame.  See https://dash.plot.ly/datatable/reference
    for help on what each parameter means.
    """
    ignore = ignore or []
    return [
        make_column(
            name=col,
            id=col,
            clearable=clearable,
            deletable=deletable,
            editable=editable,
            hideable=hideable,
            renamable=renamable,
            selectable=selectable,
            format=format,
            presentation=presentation,
            on_change=on_change,
            sort_as_null=sort_as_null,
            validation=validation,
            type=type,
        )
        for col in data.columns if col not in ignore
    ]


FILTER_OPERATORS = [
    ["ge ", ">="],
    ["le ", "<="],
    ["lt ", "<"],
    ["gt ", ">"],
    ["ne ", "!="],
    ["eq ", "="],
    ["contains "],
    ["datestartswith "],
]


def split_filter_part(filter_part):
    """
    used for server side dash table filtering.  This parses the filter string sent from the browser.
    """
    for operator_type in FILTER_OPERATORS:
        for operator in operator_type:
            if operator in filter_part:
                name_part, value_part = filter_part.split(operator, 1)
                name = name_part[name_part.find("{") + 1 : name_part.rfind("}")]

                value_part = value_part.strip()
                v0 = value_part[0]
                if v0 == value_part[-1] and v0 in ("'", '"', "`"):
                    value = value_part[1:-1].replace("\\" + v0, v0)
                else:
                    try:
                        if int(value_part) == float(value_part):
                            value = int(value_part)
                        else:
                            value = float(value_part)
                    except ValueError:
                        value = value_part

                # word operators need spaces after them in the filter string,
                # but we don't want these later
                return name, operator_type[0].strip(), value

    return [None] * 3


def filter_and_sort_data(data: DataFrame, filter_by: str, sort_by: list) -> DataFrame:
    """
    used for server side dash table filtering and sorting operations.
    """
    filtering_expressions = filter_by.split(" && ")
    for filter_part in filtering_expressions:
        col_name, operator, filter_value = split_filter_part(filter_part)

        if operator in ("eq", "ne", "lt", "le", "gt", "ge"):
            # these operators match pandas series operator method names
            data = data.loc[getattr(data[col_name], operator)(filter_value)]
        elif operator == "contains":
            data = data.loc[data[col_name].astype(str).str.contains(str(filter_value))]
        elif operator == "datestartswith":
            # this is a simplification of the front-end filtering logic,
            # only works with complete fields in standard format
            data = data.loc[data[col_name].astype(str).str.startswith(str(filter_value))]

    if len(sort_by):
        data = data.sort_values(
            [col["column_id"] for col in sort_by], ascending=[col["direction"] == "asc" for col in sort_by]
        )
    return data


def sparsify_column(
    df: DataFrame,
    col_to_sparsify: str,
    bold: bool = True,
    lines: bool = True,
    backgrnd_color: str = "white",
    verify_col_is_monotonic: bool = True,
    colors: list = None,
) -> List:
    """
    Hide repeated values in data table column (like multiindex formatting of pandas dfs), optionally add horizontal
    separating lines. Should only be used if data order is FIXED (ie user isn't able to sort data table columns), and
    SORTED by the col_to_sparsify column. Returns style_data_conditional list
    """
    if verify_col_is_monotonic and (not df[col_to_sparsify].is_monotonic):  # data table was not sorted
        # sparse formatting would make data_table confusing to read -> don't apply it
        return []

    sdc = []
    previous_value = None
    if colors:
        colors = cycle(colors)
        color = next(colors)
    else:
        color = backgrnd_color

    for idx in df.index:  # iterate through table's rows
        current_value = df.at[idx, col_to_sparsify]

        if current_value == previous_value:  # on a repeat cell -> should be hidden
            sdc.extend(
                [
                    {
                        "if": {
                            "column_id": col_to_sparsify,
                            "row_index": idx,
                        },
                        "color": color,  # can still be seen when cell is selected. helps check for sorting errors
                    },
                    {"if": {"row_index": idx}, "backgroundColor": color},
                ]
            )

        else:  # first row with a new value in col_to_sparsify column -> don't hide
            color = next(colors) if colors else backgrnd_color
            previous_value = current_value

            sdc.append(
                (
                    {
                        "if": {"row_index": idx},
                        "border-top": "1.5px solid black" if lines else None,
                        "backgroundColor": color,
                    }
                )
            )

            sdc.append(
                (
                    {
                        "if": {
                            "column_id": col_to_sparsify,
                            "row_index": idx,
                        },
                        "fontWeight": "bold" if bold else None,
                    }
                )
            )

    return sdc
