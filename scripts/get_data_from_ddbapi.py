import pandas as pd
from ddbapi import zp_pages
import os

places = orte = [
    "Stuttgart", "Köln", "Hamburg", "Bonn", "Bad Godesberg", "Kleve (Kreis Kleve)", "Jülich", "Dortmund",
    "Siegburg", "Euskirchen", "Halle (Saale)", "Münster (Westf)", "Berlin", "Duisburg", "Bielefeld",
    "Stuttgart-Untertürkheim", "Untertürkheim", "Feuerbach (Stuttgart)", "Stuttgart-Feuerbach", "Stuttgart-Zuffenhausen",
    "Zuffenhausen", "Botnang", "Degerloch", "Münster (Stuttgart)", "Obertürkheim", "Stuttgart-Botnang",
    "Stuttgart-Degerloch", "Stuttgart-Münster", "Stuttgart-Obertürkheim", "Aachen", "Ruhrort", "Bonn-Bad Godesberg",
    "Karlsruhe", "Solingen", "Moers", "Meiderich", "Regierungsbezirk Aachen", "Düren", "Mannheim", "Beckum",
    "Mülheim an der Ruhr", "Gütersloh", "München-Gladbach", "Warendorf", "Ahlen (Kreis Warendorf)", "Dinslaken",
    "Mönchengladbach", "Gladbach-Rheydt", "Ohligs", "Oelde", "Wiedenbrück", "Dresden", "Iserlohn", "Hamborn",
    "Oberhausen (Rheinland)", "Wesel", "Düsseldorf", "Biberach an der Riß", "Merseburg", "Kreis Solingen",
    "Gräfrath", "Duisburg-Hamborn", "Bad Buchau", "Hagen", "Hamburg-Harburg", "Harburg (Elbe)",
    "Harburg-Wilhelmsburg", "Arnsberg", "Haan", "Riedlingen", "Wülfrath", "Witten", "Krefeld", "Velbert",
    "Velbert-Langenberg", "Mettmann", "Hamm (Westf)", "Soest", "Werl", "Hannover", "Geldern", "Bergheim (Erft)",
    "Bergedorf", "Castrop-Rauxel", "Geesthacht", "Hamburg-Bergedorf", "Hamburg-Lohbrügge", "Stormarn", "Leipzig",
    "Bensberg", "Bergisch Gladbach", "Bergisch Gladbach-Bensberg", "Schwarzenberg/Erzgeb.", "Dorsten",
    "Ochsenhausen", "Heiligenhaus", "Neviges", "Landkreis Kempen-Krefeld", "New York, NY", "Heidelberg"
]
outdir = "data"
if not os.path.isdir(outdir):
    os.mkdir(outdir)
#Save all the datasets individually - so we have a checkpoint for the org. data
for place in places:
    df = zp_pages(
        publication_date='[1850-01-01T12:00:00Z TO 1980-12-31T12:00:00Z]', 
        place_of_distribution=place, 
        plainpagefulltext=["Heiratsgesuch"]
        )
    df.to_csv("data/" + place.replace(" ", "_") +'_newspaper.csv', sep=';', index=False)
    

#now reload the dfs to concat them 
paths_to_dfs = ["data/" + x for x in os.listdir("data")]
df_list = []
for paths_to_df in paths_to_dfs:
    df_list.append(pd.read_csv(paths_to_df, sep=";"))

df_full = pd.concat(df_list)

msk = df_full.duplicated()
df_filtered = df_full[msk == False]

df_filtered.to_csv("newspaper_concat.csv", sep=";")


