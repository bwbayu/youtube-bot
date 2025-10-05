import pandas as pd
import random
import numpy as np
import torch
from sklearn.model_selection import train_test_split

# Set seed to make random operations reproducible across runs
def set_seed(seed_value=42):
    random.seed(seed_value)
    np.random.seed(seed_value)
    torch.manual_seed(seed_value)
    torch.cuda.manual_seed(seed_value)
    torch.cuda.manual_seed_all(seed_value)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
SEED = 42
set_seed(SEED)

# read data
df = pd.read_csv("data/data_judol_balanced.csv")
df['label'] = df['label'].astype(int)
print(df.info())

# separate training data and label
y = df['label']
X = df.drop(columns=['label', 'label_category'])

# split dataset to train,valid,test with ratio 8:1:1
X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.2, random_state=SEED)
X_valid, X_test, y_valid, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=SEED)

print(f"Jumlah Training Data: {len(X_train)}")
print(y_train.value_counts())
print("========================================")
print(f"Jumlah Validation Data: {len(X_valid)}")
print(y_valid.value_counts())
print("========================================")
print(f"Jumlah Testing Data: {len(X_test)}")
print(y_test.value_counts())

# save to csv
df_train = pd.concat([X_train, y_train], axis=1).reset_index(drop=True)
df_train.to_csv("data/data_train_judol.csv", index=False)
df_valid = pd.concat([X_valid, y_valid], axis=1).reset_index(drop=True)
df_valid.to_csv("data/data_valid_judol.csv", index=False)
df_test = pd.concat([X_test, y_test], axis=1).reset_index(drop=True)
df_test.to_csv("data/data_test_judol.csv", index=False)