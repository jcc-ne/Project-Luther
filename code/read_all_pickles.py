import pandas as pd
import glob
import matplotlib.pyplot as plt
import numpy as np

dfs = []
pickles = glob.glob('*.pickle')
for p in pickles:
    dfs.append(pd.read_pickle(p))

df = pd.concat(dfs)
df = df.dropna()
df['Release Date'] = pd.to_datetime(df['Release Date'], errors='coerce')
df['Month'] = df['Release Date'].apply(lambda x: x.month)
df['WoY'] = df['Release Date'].apply(lambda x: x.isocalendar()[1])


def assign_grp(ind, ind_grp):
    for i, r in enumerate(ind_grp):
        if ind in r:
            return i


def budget_groups(budget, budgets):
    budg_quantiles = [np.percentile(budgets, 25),
                      np.percentile(budgets, 50),
                      np.percentile(budgets, 75),
                      np.percentile(budgets, 90)]
    for i, q in enumerate(budg_quantiles):
        if budget < q:
            return i
    return 4


# -- Month group operation
dg_m = df.groupby('Month').agg({'Domestic:': sum,
                                'Budget': sum,
                                'Title': 'count'})
dg_m = dg_m / dg_m.max()
dg_m.plot(kind='bar', alpha=0.6)
plt.legend(loc='lower right')

ind = dg_m.Title.sort_values().index
ind_grp = np.array_split(ind, 10)
df['quantity_m_index'] = df.WoY.apply(lambda x: assign_grp(x, ind_grp))

ind = dg_m.Title.sort_values().index
ind_grp = np.array_split(ind, 10)
df['quantity_m_index'] = df.WoY.apply(lambda x: assign_grp(x, ind_grp))

ind = dg_m.Budget.sort_values().index
ind_grp = np.array_split(ind, 10)
df['bigbudget_m_index'] = df.WoY.apply(lambda x: assign_grp(x, ind_grp))

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

# -- budget_groups
df['budget_group'] = df.Budget.apply(lambda x: budget_groups(x, df.Budget))


dg_w = dg_w / dg_w.max()
dg_w.plot(kind='bar', alpha=0.6)
plt.legend(loc='lower right')
