# -*- coding: utf-8 -*-
"""kaggle.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1LLVDKa4AfudTqyKQSLVkJyg5ZU-AqkWw
"""

!pip install boruta

import pandas as pd
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, GradientBoostingClassifier
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import StratifiedKFold
from boruta import BorutaPy
from sklearn import preprocessing
import numpy as np

dataset = pd.read_csv("train.csv")

dataset.head()

y = dataset['SalePrice'].values
X = dataset.drop('SalePrice', axis=1)
le = preprocessing.LabelEncoder()

for column in X:
  if X[column].isnull().values.any():
    if X[column].dtype == 'float64':
      X[column].fillna(0.0, inplace=True)
    else:
      X[column].fillna('', inplace=True)
      X[[column]] = X[[column]].apply(le.fit_transform)

X = X.apply(le.fit_transform)

X.head()

x_labels = X.columns[1:]
X = X.values[:, 1:]

rf = RandomForestClassifier(n_jobs=-1, class_weight='balanced', max_depth=5)

# define Boruta feature selection method
feat_selector = BorutaPy(rf, n_estimators='auto', verbose=2, random_state=1)

# find all relevant features - 5 features should be selected
feat_selector.fit(X, y)

# check selected features - first 5 features are selected
feat_selector.support_

# check ranking of features
feat_selector.ranking_

# call transform() on X to filter it down to selected features
X_filtered = feat_selector.transform(X)

features_selected = []
index_selected = []
counter = 0
# for columns in dataset:
#   print(columns)
for index, label in enumerate(x_labels):
  if feat_selector.ranking_[index] < 50:
    features_selected.append(label)
    index_selected.append(index)

X = X[:, index_selected]

skf = StratifiedKFold(n_splits=4)
skf.get_n_splits(X, y)

clfs = [RandomForestClassifier(n_estimators=100, n_jobs=-1, criterion='gini'),
        RandomForestClassifier(n_estimators=100, n_jobs=-1, criterion='entropy'),
        ExtraTreesClassifier(n_estimators=100, n_jobs=-1, criterion='gini'),
        ExtraTreesClassifier(n_estimators=100, n_jobs=-1, criterion='entropy'),
        GradientBoostingClassifier(learning_rate=0.1, subsample=0.8, max_depth=6, n_estimators=50)]

dataset_blend_train = np.zeros((X.shape[0], len(clfs)))

for j, clf in enumerate(clfs):
  print(clf)
  count = 0
  for train, test in skf.split(X, y):
      print("round {}".format(count))
      X_train = X[train]
      y_train = y[train]
      X_test = X[test]
      y_test = y[test]
      clf.fit(X_train, y_train)
      y_submission = clf.predict(X_test)
      dataset_blend_train[test, j] = y_submission
      count += 1

final_linear = LinearRegression()
final_linear.fit(dataset_blend_train, y)

test_X = pd.read_csv("test.csv")
for column in test_X:
  if test_X[column].isnull().values.any():
    if test_X[column].dtype == 'float64':
      test_X[column].fillna(0.0, inplace=True)
    else:
      test_X[column].fillna('', inplace=True)
      test_X[[column]] = test_X[[column]].apply(le.fit_transform)
test_X = test_X.apply(le.fit_transform)

test_X = test_X.values[:, 1:]
test_X = test_X[:, index_selected]

dataset_blend_test = np.zeros((test_X.shape[0], len(clfs)))
for j, clf in enumerate(clfs):
  print(clf)
  clf.fit(X, y)
  y_submission = clf.predict(test_X)
  dataset_blend_test[:, j] = y_submission

final_linear.predict(dataset_blend_test)

output = pd.DataFrame()

output[['Id']] = pd.read_csv("test.csv")[['Id']]

output['SalePrice'] = final_linear.predict(dataset_blend_test)

output.to_csv('submission.csv', index=False)
