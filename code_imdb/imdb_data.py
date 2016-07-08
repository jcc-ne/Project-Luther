import imdb
import pandas as pd
import sqlalchemy
import re
import seaborn as sns
from dateutil import parser
import numpy as np
import matplotlib.pyplot as plt

# <codecell>

ia = imdb.IMDb('sql',
               uri='sqlite:///Users/janine/Documents/Projects/Metis/'
               'Project-Luther/data/imdb_data.db')

def budget_groups(budget, budgets, n_percentiles=None, budget_levels=[]):
    budg_percentiles = []
    if n_percentiles:
        assert budget_levels == []
        for i in np.linspace(0, 100, n_percentiles+1):
            budg_percentiles.append(np.percentile(budgets, i))
        budg_percentiles.pop(0)
    elif budget_levels:
        assert n_percentiles == None
        for i in budget_levels:
            budg_percentiles.append(np.percentile(budgets, i))
    for i, q in enumerate(budg_percentiles):
        if budget < q:
            return i
    return len(budg_percentiles) - 1


def assign_grp(ind, ind_grp):
    for i, r in enumerate(ind_grp):
        if ind in r:
            return i


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


def get_dummies(ds, prefix=''):
    dummies = pd.get_dummies(df_dum[[1, 2, 3]].stack(),
                             prefix=prefix).groupby(level=0).sum()
#     cols = ['{}_{}'.format(prefix, c).strip('_') for c in dummies.columns]
#     dummies.columns = cols
    return dummies


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
    df['month'] = df['release date'].apply(lambda x: x.month)
    df['year'] = df['release date'].apply(lambda x: x.year)

    df.loc[df.genres == 'News', 'genres'] = 'Drama'
    df.loc[df.genres.str.startswith('_'), 'genres'] = 'Drama'
    df['mpaa_short'] = df.mpaa.apply(mpaa)

    sns.pairplot(df[['budget', 'gross', 'genres']], hue='genres', size=5)
    sns.pairplot(df[['budget', 'gross', 'mpaa_short']], hue='mpaa_short', size=5)

    df0 = df.copy()
    df = df[['title', 'gross', 'budget', 'release date', 'rating',
             'month', 'year', 'genres', 'mpaa_short']]


    dg_m = df.groupby('month').agg({'gross': sum,
                                    'budget': sum,
                                    'title': 'count'})
    df.loc[:, 'total_titles_by_month'] = df.month.apply(
        lambda x: dg_m.loc[x, 'title'])
    df.loc[:, 'total_gross_by_month'] = df.month.apply(
        lambda x: dg_m.loc[x, 'gross'])
    df.loc[:, 'total_budget_by_month'] = df.month.apply(
        lambda x: dg_m.loc[x, 'budget'])


    # give index
    ind = dg_m.title.sort_values().index
    ind_grp = np.array_split(ind, 4)
    df.loc[:, 'quantity_m_index'] = df.month.apply(lambda x: assign_grp(x, ind_grp))

    ind = dg_m.budget.sort_values().index
    ind_grp = np.array_split(ind, 4)
    df.loc[:, 'bigbudget_m_index'] = df.month.apply(
        lambda x: assign_grp(x, ind_grp))

    df_dum_bb = pd.get_dummies(df.bigbudget_m_index, prefix='bigbudget')

    df = pd.concat([df, df_dum_bb], axis=1)


    # -- budget_groups
#     n_percentiles = 4
    df['budget_group'] = df.budget.apply(
        lambda x: budget_groups(x, df.budget,
                                budget_levels=[25,50,75,100]))

    # budget group
#     df = df.drop(['bg_0', 'bg_1', 'bg_2'], axis=1)
    df_dum_bg  = pd.get_dummies(df.budget_group, prefix='bg')

    df = pd.concat([df, df_dum_bg], axis=1)
    return df


import statsmodels.formula.api as smf
import numpy as np

r_formula = 'gross ~ budget'
r_formula = ('np.log(gross) ~ np.log(budget) + bg_0 * np.log(total_budget_by_month) '
             '+ bg_2 * np.log(total_budget_by_month)'
             '+ bg_3 * np.log(total_budget_by_month)')
r_formula = ('gross ~ budget + bg_0 * total_budget_by_month '
#                '+ bg_1 * total_budget_by_month'
             '+ bg_3 * total_budget_by_month')
r_formula = 'gross ~ budget + bigbudget_0 + bigbudget_3'
r_formula = 'gross_norm ~ budget_norm'
r_formula = 'gross_norm ~ budget_norm + bigbudget_1 + bigbudget_2 + bigbudget_3'
r_formula = 'np.log10(gross) ~ np.log10(budget)'
r_formula = 'np.log10(gross_norm) ~ np.log10(budget_norm)'
r_formula = 'gross ~ budget + total_titles_by_month + total_budget_by_month + total_gross_by_month'
r_formula = 'gross_norm ~ budget_norm + total_titles_by_month + total_budget_by_month + total_gross_by_month'

def run_sm_ols(df):
    model = smf.ols(r_formula, data=df)
    fit = model.fit()
    print fit.summary()


from sklearn import linear_model
import patsy

def run_sklearn_lr(df):
    lr = linear_model.LinearRegression(normalize=True)
    y = np.log10(df.gross.values)
    X = np.log10(df.budget.values).reshape((-1 ,1))
    lr.fit(X, y)

def run_sklearn_patsy(df):
    lr = linear_model.LinearRegression(normalize=True)
    y, X = patsy.dmatrices(r_formula, data=df)
    lr.fit(X, y)
    lr.score(X, y)


def run_sklearn_lasso(df):
    lassocv  = linear_model.LassoCV()
    y = np.log10(df.gross.values)
    X = np.log10(df.budget.values).reshape((-1 ,1))
    lassocv.fit(X, y)


def run_sklearn_lasso_patsy(df):
    lassocv  = linear_model.LassoCV(normalize=True)
    y, X = patsy.dmatrices(r_formula, data=df3)
    y = y.T[0]
    lassocv.fit(X, y)
    lassocv.score(X, y)

    ridgecv = linear_model.RidgeCV(normalize=True)
    ridgecv.fit(X, y)
    ridgecv.score(X, y)

    encv = linear_model.ElasticNetCV(normalize=True)
    encv.fit(X, y)
    encv.score(X, y)

# <codecell>
