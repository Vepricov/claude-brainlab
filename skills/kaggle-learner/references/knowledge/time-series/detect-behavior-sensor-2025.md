# CMI - Detect Behavior with Sensor Data (2025)
> Last updated: 2026-01-23
> Source count: 1
---

### CMI - Detect Behavior with Sensor Data (2025)

- 2nd Place: cucutzik - Private LB: ~
- 3rd Place: Team RIST - Private LB: ~

**1st Place - Devin | Ogurtsov | zyz**

**2nd Place - cucutzik**

**3rd Place - Team RIST**

**4th Place - Rotter (Rotem D**)

**5th Place - SOK (Soichi**

**6th Place - Alina (Alina G**

**7th Place - Team BBB**

**8th Place - MambaSeries**

**9th Place - SensorFusion**

**10th Place - TSLearn**

**13th Place - Bidirectional Mamba (Reference from summary)**

---

### CMI - Detect Behavior with Sensor Data (2025) - 2025-01-22
**Source:** [Kaggle Competition](https://www.kaggle.com/competitions/cmi-detect-behavior-with-sensor-data)

**Key Techniques:**

**Results:** 1st place (2657 teams)

**Resources:**
- [1st Place Solution (Kaggle)](https://www.kaggle.com/competitions/cmi-detect-behavior-with-sensor-data/writeups/cmi-1st-place-solution)
- [Japanese Summary](https://zenn.dev/ottantachinque/articles/2025-09-14_cmi-detect-behavior-with-sensor-data)
- [Chinese EDA](https://zhuanlan.zhihu.com/p/1943779452640273827)

```python
import numpy as np

def tof_image_2x2_pooling(tof_data):
    """

    """
    n_timesteps = tof_data.shape[0]

    if len(tof_data.shape) == 2:
        n_tof_sensors = tof_data.shape[1] // 64
        tof_reshaped = tof_data.reshape(n_timesteps, n_tof_sensors, 8, 8)
    else:
        tof_reshaped = tof_data

    n_tof_sensors = tof_reshaped.shape[1]
    pooled_features = []

    for t in range(n_timesteps):
        for sensor in range(n_tof_sensors):
            sensor_data = tof_reshaped[t, sensor]  # (8, 8)

            patches = []
            for i in range(0, 8, 2):
                for j in range(0, 8, 2):
                    patch = sensor_data[i:i+2, j:j+2]
                    patches.append(patch.mean())
            pooled = np.array(patches)

            pooled_features.append(pooled)

    return np.array(pooled_features)  # (n_timesteps, n_tof_sensors * n_patches)
```

```python
import numpy as np

def quaternion_to_6d(quaternion_data):
    """

    """

    w = quaternion_data[..., 0:1]
    x = quaternion_data[..., 1:2]
    y = quaternion_data[..., 2:3]
    z = quaternion_data[..., 3:4]

    norm = np.sqrt(w**2 + x**2 + y**2 + z**2)
    w, x, y, z = w/norm, x/norm, y/norm, z/norm

    # R = [w  -z  y   z]
    #     [z   w  -x  y]
    #     [-y  x   w  z]
    # col1 = [w, z, -y]
    # col2 = [-z, w, x]

    # R[0,:] = [1 - 2(y^2 + z^2),     2(xy - wz),     2(xz + wy)]
    # R[1,:] = [    2(xy + wz), 1 - 2(x^2 + z^2),     2(yz - wx)]

    x2 = x * x
    y2 = y * y
    z2 = z * z

    r00 = 1 - 2 * (y2 + z2)
    r01 = 2 * (x * y - w * z)
    r02 = 2 * (x * z + w * y)
    r10 = 2 * (x * y + w * z)
    r11 = 1 - 2 * (x2 + z2)
    r12 = 2 * (y * z - w * x)

    rotation_6d = np.concatenate([
        r00, r01, r02, r10, r11, r12
    ], axis=-1)

    return rotation_6d

# rot_data shape: (n_timesteps, 4) or (n_timesteps, n_samples, 4)
# rot_6d = quaternion_to_6d(rot_data)
```

```python
import torch
import torch.nn as nn

class PhaseAwareAttention(nn.Module):
    """

    """
    def __init__(self, d_model, n_heads=8, dropout=0.1):
        super().__init__()

        self.attentions = nn.ModuleList([
            nn.MultiheadAttention(d_model, n_heads, dropout=dropout)
            for _ in range(3)
        ])
        self.norms = nn.ModuleList([nn.LayerNorm(d_model) for _ in range(3)])
        self.fcs = nn.ModuleList([nn.Linear(d_model, d_model) for _ in range(3)])

        self.phase_classifier = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
        )

    def forward(self, x, phase_labels=None):
        """
        """
        batch_size, seq_len, d_model = x.shape

        phase_probs = self.phase_classifier(x.mean(dim=1))  # (batch, 3)
        phase_probs = torch.softmax(phase_probs, dim=-1)  # (batch, 3)

        if phase_labels is None:
            phase_labels = torch.argmax(phase_probs, dim=-1)  # (batch,)

        output = torch.zeros_like(x)

        for b in range(batch_size):

            x_b = x[b:b+1]  # (1, seq_len, d_model)
            attn = self.attentions[phase]
            norm = self.norms[phase]
            fc = self.fcs[phase]

            x_b = norm(x_b)
            x_b, _ = attn(x_b, x_b, x_b)
            x_b = fc(x_b)

            weight = phase_probs[b, phase]
            output[b:b+1] = x_b * weight

        return output, phase_probs
```

```python
import numpy as np
from scipy.optimize import linear_sum_assignment

def hungarian_global_label_assignment(pred_probs, subject_ids, sequence_ids,
                                    gesture_ids, orientation_ids):
    """

        sequence_ids: (n_sequences,) - sequence ID

    """
    n_sequences = pred_probs.shape[0]
    n_classes = pred_probs.shape[1]

    cost_matrix = -np.log(pred_probs + 1e-10)

    final_labels = np.zeros(n_sequences, dtype=int)

    for subject_id in np.unique(subject_ids):
        mask = subject_ids == subject_id
        subject_seqs = np.where(mask)[0]

        if len(subject_seqs) == 0:
            continue

        subject_probs = pred_probs[subject_seqs]  # (n_subject_seqs, n_classes)

        row_ind, col_ind = linear_sum_assignment(subject_probs)

        for seq_idx, label_idx in zip(row_ind, col_ind):
            final_labels[subject_seqs[seq_idx]] = label_idx

    return final_labels

def simple_hungarian_assignment(pred_probs, sequence_ids, gesture_ids, orientation_ids):
    """

        pred_probs: (n_sequences, n_classes)
        sequence_ids: (n_sequences,)
        gesture_ids: (n_sequences,)
        orientation_ids: (n_sequences,)
    """
    n_sequences = pred_probs.shape[0]
    n_classes = pred_probs.shape[1]

    final_labels = np.zeros(n_sequences, dtype=int)

    for orientation_id in np.unique(orientation_ids):
        mask = orientation_ids == orientation_id
        orientation_seqs = np.where(mask)[0]

        if len(orientation_seqs) == 0:
            continue

        orientation_probs = pred_probs[orientation_seqs]
        orientation_gestures = gesture_ids[orientation_seqs]

        row_ind, col_ind = linear_sum_assignment(orientation_probs)

        for seq_idx, label_idx in zip(row_ind, col_ind):
            final_labels[orientation_seqs[seq_idx]] = label_idx

    return final_labels
```

```python
import numpy as np

def phase_aware_mixup(X, y, phase_labels, alpha=0.2, beta=0.2):
    """

        mixed_X, mixed_y, lambda_a, lambda_b, phase_labels
    """
    batch_size, seq_len, n_features = X.shape

    if phase_labels is None:
        return standard_mixup(X, y, alpha)

    mixed_X = X.copy()
    mixed_y = y.copy()
    lambda_as = np.zeros(batch_size)
    lambda_bs = np.zeros(batch_size)

    for i in range(batch_size):
        same_phase_mask = (phase_labels[i, 0] == phase_labels[:, 0])

        if same_phase_mask.sum() == 0:
            continue

        same_phase_indices = np.where(same_phase_mask)[0]
        j = np.random.choice(same_phase_indices)

        # Mixup
        mixed_X[i] = alpha * X[i] + (1 - alpha) * X[j]
        mixed_y[i] = alpha * y[i] + (1 - alpha) * y[j]
        lambda_as[i] = alpha

        if beta > 0:
            pass

    return mixed_X, mixed_y, lambda_as, lambda_bs, phase_labels

def standard_mixup(X, y, alpha=0.2):
    batch_size = X.shape[0]

    if batch_size < 2:
        return X, y, np.zeros(batch_size), None, None

    mixed_X = X.copy()
    mixed_y = y.copy()
    lambda_as = np.random.beta(alpha, alpha, batch_size)

    for i in range(batch_size):
        j = i
        while j == i:
            j = np.random.randint(0, batch_size)

        mixed_X[i] = lambda_as[i] * X[i] + (1 - lambda_as[i]) * X[j]
        mixed_y[i] = lambda_as[i] * y[i] + (1 - lambda_as[i]) * y[j]

    return mixed_X, mixed_y, lambda_as, None, None
```

```python
import numpy as np

def remove_gravity_and_extract_features(acc_data):
    """

    """
    n_timesteps = acc_data.shape[0]

    acc_no_gravity = acc_data - gravity

    features = []

    for t in range(n_timesteps):
        feat = []

        if t > 0:
            diff = acc_no_gravity[t] - acc_no_gravity[t-1]
        else:

        window = 10
        start = max(0, t - window)
        end = min(n_timesteps, t + window + 1)
        window_data = acc_no_gravity[start:end]

        if t >= window:
            fft_energy = np.abs(fft_data)
        else:
            feat.append(0)

        features.append(feat)

    features = np.array(features)  # (n_timesteps, n_features)
    if features.shape[1] < 35:
        pass

    return features
```

```python
import numpy as np

def time_series_to_image(series_data, image_size=(224, 224)):
    """

    """
    n_timesteps, n_features = series_data.shape
    height, width = image_size

    if n_timesteps * n_features == height * width:
        image = series_data.reshape(height, width)
        return image[np.newaxis, :, :]  # (1, height, width)

    if n_features == 3:
        normalized = (series_data - series_data.min()) / (series_data.max() - series_data.min() + 1e-10)
        image = (normalized * 255).astype(np.uint8)

        if n_timesteps != height or n_features != width:
            image = image.reshape(height, width, 3)

        return image.transpose(2, 0, 1)  # (3, height, width)

    if n_features >= 3:
        selected_data = series_data[:, :3]
    else:
        selected_data = np.concatenate([series_data, series_data, series_data], axis=1)[:, :3]

    normalized = (selected_data - selected_data.min()) / (selected_data.max() - selected_data.min() + 1e-10)
    image = (normalized * 255).astype(np.uint8)

    image = image.reshape(n_timesteps, 3, 1).reshape(height, width, 3)

    return image.transpose(2, 0, 1)  # (3, height, width)
```

```python
import polars as pl
import numpy as np

def remove_invalid_sequences(train_df, train_events):
    """

    """
    invalid_subjects = ['SUBJ_019262', 'SUBJ_045235']

    cleaned_df = train_df.filter(~pl.col('subject').is_in(invalid_subjects))

    gesture_counts = train_df.groupby('sequence_id')['gesture'].n_unique()
    valid_gestures = gesture_counts.filter(pl.col('gesture') > 0)
    cleaned_df = cleaned_df.filter(pl.col('sequence_id').is_in(valid_gestures['sequence_id']))

    return cleaned_df
```

```python
import numpy as np

def align_left_to_right_handed(sensor_data, sensor_type='IMU'):
    """

    """
    if sensor_type == 'IMU':

        acc_y = sensor_data[:, 1]  # acc_y
        acc_z = sensor_data[:, 2]  # acc_z

        aligned_acc_y = acc_y
        aligned_acc_z = acc_z

        aligned_data = sensor_data.copy()
        aligned_data[:, 0] = aligned_acc_x

    elif sensor_type == 'THM':

        aligned_data = sensor_data.copy()

    elif sensor_type == 'TOF':

        aligned_data = sensor_data.copy()

    return aligned_data
```

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

|------|---------|---------|

|------|---------|------|

|------|------|---------|

|------|---------|---------|

|------|---------|---------|

---

```python
def entmax(x, alpha=1.5, dim=-1):
    return torch.softmax(x * alpha, dim=dim)
```

|---------|--------|------|

|------|---------|-----------|

```python
def preprocess_eeg_optimal(eeg_raw, votes):
    """
    """
    bipolar = longitudinal_bipolar_montage(eeg_raw)

    filtered = bandpass_filter(bipolar, lowcut=0.5, highcut=40, fs=200)

    normalized = np.clip(filtered, -1024, 1024) / 32.0

    if votes < 10:
    else:
        weight = 1.0

    return normalized, weight
```

|------|------|---------|

---

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
