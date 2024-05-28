import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from scipy.spatial import distance
from scipy import interpolate

from os.path import exists
import pickle
import ibmdata

from ibmdata.plot.wafermap import wafermap, wafermap_gallery, WafermapConfig
import matplotlib as mpl
import itertools

from sklearn.linear_model import OrthogonalMatchingPursuit
from sklearn.linear_model import OrthogonalMatchingPursuitCV
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import squareform

pd.options.mode.chained_assignment = None

def get_product_step_pn(products: list[str])->pd.DataFrame:
    """
    stores a pickle file of a dataframe of schemas and rlse part number and ec values given a list of product schemas to pull from 
    and returns the resulting dataframe
    """
    pickle_file = "product_step_pn.pkl"
    stored_product_step_df = pd.DataFrame()
    stored_products = []
    if exists(pickle_file):
        stored_product_step_df = pd.read_pickle(pickle_file)
        stored_products.extend(stored_product_step_df['pe_product_schema'].unique())
    missing_products = [product for product in products if product.lower() not in [var.lower() for var in stored_products]]
    
    if len(missing_products) > 0:
        product_step_df = pull_product_step_pn(missing_products)

        if len(stored_product_step_df) > 0:
            product_step_df = pd.concat([product_step_df, stored_product_step_df]).drop_duplicates().reset_index(drop=True)
        
        product_step_df.to_pickle(pickle_file)

        return product_step_df
    else:
        return stored_product_step_df[stored_product_step_df['pe_product_schema'].isin(products)]

def pull_product_step_pn(products: list[str])->pd.DataFrame:
    """
    returns a dataframe of schemas and rlse part number and ec values given a list of product schemas to pull from 
    """
    product_step_df = ibmdata.isdw.query(f"""
    select distinct pe_product_schema, rlse_step_pn, rlse_step_ec
    from
    (
        select testedwaferpass.pe_product_schema, geography.rlse_step_pn, geography.rlse_step_ec, geography.geography_updt_ts,
        ROW_NUMBER() OVER(PARTITION BY testedwaferpass.pe_product_schema ORDER BY geography.geography_updt_ts DESC) AS row_number
        from 
        testedchippass
        join geography on testedchippass.geographykey = geography.geographykey
        join testedwaferpass on testedchippass.testedwaferpasskey = testedwaferpass.testedwaferpasskey
        left join pedata_pn_master on pedata_pn_master.partnumber = testedwaferpass.pe_chip_pn
        where
        testedwaferpass.pe_product_schema in ('{"','".join(products)}')
        and rlse_step_pn not in ('GENERAL','')
    )
    where row_number = 1
    """)
    return product_step_df

def join_schema(data: pd.DataFrame)->str:
    """
    Updates the passed in dataframe and adds a column 'pe_product_schema'. Requires a wafer_id column
    Returns the column name representing the schema
    """
    schemaList = ['schema','pe_product_schema']
    schemaCols = [col for col in schemaList if col in data.columns]
    data.columns = data.columns.str.lower()
    if 'wafer_id' not in data.columns:
        raise Exception('Column wafer_id required in input dataset.')
    wafers = data.wafer_id.unique()
    if len(schemaCols) == 0:
        schema_df = ibmdata.isdw.query(f"""
        select distinct pe_product_schema, wafer_id
        from testedwaferpass
        where testedwaferpass.pe_product_schema is not null
        and testedwaferpass.wafer_id in ('{"','".join(wafers)}')
        """)
        data = pd.merge(data, schema_df, how='left', on=['wafer_id'])
        schemaCol = "pe_product_schema"
    else:
        schemaCol = schemaCols[0]
    data['chip_cnt'] = 1
    data['waf_chip_cnt'] = data.groupby('wafer_id').chip_cnt.transform('sum')
    return schemaCol

def interpolate_wmaps(data: pd.DataFrame, failCol: str, schema_geodf: pd.DataFrame, wafx: str = 'unitcell_x', wafy: str = 'unitcell_y')->list[pd.DataFrame]:
    """
    takes an input dataframe of wafermap coordinates and fail column value and fills in empty chip locations with similar values to nearby failing chips.
    """
    filldfs = []
    wafx_cols = schema_geodf[wafx].unique()
    wafx_cols.sort()
    wafy_cols = schema_geodf[wafy].unique()
    wafy_cols.sort()
    for wafer, waferdf in data.groupby(['wafer_id']):
        tempdf = pd.merge(schema_geodf[[wafx,wafy]], waferdf[[wafx,wafy,failCol]], how="left", on=[wafx,wafy], suffixes=["","_drop"])
        missingcnt = tempdf[failCol].isnull().sum()
        pivotdf = pd.pivot_table(tempdf, values=failCol, index=[wafy], columns=[wafx], dropna=False).reset_index()
        pivotdf = pivotdf.drop(columns=[wafy])
        array = pivotdf.to_numpy()

        #mask invalid values
        array = np.ma.masked_invalid(array)
        xx, yy = np.meshgrid(wafx_cols, wafy_cols)
        #get only the valid values
        x1 = xx[~array.mask]
        y1 = yy[~array.mask]
        newarr = array[~array.mask]

        #method = ['linear', 'nearest', 'cubic']
        GD1 = interpolate.griddata((x1, y1), newarr.ravel(), (xx, yy), method='nearest')

        newdf = pd.DataFrame(GD1, columns = wafx_cols, index = wafy_cols).reset_index()
        newdf = newdf.rename(columns = {'index':wafy})
        newXdf = pd.melt(newdf, id_vars=[wafy], value_vars=wafx_cols, var_name=wafx, value_name=failCol)
        newXdf = pd.merge(schema_geodf, newXdf[[wafx,wafy,failCol]], how="left", on=[wafx,wafy], suffixes=["","_drop"])
        newXdf['wafer_id'] = wafer
        newXdf['missing_cnt'] = missingcnt
        filldfs.append(newXdf)
    return filldfs

