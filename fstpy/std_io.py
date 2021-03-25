# -*- coding: utf-8 -*-
import datetime
import multiprocessing as mp
import os.path
import pathlib
import sys
import time

import dask.array as da
import numpy as np
import pandas as pd
import rpnpy.librmn.all as rmn

from fstpy.extra import get_std_file_header

from .exceptions import StandardFileError, StandardFileReaderError
from .logger_config import logger
from .std_dec import get_grid_identifier
from .utils import create_1row_df_from_model, validate_df_not_empty


def open_fst(path:str, mode:str, caller_class:str, error_class:Exception):
    file_modification_time = get_file_modification_time(path,mode,caller_class,error_class)
    file_id = rmn.fstopenall(path, mode)
    logger.info(caller_class + ' - opening file %s', path)
    return file_id, file_modification_time

def close_fst(file_id:int, file:str,caller_class:str):
    logger.info(caller_class + ' - closing file %s', file)
    rmn.fstcloseall(file_id)

def parallel_get_dataframe_from_file(files, get_records_func, n_cores):
    # Step 1: Init multiprocessing.Pool()
    pool = mp.Pool(n_cores)
    df_list = pool.starmap(get_records_func, [file for file in files])
    pool.close()    
    df = pd.concat(df_list)
    return df

def add_grid_column(df):
    vcreate_grid_identifier = np.vectorize(get_grid_identifier,otypes=['str'])    
    df['grid'] = vcreate_grid_identifier(df['nomvar'],df['ip1'],df['ip2'],df['ig1'],df['ig2'])
    return df
    
def get_dataframe_from_file(file:str,query:str,array_container:str=None):
    f_mod_time = get_file_modification_time(file,rmn.FST_RO,'get_records_and_load',StandardFileReaderError)
    unit = rmn.fstopenall(file)

    records = get_std_file_header(unit)

    rmn.fstcloseall(unit)

    df = pd.DataFrame(records)
    
    df.loc[:,'path'] = file
    df.loc[:,'file_modification_time'] = f_mod_time
    
    df = add_grid_column(df)

    if (query is None) == False:
        # valid_params = ['datev','etiket','ip1', 'ip2','ip3','typvar','nomvar']
        # query_str = []
        # for k,v in query.items():
        #     if k in valid_params:
        #         if isinstance(v,str):
        #             query_str.append(f'{k}=="{v}"')
        #         else:
        #             query_str.append(f'({k}=="{v}")')
        #     else:
        #         raise StandardFileReaderError('invalid key in query!')    
        subdf = df.query(query)
        
        # add metadata of this query
        metadf = df.query('nomvar in ["^>", ">>", "^^", "!!", "!!SF", "HY", "P0", "PT", "E1"]')

        subdfmeta = metadf.query('grid in %s'%subdf.grid.unique())    
        if (not subdf.empty) and (not subdfmeta.empty):
            df = pd.concat([subdf,subdfmeta])
        elif (not subdf.empty) and (subdfmeta.empty):    
            df = subdf
        elif subdf.empty:
            df = subdf   

    return df   

def _fstluk(key):
    return rmn.fstluk(int(key))['d']

def _fstluk_dask(key):
    return da.from_array(rmn.fstluk(int(key))['d'])

def add_numpy_data_column(df):
    vfstluk = np.vectorize(_fstluk,otypes='O')
    df.loc[:,'d'] = vfstluk(df['key'])
    return df

def add_dask_data_column(df):
    vfstluk = np.vectorize(_fstluk_dask,otypes='O')
    df.loc[:,'d'] = vfstluk(df['key'])
    return df

def get_dataframe_from_file_and_load(file:str,query:str,array_container:str):
    df = get_dataframe_from_file(file,query,None)
    unit=rmn.fstopenall(file,rmn.FST_RO)
    if array_container in ['numpy','dask.array']:
        if array_container == 'numpy':
            df = add_numpy_data_column(df)
        else:
            df = add_dask_data_column(df)    
    # df['d'] = None
    # for i in df.index:
    #     df.at[i,'d'] = rmn.fstluk(int(df.at[i,'key']))['d']

    rmn.fstcloseall(unit)    
    return df

