# Building a tool (maybe with AI) to check UKCP data is in a good state

This is an experiment in seeing if we can train a Machine Learning model, or build
a deterministic tool, to be able to tell us about the UKCP archives. 

We want to answer these questions:
1. Which sets of files differ from each other and how do they differ?
  - Do some file sets have irregular dimension sizes?
  - Do some file sets use different IDs for coordinate variables?
2. Is an individual file an outlier?
  - Does it have features or feature values that are not found elsewhere?
3. Which file names are outliers?
  - Given a file name X, what is the probability it is compliant/correct?

## TO-DOS

- [ ] Need to manage `latest` properly - as these are just separate records at present.
- [ ] Extracting the vocabularies is quirky:
  - for "variables": we need an even deeper merge than the current merge_dicts() at depth: 2
    - probably need to go to depth: 3

## Creating a training dataset

Here is the plan for creating a training dataset:
- Scan a set of files
- Capture numerous features
- Put them all into a gzipped CSV file

The main dataset should be optmised for storage, which means:
- use text fields and not one-hot encoding

## Working with the dataset

Try a range of ML models, looking at:
- Classification
- Outliers

Can I establish what a good file looks like?

## Intermediate format

The `extract` process takes the main content of each NetCDF file and records it in a JSON
structure. These are all written to: `{outputdir}/#####.json`

This format gets all the useful info so that it can be quickly processed from JSON into 
CSV (or other formats).

## Features

- time_dim_name
- time_dim_value
- lat_dim_name
- lat_dim_length
- 

- varid_filename
- varid_content

## Start with some random files

Generated with:

```
for i in land-cpm land-gcm land-rcm ; do fbi_random /badc/ukcp18/data/$i | grep \.nc >> filelist.txt ; done
```

Written to: `filelist.txt`

Creating file lists:

```
find -L /badc/ukcp18/data/land-gcm -type f -iname "*.nc" > filelist-land-gcm.txt
find -L /badc/ukcp18/data/land-rcm -type f -iname "*.nc" > filelist-land-rcm.txt
find -L /badc/ukcp18/data/land-prob -type f -iname "*.nc" > filelist-land-prob.txt
find -L /badc/ukcp18/data/land-cpm -type f -iname "*.nc" > filelist-land-cpm.txt
```

## Testing the code before running on whole UKCP archive

On ingest server, ran this, to generate a long list of random files (10 x 100 x 4 = 4,000):

```
$ for x in $(seq 1 100); do for i in land-prob land-cpm land-gcm land-rcm ; do fbi_random /badc/ukcp18/data/$i | grep "\.nc" >> /tmp/filelist-ukcp.txt ; done ; done
$ shuf /tmp/filelist-ukcp.txt > /tmp/ukcp-filelist.txt
$ scp /tmp/ukcp-filelist.txt HERE:random-filelist.txt
```

## Extracting all using LOTUS

```
$ for i in $(seq 1 712) ; do sbatch -p short-serial -t 03:00:00 \
     -o /gws/pw/j07/ukcp18/ai-astephen/lotus-outputs/${i}.out \
     -e /gws/pw/j07/ukcp18/ai-astephen/lotus-outputs/${i}.err \
     $PWD/extract.py -b ${i} ; done
```

Some checks to see they all worked:

```
$ find /gws/pw/j07/ukcp18/ai-astephen/lotus-outputs/ -name "*.out" -size +120000c -size -160000c -exec ls -l {} \; | wc -l
72
$ find /gws/pw/j07/ukcp18/ai-astephen/lotus-outputs/ -name "*.err" -size -1 -exec ls -l {} \; | wc -l
72
```

## Setting up VSCode with remote (JASMIN) host

- Click on the run button (Right triangle in top right of editor)
- Prompted for Python interpreter - provide path
- Paste in this (jaspy) env: 