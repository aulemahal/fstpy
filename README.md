Introduction
============

What is it?
-----------

Fstpy is a high level interface to rpn's rpnpy python library that
produces pandas dataframes or Xarray's from CMC standard files. In order
to promote decoupling, modularization and collaboration, fstpy only
reads and writes. All other operations and algorithms can be
independent.

Fstpy philosophy
-----------------

The idea of ​​using a dataframe is to have a pythonic way of working
with standard files without having to know the mechanics of rmnlib.
Since many people come here with numpy, pandas and xarray knowledge, the
learning curve is much less steep.

Dataframes
----------

They are good for organizing information. eg: select all the tt's, sort
them by grid then by level and produce 3d matrices for each tt of each
grid. Dataframes will help to integrate new model changes and new data
types. Thanks to the dataframes we can also export our results more
easily to different types of formats.

Xarray's
--------

They are used to analyse grouped and indexed data. They are espceially
good for working with n-dimensional meteorological data. They also offer
a great variety of built-in plotting functions.

Requirements
============

If you don't already have python 3.6, numpy, pandas, dask and xarray,
install usage requirements in a personal conda environment

``` bash
# This applies for CMC science users
# create a link in your science home directory to the sitestore to 
# put conda environments, defaults in your home directory (not good)  
mkdir $sitestore_ppp4/conda/.conda  
ln -s $sitestore_ppp4/conda/.conda /home/$science-user/.conda  
# get conda if you don't already have it  
. ssmuse-sh -x cmd/cmdm/satellite/master_u1/miniconda3_4.9.2_ubuntu-18.04-skylake-64   
# create a conda environment for fstpy's requirements   
conda create -n fstpy_req python=3.6   
# whenever you need to use this environment on science run the following
# (if you have'nt loaded the conda ssm, you'll need to do it everytime)
# unless you put it in your profile
. activate fstpy_req   
# installing required packages in fstpy_req environment  
conda install -n fstpy_req numpy pandas dask xarray    
# get rmn python library    
. r.load.dot eccc/mrd/rpn/MIG/ENV/migdep/5.1.1 eccc/mrd/rpn/MIG/ENV/rpnpy/2.1.2    
# you are now ready to use fstpy
# when you don't wnat to use the environment anymore run the following    
# conda deactivate    
```

Installation
============

Use the ssm package

    . ssmuse-sh -d /fs/site4/eccc/cmd/w/sbf000/fstpy-beta-1.0.2 

Using fstpy in scripts or Jupyter Lab/Notebook
----------------------------------------------

### set your environment

``` bash
# activate your conda environment     
. activate fstpy_req     
# get rmn python library      
. r.load.dot eccc/mrd/rpn/MIG/ENV/migdep/5.1.1 eccc/mrd/rpn/MIG/ENV/rpnpy/2.1.2      
# get fstpy ssm package
. ssmuse-sh -d /fs/site4/eccc/cmd/w/sbf000/fstpy-beta-1.0.2      
```

### use fstpy

``` python
# inside your script    
import fstpy.all as fstpy   
df = fstpy.StandardFileReader('path to my fst file').to_pandas()
```

### Usage example

``` python
data_path = prefix + '/data/'    
import fstpy.all as fstpy
# setup your file to read    
records=fstpy.StandardFileReader(data_path + 'ttuvre.std').to_pandas()    
# display selected records in a rpn voir format    
fstpy.voir(records)    
# get statistics on the selected records    
df = fstpy.fststat(records)    
# get a subset of records containing only UU and VV momvar    
just_tt_and_uv = fstpy.select(records,'nomvar in ["TT","UV"]')    
# display selected records in a rpn voir format   
fstpy.voir(just_tt_and_uv)    
dest_path = '/tmp/out.std'    
# write the selected records to the output file    
fstpy.StandardFileWriter(dest_path,just_tt_and_uv).to_fst()    
```

Contributing
============

Creating the developpement environment
--------------------------------------

``` bash
# get conda if you don't already have it  
. ssmuse-sh -x cmd/cmdm/satellite/master_u1/miniconda3_4.9.2_ubuntu-18.04-skylake-64   
# create a conda environment for fstpy's requirements   
conda create -n fstpy_dev python=3.6   
# whenever you need to use this environment on science run the following (if you have'nt loaded the conda ssm, you'll need to do it everytime)
# unless you put it in your profile
. activate fstpy_dev   
# installing required packages in fstpy_req environment  
conda install sphinx
conda install -c conda-forge sphinx-autodoc-typehints
conda install -c conda-forge sphinx-gallery
conda install -c conda-forge sphinx_rtd_theme
conda install numpy pandas dask xarray pytest
```

Getting the source code
-----------------------

``` bash
git clone git@gitlab.science.gc.ca:sbf000/fstpy.git
# create a new branch
git checkout -b my_change
# modify the code
# commit your changes
# fetch changes
git fetch
# merge recent master
git merge origin master
# push your changes
git push origin my_change
```

Then create a merge request on science's gitlab
<https://gitlab.science.gc.ca/sbf000/fstpy/merge_requests>

Testing
-------

``` bash
# From the $project_root/test directory of the project
. activate fstpy_dev    
# get rmn python library      
. r.load.dot eccc/mrd/rpn/MIG/ENV/migdep/5.1.1 eccc/mrd/rpn/MIG/ENV/rpnpy/2.1.2     
python -m pytest  
```

Building documentation
----------------------

``` bash
# This will build documentation in docs/build and there you will find index.html 
make clean    
make html   
sphinx-build source build 
```

Conda basics
============

[conda
reference](https://kiwidamien.github.io/save-the-environment-with-conda-and-how-to-let-others-run-your-programs.html)

get cmc conda
-------------

``` bash
. ssmuse-sh -x cmd/cmdm/satellite/master_u1/miniconda3_4.9.2_ubuntu-18.04-skylake-64
```

create an environment
---------------------

``` bash
conda create --name fstpy_dev python=3.6
```

activate an environment
-----------------------

``` bash
. activate fstpy_dev
```

install stuff in the env
------------------------

``` bash
conda install -c conda-forge sphinx-autodoc-typehints
conda install -c conda-forge sphinx-gallery
conda install -c conda-forge sphinx_rtd_theme
conda install ipykernel
conda install jupyter-lab
conda install numpy pandas dask xarray pytest
conda install sphinx
```

export env to file
------------------

``` bash
conda env export > environment.yaml
```

deactivate the env
------------------

``` bash
conda deactivate
```

deleting the env
----------------

``` bash
conda env remove --name fstpy_dev
```

list all envs
-------------

``` bash
conda info --envs
```

recreate the env from yml specs
-------------------------------

``` bash
conda env create --file environment.yaml
```

Acknowledgements
================

Great thanks to:

-   [Phillipe Carphin](mailto:Phillipe.Carphin2@canada.ca) for inspiring
    the use of pandas.

-   [Dominik Jacques](mailto:Dominik.Jacques@canada.ca) for the awsome
    domUtils project, a great structure of what should be a python
    project.

-   [Micheal Neish](mailto:Micheal.Neish@canada.ca) for the awsome
    fstd2nc project, great insights on how to develop xarray structure
    from CMC standard files and great functions to work on fst files.