def DCT(P,Q,x,y,ignore=[]):
    A = []
    for u in range(1,P+1):
        for v in range(1,Q+1):
            if u == 1:
                alpha = np.sqrt(1/P)
            else:
                alpha = np.sqrt(2/P)
            if v == 1:
                beta = np.sqrt(1/Q)
            else:
                beta = np.sqrt(2/Q)
            transform = alpha*beta*np.cos((np.pi*(2*x-1)*(u-1))/(2*P))*np.cos((np.pi*(2*y-1)*(v-1))/(2*Q))
            if (u,v) in ignore:
                transform = 0
            A.append(transform)
    return np.array(A)

def parseData(data, groupby = 'wafer_id', b_input = None, x = 'unitcell_x', y = 'unitcell_y', P = 1, Q = 1, ignore = []):
    wafers = data[groupby].unique()
    B = []
    Alpha = []
    for waferid in wafers:
        cur_df = data[data[groupby]== waferid]
        b = np.array(cur_df[b_input])
        xy = cur_df[['rankx','ranky']].values.tolist()
        tempA = []
        for x,y in xy:
            tempA.append(DCT(P,Q,x,y,ignore))
        A = np.array(tempA)
        B.append(b)
        Alpha.append(A)
    return wafers, B, Alpha

def createEuclidianDistanceMatrix(etas):
    output = []
    for a in etas:
        row = []
        for b in etas:
            row.append(distance.euclidean(a,b))
        output.append(row)
    return output

def runRobustFeatureExtraction(data: pd.DataFrame, failcol: str, t: int = 100, wafx: str = 'unitcell_x', wafy: str = 'unitcell_y', interpolate_wmap: bool = False):
    schema = join_schema(data)
    productdf = get_product_step_pn(data[schema].unique())
    for prod, proddf in productdf.groupby(['pe_product_schema']):
        schema_geodf = ibmdata.isdw.geography.get_geography(stepec=proddf[['rlse_step_ec']].iloc[0][0])
        devloclist = ibmdata.plot.wafermap._common.determine_product_chip_id(schema_geodf)
        schema_geodf = schema_geodf.loc[schema_geodf.devloc.isin(devloclist) & schema_geodf.unitcell_x.ne(0)]
        #schema_geodf.loc[:,'rankx'] = schema_geodf.loc[:,wafx].rank(method='dense').astype(int)
        #schema_geodf.loc[:,'ranky'] = schema_geodf.loc[:,wafy].rank(method='dense').astype(int)
        schema_geodf['rankx'] = schema_geodf[wafx].rank(method='dense').astype(int)
        schema_geodf['ranky'] = schema_geodf[wafy].rank(method='dense').astype(int)
        P = schema_geodf['rankx'].max()
        Q = schema_geodf['ranky'].max()
        validcoords = [tuple(coord) for coord in schema_geodf[['rankx','ranky']].to_numpy()]
        allcoords = [tuple(coord) for coord in list(itertools.product(range(1,P+1),range(1,Q+1)))]
        ignore = [coord for coord in allcoords if coord not in validcoords]
        
        if interpolate_wmap:
            filldfs = interpolate_wmaps(data[data[schema]==prod], failcol, schema_geodf)
            df = pd.concat(filldfs)
        else:
            df = pd.merge(data,schema_geodf,how='left',on=[wafx,wafy],suffixes=["","_drop"])
        
        wafers, B, Alpha = parseData(df, groupby = 'wafer_id', b_input = failcol, x = wafx, y = wafy, P = P, Q = Q, ignore = ignore)
        
        etas = []
        nonzero_indices = []
        for i in range(len(wafers)):
            #print(wafers[i])
            #print(Alpha[i])
            #print(Alpha[i].shape)
            #flatten_arr = np.ravel(Alpha[i])
            #result = np.all(Alpha[i]==flatten_arr[0])
            #if result:
            #    print("Alpha unique = 1")
            #print(B[i])
            #print(B[i].shape)
            #print(np.any(np.isnan(Alpha[i])))
            #print(np.any(np.isnan(B[i])))
            #flatten_arr = np.ravel(B[i])
            #result = np.all(B[i]==flatten_arr[0])
            #if result:
            #    print("B unique = 1")
            omp = OrthogonalMatchingPursuit(n_nonzero_coefs=15, normalize=False)
            #print(omp)
            omp.fit(Alpha[i], B[i])
            #print(omp)
            coef = omp.coef_
            #print(coef)
            (idx_r,) = coef.nonzero()
            etas.append(coef)
            nonzero_indices.append(idx_r)

        DistMatrix = createEuclidianDistanceMatrix(etas)
        dists = squareform(DistMatrix)
        linkage_matrix = linkage(dists, "complete")

        results = fcluster(linkage_matrix, t=t, criterion='distance')
        #results = fcluster(linkage_matrix, t=t, criterion='maxclust')

        from collections import defaultdict
        clusters = defaultdict(list)
        for i, c in enumerate(results):
            clusters[c].append(wafers[i])

        resultsdf = pd.DataFrame(data={'wafer_id':wafers, 'result':results})
        resultsdf['wafer_cnt'] = resultsdf.groupby('result').wafer_id.transform('count')
        classifieddf = pd.merge(df, resultsdf, on=['wafer_id'], how='left')
        
        plot_summary_wafermaps(classifieddf, failcol)
        plot_sample_wafermaps(classifieddf, failcol, interpolate_wmap)


