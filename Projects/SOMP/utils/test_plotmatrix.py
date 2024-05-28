import unittest

from dash import html
from pandas import DataFrame

from .plots import table_header, table_body, generate_plot_matrix, plot_matrix_table, _index_depth


class TestPlotMatrix(unittest.TestCase):
    @staticmethod
    def _make_plots(columns: list) -> dict:
        return dict(
            foo={col: pos for pos, col in enumerate(columns)},
            bar={col: pos for pos, col in enumerate(columns[:-1])},
            baz={col: pos for pos, col in enumerate(columns[1:])},
        )

    def test_index_depth(self):
        self.assertEqual(1, _index_depth(None))
        self.assertEqual(1, _index_depth(""))
        self.assertEqual(1, _index_depth("foo"))
        self.assertEqual(2, _index_depth(("foo", "bar")))
        self.assertEqual(3, _index_depth(["foo", "bar", "baz"]))
        self.assertEqual(1, _index_depth(1))

    def test_table_header(self):
        columns = ["a", "b", "c", "d"]
        plots = self._make_plots(columns)
        thead = table_header(plots)
        self.assertEqual(1, len(thead.children))
        tr = thead.children[0]
        self.assertEqual(len(columns) + 1, len(tr.children))
        corner = tr.children[0]
        self.assertEqual(1, corner.colSpan)
        self.assertEqual(1, corner.rowSpan)
        for colname, th in zip(columns, tr.children[1:]):
            self.assertEqual([colname], th.children)

    def test_table_header_two_levels(self):
        columns = [("a", "1"), ("a", "2"), ("b", "3"), ("c", "4"), ("c", "5")]
        plots = self._make_plots(columns)
        thead = table_header(plots)
        self.assertEqual(2, len(thead.children))
        tr = thead.children[0]
        self.assertEqual(3 + 1, len(tr.children))
        corner = tr.children[0]
        self.assertEqual(1, corner.colSpan)
        self.assertEqual(2, corner.rowSpan)
        for (colname, span), th in zip((("a", 2), ("b", 1), ("c", 2)), tr.children[1:]):
            self.assertEqual([colname], th.children)
            self.assertEqual(span, th.colSpan)

        tr = thead.children[1]
        self.assertEqual(len(columns), len(tr.children))
        for colname, th in zip(columns, tr.children):
            self.assertEqual([colname[1]], th.children)

    def test_table_body(self):
        plots = self._make_plots(["a", "b"])
        tbody = table_body(plots)
        self.assertEqual(3, len(tbody.children))
        for row in tbody.children:
            self.assertEqual(1 + 2, len(row.children))

    def test_table_body_two_levels(self):
        plots = {
            (0, 1): dict(a=1, b=2),
            (0, 2): dict(a=3),
            (1, 1): dict(a=4, b=5),
            (2, 1): dict(a=6, b=7),
        }
        tbody = table_body(plots)
        self.assertEqual(4, len(tbody.children))

        tr = tbody.children[0]
        self.assertEqual(4, len(tr.children))
        self.assertEqual(0, tr.children[0].children)
        self.assertEqual(1, tr.children[1].children)

        tr = tbody.children[1]
        self.assertEqual(3, len(tr.children))
        self.assertEqual(2, tr.children[0].children)
        self.assertEqual("", tr.children[-1].children)

        tr = tbody.children[2]
        self.assertEqual(4, len(tr.children))
        self.assertEqual(1, tr.children[0].children)
        self.assertEqual(1, tr.children[1].children)

        tr = tbody.children[3]
        self.assertEqual(3, len(tr.children))
        self.assertEqual(2, tr.children[0].children)

    @staticmethod
    def plotfunc(data):
        return data.shape

    def test_generate_plot_matrix(self):
        df = DataFrame([[1, 2, 3, 4], [5, 2, 3, 4], [5, 6, 7, 8]], columns=["a", "b", "c", "d"])

        for workers in (1, 2):
            plots = generate_plot_matrix(df, col_vars=["b"], row_vars=["a"], plot_func=self.plotfunc, workers=workers)
            self.assertIn((1,), plots)
            self.assertIn((5,), plots)

            row1 = plots[(1,)]
            self.assertIn((2,), row1)
            self.assertEqual((1, 4), row1[(2,)])

            row2 = plots[(5,)]
            self.assertIn((2,), row2)
            self.assertIn((6,), row2)
            self.assertEqual((1, 4), row1[(2,)])
            self.assertEqual((1, 4), row2[(6,)])

    def test_plot_matrix_table(self):
        df = DataFrame([[1, 2, 3, 4], [5, 2, 3, 4], [5, 6, 7, 8]], columns=["a", "b", "c", "d"])

        for workers in (1, 2):
            table = plot_matrix_table(df, col_vars=["b"], row_vars=["a"], plot_func=self.plotfunc, workers=workers)
            self.assertIsInstance(table, html.Div)
            self.assertIsInstance(table.children, html.Table)


if __name__ == "__main__":
    unittest.main()