# written by Micheal Neish creator of fstd2nc
# Lightweight test for FST files.
# Uses the same test for fstd98 random files from wkoffit.c (librmn 16.2).
#
# The 'isFST' test from rpnpy calls c_wkoffit, which has a bug when testing
# many small (non-FST) files.  Under certain conditions the file handles are
# not closed properly, which causes the application to run out of file handles
# after testing ~1020 small non-FST files.
def maybeFST(filename):
  with open(filename, 'rb') as f:
    buf = f.read(16)
    if len(buf) < 16: return False
    # Same check as c_wkoffit in librmn
    return buf[12:] == b'STDR'

def get_file_modification_time(path:str,mode:str,caller_class,exception_class):
    file = pathlib.Path(path)
    if not file.exists():
        return datetime.datetime.now()
    if (mode == rmn.FST_RO) and (not maybeFST(path)):
        raise exception_class(caller_class + 'not an fst standard file!')
   
    file_modification_time = time.ctime(os.path.getmtime(path))
    file_modification_time = datetime.datetime.strptime(file_modification_time, "%a %b %d %H:%M:%S %Y")

    return file_modification_time    

def read_record(array_container,key):
    if array_container == 'dask.array':
        return da.from_array(rmn.fstluk(key)['d'])
    elif array_container == 'numpy':
        return rmn.fstluk(key)['d']

def strip_string_values(record):
    record['nomvar'] = record['nomvar'].strip()
    record['etiket'] = record['etiket'].strip()
    record['typvar'] = record['typvar'].strip()

def remove_extra_keys(record):
    for k in ['swa','dltf','ubc','lng','xtra1','xtra2','xtra3']:
        record.pop(k,None)
    
def get_2d_lat_lon(df:pd.DataFrame) -> pd.DataFrame:
  
    """get_2d_lat_lon Gets the latitudes and longitudes as 2d arrays associated with the supplied grids

    :return: a pandas Dataframe object containing the lat and lon meta data of the grids
    :rtype: pd.DataFrame
    :raises StandardFileError: no records to process
    """
    validate_df_not_empty(df,'get_2d_lat_lon',StandardFileError)
    #remove record wich have X grid type
    without_x_grid_df = df.query('grtyp != "X"')

    latlon_df = get_lat_lon(df)

    validate_df_not_empty(latlon_df,'get_2d_lat_lon - while trying to find [">>","^^"]',StandardFileError)
    
    no_meta_df = without_x_grid_df.query('nomvar not in %s'%["^>", ">>", "^^", "!!", "!!SF", "HY", "P0", "PT", "E1"])

    latlons = []
    path_groups = no_meta_df.groupby(no_meta_df.path)
    for _, path_group in path_groups:
        path = path_group.iloc[0]['path']
        file_id = rmn.fstopenall(path, rmn.FST_RO)
        grid_groups = path_group.groupby(path_group.grid)
        for _, grid_group in grid_groups:
            row = grid_group.iloc[0]
            rec = rmn.fstlir(file_id, nomvar='%s'%row['nomvar'])
            try:
                g = rmn.readGrid(file_id, rec)
                # lat=grid['lat']
                # lon=grid['lon']
            except Exception:
                logger.warning('get_2d_lat_lon - no lat lon for this record')
                continue
            
            grid = rmn.gdll(g)
            tictic_df = latlon_df.query('(nomvar=="^^") and (grid=="%s")'%row['grid'],no_fail=True)
            tactac_df = latlon_df.query('(nomvar==">>") and (grid=="%s")'%row['grid'],no_fail=True)
            lat_df = create_1row_df_from_model(tictic_df)
            lat_df.loc[:,'nomvar'] = 'LA'
            lat_df.at[0,'d'] = grid['lat']
            lat_df.at[0,'ni'] = grid['lat'].shape[0]
            lat_df.at[0,'nj'] = grid['lat'].shape[1]
            lat_df.at[0,'shape'] = grid['lat'].shape
            lon_df = create_1row_df_from_model(tactac_df)
            lon_df.loc[:,'nomvar'] = 'LO'
            lon_df.at[0,'d'] = grid['lon']
            lon_df.at[0,'ni'] = grid['lon'].shape[0]
            lon_df.at[0,'nj'] = grid['lon'].shape[1]
            lon_df.at[0,'shape'] = grid['lon'].shape
            latlons.append(lat_df)
            latlons.append(lon_df)

        rmn.fstcloseall(file_id)
    latlon = pd.concat(latlons)
    latlon.reset_index(inplace=True,drop=True)
    return latlon

