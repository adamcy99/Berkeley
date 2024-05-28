import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import pyodbc
con = pyodbc.connect('DSN=ISDW')

# Use SQL to pull the required dataframes
daysback = 300

wafAndWhere = """
and last_test_date > CURRENT_DATE - %d days
--and last_test_date between '2019-01-01' and CURRENT_DATE
--and last_test_date between '2019-05-06' and '2019-05-12'
and tw.level in ('C5')
and tw.family_code not in ('5S','5M')
--and tw.family_code in ('US')
--and trim(lot_grade) in ('6.1','6.2','6.3','6.4','6.5')
--and lot_id like ('8IQU06001%%')
--and tw.wafer_id in ('6A062213SOG5')
and lot_id not in ('8IQT07017.000', '8IQT07017.010', '8IQT07019.000', '8IQT07020.000', '8IQT07020.005','8IQT07027.000','8IQT07027.002','8IQT07027.027')

"""% (daysback)

parmAndWhere = """
and tp.parm_label in (
            '51~C5~M7125P125A_BANK00',
            '51~C5~M7125P125A_BANK01',
            '51~C5~M7125P125A_BANK02',
            '51~C5~M7125P125A_BANK03'
            )
%s
"""% (wafAndWhere)

andWhere = """
and SUBSTR(TRIM(UPPER(dds.calcdefs)),1,4) in ('DI51')
and TRIM(UPPER(dds.corner)) in ('M7125P125AA')
%s
""" % (wafAndWhere)

