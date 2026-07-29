import pandas as pd

df = pd.read_csv('Sample - Superstore.csv', encoding='latin-1')
print(df.shape)

df = df.rename(columns={
    'Order Date': 'ORDER DATE',
    'Customer ID': 'Customer #',
    'Sub-Category': 'Sub/Category',
    'Postal Code': 'Postal Code ',
})
print(df.columns.tolist())

import numpy as np
rng = np.random.default_rng(42)

sales = df['Sales'].map(lambda v: f'{v:,.2f}')   # every value becomes a string with commas
idx = df.index.to_numpy()
rng.shuffle(idx)

sales.loc[idx[:60]] = ('$' + sales.loc[idx[:60]]).to_numpy() # 60 rows get a currency symbol
sales.loc[idx[60:100]]  = 'N/A'                        # 40 rows unparseable
sales.loc[idx[100:130]] = '-'                          # 30 more, different flavor

df['Sales'] = sales
print(df['Sales'].dtype)
print(df['Sales'].sample(10, random_state=1).tolist())

pc_rows = rng.choice(df.index, size=int(len(df) * 0.05), replace=False)
df.loc[pc_rows, 'Postal Code '] = np.nan

sales_rows = rng.choice(df.index, size=25, replace=False)
df.loc[sales_rows, 'Sales'] = np.nan

print(df.isna().sum())

dupes = df.sample(n=200, random_state=7)
df = pd.concat([df, dupes], ignore_index=True)
print(df.shape)
print(df.duplicated().sum())

junk = [
    'Superstore Sales Export',
    'Generated: 2026-07-24 09:14:22',
    'CONFIDENTIAL - Internal Use Only',
    '',
]

with open('messy_sales.csv', 'w', newline='', encoding='latin-1') as f:
    for line in junk:
        f.write(line + '\n')
    df.to_csv(f, index=False)

print('wrote messy_sales.csv')