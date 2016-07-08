# <codecell>
import pandas as pd
import glob
import matplotlib.pyplot as plt
import numpy as np
import statsmodels.formula.api as smf
import seaborn as sns
import re


# <codecell>
def assign_grp(ind, ind_grp):
    for i, r in enumerate(ind_grp):
        if ind in r:
            return i


def budget_groups(budget, budgets, n_percentiles):
    budg_percentiles = []
    for i in np.linspace(0, 100, n_percentiles+1):
        budg_percentiles.append(np.percentile(budgets, i))
    budg_percentiles.pop(0)
    for i, q in enumerate(budg_percentiles):
        if budget < q:
            return i
    return n_percentiles - 1


dfs = []
pickles = glob.glob('*.pickle')
for p in pickles:
    dfs.append(pd.read_pickle(p))

df = pd.concat(dfs)
df = df.dropna()
df['Release Date'] = pd.to_datetime(df['Release Date'], errors='coerce')
df['Month'] = df['Release Date'].apply(lambda x: x.month)
df['WoY'] = df['Release Date'].apply(lambda x: x.isocalendar()[1])
df = df.rename(columns={'Domestic:': 'Domestic'})
df.loc[:, 'Domestic_norm'] = df['Domestic'] / df['Domestic'].max()
df.loc[:, 'Budget_norm'] = df['Budget'] / df['Budget'].max()

# <codecell>
# -- Month group operation
dg_m = df.groupby('Month').agg({'Domestic': sum,
                                'Budget': sum,
                                'Title': 'count'})
df.loc[:, 'total_m_titles'] = df.Month.apply(lambda x: dg_m.loc[x, 'Domestic'])
df.loc[:, 'total_budget'] = df.Month.apply(lambda x: dg_m.loc[x, 'Budget'])

ind = dg_m.Title.sort_values().index
ind_grp = np.array_split(ind, 4)
df.loc[:, 'quantity_m_index'] = df.Month.apply(lambda x: assign_grp(x, ind_grp))

ind = dg_m.Budget.sort_values().index
ind_grp = np.array_split(ind, 4)
df.loc[:, 'bigbudget_m_index'] = df.Month.apply(
    lambda x: assign_grp(x, ind_grp))

# <codecell>
dg_m = dg_m / dg_m.max()
dg_m2 = dg_m.copy()
dg_m2.columns = ['Norm. Domestic', 'Norm. Budget', 'Count #']
dg_m2.plot(kind='bar', alpha=0.6)
plt.legend(loc='upper left')

# <codecell>
# -- Week of the year group operation
dg_w = df.groupby('WoY', as_index=False).agg({'Domestic:': sum,
                                              'Budget': sum,
                                              'Title': 'count'})
dg_w['avgBudget'] = dg_w['Budget'] / dg_w['Title']
dg_w['avgDomestic'] = dg_w['Domestic:'] / dg_w['Title']
ind = dg_w.Budget.sort_values().index
ind_grp = np.array_split(ind, 10)


dg_w['bigbudget_w_index'] = dg_w.WoY.apply(lambda x: assign_grp(x, ind_grp))
df['bigbudget_w_index'] = df.WoY.apply(lambda x: assign_grp(x, ind_grp))

ind = dg_w.Title.sort_values().index
ind_grp = np.array_split(ind, 10)
df['quantity_w_index'] = df.WoY.apply(lambda x: assign_grp(x, ind_grp))


# -- season group operation
season_groups = [(1, 2, 3), (4, 5, 6), (7, 8, 9), (10, 11, 12)]
df['Season'] = df['Month'].apply(lambda x: assign_grp(x, season_groups))
dg_s = df.groupby('Season', as_index=False).agg({'Domestic:': sum,
                                                 'Budget': sum,
                                                 'Title': 'count'})
ind = dg_s.Budget.sort_values().index
ind_grp = np.array_split(ind, 4)


dg_s['bigbudget_s_index'] = dg_s.Season.apply(lambda x: assign_grp(x, ind_grp))
df['bigbudget_s_index'] = df.Season.apply(lambda x: assign_grp(x, ind_grp))