pullChipAPRC = """
select * 

from(

select
lot_id,
lot_id_base,
wafer_id,
level,
lot_grade,
family_code,
last_test_date,
week,
corner,
sum(scf_bl_chipcount_top) as scf_bl_chipcount_top,
sum(scf_bl_chipcount_bottom) as scf_bl_chipcount_bottom,
sum(bl_failcount_top) as bl_count_top,
sum(bl_failcount_bottom) as bl_count_bottom,
sum(scf_failcount_top) as scf_count_top,
sum(scf_failcount_bottom) as scf_count_bottom,
sum(chip_ignore) as chip_ignore,
CASE
  WHEN AVG(NULLIF(scf_failcount_bottom + bl_failcount_bottom, 0)) > 5 THEN -1
  ELSE AVG(NULLIF(CAST(scf_failcount_bottom as DECIMAL(5)) + CAST(bl_failcount_bottom as DECIMAL(5)), 0))
END AS fail_count_multiplier,
sum(bl_chipcount_top) as bl_chipcount_top,
sum(bl_chipcount_bottom) as bl_chipcount_bottom,
sum(scf_chipcount_top) as scf_chipcount_top,
sum(scf_chipcount_bottom) as scf_chipcount_bottom,
max(bl_failcount_top) as bl_max_count_top,
max(bl_failcount_bottom) as bl_max_count_bottom,
max(scf_failcount_top) as scf_max_count_top,
max(scf_failcount_bottom) as scf_max_count_bottom,
sum(vpf_chipcount_bottom) as vpf_chipcount_bottom,
sum(hpf_chipcount_bottom) as hpf_chipcount_bottom,
sum(unc_chipcount_bottom) as unc_chipcount_bottom,
sum(pblwlx_chipcount_bottom) as pblwlx_chipcount_bottom,
sum(lopwl_chipcount_bottom) as lopwl_chipcount_bottom,
sum(lofwl_chipcount_bottom) as lofwl_chipcount_bottom,
sum(pwl_chipcount_bottom) as pwl_chipcount_bottom,
sum(swo_chipcount_bottom) as swo_chipcount_bottom,
sum(dpf_chipcount_bottom) as dpf_chipcount_bottom
from
(
    select 
    tw.lot_id,
    substr(tw.lot_id,1,9) as lot_id_base,
    tw.wafer_id,
    tw.level,
    tw.lot_grade,
    tw.family_code,
    tw.last_test_date,
    week(tw.last_test_date) as week,
    tc.wafer_id_xy,
    tc.normalized_testx,
    tc.normalized_testy,
    tc.normalized_testx || '/' || tc.normalized_testy as chip,
    g.geographykey,
    g.radius_center_5,
    CASE
      WHEN tc.normalized_testx = 4 AND tc.normalized_testy = 48 THEN 0
      WHEN tc.normalized_testx = 4 AND tc.normalized_testy = 59 THEN 0
      WHEN tc.normalized_testx = 144 AND tc.normalized_testy = 26 THEN 0
      WHEN tc.normalized_testx = 130 AND tc.normalized_testy = 15 THEN 0
      WHEN tc.normalized_testx = 88 AND tc.normalized_testy = 4 THEN 0
      WHEN tc.normalized_testx = 60 AND tc.normalized_testy = 4 THEN 0
      WHEN g.QUADRANT = '1' THEN 1
      WHEN g.QUADRANT = '2' THEN 1
      ELSE 0
    END AS chip_cnt_top,
    CASE
      WHEN tc.normalized_testx = 4 AND tc.normalized_testy = 48 THEN 0
      WHEN tc.normalized_testx = 4 AND tc.normalized_testy = 59 THEN 0
      WHEN tc.normalized_testx = 144 AND tc.normalized_testy = 26 THEN 0
      WHEN tc.normalized_testx = 130 AND tc.normalized_testy = 15 THEN 0
      WHEN tc.normalized_testx = 88 AND tc.normalized_testy = 4 THEN 0
      WHEN tc.normalized_testx = 60 AND tc.normalized_testy = 4 THEN 0
      WHEN g.QUADRANT = '3' THEN 1
      WHEN g.QUADRANT = '4' THEN 1
      ELSE 0
    END AS chip_cnt_bottom,
    1 AS chip_cnt,
    
--------
    CASE
      WHEN tc.normalized_testx = 4 AND tc.normalized_testy = 48 THEN 0
      WHEN tc.normalized_testx = 4 AND tc.normalized_testy = 59 THEN 0
      WHEN tc.normalized_testx = 144 AND tc.normalized_testy = 26 THEN 0
      WHEN tc.normalized_testx = 130 AND tc.normalized_testy = 15 THEN 0
      WHEN tc.normalized_testx = 88 AND tc.normalized_testy = 4 THEN 0
      WHEN tc.normalized_testx = 60 AND tc.normalized_testy = 4 THEN 0
      WHEN f.failcount > 1000 AND prc.categoryName = 'SCF' THEN 1
      --WHEN prc.categoryName = 'SCF' AND count >= 20 THEN 1
      --WHEN prc.categoryName = 'LoFBL' AND count >= 10 THEN 1
      ELSE 0
    END AS chip_ignore,
    CASE
      WHEN f.failcount > 1000 THEN 0
      WHEN tc.normalized_testx = 4 AND tc.normalized_testy = 48 THEN 0
      WHEN tc.normalized_testx = 4 AND tc.normalized_testy = 59 THEN 0
      WHEN tc.normalized_testx = 144 AND tc.normalized_testy = 26 THEN 0
      WHEN tc.normalized_testx = 130 AND tc.normalized_testy = 15 THEN 0
      WHEN tc.normalized_testx = 88 AND tc.normalized_testy = 4 THEN 0
      WHEN tc.normalized_testx = 60 AND tc.normalized_testy = 4 THEN 0
      WHEN prc.categoryName = 'SCF' AND g.QUADRANT = '1' AND count < 20 THEN count
      WHEN prc.categoryName = 'SCF' AND g.QUADRANT = '2' AND count < 20 THEN count
      ELSE 0
    END AS scf_failcount_top,
    CASE
      WHEN f.failcount > 1000 THEN 0
      WHEN tc.normalized_testx = 4 AND tc.normalized_testy = 48 THEN 0
      WHEN tc.normalized_testx = 4 AND tc.normalized_testy = 59 THEN 0
      WHEN tc.normalized_testx = 144 AND tc.normalized_testy = 26 THEN 0
      WHEN tc.normalized_testx = 130 AND tc.normalized_testy = 15 THEN 0
      WHEN tc.normalized_testx = 88 AND tc.normalized_testy = 4 THEN 0
      WHEN tc.normalized_testx = 60 AND tc.normalized_testy = 4 THEN 0
      WHEN prc.categoryName = 'SCF' AND g.QUADRANT = '3' AND count < 20 THEN count
      WHEN prc.categoryName = 'SCF' AND g.QUADRANT = '4' AND count < 20 THEN count
      ELSE 0
    END AS scf_failcount_bottom,
    CASE
      WHEN f.failcount > 1000 THEN 0
      WHEN tc.normalized_testx = 4 AND tc.normalized_testy = 48 THEN 0
      WHEN tc.normalized_testx = 4 AND tc.normalized_testy = 59 THEN 0
      WHEN tc.normalized_testx = 144 AND tc.normalized_testy = 26 THEN 0
      WHEN tc.normalized_testx = 130 AND tc.normalized_testy = 15 THEN 0
      WHEN tc.normalized_testx = 88 AND tc.normalized_testy = 4 THEN 0
      WHEN tc.normalized_testx = 60 AND tc.normalized_testy = 4 THEN 0
      WHEN prc.categoryName = 'LoFBL' AND g.QUADRANT = '1' AND count < 10 THEN count
      WHEN prc.categoryName = 'LoFBL' AND g.QUADRANT = '2' AND count < 10 THEN count
      ELSE 0
    END AS bl_failcount_top,
    CASE
      WHEN f.failcount > 1000 THEN 0
      WHEN tc.normalized_testx = 4 AND tc.normalized_testy = 48 THEN 0
      WHEN tc.normalized_testx = 4 AND tc.normalized_testy = 59 THEN 0
      WHEN tc.normalized_testx = 144 AND tc.normalized_testy = 26 THEN 0
      WHEN tc.normalized_testx = 130 AND tc.normalized_testy = 15 THEN 0
      WHEN tc.normalized_testx = 88 AND tc.normalized_testy = 4 THEN 0
      WHEN tc.normalized_testx = 60 AND tc.normalized_testy = 4 THEN 0
      WHEN prc.categoryName = 'LoFBL' AND g.QUADRANT = '3' AND count < 10 THEN count
      WHEN prc.categoryName = 'LoFBL' AND g.QUADRANT = '4' AND count < 10 THEN count
      ELSE 0
    END AS bl_failcount_bottom,
    CASE
      WHEN f.failcount > 1000 THEN 0
      WHEN tc.normalized_testx = 4 AND tc.normalized_testy = 48 THEN 0
      WHEN tc.normalized_testx = 4 AND tc.normalized_testy = 59 THEN 0
      WHEN tc.normalized_testx = 144 AND tc.normalized_testy = 26 THEN 0
      WHEN tc.normalized_testx = 130 AND tc.normalized_testy = 15 THEN 0
      WHEN tc.normalized_testx = 88 AND tc.normalized_testy = 4 THEN 0
      WHEN tc.normalized_testx = 60 AND tc.normalized_testy = 4 THEN 0
      WHEN prc.categoryName = 'SCF' AND g.QUADRANT = '1' AND count > 0 AND count < 20 THEN 1
      WHEN prc.categoryName = 'SCF' AND g.QUADRANT = '2' AND count > 0 AND count < 20 THEN 1
      WHEN prc.categoryName = 'LoFBL' AND g.QUADRANT = '1' AND count > 0 AND count < 10 THEN 1
      WHEN prc.categoryName = 'LoFBL' AND g.QUADRANT = '2' AND count > 0 AND count < 10 THEN 1
      ELSE 0
    END AS scf_bl_chipcount_top,
    CASE
      WHEN f.failcount > 1000 THEN 0
      WHEN tc.normalized_testx = 4 AND tc.normalized_testy = 48 THEN 0
      WHEN tc.normalized_testx = 4 AND tc.normalized_testy = 59 THEN 0
      WHEN tc.normalized_testx = 144 AND tc.normalized_testy = 26 THEN 0
      WHEN tc.normalized_testx = 130 AND tc.normalized_testy = 15 THEN 0
      WHEN tc.normalized_testx = 88 AND tc.normalized_testy = 4 THEN 0
      WHEN tc.normalized_testx = 60 AND tc.normalized_testy = 4 THEN 0
      WHEN prc.categoryName = 'SCF' AND g.QUADRANT = '3' AND count > 0 AND count < 20 THEN 1
      WHEN prc.categoryName = 'SCF' AND g.QUADRANT = '4' AND count > 0 AND count < 20 THEN 1
      WHEN prc.categoryName = 'LoFBL' AND g.QUADRANT = '3' AND count > 0 AND count < 10 THEN 1
      WHEN prc.categoryName = 'LoFBL' AND g.QUADRANT = '4' AND count > 0 AND count < 10 THEN 1
      ELSE 0
    END AS scf_bl_chipcount_bottom,
    
--------

    CASE
      WHEN f.failcount > 1000 THEN 0
      WHEN tc.normalized_testx = 4 AND tc.normalized_testy = 48 THEN 0
      WHEN tc.normalized_testx = 4 AND tc.normalized_testy = 59 THEN 0
      WHEN tc.normalized_testx = 144 AND tc.normalized_testy = 26 THEN 0
      WHEN tc.normalized_testx = 130 AND tc.normalized_testy = 15 THEN 0
      WHEN tc.normalized_testx = 88 AND tc.normalized_testy = 4 THEN 0
      WHEN tc.normalized_testx = 60 AND tc.normalized_testy = 4 THEN 0
      WHEN prc.categoryName = 'SCF' AND g.QUADRANT = '1' AND count > 0 AND count < 20 THEN 1
      WHEN prc.categoryName = 'SCF' AND g.QUADRANT = '2' AND count > 0 AND count < 20 THEN 1
      ELSE 0
    END AS scf_chipcount_top,
    CASE
      WHEN f.failcount > 1000 THEN 0
      WHEN tc.normalized_testx = 4 AND tc.normalized_testy = 48 THEN 0
      WHEN tc.normalized_testx = 4 AND tc.normalized_testy = 59 THEN 0
      WHEN tc.normalized_testx = 144 AND tc.normalized_testy = 26 THEN 0
      WHEN tc.normalized_testx = 130 AND tc.normalized_testy = 15 THEN 0
      WHEN tc.normalized_testx = 88 AND tc.normalized_testy = 4 THEN 0
      WHEN tc.normalized_testx = 60 AND tc.normalized_testy = 4 THEN 0
      WHEN prc.categoryName = 'SCF' AND g.QUADRANT = '3' AND count > 0 AND count < 20 THEN 1
      WHEN prc.categoryName = 'SCF' AND g.QUADRANT = '4' AND count > 0 AND count < 20 THEN 1
      ELSE 0
    END AS scf_chipcount_bottom,
    CASE
      WHEN f.failcount > 1000 THEN 0
      WHEN tc.normalized_testx = 4 AND tc.normalized_testy = 48 THEN 0
      WHEN tc.normalized_testx = 4 AND tc.normalized_testy = 59 THEN 0
      WHEN tc.normalized_testx = 144 AND tc.normalized_testy = 26 THEN 0
      WHEN tc.normalized_testx = 130 AND tc.normalized_testy = 15 THEN 0
      WHEN tc.normalized_testx = 88 AND tc.normalized_testy = 4 THEN 0
      WHEN tc.normalized_testx = 60 AND tc.normalized_testy = 4 THEN 0
      WHEN prc.categoryName = 'LoFBL' AND g.QUADRANT = '1' AND count > 0 AND count < 10 THEN 1
      WHEN prc.categoryName = 'LoFBL' AND g.QUADRANT = '2' AND count > 0 AND count < 10 THEN 1
      ELSE 0
    END AS bl_chipcount_top,
    CASE
      WHEN f.failcount > 1000 THEN 0
      WHEN tc.normalized_testx = 4 AND tc.normalized_testy = 48 THEN 0
      WHEN tc.normalized_testx = 4 AND tc.normalized_testy = 59 THEN 0
      WHEN tc.normalized_testx = 144 AND tc.normalized_testy = 26 THEN 0
      WHEN tc.normalized_testx = 130 AND tc.normalized_testy = 15 THEN 0
      WHEN tc.normalized_testx = 88 AND tc.normalized_testy = 4 THEN 0
      WHEN tc.normalized_testx = 60 AND tc.normalized_testy = 4 THEN 0
      WHEN prc.categoryName = 'LoFBL' AND g.QUADRANT = '3' AND count > 0 AND count < 10 THEN 1
      WHEN prc.categoryName = 'LoFBL' AND g.QUADRANT = '4' AND count > 0 AND count < 10 THEN 1
      ELSE 0
    END AS bl_chipcount_bottom,
    CASE
      WHEN tc.normalized_testx = 4 AND tc.normalized_testy = 48 THEN 0
      WHEN tc.normalized_testx = 4 AND tc.normalized_testy = 59 THEN 0
      WHEN tc.normalized_testx = 144 AND tc.normalized_testy = 26 THEN 0
      WHEN tc.normalized_testx = 130 AND tc.normalized_testy = 15 THEN 0
      WHEN tc.normalized_testx = 88 AND tc.normalized_testy = 4 THEN 0
      WHEN tc.normalized_testx = 60 AND tc.normalized_testy = 4 THEN 0
      WHEN prc.categoryName = 'VPF' AND g.QUADRANT = '3' AND count > 0 THEN 1
      WHEN prc.categoryName = 'VPF' AND g.QUADRANT = '4' AND count > 0 THEN 1
      ELSE 0
    END AS vpf_chipcount_bottom,
    CASE
      WHEN tc.normalized_testx = 4 AND tc.normalized_testy = 48 THEN 0
      WHEN tc.normalized_testx = 4 AND tc.normalized_testy = 59 THEN 0
      WHEN tc.normalized_testx = 144 AND tc.normalized_testy = 26 THEN 0
      WHEN tc.normalized_testx = 130 AND tc.normalized_testy = 15 THEN 0
      WHEN tc.normalized_testx = 88 AND tc.normalized_testy = 4 THEN 0
      WHEN tc.normalized_testx = 60 AND tc.normalized_testy = 4 THEN 0
      WHEN prc.categoryName = 'HPF' AND g.QUADRANT = '3' AND count > 0 THEN 1
      WHEN prc.categoryName = 'HPF' AND g.QUADRANT = '4' AND count > 0 THEN 1
      ELSE 0
    END AS hpf_chipcount_bottom,
    CASE
      WHEN tc.normalized_testx = 4 AND tc.normalized_testy = 48 THEN 0
      WHEN tc.normalized_testx = 4 AND tc.normalized_testy = 59 THEN 0
      WHEN tc.normalized_testx = 144 AND tc.normalized_testy = 26 THEN 0
      WHEN tc.normalized_testx = 130 AND tc.normalized_testy = 15 THEN 0
      WHEN tc.normalized_testx = 88 AND tc.normalized_testy = 4 THEN 0
      WHEN tc.normalized_testx = 60 AND tc.normalized_testy = 4 THEN 0
      WHEN prc.categoryName = 'UNC' AND g.QUADRANT = '3' AND count > 0 THEN 1
      WHEN prc.categoryName = 'UNC' AND g.QUADRANT = '4' AND count > 0 THEN 1
      ELSE 0
    END AS unc_chipcount_bottom,
    CASE
      WHEN tc.normalized_testx = 4 AND tc.normalized_testy = 48 THEN 0
      WHEN tc.normalized_testx = 4 AND tc.normalized_testy = 59 THEN 0
      WHEN tc.normalized_testx = 144 AND tc.normalized_testy = 26 THEN 0
      WHEN tc.normalized_testx = 130 AND tc.normalized_testy = 15 THEN 0
      WHEN tc.normalized_testx = 88 AND tc.normalized_testy = 4 THEN 0
      WHEN tc.normalized_testx = 60 AND tc.normalized_testy = 4 THEN 0
      WHEN prc.categoryName = 'PBLWLX' AND g.QUADRANT = '3' AND count > 0 THEN 1
      WHEN prc.categoryName = 'PBLWLX' AND g.QUADRANT = '4' AND count > 0 THEN 1
      ELSE 0
    END AS pblwlx_chipcount_bottom,
    CASE
      WHEN tc.normalized_testx = 4 AND tc.normalized_testy = 48 THEN 0
      WHEN tc.normalized_testx = 4 AND tc.normalized_testy = 59 THEN 0
      WHEN tc.normalized_testx = 144 AND tc.normalized_testy = 26 THEN 0
      WHEN tc.normalized_testx = 130 AND tc.normalized_testy = 15 THEN 0
      WHEN tc.normalized_testx = 88 AND tc.normalized_testy = 4 THEN 0
      WHEN tc.normalized_testx = 60 AND tc.normalized_testy = 4 THEN 0
      WHEN prc.categoryName = 'LoPWL' AND g.QUADRANT = '3' AND count > 0 THEN 1
      WHEN prc.categoryName = 'LoPWL' AND g.QUADRANT = '4' AND count > 0 THEN 1
      ELSE 0
    END AS lopwl_chipcount_bottom,
    CASE
      WHEN tc.normalized_testx = 4 AND tc.normalized_testy = 48 THEN 0
      WHEN tc.normalized_testx = 4 AND tc.normalized_testy = 59 THEN 0
      WHEN tc.normalized_testx = 144 AND tc.normalized_testy = 26 THEN 0
      WHEN tc.normalized_testx = 130 AND tc.normalized_testy = 15 THEN 0
      WHEN tc.normalized_testx = 88 AND tc.normalized_testy = 4 THEN 0
      WHEN tc.normalized_testx = 60 AND tc.normalized_testy = 4 THEN 0
      WHEN prc.categoryName = 'LoFWL' AND g.QUADRANT = '3' AND count > 0 THEN 1
      WHEN prc.categoryName = 'LoFWL' AND g.QUADRANT = '4' AND count > 0 THEN 1
      ELSE 0
    END AS lofwl_chipcount_bottom,
    CASE
      WHEN tc.normalized_testx = 4 AND tc.normalized_testy = 48 THEN 0
      WHEN tc.normalized_testx = 4 AND tc.normalized_testy = 59 THEN 0
      WHEN tc.normalized_testx = 144 AND tc.normalized_testy = 26 THEN 0
      WHEN tc.normalized_testx = 130 AND tc.normalized_testy = 15 THEN 0
      WHEN tc.normalized_testx = 88 AND tc.normalized_testy = 4 THEN 0
      WHEN tc.normalized_testx = 60 AND tc.normalized_testy = 4 THEN 0
      WHEN prc.categoryName = 'PWL' AND g.QUADRANT = '3' AND count > 0 THEN 1
      WHEN prc.categoryName = 'PWL' AND g.QUADRANT = '4' AND count > 0 THEN 1
      ELSE 0
    END AS pwl_chipcount_bottom,
    CASE
      WHEN tc.normalized_testx = 4 AND tc.normalized_testy = 48 THEN 0
      WHEN tc.normalized_testx = 4 AND tc.normalized_testy = 59 THEN 0
      WHEN tc.normalized_testx = 144 AND tc.normalized_testy = 26 THEN 0
      WHEN tc.normalized_testx = 130 AND tc.normalized_testy = 15 THEN 0
      WHEN tc.normalized_testx = 88 AND tc.normalized_testy = 4 THEN 0
      WHEN tc.normalized_testx = 60 AND tc.normalized_testy = 4 THEN 0
      WHEN prc.categoryName = 'SWO' AND g.QUADRANT = '3' AND count > 0 THEN 1
      WHEN prc.categoryName = 'SWO' AND g.QUADRANT = '4' AND count > 0 THEN 1
      ELSE 0
    END AS swo_chipcount_bottom,
    CASE
      WHEN tc.normalized_testx = 4 AND tc.normalized_testy = 48 THEN 0
      WHEN tc.normalized_testx = 4 AND tc.normalized_testy = 59 THEN 0
      WHEN tc.normalized_testx = 144 AND tc.normalized_testy = 26 THEN 0
      WHEN tc.normalized_testx = 130 AND tc.normalized_testy = 15 THEN 0
      WHEN tc.normalized_testx = 88 AND tc.normalized_testy = 4 THEN 0
      WHEN tc.normalized_testx = 60 AND tc.normalized_testy = 4 THEN 0
      WHEN prc.categoryName = 'DPF' AND g.QUADRANT = '3' AND count > 0 THEN 1
      WHEN prc.categoryName = 'DPF' AND g.QUADRANT = '4' AND count > 0 THEN 1
      ELSE 0
    END AS dpf_chipcount_bottom,
    dds.corner
    from 
    DMIW.PattRecChipFactR prcfr
    join DMIW_SYSTEMS.DERIVEDDATASETUP dds  on prcfr.derivedsetupkey = dds.derivedsetupkey
    join DMIW_SYSTEMS.PATTRECCATEGORY prc   on prcfr.pattRecCatKey = prc.pattRecCatKey
    join DMIW_SYSTEMS.TESTEDWAFER tw        on prcfr.testedwaferkey = tw.testedwaferkey
    join DMIW_SYSTEMS.TESTEDCHIP tc         on prcfr.testedwaferkey = tc.testedwaferkey and prcfr.testedchipkey = tc.testedchipkey
    join DMIW_SYSTEMS.GEOGRAPHY g           on prcfr.geographykey = g.geographykey
    join 
    (
    select
        testedwaferkey
        ,testedchipkey
        ,sum(parmvalue) as failcount
        from
        (
            select 
            tw.testedwaferkey
            ,tc.testedchipkey
            ,cpfr.parmvalue
            from
            dmiw.chipparmfactr cpfr
            join dmiw_systems.testedwafer tw on tw.testedwaferkey = cpfr.testedwaferkey
            join dmiw_systems.testedchip tc on tc.testedchipkey = cpfr.testedchipkey and tc.testedwaferkey = cpfr.testedwaferkey
            join dmiw_systems.testparm tp on tp.testparmkey = cpfr.testparmkey
            where
            tw.testedwaferkey is not null
            %s
        )
        group by
        testedwaferkey
        ,testedchipkey
    ) f on prcfr.testedwaferkey = f.testedwaferkey and prcfr.testedchipkey = f.testedchipkey
    
    where
    tw.testedwaferkey is not null
    %s
)
group by
lot_id,
lot_id_base,
wafer_id,
level,
lot_grade,
family_code,
last_test_date,
week,
corner
) finres

join
(
    select distinct
        w.WAFER_ID as waf_id, 
        e.EQP_ID as tool,
        e.procrsc_id as chamber,
        pd.PD_ID as PD_ID,
        wccf.cast_slot_no as slot
        from 
        DMIW.WAFER_CHAMBER_CLAIM_FACT wccf
        join DMIW_SYSTEMS.PROCESS_DEFINITION pd on wccf.processdefkey = pd.processdefkey
        join DMIW_SYSTEMS.EQUIPMENT e on wccf.equipmentkey = e.equipmentkey
        join DMIW_SYSTEMS.CONTROLJOB cj on wccf.controljobkey = cj.controljobkey
        join DMIW_SYSTEMS.WAFER w on wccf.waferkey = w.waferkey
        where
        pd.PD_ID like ('RIECAPEPLUGFCP.1')
        and e.procrsc_id not in ('Carrier','Tool')
) so on so.waf_id = finres.wafer_id
""" % (parmAndWhere, andWhere)
chipAPRC = pd.read_sql(pullChipAPRC,con)

