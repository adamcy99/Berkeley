from datetime import datetime as dt, date
from io import BytesIO
from typing import List, Sequence, Union, Any
from functools import reduce
import operator
import warnings

import flask
from ibmdata import qdat, DataFrame, Series, pd, LOG, cache

#from app import cache, LOG

ONE_MB = 1024 * 1024
REDIS_CACHE_SIZE_MAX = 512 * ONE_MB


def download_as_csv(df: DataFrame, filename: str, include_index: bool = True):
    """
    Converts a dataframe into a downloadable CSV file and returns a flask send_file
    object which you can return from a flask request handler to initiate a file
    download dialog in the users brower.
    """
    warnings.warn("use dcc.Download instead", DeprecationWarning)
    if not filename.endswith(".csv"):
        filename = filename + ".csv"

    return flask.send_file(
        BytesIO(df.to_csv(index=include_index).encode()),
        mimetype="text/csv",
        download_name=filename,
        as_attachment=True,
        max_age=1,
    )


def download_as_xls(data: DataFrame, filename: str, sheetname: str = "sheet1"):
    warnings.warn("use dcc.Download instead", DeprecationWarning)
    if not filename.endswith(".xlsx"):
        filename = filename + ".xlsx"

    bio = BytesIO()
    writer = pd.ExcelWriter(bio, engine="xlsxwriter")
    data.to_excel(writer, sheet_name=sheetname)
    writer.save()
    bio.seek(0)

    return flask.send_file(
        bio, mimetype="application/vnd.ms-excel", download_name=filename, as_attachment=True, max_age=1
    )


def download_as_zip(data: bytes, filename: str):
    """
    returns a flask send_file object which you can return from a flask
    request handler to initiate a file download dialog in the users brower.
    """
    warnings.warn("use dcc.Download instead", DeprecationWarning)
    if not filename.endswith(".zip"):
        filename = filename + ".zip"

    return flask.send_file(
        BytesIO(data), mimetype="application/zip", download_name=filename, as_attachment=True, max_age=1
    )


def str_to_date_object(date_string: str) -> date:
    """
    Takes dash date input, which has type string and returns date object
    """
    return dt.strptime(date_string[0:10], "%Y-%m-%d").date()


def get_qdat_table_last_altered_timestamp(schema: str, table: str) -> dt:
    """
    get the last alter_time for the specified qdat table
    """
    alter_time = qdat.get_table_info(schema, table)["alter_time"].iloc[0]
    return alter_time.to_pydatetime()


def number_of_days_back(months: int = 3) -> int:
    """
    Function to determine the number of days back a query will go. Includes 'months' full months, plus current
    month to-date.

    Ex: if today is in July, and months=3, function will return the number of days between April 1st and today.

    :param months: number of full months to include
    """
    today = dt.today()
    current_mo = today.month
    start_mo = current_mo - months
    start_year = today.year

    if start_mo < 1:  # start_date is not in the current year
        start_mo = 12 - abs(start_mo)
        start_year -= 1
    start_date = today.replace(year=start_year, day=1, month=start_mo)

    return (today - start_date).days


def clear_cached_funcs(*funcs):
    """
    safely remove cached function(s), useful to call when dependent data is updated
    """
    for f in funcs:
        try:
            cache.delete_memoized(f)
        except:  # occurs if function "f" has not been cached
            pass


def last_n_months(n: int) -> List[str]:
    """
    Return list of last n months (counting current month), formatted as 'YYYY-mm'
    """
    year = dt.today().year
    mon = dt.today().month
    ls = [(year, mon)]
    for i in range(n - 1):
        ls.append(prev_month(*ls[-1]))

    months = [f"{x[0]}-{x[1]:02}" for x in ls]  # convert each (year, month) tuple into 'YYYY-mm' str
    return sorted(months)


def prev_month(year: int, mo: int):
    if mo == 1:
        return year - 1, 12
    else:
        return year, mo - 1


def reformat_dates(dates: Union[List[str], str], current_format: str = "%Y-%m", new_format: str = "%Y %B"):
    """Convert list of dates represented as strs with 'current_format' to new str format"""
    if isinstance(dates, list):
        return [dt.strptime(d, current_format).strftime(new_format) for d in dates]

    elif isinstance(dates, str):
        return dt.strptime(dates, current_format).strftime(new_format)

    else:
        raise TypeError(f'Argument: "dates" must be a str or list of strs. Not {type(dates)}')


