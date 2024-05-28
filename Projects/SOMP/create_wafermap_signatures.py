import ibmdata
import numpy as np
import pandas as pd
import pteClustering as ptec


def get_geo(schema:str)->pd.DataFrame:
    steppndf = ptec.pull_product_step_pn([schema])
    try:
        schema_geodf = ibmdata.isdw.geography.get_geography(stepec=steppndf['rlse_step_ec'].iloc[0])
    except:
        print(f"schema={schema} did not find a geography")
    devloclist = ibmdata.plot.wafermap._common.determine_product_chip_id(schema_geodf)
    schema_geodf = schema_geodf[schema_geodf.devloc.isin(devloclist) & schema_geodf.unitcell_x.ne(0)]
    schema_geodf['schema'] = schema
    return schema_geodf

def create_wafermap(geodata:pd.DataFrame, signaturelist:dict, missingrange:list[int]=[0,1], outlierrange:list[int]=[0,1], outliervals:list[int]=[0,1])->pd.DataFrame:
    wafer_cnt = 1
    wafergeos = []
    for signature in signaturelist:
        for wafer in range(1,signaturelist[signature]['wafer_count']+1):
            wafergeo = geodata.copy()
            for position in signaturelist[signature]['signature']:
                patt = position[0]
                rang = position[1]
                evalresults = wafergeo.eval(patt)
                wafergeo.loc[evalresults, 'value'] = np.random.randint(rang[0],rang[1],sum(evalresults))
            wafergeo['wafer_id'] = f'wafer-{wafer_cnt}'
            wafergeo['value'] = wafergeo['value'].fillna(0)
            wafergeo['signature'] = signature
            wafersize = len(wafergeo)
            outliernum = np.random.randint(outlierrange[0],outlierrange[1])
            missingnum = np.random.randint(missingrange[0],missingrange[1])
            if outliernum > 0:
                outlier_idx = np.random.choice(wafergeo.index, replace=False, size=outliernum)
                wafergeo.loc[outlier_idx,'value'] = np.random.randint(outliervals[0],outliervals[1],outliernum)
            if missingnum > 0:
                missing_idx = np.random.choice(wafergeo.index, replace=False, size=missingnum)
                wafergeo.drop(index=missing_idx,inplace=True)
            wafergeos.append(wafergeo[['schema','wafer_id','geographykey','normalized_testx','normalized_testy','unitcell_x','unitcell_y','value','signature']])
            wafer_cnt = wafer_cnt + 1
    return pd.concat(wafergeos)
        