def plot_summary_wafermaps(data: pd.DataFrame, failcol: str):
    plotdf = data.groupby(['normalized_testx','normalized_testy','geographykey','result','wafer_cnt']).agg({failcol:'mean'}).reset_index()
    plotdf['result'] = plotdf['result'].astype(str) + '-' + plotdf['wafer_cnt'].astype(str)

    width = 800
    height = 400
    columns = 4

    print("Summary")
    fig = wafermap_gallery(
            WafermapConfig(
                plotdf, 
                chipx_column='normalized_testx', 
                chipy_column='normalized_testy', 
                color_by_column=failcol, 
                colormap = mpl.cm.RdYlGn.reversed(),
                #discrete=True, 
                title=f"wafermaps",
                #plot_type='plotly',
                plot_type='mpl',
                width=width,
                height=height,
                show_kerf_borders=False
            ), 
            wafer_column='result',
            columns = columns
        )
    plt.show()
    #fig.show()
    #fig.write_image(f"summary_wafermaps.png", engine="kaleido")

def plot_sample_wafermaps(data: pd.DataFrame, failcol: str, interpolate_wmap: str = False):
    if interpolate_wmap:
        wafsumdf = data.groupby(['wafer_id','result']).agg(missing_cnt=('missing_cnt','mean'), fail_mean=(failcol,'mean'), fail_max=(failcol,'max')).reset_index()
    else:
        wafsumdf = data.groupby(['wafer_id','result']).agg(fail_mean=(failcol,'mean'), fail_max=(failcol,'max')).reset_index()
    wafsumdf['delta'] = wafsumdf['fail_max'] - wafsumdf['fail_mean']

    sample_wafers = []
    for res, resdf in wafsumdf.groupby(['result']):
        resdf.sort_values(['delta'], inplace=True)
        sample_wafers.extend(resdf['wafer_id'].head(1))
        sample_wafers.extend(resdf['wafer_id'].tail(1))
        sample_wafers.extend(resdf['wafer_id'].sample(min(len(resdf),2)))
        if interpolate_wmap:
            resdf.sort_values(['missing_cnt'], inplace=True)
            sample_wafers.extend(resdf['wafer_id'].head(1))
            sample_wafers.extend(resdf['wafer_id'].tail(1))
            sample_wafers.extend(resdf['wafer_id'].sample(min(len(resdf),2)))
        else:
            sample_wafers.extend(resdf['wafer_id'].sample(min(len(resdf),4)))

    sampledf = data[data['wafer_id'].isin(sample_wafers)]
    sampledf['result'] = sampledf['result'].astype(object)

    width = 800
    height = 400
    columns = 4

    print("Samples")
    for res, resdf in sampledf.groupby(['result']):
        print(f"group = {res}")
        fig = wafermap_gallery(
                WafermapConfig(
                    resdf, 
                    chipx_column='normalized_testx', 
                    chipy_column='normalized_testy', 
                    color_by_column=failcol, 
                    colormap = mpl.cm.RdYlGn.reversed(),
                    #discrete=True, 
                    title=f"wafermaps - {res}",
                    #plot_type='plotly',
                    plot_type='mpl',
                    width=width,
                    height=height,
                    show_kerf_borders=False
                ), 
                wafer_column='wafer_id',
                columns = columns
            )
        plt.show()
        #fig.show()
        #fig.write_image(f"sample_wafermaps_{res}.png", engine="kaleido")