def verify_columns_in_dataframe(data: DataFrame, columns: Sequence):
    for col in columns:
        if col not in data.columns:
            raise ValueError(f"column {col} not in data, valid columns: {data.columns}")


def date_from_weekcode(wc: str):
    if not wc.startswith("WC"):
        return None
    return dt.strptime(wc[2:] + "-1", "%y%W-%w").date()


def weekcode_from_date(date):
    return date.strftime("WC%y%W")


def calculate_weekcode_range(wc_min: str, wc_max: str):
    year_min = int(wc_min[2:4])
    week_min = int(wc_min[-2:])
    year_max = int(wc_max[2:4])
    week_max = int(wc_max[-2:])
    return [
        f"WC{year}{week:02}"
        for year in range(year_min, year_max + 1)
        for week in range(week_min if year == year_min else 1, (week_max if year == year_max else 52) + 1)
    ]


def calculate_size_in_bytes(value: Any) -> int:
    f"""
    Estimates the serialized size in bytes of a value.  Anything over {REDIS_CACHE_SIZE_MAX} is too large
    for Redis to cache.  Note this is fairly expensive to compute and should probably only be used during
    debug.
    """
    try:
        import cPickle as pickle
    except ImportError:
        import pickle

    start = dt.now()
    size = len(b"!" + pickle.dumps(value))
    if size > REDIS_CACHE_SIZE_MAX:
        LOG.warning(f"value is too large for Redis cache, max is {REDIS_CACHE_SIZE_MAX / ONE_MB}mb: {size / ONE_MB}")
    LOG.debug(f"calculate_size_in_bytes took {(dt.now() - start).total_seconds()}s for size {size}")
    return size


def apply_filter_list(df: DataFrame, conditions: List[Series]) -> DataFrame:
    """
    Combine list of boolean masks with logical and, perform one step filtering on supplied DataFrame.
    Ex: apply_list_of_filters(df, [df['a'].gt(5), df['b'].lt(2)]) works like: df = df[df['a'].gt(5) & df['b'].lt(2)]
    """
    return df[reduce(operator.and_, conditions)] if conditions else df


def apply_filter_dict(data: DataFrame, filter_dict: dict) -> DataFrame:
    """
    :param data:  input dataframe
    :param filter_dict:  dict of column names to list of desired values, eg. dict(col1=[1,2,3])
                         unknown columns are silently ignored.

    :return:  the original dataframe if unfiltered, otherwise a filtered copy of the original
    """
    if not filter_dict:
        return data

    filters = [
        data[col].isin(values)
        for col, values in filter_dict.items()
        if col in data.columns and values
    ]
    return apply_filter_list(data, filters)


def test_apply_filter_dict():
    data = DataFrame(
        [
            [1, 'foo', 897, -1],
            [2, 'bar', 453, -1],
            [3, 'baz', 284, -1],
            [4, 'foo', 245, -1],
            [4, 'foo', 245,  7],
        ],
        columns=['a', 'b', 'c', 'd']
    )
    assert apply_filter_dict(data, None).equals(data)
    assert apply_filter_dict(data, None) is data  # not a copy, same dataframe if not filtered
    assert apply_filter_dict(data, dict(a=[])).equals(data)
    assert apply_filter_dict(data, dict(a=[])) is data  # not a copy
    assert apply_filter_dict(data, dict(a=[1])).equals(data[data.a.eq(1)])
    assert apply_filter_dict(data, dict(a=[1, 3], foo=['bar'])).equals(data[data.a.isin([1, 3])])
    assert apply_filter_dict(data, dict(b=['foo'], d=[-1])).equals(data[data.b.eq('foo') & data.d.eq(-1)])


def get_unique_items_in_order(full_list: list) -> list:
    """
    returns unique elements in the original insertion order
    """
    # since python 3.7 dict keys are ordered
    return list(dict.fromkeys(full_list))


def test_get_unique_items_in_order():
    assert get_unique_items_in_order([]) == []
    assert get_unique_items_in_order([1, 1, 2, 3, 4, 4, 4, 5]) == [1, 2, 3, 4, 5]
    assert get_unique_items_in_order([5, 1, 3, 1, 2, 1, 5]) == [5, 1, 3, 2]