def get_lat_lon(df):
    return get_grid_metadata_fields(df,pressure=False, vertical_descriptors=False)

def get_grid_metadata_fields(df,latitude_and_longitude=True, pressure=True, vertical_descriptors=True):
    
    path_groups = df.groupby(df.path)
    meta_dfs = []
    #for each files in the df
    for _, rec_df in path_groups:
        path = rec_df.iloc[0]['path']
        # file_modification_time = rec_df.iloc[0]['file_modification_time']
        # compare_modification_times(file_modification_time,path,rmn.FST_RO,caller,error_class)
        records = get_all_grid_metadata_fields_from_std_file(path)
        meta_df = pd.DataFrame(records)
        #print(meta_df[['nomvar','grid']])
        if meta_df.empty:
            sys.stderr.write('get_meta_data_fields - no metatada in file %s\n'%path)
            return pd.DataFrame(dtype=object)
        grid_groups = rec_df.groupby(rec_df.grid)
        #for each grid in the current file
        for _,grid_df in grid_groups:
            this_grid = grid_df.iloc[0]['grid']
            if vertical_descriptors:
                #print('vertical_descriptors')
                vertical_df = meta_df.query('(nomvar in ["!!", "HY", "!!SF", "E1"]) and (grid=="%s")'%this_grid)
                meta_dfs.append(vertical_df)
            if pressure:
                #print('pressure')
                pressure_df = meta_df.query('(nomvar in ["P0", "PT"]) and (grid=="%s")'%this_grid)
                meta_dfs.append(pressure_df)
            if latitude_and_longitude:
                #print('lati and longi')
                latlon_df = meta_df.query('(nomvar in ["^>", ">>", "^^"]) and (grid=="%s")'%this_grid)
                #print(latlon_df)
                meta_dfs.append(latlon_df)
                #print(latlon_df)
              
    if len(meta_dfs):
        result = pd.concat(meta_dfs)
        result = result.reset_index(drop=True)
        return result
    else:
        return pd.DataFrame(dtype=object)

def get_all_grid_metadata_fields_from_std_file(path):
        
    unit = rmn.fstopenall(path)
    lat_keys = rmn.fstinl(unit,nomvar='^^')
    lon_keys = rmn.fstinl(unit,nomvar='>>')
    tictac_keys = rmn.fstinl(unit,nomvar='^>')
    toctoc_keys = rmn.fstinl(unit,nomvar='!!')
    hy_keys = rmn.fstinl(unit,nomvar='HY')
    sf_keys = rmn.fstinl(unit,nomvar='!!SF')
    e1_keys = rmn.fstinl(unit,nomvar='E1')
    p0_keys = rmn.fstinl(unit,nomvar='P0')
    pt_keys = rmn.fstinl(unit,nomvar='PT')
    keys = lat_keys + lon_keys + tictac_keys + toctoc_keys + hy_keys + sf_keys + e1_keys + p0_keys + pt_keys
    records=[]
    for key in keys:
        record = rmn.fstluk(key)
        if record['dltf'] == 1:
            continue
        #record['fstinl_params'] = None
        #del record['key']
        strip_string_values(record)
        #create a grid identifier for each record
        record['grid'] = get_grid_identifier(record['nomvar'],record['ip1'],record['ip2'],record['ig1'],record['ig2'])
        remove_extra_keys(record)
        record['path'] = path
        record['file_modification_time'] = get_file_modification_time(path,rmn.FST_RO,'get_all_meta_data_fields_from_std_file',StandardFileError)
        records.append(record)
    rmn.fstcloseall(unit)  
    return records