# Label Fin Res
df = chipAPRC
conditions = [
    df['VPF_CHIPCOUNT_BOTTOM'] > 7,
    df['HPF_CHIPCOUNT_BOTTOM'] > 3,
    df['UNC_CHIPCOUNT_BOTTOM'] > 3,
    df['PBLWLX_CHIPCOUNT_BOTTOM'] > 3,
    df['LOPWL_CHIPCOUNT_BOTTOM'] > 3,
    df['LOFWL_CHIPCOUNT_BOTTOM'] > 3,
    df['PWL_CHIPCOUNT_BOTTOM'] > 3,
    df['SWO_CHIPCOUNT_BOTTOM'] > 3,
    df['DPF_CHIPCOUNT_BOTTOM'] > 3,
    df['CHIP_IGNORE'] > 2,
    df['SCF_BL_CHIPCOUNT_TOP'] - df['SCF_BL_CHIPCOUNT_BOTTOM'] > 0,
    (df['SCF_BL_CHIPCOUNT_TOP'] > 4) & (df['SCF_BL_CHIPCOUNT_BOTTOM'] > 4),
    df['SCF_BL_CHIPCOUNT_BOTTOM'] > 2,
    (df['SCF_BL_CHIPCOUNT_BOTTOM'] > 3) & (df['BL_COUNT_BOTTOM'] > 2*df['SCF_COUNT_BOTTOM'])
]
choices = [
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -1,
    -3,
    -2,
    (df['SCF_BL_CHIPCOUNT_BOTTOM'] - df['SCF_BL_CHIPCOUNT_TOP']) * 1/3 * df['FAIL_COUNT_MULTIPLIER'],
    (df['SCF_BL_CHIPCOUNT_BOTTOM'] - df['SCF_BL_CHIPCOUNT_TOP']) * df['FAIL_COUNT_MULTIPLIER'],
    (df['SCF_BL_CHIPCOUNT_BOTTOM'] - df['SCF_BL_CHIPCOUNT_TOP']) * 2/3 * df['FAIL_COUNT_MULTIPLIER']
]
#(df['SCF_CHIPCOUNT_BOTTOM'] * df['SCF_MEAN_COUNT_BOTTOM'])
df['fin_res_metric'] = np.select(conditions, choices, default=0)