ind = dg_s.Title.sort_values().index
ind_grp = np.array_split(ind, 4)
df['quantity_s_index'] = df.Season.apply(lambda x: assign_grp(x, ind_grp))


dg_w = dg_w / dg_w.max()
dg_w.plot(kind='bar', alpha=0.6)

# <codecell>
# -- budget_groups
n_percentiles = 3
df['budget_group'] = df.Budget.apply(lambda x:
                                     budget_groups(x, df.Budget, n_percentiles))


df_buds = []
for i in range(0, n_percentiles):
    df_buds.append(df[df.budget_group == i])

for dfb in df_buds:
    print dfb.budget_group.unique(),
    print dfb.budget_group.count()
    print ("bigbuget time corr DomesticGross",
           dfb.corr()['bigbudget_m_index']['Domestic'])
    print ("bigquantity time corr DomesticGross",
           dfb.corr()['quantity_m_index']['Domestic'])
    model = smf.ols('Domestic_norm ~ '
                    'Budget_norm'
                    '+ total_m_titles'
                    '+ total_budget'
                    , data=dfb)
    fit = model.fit()
    print fit.rsquared


# <codecell>
model = smf.ols('Domestic_norm ~'
                ' Budget_norm '
                '+ bigbudget_m_index '
                '+ quantity_m_index'
                , data=df)

fit = model.fit()
print fit.summary()

# <codecell>
model = smf.ols('Domestic_norm ~'
                ' Budget_norm '
                '+ total_m_titles'
                '+ total_budget'
                , data=df)

fit = model.fit()
print fit.summary()

# <codecell>
for g in df.groupby('Genre:'):
    print g[0], g[1].shape[0]
    print g[1].corr()['bigbudget_m_index']['Domestic:']
    print g[1].corr()['quantity_m_index']['Domestic:']
    print

for g in df.groupby('MPAA'):
    print g[0], g[1].shape[0]
    print g[1].corr()['bigbudget_m_index']['Domestic:']
    print g[1].corr()['quantity_m_index']['Domestic:']
    print

all_genres = df['Genre:'].unique()
dummy_genres = {}
for g in all_genres:
    genres = [g2.strip() for g2 in g1.strip().split(' ')
              for g1 in g.split('/')]
    for gg in genres:
        dummy_g = 'genre_{}'.format(gg)
        dummy_genres[dummy_g] = dummy_genres.get(dummy_g, 0) + 1


def get_dummies_str(ds, prefix=''):
    split1 = ds.str.strip().str.split('/', expand=True)
    split2 = split1[0].str.strip().str.split(' ', expand=True)
    df_dum = pd.concat([split1, split2], axis=1)
    df_dum.columns = [0, 1, 2, 3]
    for c in df_dum:
        df_dum[c] = df_dum[c].str.strip()
        df_dum[c] = df_dum[c].str.replace('-', '_')
    dummies = pd.get_dummies(df_dum[[1, 2, 3]].stack(),
                             prefix=prefix).groupby(level=0).sum()
#     cols = ['{}_{}'.format(prefix, c).strip('_') for c in dummies.columns]
#     dummies.columns = cols
    return dummies


def get_dummies(ds, prefix=''):
    dummies = pd.get_dummies(df_dum[[1, 2, 3]].stack(),
                             prefix=prefix).groupby(level=0).sum()
#     cols = ['{}_{}'.format(prefix, c).strip('_') for c in dummies.columns]
#     dummies.columns = cols
    return dummies


# <codecell>
df = df.reset_index()
df_dum = get_dummies(df['Genre:'], prefix='genre')


df2 = pd.concat([df, df_dum], axis=1)

r_formula = ' + '.join(list(df2.columns[df2.columns.str.startswith('genre_')]))
r_formula =( 'Domestic_norm ~'
            ' Budget_norm '
                '+ total_budget'
                '+ total_m_titles + ' + r_formula
            )


model = smf.ols(r_formula
    #                 '+ bb_1'
#                 '+ bb_2'
#                 '+ bb_3'
#                 '+ bb_4'
#                 '+ quantity_m_index'
                , data=df2)

fit = model.fit()
print fit.summary()

