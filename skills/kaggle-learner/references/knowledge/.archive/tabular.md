# Tabular Knowledge Base

> Last updated: 2025-01-22
> Source count: 1

## Original Summaries

### CMI - Problematic Internet Use (2024) - 2025-01-22
**Source:** [Kaggle Competition](https://www.kaggle.com/competitions/child-mind-institute-problematic-internet-use)
**Key Techniques:**

---

### CMI - Problematic Internet Use (2024)

---

## Code Templates

```python
import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.model_selection import StratifiedKFold

def train_intermediate_target_model(X_train, y_train_total, X_test):
    """
    """
    train_df = X_train.copy()
    train_df['sii'] = (y_train_total > 30).astype(int) + \
                      (y_train_total > 50).astype(int) + \
                      (y_train_total > 80).astype(int)

    # 10-fold stratified KFold
    n_folds = 10
    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=42)

    oof_preds = np.zeros(len(X_train))
    test_preds = np.zeros(len(X_test))

    for fold, (train_idx, val_idx) in enumerate(skf.split(X_train, train_df['sii'])):
        X_tr, X_val = X_train.iloc[train_idx], X_train.iloc[val_idx]
        y_tr, y_val = y_train_total.iloc[train_idx], y_train_total.iloc[val_idx]

        model = LGBMRegressor(
            n_estimators=1000,
            learning_rate=0.05,
            num_leaves=31,
            max_depth=-1,
        )

        model.fit(X_tr, y_tr, eval_set=[(X_val, y_val)],
                  early_stopping_rounds=100, verbose=False)

        oof_preds[val_idx] = model.predict(X_val)
        test_preds += model.predict(X_test) / n_folds

    return oof_preds, test_preds

def convert_total_to_sii(pred_total):
    """
    """
    pred_sii = np.zeros(len(pred_total))
    pred_sii[pred_total > 30] = 1
    pred_sii[pred_total > 50] = 2
    pred_sii[pred_total > 80] = 3
    return pred_sii.astype(int)
```

```python
import numpy as np
from lightgbm import LGBMRegressor

def multi_seed_prediction(X_train, y_train, X_test, seeds=[42, 123, 456, 789, 1011]):
    """
    """
    test_preds_all = []

    for seed in seeds:
        model = LGBMRegressor(
            n_estimators=1000,
            learning_rate=0.05,
            random_state=seed
        )

        model.fit(X_train, y_train)
        test_preds_all.append(model.predict(X_test))

    test_preds_mean = np.mean(test_preds_all, axis=0)

    return test_preds_mean

def multi_fold_multi_seed(X_train, y_train, X_test, n_folds=5, seeds=10):
    """
    """
    n_folds = 5

    test_preds = []

    for seed in seeds:
        for fold in range(n_folds):
            model = LGBMRegressor(
                n_estimators=1000,
                random_state=seed + fold * 100
            )
            # ... train and predict
            test_preds.append(model.predict(X_test))

    return np.mean(test_preds, axis=0)
```

### Pseudo Labeling

```python
import numpy as np
import pandas as pd

def pseudo_labeling(X_train, y_train, X_missing, n_iterations=3):
    """
    """
    has_label = ~y_train.isna()
    X_labeled = X_train[has_label]
    y_labeled = y_train[has_label]
    X_unlabeled = X_train[~has_label]

    model = LGBMRegressor(random_state=42)
    model.fit(X_labeled, y_labeled)

    for iteration in range(n_iterations):
        pseudo_labels = model.predict(X_unlabeled)

        X_combined = pd.concat([X_labeled, X_unlabeled])
        y_combined = pd.concat([y_labeled, pd.Series(pseudo_labels, index=X_unlabeled.index)])

        model = LGBMRegressor(random_state=42 + iteration)
        model.fit(X_combined, y_combined)

    return model

def cv_with_pseudo(X_train, y_train, X_missing):
    """
    """
    has_label = ~y_train.isna()
    X_labeled = X_train[has_label]
    y_labeled = y_train[has_label]

    pseudo_model = pseudo_labeling(X_train, y_train, X_missing)

    from sklearn.model_selection import cross_val_score
    cv_model = LGBMRegressor(random_state=42)
    cv_scores = cross_val_score(cv_model, X_labeled, y_labeled, cv=5)

    return pseudo_model, cv_scores
```

### Tweedie Loss

```python
import lightgbm as lgb

def train_with_tweedie_loss(X_train, y_train, X_val, y_val):
    """
    """
    train_data = lgb.Dataset(X_train, label=y_train)
    val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)

    params = {
        'objective': 'tweedie',
        'metric': 'rmse',
        'learning_rate': 0.05,
        'num_leaves': 31,
        'max_depth': -1,
        'verbose': -1
    }

    model = lgb.train(
        params,
        train_data,
        num_boost_round=1000,
        valid_sets=[val_data],
        early_stopping_rounds=100,
        verbose_eval=False
    )

    return model
```

```python
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

def extract_time_series_cluster_features(time_series_data, n_clusters=5):
    """
    """
    n_samples = time_series_data.shape[0]

    ts_flat = time_series_data.reshape(n_samples, -1)

    scaler = StandardScaler()
    ts_scaled = scaler.fit_transform(ts_flat)

    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(ts_scaled)

    cluster_distances = kmeans.transform(ts_scaled)

    cluster_features = pd.DataFrame({
        f'ts_cluster_dist_{i}': cluster_distances[:, i]
        for i in range(n_clusters)
    })
    cluster_features['ts_cluster_label'] = cluster_labels

    return cluster_features

# cluster_features = extract_time_series_cluster_features(time_series_data)
# X_final = pd.concat([tabular_features, cluster_features], axis=1)
```

```python
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

def clean_features(X, threshold=0.99):
    """
    """
    corr_matrix = X.corr().abs()

    upper_tri = corr_matrix.where(
        np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
    )

    to_drop = [column for column in upper_tri.columns if any(upper_tri[column] > threshold)]

    X_cleaned = X.drop(columns=to_drop)

    return X_cleaned, to_drop

def pca_reduction(X_train, X_test, variance_ratio=0.95):
    """
    """
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # PCA
    pca = PCA(n_components=variance_ratio)
    X_train_pca = pca.fit_transform(X_train_scaled)
    X_test_pca = pca.transform(X_test_scaled)

    print(f"Original features: {X_train.shape[1]}")
    print(f"PCA components: {X_train_pca.shape[1]}")
    print(f"Variance explained: {pca.explained_variance_ratio_.sum():.4f}")

    return X_train_pca, X_test_pca, pca
```

### GBM Ensemble (LGBM + XGBoost + CatBoost)

```python
import numpy as np
from lightgbm import LGBMRegressor
from xgboost import XGBRegressor
from catboost import CatBoostRegressor

def train_gbm_ensemble(X_train, y_train, X_test):
    """
    """
    models = []
    test_preds = []

    # 1. LightGBM
    lgbm = LGBMRegressor(
        n_estimators=1000,
        learning_rate=0.05,
        num_leaves=31,
        max_depth=-1,
        random_state=42,
        verbose=-1
    )
    lgbm.fit(X_train, y_train)
    models.append(lgbm)
    test_preds.append(lgbm.predict(X_test))

    # 2. XGBoost
    xgb = XGBRegressor(
        n_estimators=1000,
        learning_rate=0.05,
        max_depth=6,
        random_state=42,
        verbosity=0
    )
    xgb.fit(X_train, y_train)
    models.append(xgb)
    test_preds.append(xgb.predict(X_test))

    # 3. CatBoost
    cat = CatBoostRegressor(
        iterations=1000,
        learning_rate=0.05,
        depth=6,
        random_state=42,
        verbose=False
    )
    cat.fit(X_train, y_train)
    models.append(cat)
    test_preds.append(cat.predict(X_test))

    ensemble_pred = np.mean(test_preds, axis=0)

    return models, ensemble_pred

def weighted_gbm_ensemble(X_train, y_train, X_test, weights=[0.4, 0.3, 0.3]):
    """
    weights: [lgbm, xgb, cat]
    """
    lgbm = LGBMRegressor(random_state=42, verbose=-1).fit(X_train, y_train)
    xgb = XGBRegressor(random_state=42, verbosity=0).fit(X_train, y_train)
    cat = CatBoostRegressor(random_state=42, verbose=False).fit(X_train, y_train)

    pred_lgbm = lgbm.predict(X_test)
    pred_xgb = xgb.predict(X_test)
    pred_cat = cat.predict(X_test)

    ensemble_pred = (
        weights[0] * pred_lgbm +
        weights[1] * pred_xgb +
        weights[2] * pred_cat
    )

    return ensemble_pred
```

```python
import numpy as np

def augment_data_with_noise(X_train, y_train, n_augmented=2, nan_ratio=0.1, noise_std=0.01):
    """
    """
    X_aug_list = [X_train.copy()]
    y_aug_list = [y_train.copy()]

    for _ in range(n_augmented):
        X_aug = X_train.copy()

        mask = np.random.random(X_aug.shape) < nan_ratio
        X_aug[mask] = np.nan

        noise = np.random.normal(0, noise_std, X_aug.shape)
        X_aug = X_aug + noise

        X_aug_list.append(X_aug)
        y_aug_list.append(y_train.copy())

    X_final = pd.concat(X_aug_list, axis=0, ignore_index=True)
    y_final = pd.concat(y_aug_list, axis=0, ignore_index=True)

    return X_final, y_final

# X_aug, y_aug = augment_data_with_noise(X_train, y_train)
# model = LGBMRegressor().fit(X_aug, y_aug)
```

```python
import numpy as np
from scipy.optimize import minimize

def optimize_thresholds(y_true, y_pred_total):
    """
    """
    def qwk_loss(thresholds):
        t1, t2, t3 = thresholds
        pred_sii = np.zeros(len(y_pred_total))
        pred_sii[y_pred_total > t1] = 1
        pred_sii[y_pred_total > t2] = 2
        pred_sii[y_pred_total > t3] = 3

        from sklearn.metrics import cohen_kappa_score
        kappa = cohen_kappa_score(y_true, pred_sii, weights='quadratic')

    x0 = [30, 50, 80]

    bounds = [(0, 40), (40, 60), (60, 100)]
    constraints = {'type': 'ineq', 'fun': lambda x: x[1] - x[0]}

    result = minimize(qwk_loss, x0, bounds=bounds, constraints=constraints)

    optimal_thresholds = result.x
    print(f"Optimal thresholds: {optimal_thresholds}")

    return optimal_thresholds

def apply_specific_thresholds(pred_total):
    """
    """
    pred_sii = np.zeros(len(pred_total))

    pred_sii[pred_total > 30] = 1
    pred_sii[pred_total > 50] = 2
    pred_sii[pred_total > 80] = 3

    # if has_cgas_data and cgas_score > 80:
    #     pred_sii = 3

    return pred_sii.astype(int)
```

---

## Best Practices

|------|---------|------|

**Quadratic Weighted Kappa (QWK)：**

|------|------|

|------|---------|---------|

|------|------|------|

```python
```

|------|---------|------|

---

#### 1st Place - Lennart Haupts

```
LGBMRegressor
+ XGBoost Regressors
+ CatBoostRegressor
+ ExtraTreesRegressor
```

#### 3rd Place

```python
for seed in range(100):
    for fold in range(5):
        model = LGBMRegressor(random_state=seed)
        train_and_evaluate()
```

#### 5th Place

```
LGBM + CatBoost + XGBoost
+ Neural Network
→ Ensemble
```

#### 7th Place

#### 4th Place (underfit squad)

|------|---------|------|
| **GBM Ensemble** | 1st, 5th, 7th | LGBM + XGBoost + CatBoost |

|------|-----------|------|

|------|-----------|------|

|------|-----------|------|

|------|-----------|------|

|------|---------|------|

|------|-------------|

|------|-------------|
| **5th** | Pseudo Labeling |

|------|---------|------|

|------|------|

---

## Metadata
| Source | Date | Tags |
|--------|------|------|