conditions = [
    (df['fin_res_metric'] >= 2) & (df['fin_res_metric'] < 13),
    df['fin_res_metric'] < 2,
    df['fin_res_metric'] >= 13
]
choices = [
    "M",
    "N",
    "Y"
]
df['fin_res'] = np.select(conditions, choices, default = "N")

conditions = [
    (df['fin_res_metric'] >= 2) & (df['fin_res_metric'] < 6),
    (df['fin_res_metric'] >= 6) & (df['fin_res_metric'] < 13),
    df['fin_res_metric'] < 2,
    df['fin_res_metric'] >= 13
]
choices = [
    "M_N",
    "M_Y",
    "N",
    "Y"
]
df['fin_res2'] = np.select(conditions, choices, default = "N")


conditions = [
    df['fin_res_metric'] <= 0,
    df['fin_res_metric'] > 0,
]
choices = [
    0,
    df['fin_res_metric']
]
df['fin_res_metric2'] = np.select(conditions, choices, default = df['fin_res_metric'])

# Get FinRes labels by lot
df1 = pd.DataFrame({'count':df.groupby(["LOT_ID_BASE","fin_res2"]).size()}).reset_index()
df1 = df1.pivot_table('count','LOT_ID_BASE','fin_res2',fill_value = 0).reset_index()

