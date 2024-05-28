import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import ruptures as rpt
import datetime
import itertools
import ibmdata

from concurrent.futures import ThreadPoolExecutor, as_completed

from time_it import timeit

COLOR_CYCLE = ["#4286f4", "#f44174"]


class ChangePointDetector:
    def __init__(self):
        self.output_df = pd.DataFrame(columns=['parameter', 'lot_id', 'date'])
        self.data = None

    @timeit
    def pull_all_ilt_data(self, days_back=365, fc=('Q5', 'Q6', 'XQ', 'X2')):
        fc = str(fc)
        query = f"""
        SELECT LEFT(lot_Id,5) AS lot_id, family_Code, MIN(Last_test_date) AS date,
        tp.parm_Label as parameter, AVG(weighted_Mean) as mean 
        FROM DMIW.PTileWaferFact ptwf
        JOIN DMIW_SYSTEMS.TestParm tp ON tp.testparmkey = ptwf.testparmkey
        JOIN DMIW_SYSTEMS.TestedWafer tw ON tw.testedWaferKey = ptwf.testedWaferKey
        WHERE Last_test_date >= (current date - {days_back} days)
        AND Tech_id = '7HPP' 
        AND weighted_Mean is not null AND abs(weighted_Mean) < 1e25 
        AND family_Code IN '{fc}'
        GROUP BY LEFT(lot_Id,5), family_Code, tp.parm_Label
        ORDER BY MIN(Last_test_date), LEFT(lot_Id,5)
        """
        df = ibmdata.isdw.query(query)
        df['mean'] = df['mean'].astype(float).round(2)
        self.data = df
        print("Data Saved")

    def pull_ilt_data(self, parameter):
        return self.data[self.data.parameter == parameter].reset_index(drop=True)

    @staticmethod
    def change_point_plot(file_name, df, points, result, parm_name, cp_date, cp_lot):
        color_buffer = itertools.cycle(COLOR_CYCLE)

        fig, ax = plt.subplots(figsize=(10, 6))
        sns.set_theme(style="dark")
        sns.despine()
        x_labels = df[['lot_id', 'date']].astype('str').agg(' '.join, axis=1)

        num_points = len(points)
        plt.plot(range(num_points), points)
        plt.scatter(range(num_points), points)

        start = 0
        for stop, color in zip(result, color_buffer):
            left = max(0, start - 0.5)
            right = stop - 0.5
            plt.hlines(y=np.median(points[start:stop]),
                       xmin=left,
                       xmax=right,
                       color='r',
                       linestyle='--')
            plt.axvspan(left, right, facecolor=color, alpha=0.2, zorder=0)
            start = stop

        plt.title(f'Most recent change point for {parm_name} occurred on {cp_date} with lot {cp_lot}')
        plt.ylabel(parm_name)

        lower_bound = np.percentile(points, 25)
        upper_bound = np.percentile(points, 75)
        y_min = lower_bound - 1.5 * (upper_bound - lower_bound)
        y_max = upper_bound + 1.5 * (upper_bound - lower_bound)
        plt.ylim(y_min, y_max)
        plt.xlim(0, num_points - 1)
        plt.xticks(x_labels.index.values[result[:-1]], x_labels[result[:-1]], rotation=90, fontsize=12)

        plt.savefig(file_name, format='pdf', bbox_inches="tight", pad_inches=0.5)
        plt.close('all')
        return

    @staticmethod
    def change_point_detector(df, rbf_pen=10, time_delay=30, var='mean'):
        # Empty DataFrame
        if df.empty:
            # print('The df is empty')
            return
        if len(df) < 5:
            # print('Not enough data points')
            return

            # Find change point index

        points = np.array(df[var])
        model = "rbf"
        algor = rpt.Pelt(model=model).fit(points)
        result = algor.predict(pen=rbf_pen)

        if len(result) < 2:
            # print('No Change Points At All')
            return
        else:
            cp = result[-2]

        # find change point date
        parm_name = df.parameter[0]
        cp_lot = df.iloc[cp]['lot_id']
        cp_date = df.iloc[cp]['date']
        today = datetime.date.today()
        delta = datetime.timedelta(days=time_delay)
        if today - cp_date < delta:
            # print("Recent Change Point Detected")
            return {'df': df, 'points': points, 'result': result,
                    'parm_name': parm_name, 'cp_date': cp_date, 'cp_lot': cp_lot}
        else:
            # print("No Recent Change Points")
            return

    def param_cpd(self, param, rbf_pen=5, time_delay=30):

        # Pull data specific to param
        df = self.pull_ilt_data(param)

        # Run CPD algorithm
        return self.change_point_detector(df, time_delay=time_delay, rbf_pen=rbf_pen)

    @timeit
    def ilt_cpd_async(self, param_list, rbf_pen=5, time_delay=30):

        # Run analysis asynchronously
        # with ThreadPoolExecutor(max_workers=17) as executor:
        #     return executor.map(self.param_cpd,
        #                         param_list,
        #                         itertools.repeat(rbf_pen),
        #                         itertools.repeat(time_delay),
        #                         timeout=60)

        return [self.param_cpd(param, rbf_pen, time_delay) for param in param_list]
