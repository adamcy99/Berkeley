import datetime
import pandas as pd
from pathlib import Path
from matplotlib.backends.backend_pdf import PdfPages

from changepointdetector import ChangePointDetector
from time_it import timeit

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
pd.set_option('display.max_columns', None)

levels_dict = {"M1": "M1", "M5": "M5", "MF": "LT"}

"""
DAYS_BACK: Number of days to first data point
TIME_DELAY: Number of days to first change point
"""
DAYS_BACK = 365
TIME_DELAY = 200


@timeit
def run_cpd_async(levels, family_codes):
    today = datetime.datetime.now().strftime('%y%m%d')

    for family_code in family_codes:

        print(f"============================================\n{family_code}\n")

        # Create dir to save results; eg. --> ./CPDResults/220719/Q6
        dir_name = f"./CPDResults/{today}/{family_code}"
        Path(dir_name).mkdir(parents=True, exist_ok=True)

        # initialize cpd object
        model = ChangePointDetector()

        # Pull all data
        model.pull_all_ilt_data(DAYS_BACK, family_code)

        for level in levels:
            print(f"\n-------------------------------------------------\n\n{level}\n")

            # Read list of parameters from csv
            params = pd.read_csv(f'./Parms/{level}parms.csv', header=None, names=["Parameter", "Owner"])
            params["Parameter"] = params["Parameter"].astype('str') + f"_{levels_dict[level]}"

            # open pdf to save plots
            with PdfPages(f'{dir_name}/{family_code}_{level}_Graphs.pdf') as pdfFile:

                # run analysis on all parameters
                results = model.ilt_cpd_async(param_list=params["Parameter"],
                                              rbf_pen=5,
                                              time_delay=TIME_DELAY)

                results = list(filter(None, results))
                results = sorted(results, key=lambda x: x['cp_date'], reverse=True)

                for result in results:
                    # Plot result
                    model.change_point_plot(pdfFile, result['df'], result['points'], result['result'],
                                            result['parm_name'], result['cp_date'], result['cp_lot'])

                    # Save result to csv
                    model.output_df = model.output_df.append(pd.DataFrame([[result['parm_name'],
                                                                            result['cp_lot'],
                                                                            result['cp_date']]],
                                                                          columns=['parameter', 'lot_id', 'date']))

                # save results to csv
                model.output_df.merge(
                    params,
                    left_on='parameter',
                    right_on='Parameter'
                ).drop(
                    columns=['Parameter']
                ).rename(
                    columns={1: 'category'}
                ).to_csv(
                    f"{dir_name}/{family_code}_{level}_Data.csv",
                    index=False
                )


if __name__ == "__main__":
    run_cpd_async(["M1", "M5", "MF"], ["Q6", "X2"])