# Find Fin Res Lots
fin_res_lots = []
for lot in range(len(df1.LOT_ID_BASE)):
    if df1.Y[lot] >= 2:
        fin_res_lots.append(df1.LOT_ID_BASE[lot])
    elif float(df1.Y[lot] + df1.M_Y[lot])/float(df1.Y[lot] + df1.M_Y[lot] + df1.M_N[lot] + df1.N[lot]) > 0.15:
        fin_res_lots.append(df1.LOT_ID_BASE[lot])
fin_res_lots_labels = []
for i in range(len(fin_res_lots)):
    fin_res_lots_labels.append('Y')
items = {'LOT_ID_BASE':fin_res_lots, 'fin_res_lot':fin_res_lots_labels}
df2 = pd.DataFrame.from_dict(items)

# Add Fin Res lot label
df3 = pd.merge(df, df2, how = 'left', on=['LOT_ID_BASE'])

# Change the M to Y
df3['fin_res3'] = np.select([(df3['fin_res_lot'] == "Y") & (df3['fin_res'] == "M")],
                           ['Y'], default = df3['fin_res'])

df3['fin_res4'] = np.select([(df3['fin_res_lot'] == "Y") & (df3['fin_res2'] == "M_Y")],
                           ['Y'], default = df3['fin_res'])

