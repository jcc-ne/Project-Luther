# !pip install --user imdbpy

import imdb
import csv
from collections import defaultdict
import re


def get_movie_data(title):
    # ia.get_movie_infoset()
    ia = imdb.IMDb()
    m = ia.search_movie(title)[0]
    ia.update(m, 'business')
    return m


movie_names = defaultdict()
# movie_names = []
with open('movies.list', 'r') as f:
    r = csv.reader(f, delimiter='\t', quotechar='"')
    row = r.next()
    while row:
        year = row[-1]
        name = re.sub('{.*}', '', row[0])
        name = name.split('(')[0]
        movie_names.setdefault(name, []).append(year)
#         movie_names.append(name)
        row = r.next()