def compare_modification_times(df_file_modification_time, path:str,mode:str, caller:str,error_class:Exception):
    file_modification_time = get_file_modification_time(path,mode,caller, error_class)
    if df_file_modification_time != file_modification_time:
        #print(df_file_modification_time, file_modification_time,df_file_modification_time != file_modification_time)
        raise error_class(caller + ' - original file has been modified since the start of the operation, keys might be invalid - exiting!')


    
#df_file_modification_time = df.iloc[0]['file_modification_time']

    
# def get_all_record_keys(file_id, query):
#     if (query is None) == False:
#         keys = rmn.fstinl(file_id,**query)
#     else:
#         keys = rmn.fstinl(file_id)
#     return keys  

# def get_records(keys,load_data):
#     # from .std_dec import get_grid_identifier,decode_metadata
#     records = []    
#     if load_data:
#         for k in keys:
#             record = rmn.fstprm(k)
#             if record['dltf'] == 1:
#                 continue
#             del record['dltf']
#             record = rmn.fstluk(k)
#             # if array_container == 'dask.array':
#             #     record['d'] = da.from_array(record['d'])
#             # record['fstinl_params'] = None
#             # #del record['key']
#             # strip_string_values(record)
#             # #create a grid identifier for each record
#             # record['grid'] = get_grid_identifier(record['nomvar'],record['ip1'],record['ip2'],record['ig1'],record['ig2'])
#             # remove_extra_keys(record)

#             # if decode:
#             #     record['stacked'] = False
#             #     record.update(decode_metadata(record['nomvar'],record['etiket'],record['dateo'],record['datev'],record['deet'],record['npas'],record['datyp'],record['ip1'],record['ip2'],record['ip3']))
#             records.append(record)
#     else:    
#         for k in keys:
#             record = rmn.fstprm(k)
#             if record['dltf'] == 1:
#                 continue
#             del record['dltf']
#             # record['fstinl_params'] = {
#             #     'datev':record['datev'],
#             #     'etiket':record['etiket'],
#             #     'ip1':record['ip1'],
#             #     'ip2':record['ip2'],
#             #     'ip3':record['ip3'],
#             #     'typvar':record['typvar'],
#             #     'nomvar':record['nomvar']
#             # }
#             # key  = record['key']
#             # def read_record(array_container,key):
#             #     if array_container == 'dask.array':
#             #         return da.from_array(rmn.fstluk(key)['d'])
#             #     elif array_container == 'numpy':
#             #         return rmn.fstluk(key)['d']
            
#             # record['d'] = (read_record,array_container,key)

#             # #del record['key'] #i don't know if we need
#             # strip_string_values(record)
#             # #create a grid identifier for each record
#             # record['grid'] = get_grid_identifier(record['nomvar'],record['ip1'],record['ip2'],record['ig1'],record['ig2'])
#             # remove_extra_keys(record)

#             # if decode:
#             #     record['stacked'] = False
#             #     record.update(decode_metadata(record['nomvar'],record['etiket'],record['dateo'],record['datev'],record['deet'],record['npas'],record['datyp'],record['ip1'],record['ip2'],record['ip3']))

#             records.append(record)

#         # if decode:    
#         #     records = parallelize_records(records,massage_and_decode_record)
#         #     # for i in range(len(records)):
#         #     #     records[i] = massage_and_decode_record(records[i])
#         # else:
#         #     records = parallelize_records(records,massage_record)        
#             # for i in range(len(records)):
#             #     records[i] = massage_record(records[i])
#     return records   


    # if dateo == 0:
    #     return str(dateo)
    # dt = rmn_dateo_to_datetime_object(dateo)
    # return dt.strftime('%Y%m%d %H%M%S')

# def rmn_dateo_to_datetime_object(dateo:int):
#     import datetime
#     res = rmn.newdate(rmn.NEWDATE_STAMP2PRINT, dateo)
#     date_str = str(res[0])
#     if res[1]:
#         time_str = str(res[1])[:-2]
#     else:
#         time_str = '000000'
#     date_str = "".join([date_str,time_str])
#     return datetime.datetime.strptime(date_str, '%Y%m%d%H%M%S')





# def convert_rmnkind_to_string(ip1_kind):
#     return constants.KIND_DICT[int(ip1_kind)]

  