# Push up to GSA for Cheng Tin
# Cheng Tin wants the table to be in a specific order
df_CT = pd.DataFrame(columns=[
    "FAMILY_CODE", "LOT_ID", "WAFER_ID", "fin_res", "fin_res_metric2", "LAST_TEST_DATE",
    'fin_res2', 'fin_res_lot', 'fin_res3', 'fin_res4'])
df_CT["FAMILY_CODE"] = df3["FAMILY_CODE"]
df_CT["LOT_ID"] = df3["LOT_ID"]
df_CT["WAFER_ID"] = df3["WAFER_ID"]
df_CT["fin_res"] = df3["fin_res"]
df_CT["fin_res_metric2"] = df3["fin_res_metric2"]
df_CT["LAST_TEST_DATE"] = df3["LAST_TEST_DATE"]
df_CT["fin_res2"] = df3["fin_res2"]
df_CT["fin_res_lot"] = df3["fin_res_lot"]
df_CT["fin_res3"] = df3["fin_res3"]
df_CT["fin_res4"] = df3["fin_res4"]

# Convert to CSV File for Cheng Tin
localpath = "/Users/acyang@us.ibm.com/Downloads/finres_10days.csv"
gsapath = "/gsa/pokgsa/home/a/c/acyang/public/finres_10days.csv"

df_CT.to_csv(localpath)

import paramiko

host = "pokgsa.ibm.com"
#port = 22
transport = paramiko.Transport((host))

password = "Iiatwaicpmhfi99"                
username = "acyang"                
transport.connect(username = username, password = password)

sftp = paramiko.SFTPClient.from_transport(transport)

sftp.put(localpath, gsapath)
