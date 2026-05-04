# AMP®-Parkinson's Disease Progression Prediction (2023)

## Competition Brief

SMAPE (Symmetric Mean Absolute Percentage Error)

---

## Top Solutions Analysis

### 1st Place - Connecting Dotts (Dmitry Gordeev et al.)

```python
final_prediction = (lgb_pred + nn_pred) / 2
```

### 2nd Place - No Luck, All Skill

### 3rd Place - Hajime Tamura

### 4th/5th Place - Ambrosm (#5: Find the Control Group)

### 9th Place - Makotu

### 13th Place - FNOA

### 43rd Place - Wojciech Victor Fulmyk (Top 3% Silver)

```python
```

### 89th Place - Giba (Non-Leaky Solution)

---

## Common Techniques Across Solutions

### 1. Feature Engineering Patterns

```python
protein_stats = train.groupby('patient_id')['protein'].agg([
    'mean', 'median', 'std', 'min', 'max'
])

peptide_stats = train.groupby('patient_id')['peptide'].agg([
    'mean', 'count', 'nunique'
])
```

### 2. Model Selection Insights

- Neural Networks / MLP

### 3. Validation Strategies

```python
from sklearn.model_selection import GroupKFold

gkf = GroupKFold(n_splits=5)
for train_idx, val_idx in gkf.split(X, y, groups=patient_ids):
```

### 4. Data Leakage Prevention

---

## Code Templates

### Basic Feature Engineering

```python
import pandas as pd
import numpy as np

def create_protein_features(train_proteins, test_proteins):
    def process(df):
        stats = df.groupby('patient_id')['NPX'].agg([
            ('protein_mean', 'mean'),
            ('protein_std', 'std'),
            ('protein_min', 'min'),
            ('protein_max', 'max')
        ]).reset_index()
        return stats

    train_stats = process(train_proteins)
    test_stats = process(test_proteins)

    return train_stats, test_stats

def create_peptide_features(train_peptides, test_peptides):
    def process(df):
        stats = df.groupby('patient_id')['PeptideAbundance'].agg([
            ('peptide_mean', 'mean'),
            ('peptide_std', 'std'),
            ('peptide_count', 'count')
        ]).reset_index()
        return stats

    train_stats = process(train_peptides)
    test_stats = process(test_peptides)

    return train_stats, test_stats

def create_time_features(train_clinical, test_clinical):
    def process(df):
        df = df.copy()
        df['visit_month'] = df['visit_month'].astype(int)
        df['pred_month'] = df['visit_month'] + df['updrs_test_month']

        df['months_since_baseline'] = df.groupby('patient_id')['visit_month'].transform(lambda x: x - x.min())

        return df

    return process(train_clinical), process(test_clinical)
```

### Model Training Template

```python
import lightgbm as lgb
from sklearn.model_selection import GroupKFold
from sklearn.metrics import mean_absolute_error

def smape(y_true, y_pred):
    return 100 * np.mean(2 * np.abs(y_pred - y_true) / (np.abs(y_true) + np.abs(y_pred) + 1e-8))

def train_lightgbm(X_train, y_train, groups, params=None):
    if params is None:
        params = {
            'objective': 'regression',
            'metric': 'mae',
            'learning_rate': 0.01,
            'num_leaves': 31,
            'max_depth': -1,
            'feature_fraction': 0.8,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'verbose': -1
        }

    gkf = GroupKFold(n_splits=5)
    models = []
    scores = []

    for train_idx, val_idx in gkf.split(X_train, y_train, groups=groups):
        X_tr, X_val = X_train.iloc[train_idx], X_train.iloc[val_idx]
        y_tr, y_val = y_train.iloc[train_idx], y_train.iloc[val_idx]

        train_data = lgb.Dataset(X_tr, label=y_tr)
        val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)

        model = lgb.train(
            params,
            train_data,
            num_boost_round=10000,
            valid_sets=[train_data, val_data],
            callbacks=[lgb.early_stopping(100), lgb.log_evaluation(0)]
        )

        pred = model.predict(X_val)
        score = smape(y_val, pred)

        models.append(model)
        scores.append(score)

    print(f'Average SMAPE: {np.mean(scores):.2f}')

    return models, scores

# models, scores = train_lightgbm(X_train, y_train, patient_ids)
```

### Neural Network Template

