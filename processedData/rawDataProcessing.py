import pandas as pd
import os
import geopandas as gpd
import numpy as np
import json
import fiona

# Set working directory
# If you want to recreate, set os.chdir to the location of clone
os.chdir('/Users/Michael1/Desktop/2016primary/_working')

# Read in 2016 philly election data and wards shapefile
csv = 'https://www.philadelphiavotes.com/files/raw-data/2016_primary.csv'
#csv = 'rawData/2016_primary.csv'
df = pd.read_csv(csv)
shp = 'rawData/Political_Wards.shp'
primarygdf = gpd.read_file(shp)

# Filter out non presidential elections, drop columns, and sum up votes
dem = (df['OFFICE'] == 'PRESIDENT OF THE UNITED STATES-DEM')
rep = (df['OFFICE'] == 'PRESIDENT OF THE UNITED STATES-REP')
primary = df.loc[(dem | rep)]
primary = primary.drop(columns=['TYPE', 'OFFICE', 'PARTY'])
primary = primary.groupby(['WARD', 'CANDIDATE'], as_index=False).agg({'VOTES': 'sum'})
primary = primary.pivot_table(primary, index = 'WARD', columns='CANDIDATE', aggfunc=np.sum)
primary.columns = primary.columns.droplevel()

# Calculate winner of each ward and re-format
primary['RUNNER_UP'] = primary.T.apply(lambda x: x.nlargest(2).idxmin())
primary['THIRD_UP'] = primary[primary.columns[:-1]].T.apply(lambda x: x.nlargest(3).idxmin())
primary['WINNER'] = primary[primary.columns[:-2]].idxmax(axis=1)

# Calculate percentage of vote column
winper = []
winvote = []
runVote = []
runPer = []
thirdVote = []
thirdPer = []
for i in range(0,len(primary)):
    winper.append(max(primary.iloc[i][:-3])/sum(primary.iloc[i][:-3]))
    winvote.append(max(primary.iloc[i][:-3]))
    runVote.append(primary.iloc[i][:-3].sort_values(ascending=False)[1])
    runPer.append(primary.iloc[i][:-3].sort_values(ascending=False)[1]/sum(primary.iloc[i][:-3]))
    thirdVote.append(primary.iloc[i][:-3].sort_values(ascending=False)[2])
    thirdPer.append(primary.iloc[i][:-3].sort_values(ascending=False)[2]/sum(primary.iloc[i][:-3]))
winper = np.asarray(winper)
winvote = np.asarray(winvote)
primary['WIN_VOTES']= winvote
primary['WIN_PER'] = winper
primary['WIN_PER'] = round(primary['WIN_PER']*100)
primary['RUNUP_VOTES'] = runVote
primary['RUNUP_PER'] = runPer
primary['RUNUP_PER'] = round(primary['RUNUP_PER']*100)
primary['THIRD_VOTES'] = thirdVote
primary['THIRD_PER'] = thirdPer
primary['THIRD_PER'] = round(primary['THIRD_PER']*100)

# Prep data for attribute join
primary.index = primary.index.astype(str, copy=False)
primary.index.names = ['WARD_NUM']

# Perform attribute join based on ward
# Shapefile now has election data
primaryWards = primarygdf.merge(primary, right_index=True, left_on='WARD_NUM')
primaryWards.to_file('processedData/primary_wards.shp')

# open the shapefile using fiona and loop all features in the shapefile
features = []
with fiona.collection('processedData/primary_wards.shp', "r") as source:
    for feat in source:
        features.append(feat)

# create a dictionary to save the features
my_layer = {
    "type": "FeatureCollection",
    "features": features
}

# write the dictionary of features information to a geojson file
with open("processedData/primaryWards.geojson", "w") as featjs:
    featjs.write(json.dumps(my_layer))