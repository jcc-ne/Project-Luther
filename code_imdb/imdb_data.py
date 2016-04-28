import imdb
import pandas as pd
import sqlalchemy
import re
import seaborn as sns
from dateutil import parser


ia = imdb.IMDb('sql',
               uri='sqlite:///Users/janine/Documents/Projects/Metis/'
               'Project-Luther/data/imdb_data.db')


def get_movie_data(title, ia=None):
    # ia.get_movie_infoset()
    if not ia:
        ia = imdb.IMDb()
    m = ia.search_movie(title)[0]
    ia.update(m, ['main', 'business'])
    return m


def add_info_by_type(info_type, df, df_info, df_info_lookup, flag_group=False):
    if info_type in df.columns:
        return df
    info_id = df_info[df_info['info'] == info_type]['id'].values[0]
    df_info_par = df_info_lookup[df_info_lookup['info_type_id'] == info_id]
    if flag_group:
        df_info_par = df_info_par.groupby('movie_id', as_index=False).first()
    return df.merge(df_info_par[['movie_id', 'info']]
                    .rename(columns={'info': info_type}),
                    left_on='id', right_on='movie_id').drop('movie_id', axis=1)


def mpaa(mpaa_string):
    m = re.search('^(.*?) for', mpaa_string.lower())
    if m:
        return re.sub('(rated|rat|on appeal| )', '', m.group(1)).strip().upper()
    else:
        return None


def main():
    eng = sqlalchemy.create_engine('sqlite:///../data/imdb_data.db')

    df_info = pd.read_sql_table('info_type', eng)
    t1 = pd.read_sql_table('movie_info', eng)
    t2 = pd.read_sql_table('movie_info_idx', eng)
    df_title = pd.read_sql_table('title', eng)
    df_title = df_title[df_title.kind_id == 1]  # just movies
    df = df_title[['id', 'title', 'production_year']]

    for info_type in ['genres', 'budget', 'countries', 'mpaa', 'release dates']:
        df = add_info_by_type(info_type, df, df_info, t1)

    for info_type in ['gross']:
        df = add_info_by_type(info_type, df, df_info, t1, flag_group=True)

    for info_type in ['rating']:
        df = add_info_by_type(info_type, df, df_info, t2)

    df = df[df['countries'] == 'USA']
    df = df[df['release dates'].str.startswith('USA')]

    df['gross'] = df.gross.apply(lambda x: int(re.sub('[^0-9]', '', x)))
    df['budget'] = df.budget.apply(lambda x: int(re.sub('[^0-9]', '', x)))
    df['release date'] = df['release dates'].apply(
        lambda x: parser.parse(x.split(':')[1]))

    df.loc[df.genres == 'News', 'genres'] = 'Drama'
    df.loc[df.genres.str.startswith('_'), 'genres'] = 'Drama'

    sns.pairplot(df[['budget', 'gross', 'genres']], hue='genres', size=5)
    sns.pairplot(df[['budget', 'gross', 'mpaa_short']], hue='mpaa_short', size=5)