```python
import tensorflow as tf
from sklearn.preprocessing import StandardScaler

def create_nn_model(input_dim, hidden_units=[256, 128, 64]):
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(input_dim,)),
    ])

    for units in hidden_units:
        model.add(tf.keras.layers.Dense(
            units,
            activation='relu',
            kernel_regularizer=tf.keras.regularizers.l2(0.01)
        ))
        model.add(tf.keras.layers.Dropout(0.3))
        model.add(tf.keras.layers.BatchNormalization())

    model.add(tf.keras.layers.Dense(1, activation='linear'))

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
        loss='mae',
        metrics=['mae']
    )

    return model

def train_nn(X_train, y_train, groups, epochs=100, batch_size=32):
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)

    gkf = GroupKFold(n_splits=5)
    models = []
    scores = []

    for train_idx, val_idx in gkf.split(X_train_scaled, y_train, groups=groups):
        X_tr, X_val = X_train_scaled[train_idx], X_train_scaled[val_idx]
        y_tr, y_val = y_train.iloc[train_idx], y_train.iloc[val_idx]

        model = create_nn_model(X_train.shape[1])

        early_stop = tf.keras.callbacks.EarlyStopping(
            monitor='val_loss',
            patience=10,
            restore_best_weights=True
        )

        history = model.fit(
            X_tr, y_tr,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=[early_stop],
            verbose=0
        )

        pred = model.predict(X_val).flatten()
        score = smape(y_val, pred)

        models.append((model, scaler))
        scores.append(score)

    print(f'Average SMAPE: {np.mean(scores):.2f}')

    return models, scores
```

### Ensemble Template

```python
def ensemble_predictions(lgb_models, nn_models, X_test):
    lgb_preds = np.mean([model.predict(X_test) for model in lgb_models], axis=0)

    _, scaler = nn_models[0]
    X_test_scaled = scaler.transform(X_test)
    nn_preds = np.mean([
        model.predict(X_test_scaled).flatten()
        for model, _ in nn_models
    ], axis=0)

    final_pred = (lgb_preds + nn_preds) / 2

    return final_pred
```

---

## Best Practices

### 1. Data Understanding

### 2. Feature Engineering Guidelines

**DOs**

**DON'Ts**

### 3. Model Selection Strategy

### 4. Validation Strategy

```python
from sklearn.model_selection import GroupKFold

gkf = GroupKFold(n_splits=5)
for fold, (train_idx, val_idx) in enumerate(gkf.split(X, y, groups=patient_ids)):
    print(f'Fold {fold + 1}')
```

```python
from sklearn.model_selection import TimeSeriesSplit

tscv = TimeSeriesSplit(n_splits=5)
for fold, (train_idx, val_idx) in enumerate(tscv.split(X)):
```

### 5. Common Pitfalls

### 6. Domain Knowledge Integration

### 7. Hyperparameter Tuning

```python
params = {
    'bagging_freq': 5,
}
```

```python
```

---

## Key Takeaways

---

## Resources

### Official Writeups
- [1st Place Solution - Connecting Dotts](https://www.kaggle.com/competitions/amp-parkinsons-disease-progression-prediction/writeups/connecting-dotts-1st-place-solution)
- [2nd Place Solution - No Luck, All Skill](https://www.kaggle.com/competitions/amp-parkinsons-disease-progression-prediction/writeups/no-luck-all-skill-2nd-place-solution)
- [3rd Place Solution - Hajime Tamura](https://www.kaggle.com/competitions/amp-parkinsons-disease-progression-prediction/writeups/hajime-tamura-3rd-place-solution)
- [5th Place Solution - Ambrosm](https://www.kaggle.com/competitions/amp-parkinsons-disease-progression-prediction/writeups/ambrosm-5-find-the-control-group)
- [9th Place Solution - Makotu](https://www.kaggle.com/competitions/amp-parkinsons-disease-progression-prediction/writeups/makotu-9th-place-solution)
- [13th Place Solution - FNOA](https://www.kaggle.com/competitions/amp-parkinsons-disease-progression-prediction/writeups/fnoa-13th-place-solution)
- [43rd Place Solution - Wojciech Victor Fulmyk](https://www.kaggle.com/competitions/amp-parkinsons-disease-progression-prediction/writeups/wojciech-victor-fulmyk-43rd-top-3-silver-medal-sol)
- [89th Place Solution - Giba (Non-Leaky)](https://www.kaggle.com/competitions/amp-parkinsons-disease-progression-prediction/writeups/giba-top-89-non-leaky-solution)

### External Resources
- [H2O.ai Blog: Navigating the Parkinson's Disease Prediction Challenge with AI](https://h2o.ai/blog/2023/winners-insight-navigating-the-parkinsons-disease-prediction-challenge-with-ai/)

### Competition Pages
- [Main Competition Page](https://www.kaggle.com/competitions/amp-parkinsons-disease-progression-prediction)
- [Data Description](https://www.kaggle.com/competitions/amp-parkinsons-disease-progression-prediction/data)
- [Discussion Forum](https://www.kaggle.com/c/amp-parkinsons-disease-progression-prediction/discussion)

### Code Notebooks
- [LightGBM Starter with Added Features](https://www.kaggle.com/code/sijovm/lightgbm-starter-with-added-features)
- [XGB Baseline with Added Features](https://www.kaggle.com/code/sijovm/xgb-baseline-with-added-features)
- [AMP® - PDPP EDA + TF Model](https://www.kaggle.com/code/callmewenhao/amp-pdpp-eda-tf-model)
- [AMP® - PDPP EDA](https://www.kaggle.com/code/gunesevitan/amp-pdpp-eda)
