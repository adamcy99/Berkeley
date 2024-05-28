from typing import Union, List

def get_min_col_width_list_for_style_cell_conditional(
    columns: Union[list, str], char_width: int = 10, padding: int = 20, add_min_width: bool = False
) -> List[dict]:
    """
    Creates a list-of-dicts setting the minimum column widths of a table based on column name length. Hand
    the output of this method to the style_cell_conditional arg of dash_table.DataTable. Note, this sets
    only the minimum width. Max width is defined by column contents.
    N.B. DataTable arg fixed_rows={'headers': True} must also be used
    :param columns: Name of a single column or list of multiple columns for which to set min width
    :param char_width: width added for each char in column name
    :param padding: fixed value added to each column width
    :ret: list-of-dicts to hand to style_cell_conditional arg
    """
    if type(columns) == str:
        columns = [columns]
    ret = list()
    for c in columns:
        if_dict = {"if": {"column_id": c}, "width": f"{len(c) * char_width + padding}px"}
        if add_min_width:
            if_dict['minWidth'] = if_dict['width']
        ret.append(if_dict)
    return ret
