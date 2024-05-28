import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from scipy.spatial import distance
from scipy import interpolate

from os.path import exists
import ibmdata
from ibmdata.plot.wafermap import wafermap, wafermap_gallery, WafermapConfig
import matplotlib
import itertools

from sklearn.linear_model import OrthogonalMatchingPursuit
from sklearn.linear_model import OrthogonalMatchingPursuitCV
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import squareform
from collections import defaultdict

pd.options.mode.chained_assignment = None

try:
    import debugdict
    from app import LOG
    DEBUG = debugdict.Debugdict()
except ImportError:
    from ibmdata import LOG
    DEBUG = None
    
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
        true
        and geography.RADIUS_CENTER_5 IS NOT NULL 
        and TRIM(geography.RADIUS_CENTER_5) != ''
        and testedwaferpass.pe_product_schema in ('{"','".join(products)}')
        and geography.rlse_step_pn not in ('GENERAL','')
    )
    where row_number = 1
    """)
    return product_step_df


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
        if missingcnt > (len(tempdf) * 0.9):
            LOG.info(f"wafer {wafer} dropped due to low sample size of {len(waferdf)} chips (<10% of the wafer)")
            continue
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

def runRobustFeatureExtraction(schema: str, data: pd.DataFrame, failcol: str, t: int = 100, criterion: str = 'distance', wafx: str = 'unitcell_x', wafy: str = 'unitcell_y', interpolate_wmap: bool = False):
    proddf = pull_product_step_pn([schema])
    geodf = ibmdata.isdw.geography.get_geography(stepec=proddf[['rlse_step_ec']].iloc[0][0])
    devloclist = ibmdata.plot.wafermap._common.determine_product_chip_id(geodf)
    geodf = geodf.loc[geodf.devloc.isin(devloclist) & geodf.unitcell_x.ne(0)]
    processeddf, wafers, B, Alpha, etas, nonzero_indices = robustFeatureExtraction(data, geodf, failcol, wafx, wafy, interpolate_wmap)
    classifieddf, resultsdf, clusters, results  = hierarchicalClustering(processeddf, etas, wafers, t, criterion)
    fig = plot_summary_wafermaps(classifieddf, failcol, 'plotly', True)
    fig.show()
    samples = plot_sample_wafermaps(classifieddf, failcol, interpolate_wmap, 'plotly', True)
    for sample in samples:
        sample.show()
    

def robustFeatureExtraction(data: pd.DataFrame, geodata: pd.DataFrame, failcol: str, wafx: str = 'unitcell_x', wafy: str = 'unitcell_y', interpolate_wmap: bool = False, use_somp = False):
    #schema_geodf.loc[:,'rankx'] = schema_geodf.loc[:,wafx].rank(method='dense').astype(int)
    #schema_geodf.loc[:,'ranky'] = schema_geodf.loc[:,wafy].rank(method='dense').astype(int)
    geodata['rankx'] = geodata[wafx].rank(method='dense').astype(int)
    geodata['ranky'] = geodata[wafy].rank(method='dense').astype(int)
    P = geodata['rankx'].max()
    Q = geodata['ranky'].max()
    validcoords = [tuple(coord) for coord in geodata[['rankx','ranky']].to_numpy()]
    allcoords = [tuple(coord) for coord in list(itertools.product(range(1,P+1),range(1,Q+1)))]
    ignore = [coord for coord in allcoords if coord not in validcoords]
    
    if interpolate_wmap:
        filldfs = interpolate_wmaps(data, failcol, geodata[list(set([wafx,wafy,'normalized_testx','normalized_testy','geographykey','rankx','ranky']))], wafx, wafy)
        df = pd.concat(filldfs)
    else:
        df = pd.merge(data,geodata[list(set([wafx,wafy,'normalized_testx','normalized_testy','geographykey','rankx','ranky']))],how='left',on=[wafx,wafy],suffixes=["","_drop"])

    wafers, B, Alpha = parseData(df, groupby = 'wafer_id', b_input = failcol, x = wafx, y = wafy, P = P, Q = Q, ignore = ignore)

    if not use_somp:
        etas = []
        nonzero_indices = []
        for i in range(len(wafers)):
            omp = OrthogonalMatchingPursuit(n_nonzero_coefs=15, normalize=False)
            omp.fit(Alpha[i], B[i])
            coef = omp.coef_
            (idx_r,) = coef.nonzero()
            etas.append(coef)
            nonzero_indices.append(idx_r)
            
            if DEBUG is not None and LOG.getEffectiveLevel() == ibmdata.logging.DEBUG:
                DEBUG.addval("wafers", wafers)
                DEBUG.addval("Alpha", Alpha)
                DEBUG.addval("B", B)
                DEBUG.addval("etas", etas)
                DEBUG.addval("nonzero_indices", nonzero_indices)
    else:
        result = somp(Alpha, B, nonneg=False, ncoef=15,verbose=False)
        etas = result.coef
        nonzero_indices = []
    df.drop(columns=['rankx','ranky'],inplace=True)    
    #classifieddf = hierarchicalClustering(df, etas, wafers, t, criterion)
    #plot_results(classifieddf, failcol, interpolate_wmap)
    return df, wafers, B, Alpha, etas, nonzero_indices

    
def hierarchicalClustering(df: pd.DataFrame, etas: list, wafers: list, t: int = 100, criterion: str = 'distance'):
    DistMatrix = createEuclidianDistanceMatrix(etas)
    dists = squareform(DistMatrix)
    linkage_matrix = linkage(dists, "complete")

    if t > 0:
        k = t
    else:
        last = linkage_matrix[-10:, 2]
        last_rev = last[::-1]
        idxs = np.arange(1, len(last) + 1)

        acceleration = np.diff(last, 2)  # 2nd derivative of the distances
        acceleration_rev = acceleration[::-1]
        k = acceleration_rev.argmax() + 2 
        #large_accelerations = [i for i, a in enumerate(acceleration_rev) if a > 20]
        #if len(large_accelerations) > 0:
        #    k = large_accelerations[-1] + 2
        LOG.info(f"max cluster = {k}")
    
    results = fcluster(linkage_matrix, t=k, criterion=criterion)

    clusters = defaultdict(list)
    for i, c in enumerate(results):
        clusters[c].append(wafers[i])

    resultsdf = pd.DataFrame(data={'wafer_id':wafers, 'result':results})
    resultsdf['wafer_cnt'] = resultsdf.groupby('result').wafer_id.transform('count')
    classifieddf= pd.merge(df, resultsdf, on=['wafer_id'], how='left')
    
    return classifieddf, resultsdf, clusters, results

def plot_results(data:pd.DataFrame, failcol:str, interpolate_wmap: bool = False):
    plot_summary_wafermaps(data, failcol)
    plot_sample_wafermaps(data, failcol, interpolate_wmap)


def plot_summary_wafermaps(data: pd.DataFrame, failcol: str, plot_type: str = "mpl", returnfig: bool = False):
    plotdf = data.groupby(['normalized_testx','normalized_testy','geographykey','result','wafer_cnt']).agg({failcol:'mean'}).reset_index()
    plotdf['result'] = plotdf['result'].astype(str) + '-' + plotdf['wafer_cnt'].astype(str)

    width = 800
    height = 400
    columns = 4

    fig = wafermap_gallery(
            WafermapConfig(
                plotdf, 
                chipx_column='normalized_testx', 
                chipy_column='normalized_testy', 
                color_by_column=failcol, 
                colormap = matplotlib.cm.RdYlGn.reversed(),
                #discrete=True, 
                title=f"wafermaps",
                #plot_type='plotly',
                plot_type=plot_type,
                width=width,
                height=height,
                show_kerf_borders=False
            ), 
            wafer_column='result',
            columns = columns
        )
    if returnfig:
        return fig
    
    if plot_type == 'mpl':
        plt.show()
    else:
        fig.show()
        #fig.write_image(f"summary_wafermaps.png", engine="kaleido")

def plot_sample_wafermaps(data: pd.DataFrame, failcol: str, interpolate_wmap: str = False, plot_type: str = "mpl", returnfig: bool = False):
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
    figlist = []
    for res, resdf in sampledf.groupby(['result']):
        #print(f"group = {res}")
        fig = wafermap_gallery(
                WafermapConfig(
                    resdf, 
                    chipx_column='normalized_testx', 
                    chipy_column='normalized_testy', 
                    color_by_column=failcol, 
                    colormap = matplotlib.cm.RdYlGn.reversed(),
                    #discrete=True,
                    title=f"wafermaps - {res}",
                    #plot_type='plotly',
                    plot_type=plot_type,
                    width=width,
                    height=height,
                    show_kerf_borders=False
                ),
                wafer_column='wafer_id',
                columns = columns
            )

        if returnfig:
            figlist.append(fig)
        else:
            if plot_type == 'mpl':
                plt.show()
            else:
                fig.show()
                #fig.write_image(f"sample_wafermaps_{res}.png", engine="kaleido")
    
    if returnfig:
        return figlist
import numpy as np
from scipy.optimize import nnls

class Result(object):
    '''Result object for storing input and output data for omp.  When called from 
    `omp`, runtime parameters are passed as keyword arguments and stored in the 
    `params` dictionary.
    Attributes:
        X:  Predictor array after (optional) standardization.
        y:  Response array after (optional) standarization.
        ypred:  Predicted response.
        residual:  Residual vector.
        coef:  Solution coefficients.
        active:  Indices of the active (non-zero) coefficient set.
        err:  Relative error per iteration.
        params:  Dictionary of runtime parameters passed as keyword args.   
    '''
    
    def __init__(self, **kwargs):
        
        # to be computed
        self.X = None
        self.y = None
        self.ypred = None
        self.residual = None
        self.coef = None
        self.active = None
        self.err = None
        
        # runtime parameters
        self.params = {}
        for key, val in kwargs.items():
            self.params[key] = val
            
    def update(self, coef, active, err, residual, ypred):
        '''Update the solution attributes.
        '''
        self.coef = coef
        self.active = active
        self.err = err
        self.residual = residual
        self.ypred = ypred

def somp(X, y, nonneg=True, ncoef=None, maxit=200, tol=1e-3, ztol=1e-12, verbose=True):
    '''Compute sparse orthogonal matching pursuit solution with unconstrained
    or non-negative coefficients.
    
    Args:
        X: Dictionary array of size n_samples x n_features. 
        y: Reponse array of size n_samples x 1.
        nonneg: Enforce non-negative coefficients.
        ncoef: Max number of coefficients.  Set to n_features/2 by default.
        tol: Convergence tolerance.  If relative error is less than
            tol * ||y||_2, exit.
        ztol: Residual covariance threshold.  If all coefficients are less 
            than ztol * ||y||_2, exit.
        verbose: Boolean, print some info at each iteration.
        
    Returns:
        result:  Result object.  See Result.__doc__
    '''
    
    def norm2(x):
        return np.linalg.norm(x) / np.sqrt(len(x))
    
    # initialize result object
    result = Result(nnoneg=nonneg, ncoef=ncoef, maxit=maxit,
                    tol=tol, ztol=ztol)
    if verbose:
        print(result.params)
    
    # check to see if we have the same number of X and y inputs
    if len(X) != len(y):
        print('Must have equal number of X and y inputs')
        return result
    # set n = number of inputs
    n = len(y)
    
    # check that n_samples match
    for i in range(n):
        if X[i].shape[0] != len(y[i]):
            print('X and y must have same number of rows (samples)')
            return result
    
    # check types, try to make somewhat user friendly
    for i,item in enumerate(X):
        if type(item) is not np.ndarray:
            X[i] = np.array(item)
    for i,item in enumerate(y):
        if type(item) is not np.ndarray:
            y[i] = np.array(item)
    
    # store arrays in result object    
    result.y = y
    result.X = X
    
    # for rest of call, want y to have ndim=1
    for i,item in enumerate(y):
        if np.ndim(item) > 1:
            y[i] = np.reshape(item, (len(item),))
        
    # by default set max number of coef to half of total possible
    if ncoef is None:
        ncoef = int(X[0].shape[1]/2)
    
    # initialize things
    X_transpose = []
    for x in X:
        X_transpose.append(x.T)               # store for repeated use
    #active = np.array([], dtype=int)         # initialize list of active set
    active = []
    # coef are the output vectors. 1 vector for each input pair given
    coef = []
    for i in range(n):
        coef.append(np.zeros(X[0].shape[1], dtype=float)) # solution vector
    residual = y                             # residual vector
    
    ypred = []
    for i in range(n):
        ypred.append(np.zeros(y[0].shape, dtype=float))
    
    #### Revisit ####
    # How to deal with ynorm and err?
    # err = Min of all ynorm? Max of all ynorm? Avg of all ynorm? Maybe take linear comb of all y and then find ynorm from that?
    ynorm = []
    for i in range(n):
        ynorm.append(norm2(y[i]))                         # store for computing relative err
    ynorm = np.mean(ynorm)
    err = np.zeros(maxit, dtype=float)       # relative err vector
    
    # Check if response has zero norm, because then we're done. This can happen
    # in the corner case where the response is constant and you normalize it.
    if ynorm < tol:     # the same as ||residual|| < tol * ||residual||
        print('Norm of the response is less than convergence tolerance.')
        result.update(coef, active, err[0], residual, ypred)
        return result
    
    # convert tolerances to relative
    tol = tol * ynorm       # convergence tolerance
    ztol = ztol * ynorm     # threshold for residual covariance
    
    if verbose:
        print('\nIteration, relative error, number of non-zeros')
   
    # main iteration
    for it in range(maxit):
        
        # compute residual covariance vector and check threshold
        ##### introduce linear combination into this step for S-OMP #####
        if nonneg:
            rcov = np.dot(X_transpose[0], residual[0])
            for i in range(1,len(y)):
                rcov += np.dot(X_transpose[i], residual[i])
            i = np.argmax(rcov)
            rc = rcov[i]
        else:
            rcov = np.abs(np.dot(X_transpose[0], residual[0]))
            for i in range(1,len(y)):
                rcov += np.abs(np.dot(X_transpose[i], residual[i]))
            i = np.argmax(rcov)
            rc = np.abs(rcov[i])
        if rc < ztol:
            print('All residual covariances are below threshold.')
            break
        
        # update active set
        if i not in active:
            #active = np.concatenate([active, [i]], axis=1)
            active.append(i)
            
        # solve for new coefficients on active set
        # _ are varaibles that don't matter we only care about coefi
        for i in range(n):
            if nonneg:
                coefi, _ = nnls(X[i][:, active], y[i])
            else:
                coefi, _, _, _ = np.linalg.lstsq(X[i][:, active], y[i],rcond=None)
            coef[i][active] = coefi   # update solution
        
        # update residual vector and error
        for i in range(n):
            residual[i] = y[i] - np.dot(X[i][:,active], coefi)
            ypred[i] = y[i] - residual[i]
        ##### Revisit #####
        # same issue as ynorm, how do we deal with error?
        # err = Min of all residual? Max of all residual? 
        # err = Avg of all residual? Maybe take linear comb of all residual and then find residualnorm from that?
        resnorm = []
        for i in range(n):
            resnorm.append(norm2(residual[i]))
        resnorm = np.mean(resnorm)
        err[it] = resnorm / ynorm  
        
        # print status
        if verbose:
            print('{}, {}, {}'.format(it, err[it], len(active)))
            
        # check stopping criteria
        if err[it] < tol:  # converged
            print('\nConverged.')
            break
        if len(active) >= ncoef:   # hit max coefficients
            print('\nFound solution with max number of coefficients.')
            break
        if it == maxit-1:  # max iterations
            print('\nHit max iterations.')
    
    result.update(coef, active, err[:(it+1)], residual, ypred)
    return result
