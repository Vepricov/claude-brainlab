# Child Mind Institute - Detect Sleep States (2023)
> Last updated: 2026-01-23
> Source count: 1
---

### Child Mind Institute - Detect Sleep States (2023)

- 1st Place: shimacos vs sakami vs kami - Private LB: **0.852**
- 2nd Place: K-Mat - Private LB: ~0.850
- 3rd Place: cucutzik - Private LB: ~0.849

**1st Place - shimacos vs sakami vs kami (kami, sakami0000, shimacos)**

**2nd Place - K-Mat**

**3rd Place - cucutzik**

**4th Place - RSI (Recurring Sleep Inertia)**

**5th Place - Andris (Andris Apinis)**

**6th Place - CPMP (Cyprien)</

**7th Place - maxplotlib (Max)**

**8th Place - KaggleRank**

**9th Place - DeepSleep**

**10th Place - SleepTracker (Ali**

---

### Child Mind Institute - Detect Sleep States (2023) - 2025-01-22
**Source:** [Kaggle Competition](https://www.kaggle.com/competitions/child-mind-institute-detect-sleep-states)

**Key Techniques:**

**Results:** 1st place (Private LB: 0.852, 1877 teams)

**Resources:**
- [1st Place Solution (Kaggle)](https://www.kaggle.com/competitions/child-mind-institute-detect-sleep-states/discussion/459715)
- [1st Place GitHub](https://github.com/sakami0000/child-mind-institute-detect-sleep-states-1st-place)
- [Comprehensive Chinese Summary](https://zhuanlan.zhihu.com/p/675470807)
- [Japanese Presentation](https://speakerdeck.com/unonao/shui-mian-konpe-1st-place-solution)

```python
import polars as pl
import numpy as np

def create_decaying_target(train_df, train_events_df, n_epochs=20):
    """

    """
    tolerance_steps = [12, 36, 60, 90, 120, 150, 180, 240, 300, 360]  # 1min~30min
    target_columns = ["event_onset", "event_wakeup"]

    train_df = (
        train_df.join(train_events_df.select(["series_id", "step", "event"]),
                      on=["series_id", "step"], how="left")
        .to_dummies(columns=["event"])
        .with_columns(
            pl.max_horizontal(
                pl.col(target_columns)
                .rolling_max(window_size * 2 - 1, min_periods=1, center=True)
                .over("series_id")
                * (1 - i / len(tolerance_steps))
                for i, window_size in enumerate(tolerance_steps)
            )
        )
    )

    def update_targets_epoch(targets, epoch, n_epochs):
        return np.where(
            targets == 1.0,
            1.0,
            (targets - (1.0 / n_epochs)).clip(min=0.0)
        )

    return train_df, update_targets_epoch

# train_df, update_fn = create_decaying_target(train_df, train_events, n_epochs=20)
# for epoch in range(n_epochs):
#     targets = update_fn(targets, epoch, n_epochs)
```

```python
import numpy as np

def optimize_tolerance_edges(predictions_2nd_level):
    """

    """

    def calculate_candidate_scores(predictions):
        tolerance_steps = [12, 36, 60, 90, 120, 150, 180, 240, 300, 360]
        scores = {}

        for candidate_idx in range(len(predictions)):
            score = 0
            for tol_step in tolerance_steps:
                start = max(0, candidate_idx - tol_step)
                end = min(len(predictions), candidate_idx + tol_step)
                score += predictions[start:end].sum()
            scores[candidate_idx] = score

        return scores

    def greedy_event_selection(predictions, max_events=500):
        """

        """
        selected_events = []
        remaining_predictions = predictions.copy()

        for _ in range(min(max_events, len(predictions) // 12)):
            scores = calculate_candidate_scores(remaining_predictions)
            best_idx = max(scores, key=scores.get)
            selected_events.append(best_idx)

            for tol_step in tolerance_steps:
                start_gt = max(0, best_idx - tol_step)
                end_gt = min(len(remaining_predictions), best_idx + tol_step)
                remaining_predictions[start_gt:end_gt] = 0

        return selected_events

    return greedy_event_selection(predictions_2nd_level)
```

### Daily Normalization (1st Place approach)
```python
import numpy as np

def daily_normalize(predictions, series_ids):
    """

    """
    normalized = predictions.copy()

    for series_id in np.unique(series_ids):
        mask = series_ids == series_id
        daily_preds = predictions[mask]

        n_days = len(daily_preds) // 17280

        for day in range(n_days):
            start = day * 17280
            end = start + 17280
            day_preds = daily_preds[start:end]

            day_min, day_max = day_preds.min(), day_preds.max()
            if day_max > day_min:
                normalized[mask][start:end] = (day_preds - day_min) / (day_max - day_min)

    return normalized
```

```python
from scipy.signal import find_peaks

def detect_events_find_peaks(predictions, score_th=0.005, distance=72):
    """

    """

    onset_peaks, _ = find_peaks(
        onset_preds,
        height=score_th,
        distance=distance
    )

    wakeup_peaks, _ = find_peaks(
        wakeup_preds,
        height=score_th,
        distance=distance
    )

    return {
        'onset': onset_peaks,
        'wakeup': wakeup_peaks
    }
```

```python
import numpy as np

def rolling_mean_smooth(predictions, window=12, center=True):
    """

    """
    smoothed = np.zeros_like(predictions)

    for i in range(len(predictions)):
        start = max(0, i - window // 2)
        end = min(len(predictions), i + window // 2 + 1)
        smoothed[i] = predictions[start:end].mean()

    return smoothed

def detect_events_with_smooth(predictions, window=12, distance=72):
    smoothed = rolling_mean_smooth(predictions, window=window)
    return detect_events_find_peaks(smoothed, distance=distance)
```

```python
def two_level_modeling(train_series, train_events):
    """

    """
    # ==================== 1st Level ====================

    first_level_models = [
        CNNGRUModel(),           # CNN + GRU + CNN
        CNNTransformerModel(),   # CNN + GRU + Transformer + CNN
        LSTMUNetModel(),         # LSTM + UNet1d + UNet
    ]

    for model in first_level_models:
        model.fit(train_series, train_events)

    first_level_preds = []
    for model in first_level_models:
        pred = model.predict(train_series)  # shape: [n_steps_5sec, 2]
        first_level_preds.append(pred)

    # ==================== 2nd Level ====================

    minute_features = aggregate_to_minute(first_level_preds, train_series)

    second_level_models = [
        LightGBMRegressor(),
        CatBoostRegressor(),
        CNNGRUModel(),
        CNNTransformerModel(),
        CNNModel()
    ]

    for model in second_level_models:
        model.fit(minute_features, train_events)

    second_level_preds = []
    for model in second_level_models:
        pred = model.predict(minute_features)  # shape: [n_steps_1min, 2]
        second_level_preds.append(pred)

    # Daily normalization
    final_preds = np.mean(second_level_preds, axis=0)
    final_preds = daily_normalize(final_preds, series_ids)

    events = optimize_tolerance_edges(final_preds)

    return events

def aggregate_to_minute(first_level_preds, train_series):
    n_steps_minute = len(train_series) // 12

    minute_features = []
    for i in range(n_steps_minute):
        start = i * 12
        end = start + 12

        preds_5sec = [p[start:end] for p in first_level_preds]

        raw_feats = train_series[start:end]

        minute_feat = np.concatenate([
        ])

        minute_features.append(minute_feat)

    return np.array(minute_features)
```

```python
import pandas as pd
import numpy as np

def create_sleep_features(series_df):
    """

    """
    df = series_df.copy()

    df['enmo_abs_diff'] = df['enmo'].diff().abs()
    df['enmo'] = df['enmo_abs_diff'].rolling(window=5, center=True, min_periods=1).mean()

    df['anglez_abs_diff'] = df['anglez'].diff().abs()
    df['anglez'] = df['anglez_abs_diff'].rolling(window=5, center=True, min_periods=1).mean()

    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['hour'] = df['timestamp'].dt.hour
    df['minute'] = df['timestamp'].dt.minute
    df['weekday'] = df['timestamp'].dt.weekday
    df['is_weekend'] = df['weekday'].isin([5, 6]).astype(int)

    df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
    df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)

    for col in ['enmo', 'anglez']:
        for window in [10, 30, 60]:
            df[f'{col}_rolling_mean_{window}'] = df[col].rolling(window=window, min_periods=1).mean()
            df[f'{col}_rolling_std_{window}'] = df[col].rolling(window=window, min_periods=1).std()
            df[f'{col}_rolling_max_{window}'] = df[col].rolling(window=window, min_periods=1).max()
            df[f'{col}_rolling_min_{window}'] = df[col].rolling(window=window, min_periods=1).min()

    df['anglez_times_enmo'] = df['anglez_abs_diff'] * df['enmo_abs_diff']
    df['anglez_div_enmo'] = df['anglez_abs_diff'] / (df['enmo_abs_diff'] + 1e-6)

    return df
```

|------|---------|

---

|---------|---------|---------|

#### 1st Place - Team Sony (yamash, suguuuuu, kfuji, Muku)

|------|------|-------|

- 2-Stage Training (votes ≥10)

#### 2nd Place - COOLZ

```
    ↓
┌─────┴─────┐
↓           ↓
3D-CNN    2D-CNN
(x3d-l)  (EfficientNetB5)
    ↓           ↓
Spectrogram  Raw EEG
    └─────┬─────┘
         ↓
   Double Head
         ↓
    Ensemble
```

- **2-Stage Training**：

#### 3rd Place - nvidia-dd (DIETER)

```
EEG → MelSpectrogram → 2D CNN
     ↓
EEG → 1D-Convolutions → Squeezeformer
     ↓
  Ensemble
```

|------|---------|------|

|------|---------|------|

|------|--------|------|

|------|---------|------|------|

|------|---------|--------|---------|

|------|---------|------------|------|

|------|---------|---------|

|------|---------|---------|------|

---

## Child Mind Institute - Top 10 Solutions Comparison

#### 1st Place - shimacos vs sakami vs kami (kami, sakami0000, shimacos)

```
    CNN+GRU+CNN, CNN+GRU+Transformer+CNN,
    LSTM+UNet1d+UNet, LSTM+UNet1d+UNet, 1dCNN+UNet1d+Transformer
    ↓
    LightGBM, CatBoost, CNN+GRU, CNN+Transformer, CNN
    ↓
    Daily Normalize → Greedy Search → Final Events
```

#### 2nd Place - K-Mat

```
    ↓
Stage 2: Error Modeling (LGBM)
    ↓
```

#### 3rd Place - cucutzik

|------|---------|------|

|------|---------|------|

|------|---------|---------|

|------|---------|---------|

|------|------|------|------|

|------|---------|---------|---------|

|------|---------|---------|------|

|------|---------|------|

|------|---------|------|

---

## CMI - Detect Behavior with Sensor Data - Top 10 Solutions Comparison

#### 1st Place - Devin | Ogurtsov | zyz (Andrey Ogurtsov, Devin, zyz)

```
Devin's part:

Ogurtsov's part:

zyz part:
```

#### 2nd Place - cucutzik

```

    Residual SE-CNN Block + Attention

    Pseudo Label:

```

#### 3rd Place - Team RIST

```

```

|------|---------|------|

|------|---------|------|

```
```

|------|---------|---------|

|------|---------|---------|

```python
def detect_periodicity(series):

    daily_chunks = [downsampled[i*1440:(i+1)*1440] for i in range(n_days)]

    for i in range(n_days - 1):
        similarity = np.mean(daily_chunks[i] == daily_chunks[i+1])

        cos_sim = np.dot(daily_chunks[i], daily_chunks[i+1]) / (
            np.linalg.norm(daily_chunks[i]) * np.linalg.norm(daily_chunks[i+1])
        )

        if similarity > threshold or cos_sim > threshold:

    return False
```

```python
```

```
00:22:45

```

|------|------|------|

|------|---------|-----------|---------|

|------|---------|-------------|

---

|-------|---------|------|--------|

**IMU (Inertial Measurement Unit)：**

**THM (Thermopile)：**

**TOF (Time-of-Flight)：**

```
```

|------|---------|---------|

```python
def tof_2x2_pooling_with_mask(tof_data):
    """
    """
    for sensor_idx in range(5):
        sensor = tof_data[:, sensor_idx*64:(sensor_idx+1)*64]
        sensor = sensor.reshape(-1, 8, 8)

        # 2×2 pooling
        pooled = sensor.reshape(-1, 4, 2, 2).mean(axis=(2, 3))

        mask = (sensor == -1).reshape(-1, 4, 2, 2).any(axis=(2, 3))

        features[:, sensor_idx*4:(sensor_idx+1)*4] = pooled
        features[:, 20+sensor_idx*4:20+(sensor_idx+1)*4] = mask

    return features
```

|------|---------|------|

```python
from scipy.optimize import linear_sum_assignment

def hungarian_post_process(predictions, subject_ids, sequence_ids):
    """
    """
    for subject in unique(subject_ids):
        mask = subject_ids == subject
        preds = predictions[mask]
        seqs = sequence_ids[mask]

        cost_matrix = -np.log(preds + 1e-10)

        row_ind, col_ind = linear_sum_assignment(cost_matrix)

        for i, j in zip(row_ind, col_ind):
            predictions[mask][i] = np.zeros(n_classes)
            predictions[mask][i][j] = 1.0

    return predictions
```

```
Transition → Pause → Gesture
```

|------|---------|------|---------|

|------|---------|------|

```python
class PhaseAwareAttention(nn.Module):
    """
    """
    def __init__(self, d_model, n_heads=8):
        super().__init__()
        self.phase_emb = nn.Embedding(3, d_model)

        self.transition_attn = nn.MultiheadAttention(d_model, n_heads)
        self.pause_attn = nn.MultiheadAttention(d_model, n_heads)
        self.gesture_attn = nn.MultiheadAttention(d_model, n_heads)

    def forward(self, x, phase_labels):
        # phase_labels: [batch, seq_len] ∈ {0, 1, 2}
        batch, seq_len, d_model = x.shape

        outputs = []
        for t in range(seq_len):
            phase = phase_labels[:, t]  # [batch]

            if phase == 0:  # Transition
                attn_out, _ = self.transition_attn(x[:, t:t+1], x, x)
            elif phase == 1:  # Pause
                attn_out, _ = self.pause_attn(x[:, t:t+1], x, x)
            else:  # Gesture
                attn_out, _ = self.gesture_attn(x[:, t:t+1], x, x)

            outputs.append(attn_out)

        return torch.cat(outputs, dim=1)
```

|------|---------|---------|

|------|---------|

```python
def get_model_input(data):
    """
    """
    has_tof = (data['tof'] != -1).any()
    has_thm = (data['thm'] != -1).any()

    if has_tof and has_thm:
        return model_all(data['imu'], data['tof'], data['thm'])
    elif has_tof:
        return model_imu_tof(data['imu'], data['tof'])
    elif has_thm:
        return model_imu_thm(data['imu'], data['thm'])
    else:
        return model_imu(data['imu'])
```

|---------|------|---------|

```python
ANOMALY_SUBJECTS = ['SUBJ_019262', 'SUBJ_045235']

def filter_anomaly_subjects(dataframe):
    """
    """
    mask = ~dataframe['subject'].isin(ANOMALY_SUBJECTS)
    return dataframe[mask]
```

```python
def align_right_handed_system(data):
    """
    """
    data['X_gyro'] = -data['X_gyro']
    data['Y_gyro'] = -data['Y_gyro']

    data['orientation_X'] = -data['orientation_X']
    data['orientation_Y'] = -data['orientation_Y']

    return data
```

|------|---------|-----------|---------|

|------|-----------|-----------|
