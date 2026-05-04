# BirdCLEF 2024
> Last updated: 2026-01-23
> Source count: 1
---

### BirdCLEF 2024 - Bird Sound Identification (2024)

|------|------|------------|-----------|----------|

|--------|---------------|---------------|

**1st Place - Team Kefir (vkop, great_alex, etc.)**

**2nd Place - ADSR**

- EfficientNet B0 backbone

**3rd Place - NVBird (Theo Viel)**

---

   ```python
   # T = std + var + rms + pwr
   T = std + var + rms + pwr
   threshold = np.quantile(T, 0.8)
   clean_data = data[T < threshold]
   ```

4. **Min() Ensemble（1st Place）**
   ```python
   predictions = np.min([model1_pred, model2_pred, model3_pred], axis=0)
   ```

6. **Checkpoint Soup（2nd Place）**

|------|---------------|----------------|

- [1st Place Writeup](https://www.kaggle.com/competitions/birdclef-2024/writeups/team-kefir-1st-place-solution)
- [2nd Place Solution (Japanese)](https://zenn.dev/yuto_mo/articles/85eee84a753159)
- [3rd Place GitHub](https://github.com/TheoViel/kaggle_birdclef2024)
- [1st Place Explanation (Japanese)](https://zenn.dev/yuto_mo/articles/ad43c630729073)

**4th Place - Team**

**5th Place - HiddenLayer**

**6th Place - BirdWhisperer**

**7th Place - AudioZenith**

**8th Place - SpecDroid**

- ResNeSt：26-9t layers, Split-Attention blocks
- Focal Loss：γ=2.0, α=0.25

**9th Place - MelMaster**

**10th Place - SoundScape**

---

### BirdCLEF+ 2025 - Multi-Taxonomic Sound Identification (2025)

- 1st Place: Nikita Babych - Private LB **0.927**
- 2nd Place: Volodymyr Vialactea - Private LB ~0.926
- 3rd Place: Team - Private LB ~0.925

|------|----------|---------|------|----------|

**1st Place - Multi-Iterative Noisy Student (Nikita Babych)**

**4th Place - Soft AUC Loss (dylan.liu)**

**5th Place - Self-Distillation (Noir)**

**6th Place - SED + AttBlockV2**

- Mel-Spectrogram：Mixup2、Time masking、FilterAugment、FrequencyMasking、PinkNoise

**12th Place - Checkpoint Soups + EMA**

---

## Original Summaries

### BirdCLEF 2024 - Bird Sound Identification (2024) - 2026-01-23
**Source:** [Kaggle Competition](https://www.kaggle.com/competitions/birdclef-2024)

**Key Techniques:**

**Results:** 1st place (Private LB: 0.690, Public LB: 0.729, 2935 teams)

**Resources:**
- [1st Place Writeup](https://www.kaggle.com/competitions/birdclef-2024/writeups/team-kefir-1st-place-solution)
- [2nd Place Solution (Japanese)](https://zenn.dev/yuto_mo/articles/85eee84a753159)
- [3rd Place GitHub](https://github.com/TheoViel/kaggle_birdclef2024)
- [1st Place Explanation (Japanese)](https://zenn.dev/yuto_mo/articles/ad43c630729073)

### BirdCLEF+ 2025 - Multi-Taxonomic Sound Identification (2025) - 2026-01-22

**Key Techniques:**

**Results:** 1st place (Private LB: 0.927, ~2000 teams)

**Resources:**
- [1st Place Solution (Kaggle)](https://www.kaggle.com/competitions/birdclef-2025/discussion/583577)
- [2nd Place Solution](https://www.kaggle.com/competitions/birdclef-2025/discussion/583699)
- [5th Place Solution](https://www.kaggle.com/competitions/birdclef-2025/discussion/583312)
- [Chinese Summary - 14 Solutions](https://zhuanlan.zhihu.com/p/1920582942931019095)

---

## Code Templates

```python
import numpy as np
import librosa

class StatisticsTNoiseFilter:
    """
    """

    def __init__(self, quantile: float = 0.8):
        self.quantile = quantile

    def compute_statistics(self, audio: np.ndarray, sample_rate: int) -> dict:
        # RMS (Root Mean Square)
        rms = librosa.feature.rms(y=audio)[0]

        zcr = librosa.feature.zero_crossing_rate(audio)[0]

        std = np.std(audio)

        var = np.var(audio)

        pwr = np.mean(audio ** 2)

        return {
            'std': std,
            'var': var,
            'rms': np.mean(rms),
            'pwr': pwr,
            'zcr': np.mean(zcr),
        }

    def compute_T(self, stats: dict) -> float:
        T = (
            stats['std'] +
            stats['var'] +
            stats['rms'] +
            stats['pwr']
        )
        return T

    def filter_audio(
        self,
        audio_paths: list[str],
        sample_rate: int = 32000
    ) -> list[str]:
        """

        Args:

        Returns:
        """
        T_values = []

        for path in audio_paths:
            audio, _ = librosa.load(path, sr=sample_rate)
            stats = self.compute_statistics(audio, sample_rate)
            T = self.compute_T(stats)
            T_values.append(T)

        threshold = np.quantile(T_values, self.quantile)

        filtered_paths = [
            path for path, T in zip(audio_paths, T_values)
            if T < threshold
        ]

        return filtered_paths
```

```python
import numpy as np
import pandas as pd
from typing import Optional

class GoogleClassifierPreLabeler:
    """
    """

    def __init__(self, model, pseudo_label_coeff: float = 0.05):
        """
        Args:
            model: Google Bird Vocalization Classifier
        """
        self.model = model
        self.pseudo_label_coeff = pseudo_label_coeff

    def predict(self, audio_chunk: np.ndarray) -> dict:
        predictions = self.model.predict(audio_chunk)
        return predictions

    def filter_and_relabel(
        self,
        audio_path: str,
        primary_label: str,
        secondary_labels: Optional[list[str]] = None
    ) -> Optional[dict]:
        """

        Args:

        Returns:
        """
        predictions = self.predict(audio_path)
        max_class = max(predictions, key=predictions.get)
        max_prob = predictions[max_class]

        if max_class != primary_label:
            if secondary_labels and max_class in secondary_labels:
                primary_label = max_class
            else:
                return None

        num_classes = len(predictions)
        label_vector = np.zeros(num_classes)

        label_vector[primary_label] = 0.5

        if secondary_labels:
            for sec_label in secondary_labels:
                label_vector[sec_label] += 0.5 / len(secondary_labels)

        for class_name, prob in predictions.items():
            label_vector[class_name] += self.pseudo_label_coeff * prob

        return {'label_vector': label_vector, 'primary': primary_label}

    def relabel_soundscape(self, audio_path: str) -> np.ndarray:
        predictions = self.predict(audio_path)
        return np.array([predictions.get(cls, 0) for cls in range(self.num_classes)])
```

```python
import torch
import torch.nn as nn
import torch.nn.functional as F

class CESigmoidTrainer:
    """

    """

    def __init__(self, model: nn.Module, num_classes: int):
        self.model = model
        self.num_classes = num_classes
        self.criterion = nn.CrossEntropyLoss()

    def train_step(self, batch: dict) -> torch.Tensor:
        """

        Args:

        Returns:
            loss: CE Loss
        """
        mel_spec = batch['mel_spec']  # (B, C, H, W)
        labels = batch['labels']      # (B, num_classes)

        logits = self.model(mel_spec)  # (B, num_classes)

        target_labels = torch.argmax(labels, dim=1)  # (B,)

        # CE Loss + Softmax
        loss = self.criterion(logits, target_labels)

        return loss

    @torch.no_grad()
    def predict(self, mel_spec: torch.Tensor) -> torch.Tensor:
        """

        Args:
            mel_spec: (B, C, H, W)

        Returns:
        """
        logits = self.model(mel_spec)  # (B, num_classes)

        probabilities = torch.sigmoid(logits)

        return probabilities

    def fit(self, train_loader, val_loader, num_epochs: int, lr: float = 1e-3):
        optimizer = torch.optim.AdamW(self.model.parameters(), lr=lr)
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer, T_max=num_epochs
        )

        for epoch in range(num_epochs):
            self.model.train()
            train_loss = 0
            for batch in train_loader:
                loss = self.train_step(batch)
                loss.backward()
                optimizer.step()
                optimizer.zero_grad()
                train_loss += loss.item()

            self.model.eval()
            val_preds = []
            val_labels = []
            for batch in val_loader:
                mel_spec = batch['mel_spec']
                labels = batch['labels']
                probs = self.predict(mel_spec)
                val_preds.append(probs.cpu().numpy())
                val_labels.append(labels.cpu().numpy())

            val_preds = np.concatenate(val_preds)
            val_labels = np.concatenate(val_labels)
            val_auc = self.compute_auc(val_labels, val_preds)

            print(f"Epoch {epoch}: Train Loss={train_loss/len(train_loader):.4f}, Val AUC={val_auc:.4f}")
            scheduler.step()
```

### Min() Ensemble（BirdCLEF 2024 - 1st Place）

```python
import numpy as np
import torch

class MinEnsemble:
    """
    Min() Ensemble

    """

    def __init__(self, models: list[nn.Module]):
        self.models = models

    @torch.no_grad()
    def predict_min(self, mel_spec: torch.Tensor) -> np.ndarray:
        """

        Args:
            mel_spec: (B, C, H, W)

        Returns:
        """
        predictions = []

        for model in self.models:
            model.eval()
            logits = model(mel_spec)
            probs = torch.sigmoid(logits)  # Sigmoid
            predictions.append(probs.cpu().numpy())

        # Stack: (num_models, B, num_classes)
        predictions = np.stack(predictions, axis=0)

        min_predictions = np.min(predictions, axis=0)

        return min_predictions

    def predict_mean(self, mel_spec: torch.Tensor) -> np.ndarray:
        predictions = []

        for model in self.models:
            model.eval()
            logits = model(mel_spec)
            probs = torch.sigmoid(logits)
            predictions.append(probs.cpu().numpy())

        predictions = np.stack(predictions, axis=0)
        mean_predictions = np.mean(predictions, axis=0)

        return mean_predictions

# min_ensemble = MinEnsemble([model1, model2, model3, model4, model5])
# predictions = min_ensemble.predict_min(test_mel_spec)
```

### Checkpoint Soup（BirdCLEF 2024 - 2nd Place）

```python
import torch
import torch.nn as nn
from typing import list

class CheckpointSoup:
    """
    Checkpoint Soup

    """

    def __init__(self, model: nn.Module, metrics: list[str] = ['auc', 'lrap', 'f1']):
        self.model = model
        self.metrics = metrics

    def add_checkpoint(self, epoch: int, state_dict: dict, scores: dict):
        """

        Args:
        """
        should_save = False
        for metric in self.metrics:
            if epoch == 0:
                should_save = True
                break
            best_score = max([ckpt[2].get(metric, 0) for ckpt in self.checkpoints])
            if scores.get(metric, 0) >= best_score:
                should_save = True
                break

        if should_save:
            self.checkpoints.append((epoch, state_dict.copy(), scores))
            print(f"Checkpoint {epoch} saved: {scores}")

    def make_soup(self) -> dict:
        """

        Returns:
        """
        if not self.checkpoints:
            raise ValueError("No checkpoints to average")

        soup_state_dict = self.checkpoints[0][1].copy()

        for _, ckpt, _ in self.checkpoints[1:]:
            for key in soup_state_dict.keys():
                if key in ckpt:
                    soup_state_dict[key] += ckpt[key]

        num_checkpoints = len(self.checkpoints)
        for key in soup_state_dict.keys():
            soup_state_dict[key] /= num_checkpoints

        print(f"Soup made from {num_checkpoints} checkpoints (epochs: {[ckpt[0] for ckpt in self.checkpoints]})")
        return soup_state_dict

    def load_soup(self, model: nn.Module):
        soup = self.make_soup()
        model.load_state_dict(soup)
        return model

# checkpoint_soup = CheckpointSoup(model, metrics=['auc', 'lrap', 'f1'])
#
# for epoch in range(num_epochs):
#     train(...)
#     scores = validate(...)
#     checkpoint_soup.add_checkpoint(epoch, model.state_dict(), scores)
#
# final_model = checkpoint_soup.load_soup(model)
```

```python
import numpy as np
import torch
from typing import list

class IterativePseudoLabeling:
    """

    """

    def __init__(
        self,
        base_model_class,
        pseudo_label_chance: float = 0.35,
        amp_exp_min: float = -0.5,
        amp_exp_max: float = 0.1,
        num_iterations: int = 3,
    ):
        self.base_model_class = base_model_class
        self.pseudo_label_chance = pseudo_label_chance
        self.amp_exp_min = amp_exp_min
        self.amp_exp_max = amp_exp_max
        self.num_iterations = num_iterations
        self.ensemble_models = []

    def generate_pseudo_labels(
        self,
        unlabeled_audio_paths: list[str],
        unlabeled_soundscapes: list[str]
    ) -> list[dict]:
        """

        Args:

        Returns:
            pseudo_samples: [{audio_path, label_vector}, ...]
        """
        pseudo_samples = []

        for audio_path in unlabeled_soundscapes:
            predictions = []
            for model in self.ensemble_models:
                pred = self.predict_with_model(model, audio_path)
                predictions.append(pred)

            avg_pred = np.mean(predictions, axis=0)
            pseudo_samples.append({
                'audio_path': audio_path,
                'label_vector': avg_pred
            })

        return pseudo_samples

    def mix_pseudo_labels(
        self,
        train_sample: dict,
        pseudo_sample: dict,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """

        Args:

        Returns:
        """
        train_audio = train_sample['audio']
        train_label = train_sample['label_vector']
        pseudo_audio = pseudo_sample['audio']
        pseudo_label = pseudo_sample['label_vector']

        amp_factor = 10 ** np.random.uniform(self.amp_exp_min, self.amp_exp_max)

        mixed_audio = train_audio * amp_factor + pseudo_audio * amp_factor

        mixed_label = np.maximum(train_label, pseudo_label)

        return mixed_audio, mixed_label

    def train_with_pseudo_labels(
        self,
        train_data: list[dict],
        pseudo_samples: list[dict],
        num_epochs: int = 50,
    ):
        model = self.base_model_class()
        optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
        criterion = torch.nn.BCEWithLogitsLoss()

        for epoch in range(num_epochs):
            for train_sample in train_data:
                if np.random.random() < self.pseudo_label_chance:
                    pseudo_sample = np.random.choice(pseudo_samples)
                    audio, label = self.mix_pseudo_labels(train_sample, pseudo_sample)
                else:
                    audio = train_sample['audio']
                    label = train_sample['label_vector']

                loss = self.train_step(model, audio, label, criterion)
                loss.backward()
                optimizer.step()
                optimizer.zero_grad()

        return model

    def fit(self, train_data, unlabeled_soundscapes):
        for iteration in range(self.num_iterations):
            print(f"\n=== Iteration {iteration + 1}/{self.num_iterations} ===")

            pseudo_samples = self.generate_pseudo_labels(train_data, unlabeled_soundscapes)
            print(f"Generated {len(pseudo_samples)} pseudo labels")

            new_model = self.train_with_pseudo_labels(train_data, pseudo_samples)
            self.ensemble_models.append(new_model)

            ensemble_score = self.evaluate_ensemble()
            print(f"Ensemble score: {ensemble_score:.4f}")

        return self.ensemble_models
```

|------|---------------|----------------|

|------|---------|------|

```python
# T = std + var + rms + pwr
T = std + var + rms + pwr
threshold = np.quantile(T, 0.8)
clean_data = data[T < threshold]
```

**3. Min() Ensemble（1st Place）**
```python
predictions = np.min([model1_pred, model2_pred, model3_pred], axis=0)
```

**5. Checkpoint Soup（2nd Place）**

|------|------|------|

|------|----------|

```python
augmented = resize(mel_spec, (new_height, new_width))
```

|------|---------------|----------------|------|

|------|------|----------|

|------|-------------|---------------------|

|------|---------|------|

|------|--------|-------|-------------|----------|

```python

```

```

```

|------|------|--------|------|

```python
high_threshold = 0.7
low_threshold = 0.3

positive_mask = probs >= high_threshold

negative_mask = probs <= low_threshold

uncertain_mask = (probs > low_threshold) & (probs < high_threshold)

valid_mask = positive_mask | negative_mask
```

|------|---------|--------|------|

```python

def precompute_mel_spectrograms(audio_files, cache_dir="cache/mel"):
    os.makedirs(cache_dir, exist_ok=True)

    for audio_file in tqdm(audio_files):
        cache_path = os.path.join(cache_dir, f"{Path(audio_file).stem}.npy")

        if not os.path.exists(cache_path):
            waveform, sr = torchaudio.load(audio_file)
            mel_spec = extract_mel_spectrogram(waveform, sr)

            np.save(cache_path, mel_spec.numpy())
```

```python

def sliding_window_inference_optimized(model, audio_path):
    waveform, sr = torchaudio.load(audio_path)

    all_windows = extract_all_windows(waveform, sr)

    with torch.no_grad():
        predictions = model(all_windows)  # (num_windows, num_classes)

    smoothed_predictions = smooth_adjacent_windows(predictions)

    return smoothed_predictions
```

|------|------|

|------|---------|------|

```python
rare_species = [species for species in all_species
                if get_sample_count(species) < 30]

rare_model = create_model(num_classes=len(rare_species))
rare_model.train_on(rare_species_data)

final_prediction = 0.7 * general_model + 0.3 * rare_model
```

|------|---------|-----------|------|

```python
predictions = np.mean([model1_pred, model2_pred, model3_pred], axis=0)

weights = [0.3, 0.3, 0.4]
predictions = np.average([model1_pred, model2_pred, model3_pred],
                         axis=0, weights=weights)

for i in range(len(predictions)):
    pred_min = predictions[i].min()
    pred_max = predictions[i].max()
    predictions[i] = (predictions[i] - pred_min) / (pred_max - pred_min)

predictions = np.mean(predictions, axis=0)
```

|------|-----------|------|

|------|------|---------|

---

---

## Google Brain - Ventilator Pressure Prediction (2021)

- 1st Place: group16 (Gilles Vandewiele et al.) - MAE ~0.104
- 2nd Place: ambrosm - MAE ~0.105
- 3rd Place: Upstage - MAE ~0.106

---

---

#### 1st Place - group16 (Gilles Vandewiele et al.)

  ```python
  class VentilatorModel(nn.Module):
      def __init__(self):
          self.cnn = CNN1D(input_dim=5)  # u_in, u_out, R, C, time_step
          self.lstm = LSTM(hidden_dim=256, num_layers=2)
          self.transformer = TransformerEncoder(num_layers=2, nhead=8)

      def forward(self, x):
          x = self.cnn(x)
          x = self.lstm(x)
          x = self.transformer(x)
          return self.fc(x)
  ```

---

#### 2nd Place - ambrosm

  ```python
  def pid_inverse(u_in, u_out, R, C):
      """

      """
      pressures = []

      for breath_id in unique_breaths:
          u_in_breath = u_in[breath_id]
          u_out_breath = u_out[breath_id]

          Kp, Ki, Kd = fit_pid_parameters(u_in_breath, u_out_breath)

          pressure = inverse_pid(u_in_breath, Kp, Ki, Kd, R, C)
          pressures.append(pressure)

      return pressures
  ```

**Writeup**：[Kaggle Writeup](https://www.kaggle.com/competitions/ventilator-pressure-prediction/writeups/ambrosm-2-solution-the-inverse-of-a-pid-controller)

---

#### 3rd Place - Upstage

  ```python
  class UpstageModel(nn.Module):
      def __init__(self):
          self.embedding = Embedding(num_r_values * num_c_values, 64)
          self.lstm1 = LSTM(input_dim=64+3, hidden_dim=256, num_layers=2, bidirectional=True)
          self.lstm2 = LSTM(input_dim=512, hidden_dim=128, num_layers=1)
          self.fc_pressure = Linear(128, 1)

      def forward(self, u_in, u_out, R, C):
          rc_embed = self.embedding(R * 100 + C)

          x = torch.cat([u_in, u_out, rc_embed], dim=-1)

          x = self.lstm1(x)
          x = self.lstm2(x)

          pressure = self.fc_pressure(x)
          delta = self.fc_delta(x)

          return pressure, delta
  ```

  ```python
  def loss_function(pressure_pred, delta_pred, pressure_true):
      loss_pressure = F.l1_loss(pressure_pred, pressure_true)

      delta_true = pressure_true[:, 1:] - pressure_true[:, :-1]
      loss_delta = F.l1_loss(delta_pred[:, :-1], delta_true)

      return loss_pressure + 0.3 * loss_delta
  ```

**Writeup**：[Kaggle Writeup](https://www.kaggle.com/competitions/ventilator-pressure-prediction/writeups/upstage-making-ai-beneficial-3rd-place-single-mode)

---

#### 4th Place - Jun Koda

  ```python
  u_in = α * pressure_target + β

  pressure = pressure_peak * exp(-t / τ)

  ```

  ```python
  def predict_pressure(u_in, u_out, R, C):
      pressures = []

      for t in range(len(u_in)):
              pressure[t] = (u_in[t] - β) / α
              pressure[t] = pressure_peak * exp(-t / (R * C))

      return pressures
  ```

**Writeup**：[Kaggle Writeup](https://www.kaggle.com/competitions/ventilator-pressure-prediction/writeups/jun-koda-4th-place-solution-hacking-the-pid-contro)

---

#### 6th Place - 0-0ggg

  ```python
  class MultiTaskLSTM(nn.Module):
      def __init__(self, input_dim=5, hidden_dim=128):
          super().__init__()
          self.lstm = LSTM(input_dim, hidden_dim, num_layers=2, dropout=0.2)
          self.fc_pressure = Linear(hidden_dim, 1)
          self.fc_delta = Linear(hidden_dim, 1)

      def forward(self, x):
          x, _ = self.lstm(x)

          pressure = self.fc_pressure(x)
          delta = self.fc_delta(x)

          return pressure, delta
  ```

  ```python
  def train_step(model, batch):
      pressure_pred, delta_pred = model(batch)

      loss_pressure = mae_loss(pressure_pred, batch.pressure)

      delta_true = batch.pressure[:, 1:] - batch.pressure[:, :-1]
      loss_delta = mae_loss(delta_pred[:, :-1], delta_true)

      loss = loss_pressure + 0.2 * loss_delta
      return loss
  ```

**Writeup**：[Kaggle Writeup](https://www.kaggle.com/competitions/ventilator-pressure-prediction/writeups/0-0ggg-6th-place-solution-single-multi-task-lstm)

---

#### 14th Place - pksha (Team "no pressure")

  ```python
  class MultitaskLSTM(nn.Module):
      def __init__(self):
          self.lstm = LSTM(input_dim=6, hidden_dim=128, num_layers=2, bidirectional=True)
          self.fc1 = Linear(256, 64)
          self.fc_pressure = Linear(64, 1)
          self.fc_delta = Linear(64, 1)

      def forward(self, x):
          x, _ = self.lstm(x)
          x = F.relu(self.fc1(x))
          pressure = self.fc_pressure(x)
          delta = self.fc_delta(x)
          return pressure, delta
  ```

**Writeup**：[Kaggle Writeup](https://www.kaggle.com/competitions/ventilator-pressure-prediction/writeups/pksha-no-pressure-14th-place-solution-multitask-ls)

---

#### 16th Place - player2-has-flatlined

  1. Baseline LSTM：MAE ~0.15

**Writeup**：[Kaggle Writeup](https://www.kaggle.com/competitions/ventilator-pressure-prediction/writeups/player2-has-flatlined-16th-place-journey-writeup-n)

---

#### 20th Place - hyeongchan-nikita / kozistr

  ```python
  def multi_task_loss(pressure_pred, delta_pred, pressure_true):
      loss_pressure = F.l1_loss(pressure_pred, pressure_true)

      delta_true = torch.diff(pressure_true, dim=1)
      loss_delta = F.l1_loss(delta_pred[:, :-1], delta_true)

      return loss_pressure + 0.15 * loss_delta
  ```

  - Dropout：0.3

**Writeup**：[Kaggle Writeup](https://www.kaggle.com/competitions/ventilator-pressure-prediction/writeups/hyeongchan-nikita-20th-place-solution-model-multi-)

---

```python
import numpy as np
from scipy.optimize import minimize

def fit_pid_parameters(u_in, u_out, initial_pressure=0):
    """

    Args:

    Returns:
    """

    def pid_loss(params, u_in, u_out):
        Kp, Ki, Kd = params

        pressure_pred = simulate_pid(u_in, u_out, Kp, Ki, Kd, initial_pressure)

        error = np.mean((u_in - target_from_pressure(pressure_pred)) ** 2)
        return error

    x0 = [1.0, 0.1, 0.5]

    bounds = [(0, None), (0, None), (0, None)]

    result = minimize(pid_loss, x0, args=(u_in, u_out), bounds=bounds)

    return result.x

def simulate_pid(u_in, u_out, Kp, Ki, Kd, initial_pressure):
    """

    Args:

    Returns:
    """
    n_steps = len(u_in)
    pressure = np.zeros(n_steps)
    pressure[0] = initial_pressure

    integral = 0
    prev_error = 0

    for t in range(1, n_steps):

        pv = pressure[t-1]

        error = setpoint - pv

        integral += error

        derivative = error - prev_error
        prev_error = error

        output = Kp * error + Ki * integral + Kd * derivative

        # dP/dt = (u_in - P) / (R * C)

        pressure[t] = pressure[t-1] + (output - pressure[t-1]) / tau

        if u_out[t] == 1:

    return pressure

def predict_pressure_pid(u_in, u_out, R, C):
    """

    Args:

    Returns:
    """
    breath_ids = get_breath_ids(u_out)

    pressures = []

    for breath_id in breath_ids:
        u_in_breath = u_in[breath_id]
        u_out_breath = u_out[breath_id]

        Kp, Ki, Kd = fit_pid_parameters(u_in_breath, u_out_breath)

        pressure_breath = inverse_pid(u_in_breath, u_out_breath, Kp, Ki, Kd, R, C)
        pressures.extend(pressure_breath)

    return np.array(pressures)

def inverse_pid(u_in, u_out, Kp, Ki, Kd, R, C):
    """

    u_in ≈ Kp * (target - current)
    => target ≈ u_in / Kp + current
    """
    n_steps = len(u_in)
    pressure = np.zeros(n_steps)

    for t in range(1, n_steps):
            pressure[t] = pressure[t-1] + u_in[t] / Kp
            tau = R * C
            pressure[t] = pressure[t-1] * np.exp(-1 / tau)

    return pressure
```

```python
import torch
import torch.nn as nn

class MultiTaskVentilatorLSTM(nn.Module):

    def __init__(self, input_dim=5, hidden_dim=128, num_layers=2, dropout=0.2):
        super().__init__()

        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            dropout=dropout,
            batch_first=True,
            bidirectional=True
        )

        self.fc1 = nn.Linear(hidden_dim * 2, 64)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        lstm_out, _ = self.lstm(x)  # (batch, seq, hidden*2)

        out = F.relu(self.fc1(lstm_out))
        out = self.dropout(out)

        pressure = self.fc_pressure(out).squeeze(-1)  # (batch, seq)
        delta = self.fc_delta(out).squeeze(-1)        # (batch, seq)

        return pressure, delta

def multi_task_loss(pressure_pred, delta_pred, pressure_true, delta_weight=0.2):
    """

    Args:

    Returns:
    """
    loss_pressure = F.l1_loss(pressure_pred, pressure_true)

    delta_true = pressure_true[:, 1:] - pressure_true[:, :-1]
    delta_pred_trimmed = delta_pred[:, 1:]

    loss_delta = F.l1_loss(delta_pred_trimmed, delta_true)

    total_loss = loss_pressure + delta_weight * loss_delta

    return total_loss

def train_model(model, train_loader, val_loader, num_epochs=30, lr=1e-3):
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingWarmRestarts(
        optimizer, T_0=10, T_mult=2
    )

    best_val_loss = float('inf')
    patience = 5
    patience_counter = 0

    for epoch in range(num_epochs):
        model.train()
        train_loss = 0

        for batch in train_loader:
            x = batch['features']  # (batch, seq, 5)
            y = batch['pressure']  # (batch, seq)

            optimizer.zero_grad()

            pressure_pred, delta_pred = model(x)

            loss = multi_task_loss(pressure_pred, delta_pred, y)

            loss.backward()
            optimizer.step()

            train_loss += loss.item()

        model.eval()
        val_loss = 0

        with torch.no_grad():
            for batch in val_loader:
                x = batch['features']
                y = batch['pressure']

                pressure_pred, delta_pred = model(x)
                loss = multi_task_loss(pressure_pred, delta_pred, y)
                val_loss += loss.item()

        scheduler.step()

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            torch.save(model.state_dict(), 'best_model.pth')
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print(f'Early stopping at epoch {epoch}')
                break

        print(f'Epoch {epoch}: Train Loss={train_loss/len(train_loader):.4f}, '
              f'Val Loss={val_loss/len(val_loader):.4f}')

    model.load_state_dict(torch.load('best_model.pth'))
    return model
```

```python
import numpy as np
import pandas as pd

def create_features(df):
    """

    Args:

    Returns:
    """
    df = df.copy()

    features = df[['u_in', 'u_out', 'R', 'C']].copy()

    for lag in [1, 2, 3]:
        features[f'u_in_lag{lag}'] = df['u_in'].shift(lag)

    features['u_in_diff1'] = df['u_in'].diff()
    features['u_in_diff2'] = df['u_in'].diff(2)

    for window in [5, 10]:
        features[f'u_in_rolling_mean_{window}'] = df['u_in'].rolling(window).mean()
        features[f'u_in_rolling_std_{window}'] = df['u_in'].rolling(window).std()
        features[f'u_in_rolling_max_{window}'] = df['u_in'].rolling(window).max()
        features[f'u_in_rolling_min_{window}'] = df['u_in'].rolling(window).min()

    features['u_in_cumsum'] = df['u_in'].cumsum()
    features['u_in_cummax'] = df['u_in'].cummax()

    features['u_in_R'] = df['u_in'] * df['R']
    features['u_in_C'] = df['u_in'] * df['C']

    features['time_step'] = np.arange(len(df))
    features['time_sin'] = np.sin(2 * np.pi * features['time_step'] / 80)
    features['time_cos'] = np.cos(2 * np.pi * features['time_step'] / 80)

    breath_groups = df.groupby('breath_id')

    features['u_in_breath_mean'] = breath_groups['u_in'].transform('mean')
    features['u_in_breath_max'] = breath_groups['u_in'].transform('max')
    features['u_in_breath_std'] = breath_groups['u_in'].transform('std')

    features['u_out_lag1'] = df['u_out'].shift(1)
    features['inhale_start'] = (features['u_out_lag1'] == 1) & (df['u_out'] == 0)
    features['exhale_start'] = (features['u_out_lag1'] == 0) & (df['u_out'] == 1)

    features = features.fillna(method='bfill').fillna(0)

    return features

# df = pd.read_csv('train.csv')
# features = create_features(df)
# print(features.shape)
```

---

|------|---------|

```python
for delta_weight in [0.1, 0.15, 0.2, 0.25, 0.3]:
    loss = multi_task_loss(pressure_pred, delta_pred, pressure_true, delta_weight)
    val_mae = evaluate(val_loader, delta_weight)
    print(f'delta_weight={delta_weight}: val_mae={val_mae:.4f}')
```

|------|------|

**Group K-Fold：**
```python
from sklearn.model_selection import GroupKFold

gkf = GroupKFold(n_splits=5)

for fold, (train_idx, val_idx) in enumerate(gkf.split(X, y, groups=df['breath_id'])):
    print(f'Fold {fold}: Train={len(train_idx)}, Val={len(val_idx)}')

    X_train, X_val = X[train_idx], X[val_idx]
    y_train, y_val = y[train_idx], y[val_idx]

    model = train_model(X_train, y_train)
```

```python
from sklearn.model_selection import TimeSeriesSplit

tscv = TimeSeriesSplit(n_splits=5)

for fold, (train_idx, val_idx) in enumerate(tscv.split(X)):
    X_train, X_val = X[train_idx], X[val_idx]
    y_train, y_val = y[train_idx], y[val_idx]
```

|------|---------|------|

```python
def ensemble_predictions(predictions_list, weights=None):
    """

    Args:

    Returns:
    """
    if weights is None:
        ensemble_pred = np.mean(predictions_list, axis=0)
    else:
        ensemble_pred = np.average(predictions_list, axis=0, weights=weights)

    return ensemble_pred

# pred1 = model1.predict(X_val)
# pred2 = model2.predict(X_val)
# pred3 = model3.predict(X_val)
#
# ensemble = ensemble_predictions([pred1, pred2, pred3])
#
# weights = [0.3, 0.3, 0.4]
# ensemble = ensemble_predictions([pred1, pred2, pred3], weights)
```

|------|------|---------|

---

## Metadata

| Source | Date | Tags |
|--------|------|------|

---

## Cornell Birdcall Identification (BirdCLEF 2020)

  - 1st Place: Ryan Wong - F1 ~0.71
  - 2nd Place: niw
  - 3rd Place: TheoViel

#### 1st Place - ResNeSt + Attention Pooling + Large Ensemble (Ryan Wong)

  - ResNeSt-50 (Split-Attention variants of ResNet)
  ```python
  class AttentionPooling(nn.Module):
      def __init__(self, input_dim, hidden_dim=128):
          super().__init__()
          self.attention = nn.Sequential(
              nn.Linear(input_dim, hidden_dim),
              nn.Tanh(),
              nn.Linear(hidden_dim, 1)
          )

      def forward(self, x):
          # x: (batch, time, features)
          weights = F.softmax(self.attention(x), dim=1)
          return (x * weights).sum(dim=1)
  ```
  - Loss：Binary Cross-Entropy
  - Optimizer：AdamW
  - Batch Size：32
  - Epochs：~30

#### 2nd Place - Efficient Ensemble with Strong Data Augmentation (niw)

  - Mel-spectrogram（128 Mel bins）
  - MFCC（Mel-Frequency Cepstral Coefficients）
  - Chroma features
  - Spectral contrast
  - EfficientNet-B0
  - DenseNet-121

#### 3rd Place - Simple yet Effective Approach (TheoViel)

  - 128 Mel bins
  - Global Average Pooling
  - Early stopping
  - Learning rate scheduling

#### 4th Place - Logmels Spectral Features (dimabert & ususani)

  - 128 Mel bins
  - ResNet50
  - ResNeSt50
  - EfficientNet
- **Loss Function**：
  - Binary Cross-Entropy
  - Label Smoothing

#### 5th Place - Dual Approach with Different Architectures (Kramarenko Vladislav)

#### 6th Place - Sound Event Detection with Attention (Deep)

  - Temporal Attention Module
  - Multi-head Attention
  - Mixup augmentation
  - CutMix
  - SpecAugment

#### 7th Place - Three Geese and a GAN (CPJKU)

- **GAN-based Augmentation**：
  - Modified ResNet
  - Attention pooling
  - Multi-task learning

#### 17th Place - File-level Post-processing

```python
import torch
import torch.nn as nn
import torchaudio
import numpy as np

class MelSpectrogramExtractor:
    def __init__(self, sample_rate=32000, n_mels=128, n_fft=2048, hop_length=512):
        self.sample_rate = sample_rate
        self.n_mels = n_mels
        self.n_fft = n_fft
        self.hop_length = hop_length

        # Mel-spectrogram transform
        self.mel_transform = torchaudio.transforms.MelSpectrogram(
            sample_rate=sample_rate,
            n_fft=n_fft,
            hop_length=hop_length,
            n_mels=n_mels,
            f_min=0,
            f_max=16000
        )

        # Amplitude to dB
        self.amplitude_to_db = torchaudio.transforms.AmplitudeToDB()

    def extract(self, waveform):
        # Compute mel-spectrogram
        mel_spec = self.mel_transform(waveform)

        # Convert to dB scale
        mel_spec_db = self.amplitude_to_db(mel_spec)

        # Normalize to [0, 1]
        mel_spec_norm = (mel_spec_db - mel_spec_db.min()) / (mel_spec_db.max() - mel_spec_db.min() + 1e-8)

        return mel_spec_norm

extractor = MelSpectrogramExtractor(sample_rate=32000, n_mels=128)
waveform, sr = torchaudio.load("bird_audio.wav")
if sr != 32000:
    resampler = torchaudio.transforms.Resample(sr, 32000)
    waveform = resampler(waveform)
mel_spec = extractor.extract(waveform)
```

```python
import torch
import torch.nn as nn
import torch.nn.functional as F

class AttentionPooling2d(nn.Module):
    """2D Attention Pooling for spectrograms"""
    def __init__(self, in_channels, hidden_dim=128):
        super().__init__()
        self.attention = nn.Sequential(
            nn.Conv2d(in_channels, hidden_dim, kernel_size=1),
            nn.BatchNorm2d(hidden_dim),
            nn.Tanh(),
            nn.Conv2d(hidden_dim, 1, kernel_size=1)
        )

    def forward(self, x):
        # x: (batch, channels, time, freq)
        attn_weights = F.softmax(self.attention(x), dim=(2, 3))
        return (x * attn_weights).sum(dim=(2, 3))

class BirdcallClassifier(nn.Module):
    def __init__(self, num_classes=264, pretrained=True):
        super().__init__()

        from resnest.torch import resnest50

        self.backbone = resnest50(pretrained=pretrained)

        self.backbone.fc = nn.Identity()

        # Attention pooling
        self.attention_pool = AttentionPooling2d(2048, hidden_dim=128)

        # Classifier head
        self.classifier = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(2048, 512),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(512, num_classes)
        )

    def forward(self, x):
        # x: (batch, channels, time, freq) - Mel-spectrogram
        features = self.backbone(x)  # (batch, 2048, H, W)
        pooled = self.attention_pool(features)  # (batch, 2048)
        logits = self.classifier(pooled)  # (batch, num_classes)
        return logits

model = BirdcallClassifier(num_classes=264, pretrained=True)
mel_spec_batch = torch.randn(8, 3, 224, 512)  # (batch, channels, freq, time)
logits = model(mel_spec_batch)
probs = torch.sigmoid(logits)  # Multi-label prediction
```

```python
import torch
import torchaudio
import random

class BirdcallAugmentation:
    def __init__(self, sample_rate=32000):
        self.sample_rate = sample_rate

    def add_noise(self, waveform, noise_level=0.005):
        noise = torch.randn_like(waveform) * noise_level
        return waveform + noise

    def add_pink_noise(self, waveform, alpha=1):
        white_noise = torch.randn_like(waveform)
        freq_noise = torch.fft.rfft(white_noise)
        freqs = torch.fft.rfftfreq(waveform.shape[-1], 1/self.sample_rate)
        pink_filter = 1 / (freqs[1:] + 1e-8) ** alpha
        freq_noise[:, 1:] *= pink_filter
        pink_noise = torch.fft.irfft(freq_noise, n=waveform.shape[-1])
        return waveform + pink_noise * 0.01

    def time_mask(self, mel_spec, max_mask_pct=0.1):
        batch, channels, time, freq = mel_spec.shape
        mask_len = int(time * max_mask_pct)
        t = random.randint(0, mask_len)
        t0 = random.randint(0, time - t)
        mel_spec[:, :, t0:t0+t, :] = 0
        return mel_spec

    def freq_mask(self, mel_spec, max_mask_pct=0.1):
        batch, channels, time, freq = mel_spec.shape
        mask_len = int(freq * max_mask_pct)
        f = random.randint(0, mask_len)
        f0 = random.randint(0, freq - f)
        mel_spec[:, :, :, f0:f0+f] = 0
        return mel_spec

    def pitch_shift(self, waveform, shift=2.0):
        n_steps = int(shift * 10)
        resampler = torchaudio.transforms.Resample(
            self.sample_rate,
            int(self.sample_rate * (1 + shift * 0.1))
        )
        return resampler(waveform)

    def gain(self, waveform, min_gain=0.5, max_gain=1.5):
        gain = random.uniform(min_gain, max_gain)
        return waveform * gain

augmentation = BirdcallAugmentation(sample_rate=32000)
waveform, sr = torchaudio.load("bird_audio.wav")

waveform_aug = augmentation.add_noise(waveform)
waveform_aug = augmentation.gain(waveform_aug)
```

```python
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

def train_epoch(model, dataloader, criterion, optimizer, device, augmentation=None):
    model.train()
    total_loss = 0

    for batch in dataloader:
        waveforms, labels = batch
        waveforms = waveforms.to(device)
        labels = labels.to(device)

        if augmentation is not None:
            pass

        logits = model(waveforms)
        loss = criterion(logits, labels.float())

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        total_loss += loss.item()

    return total_loss / len(dataloader)

def train_model(model, train_loader, val_loader, num_epochs=30, device='cuda'):
    criterion = nn.BCEWithLogitsLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=num_epochs)

    best_val_score = 0

    for epoch in range(num_epochs):
        train_loss = train_epoch(model, train_loader, criterion, optimizer, device)

        val_score, val_loss = validate(model, val_loader, criterion, device)

        scheduler.step()

        print(f"Epoch {epoch+1}/{num_epochs}")
        print(f"Train Loss: {train_loss:.4f}")
        print(f"Val Loss: {val_loss:.4f}")
        print(f"Val F1: {val_score:.4f}")

        if val_score > best_val_score:
            best_val_score = val_score
            torch.save(model.state_dict(), 'best_model.pth')

    return model
```

```python
import numpy as np
import pandas as pd

class EnsemblePredictor:
    def __init__(self, models, threshold=0.5, min_votes=4):
        """
        Args:
        """
        self.models = models
        self.threshold = threshold
        self.min_votes = min_votes

    def predict(self, mel_spec_batch):
        all_predictions = []

        for model in self.models:
            model.eval()
            with torch.no_grad():
                logits = model(mel_spec_batch)
                probs = torch.sigmoid(logits)
                binary = (probs > self.threshold).float()
                all_predictions.append(binary.cpu().numpy())

        all_predictions = np.array(all_predictions)  # (n_models, batch, num_classes)
        votes = all_predictions.sum(axis=0)  # (batch, num_classes)

        final_pred = (votes >= self.min_votes).astype(int)

        return final_pred

def temporal_post_process(predictions, window_size=3, min_duration=3):
    """

    Args:
    """
    smoothed = predictions.copy()

    for i in range(predictions.shape[0]):
        start = max(0, i - window_size // 2)
        end = min(predictions.shape[0], i + window_size // 2 + 1)
        window = predictions[start:end]
        smoothed[i] = (window.sum(axis=0) > window_size // 2).astype(int)

    final = smoothed.copy()
    for c in range(predictions.shape[1]):
        col = smoothed[:, c]
        changes = np.diff(col, prepend=0, append=0)
        starts = np.where(changes == 1)[0]
        ends = np.where(changes == -1)[0]

        for s, e in zip(starts, ends):
            if e - s < min_duration:
                final[s:e, c] = 0

    return final

def create_submission(predictions, audio_ids, bird_species):
    """

    Args:
    """
    rows = []
    for audio_id, pred in zip(audio_ids, predictions):
        active_birds = [bird_species[i] for i, p in enumerate(pred) if p == 1]
        if active_birds:
            rows.append({
                'row_id': f"{audio_id}",
                'birds': ' '.join(active_birds)
            })
        else:
            rows.append({
                'row_id': f"{audio_id}",
                'birds': 'nocall'
            })

    submission = pd.DataFrame(rows)
    return submission
```

   - Binary Cross-Entropy Loss

---

## BirdCLEF 2021 - Birdcall Identification

  - 2nd Place: Christof Henkel
  - 3rd Place: shiro

#### 1st Place - Weak Supervision with PANNs (DR)

  - Mel-spectrogram（64/128 Mel bins）
  - Mixup
  - SpecAugment

#### 2nd Place - New Baseline with Strong Augmentation (Christof Henkel)

  - ResNet50 / ResNeSt50
  - EfficientNet variants
  - DenseNet-based models
  - Binary Cross-Entropy Loss

#### 3rd Place - Ensemble with Multiple Approaches (shiro)

  - ResNet variants
  - DenseNet variants
  - EfficientNet variants
  - Custom CNN architectures
  - MFCC features
  - Chroma features
  - Spectral contrast
  - Early stopping
  - Learning rate scheduling

#### 4th Place - Third Time's The Charm (tattaka)

  - ResNet50
  - ResNeSt50
  - DenseNet-121
  - Mixup + CutMix

#### 5th Place - Dual Approach Blending (Kramarenko Vladislav)

```python
import torch
import torch.nn as nn
from torchlibrosa.stft import Spectrogram, LogmelFilterBank

class PANNsCNN14(nn.Module):
    """
    """
    def __init__(self, sample_rate=32000, window_size=512, hop_size=320,
                 mel_bins=64, fmin=50, fmax=14000, num_classes=397):
        super().__init__()

        window = 'hann'
        center = True
        pad_mode = 'reflect'
        ref = 1.0
        amin = 1e-10
        top_db = None

        # Spectrogram extractor
        self.spectrogram_extractor = Spectrogram(
            n_fft=window_size,
            hop_length=hop_size,
            win_length=window_size,
            window=window,
            center=center,
            pad_mode=pad_mode,
            freeze_parameters=True)

        # Logmel feature extractor
        self.logmel_extractor = LogmelFilterBank(
            sr=sample_rate,
            n_fft=window_size,
            n_mels=mel_bins,
            fmin=fmin,
            fmax=fmax,
            ref=ref,
            amin=amin,
            top_db=top_db,
            freeze_parameters=True)

        self.spec_augment = SpecAugmentation(
            time_drop_width=64,
            time_stripes_num=2,
            freq_drop_width=8,
            freq_stripes_num=2)

        # CNN14 backbone
        self.bn0 = nn.BatchNorm2d(mel_bins)

        self.conv_block1 = ConvBlock(in_channels=1, out_channels=64)
        self.conv_block2 = ConvBlock(in_channels=64, out_channels=128)
        self.conv_block3 = ConvBlock(in_channels=128, out_channels=256)
        self.conv_block4 = ConvBlock(in_channels=256, out_channels=512)
        self.conv_block5 = ConvBlock(in_channels=512, out_channels=1024)
        self.conv_block6 = ConvBlock(in_channels=1024, out_channels=2048)

        self.fc1 = nn.Linear(2048, 2048, bias=True)
        self.fc_audioset = nn.Linear(2048, num_classes, bias=True)

        self.init_weight()

    def init_weight(self):
        init_bn(self.bn0)
        init_layer(self.fc1)
        init_layer(self.fc_audioset)

    def forward(self, input, mixup_lambda=None, device='cuda'):
        """
        Args:
            input: (batch_size, time_samples)
        Returns:
            output: (batch_size, num_classes)
        """
        # Spectrogram
        x = self.spectrogram_extractor(input)  # (batch, 1, time, freq)
        x = self.logmel_extractor(x)  # (batch, 1, time, mel_bins)

        # BN
        x = x.transpose(1, 3)
        x = self.bn0(x)
        x = x.transpose(1, 3)

        if self.training:
            x = self.spec_augment(x)

        # CNN blocks
        x = self.conv_block1(x, pool_size=(2, 2), pool_type='avg')
        x = F.dropout(x, p=0.2, training=self.training)

        x = self.conv_block2(x, pool_size=(2, 2), pool_type='avg')
        x = F.dropout(x, p=0.2, training=self.training)

        x = self.conv_block3(x, pool_size=(2, 2), pool_type='avg')
        x = F.dropout(x, p=0.2, training=self.training)

        x = self.conv_block4(x, pool_size=(2, 2), pool_type='avg')
        x = F.dropout(x, p=0.2, training=self.training)

        x = self.conv_block5(x, pool_size=(2, 2), pool_type='avg')
        x = F.dropout(x, p=0.2, training=self.training)

        x = self.conv_block6(x, pool_size=(1, 1), pool_type='avg')
        x = F.dropout(x, p=0.2, training=self.training)

        # Global pooling
        x = torch.mean(x, dim=3)  # (batch, channels, time)

        (x1, _) = torch.max(x, dim=2)  # (batch, channels)
        x2 = torch.mean(x, dim=2)  # (batch, channels)
        x = x1 + x2  # (batch, channels)

        x = F.dropout(x, p=0.5, training=self.training)
        x = F.relu_(self.fc1(x))
        embedding = F.dropout(x, p=0.5, training=self.training)
        clipwise_output = torch.sigmoid(self.fc_audioset(x))

        return clipwise_output

    def load_from_pretrained(self, pretrained_path):
        checkpoint = torch.load(pretrained_path, map_location='cpu')
        model_state = self.state_dict()
        pretrained_state = checkpoint['model']

        pretrained_state = {k: v for k, v in pretrained_state.items()
                          if k in model_state and v.shape == model_state[k].shape}

        model_state.update(pretrained_state)
        self.load_state_dict(model_state)
        print(f"Loaded pretrained weights from {pretrained_path}")

class ConvBlock(nn.Module):
    def __init__(self, in_channels, out_channels):
        super().__init__()

        self.conv1 = nn.Conv2d(in_channels=in_channels,
                              out_channels=out_channels,
                              kernel_size=(3, 3), stride=(1, 1),
                              padding=(1, 1), bias=False)
        self.conv2 = nn.Conv2d(in_channels=out_channels,
                              out_channels=out_channels,
                              kernel_size=(3, 3), stride=(1, 1),
                              padding=(1, 1), bias=False)
        self.bn1 = nn.BatchNorm2d(out_channels)
        self.bn2 = nn.BatchNorm2d(out_channels)

        self.init_weight()

    def init_weight(self):
        init_bn(self.bn1)
        init_bn(self.bn2)
        init_layer(self.conv1)
        init_layer(self.conv2)

    def forward(self, input, pool_size=(2, 2), pool_type='avg'):
        x = input
        x = F.relu_(self.bn1(self.conv1(x)))
        x = F.relu_(self.bn2(self.conv2(x)))
        if pool_type == 'max':
            x = F.max_pool2d(x, kernel_size=pool_size)
        elif pool_type == 'avg':
            x = F.avg_pool2d(x, kernel_size=pool_size)
        elif pool_type == 'avg+max':
            x1 = F.avg_pool2d(x, kernel_size=pool_size)
            x2 = F.max_pool2d(x, kernel_size=pool_size)
            x = x1 + x2
        else:
            raise ValueError(f'Unknown pool type: {pool_type}')
        return x

class SpecAugmentation(nn.Module):
    def __init__(self, time_drop_width, time_stripes_num,
                 freq_drop_width, freq_stripes_num):
        super().__init__()
        self.time_drop_width = time_drop_width
        self.time_stripes_num = time_stripes_num
        self.freq_drop_width = freq_drop_width
        self.freq_stripes_num = freq_stripes_num

    def forward(self, x):
        """x: (batch, channels, time, freq)"""
        self._mask_along_axis(x, self.time_drop_width,
                             self.time_stripes_num, axis=2)
        self._mask_along_axis(x, self.freq_drop_width,
                             self.freq_stripes_num, axis=3)
        return x

    def _mask_along_axis(self, x, drop_width, stripes_num, axis):
        for _ in range(stripes_num):
            drop_width = int(drop_width) if isinstance(drop_width, int) else \
                        int(drop_width * x.shape[axis])
            drop_start = int(torch.rand(1).item() * (x.shape[axis] - drop_width))

            if axis == 2:  # time axis
                x[:, :, drop_start:drop_start + drop_width, :] = 0
            elif axis == 3:  # freq axis
                x[:, :, :, drop_start:drop_start + drop_width] = 0
        return x

def init_layer(layer):
    """Initialize a Linear or Convolutional layer."""
    nn.init.xavier_uniform_(layer.weight)
    if hasattr(layer, 'bias'):
        if layer.bias is not None:
            layer.bias.data.fill_(0.)

def init_bn(bn):
    """Initialize a Batchnorm layer."""
    bn.bias.data.fill_(0.)
    bn.weight.data.fill_(1.)

model = PANNsCNN14(
    sample_rate=32000,
    window_size=512,
    hop_size=320,
    mel_bins=64,
    num_classes=397
)

# model.load_from_pretrained('path/to/pretrained/CNN14.pth')

waveform = torch.randn(4, 32000 * 5)  # (batch, 5 seconds at 32kHz)
with torch.no_grad():
    output = model(waveform)
print(output.shape)  # (4, 397)
```

```python
import torch
import numpy as np

def mixup_data(x, y, alpha=0.2):
    """

    Args:

    Returns:
    """
    if alpha > 0:
        lam = np.random.beta(alpha, alpha)
    else:
        lam = 1

    batch_size = x.size(0)
    index = torch.randperm(batch_size).to(x.device)

    mixed_x = lam * x + (1 - lam) * x[index, :]
    y_a, y_b = y, y[index]

    return mixed_x, y_a, y_b, lam

def mixup_criterion(criterion, pred, y_a, y_b, lam):
    return lam * criterion(pred, y_a) + (1 - lam) * criterion(pred, y_b)

criterion = nn.BCEWithLogitsLoss()

for batch_idx, (waveforms, labels) in enumerate(train_loader):
    waveforms = waveforms.to(device)
    labels = labels.to(device)

    waveforms_mixed, labels_a, labels_b, lam = mixup_data(
        waveforms, labels, alpha=0.2
    )

    outputs = model(waveforms_mixed)

    loss = mixup_criterion(criterion, outputs, labels_a, labels_b, lam)

    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
```

```python
import torch
import torch.nn as nn
from torch.utils.data import Dataset

class BirdcallWeakDataset(Dataset):
    """
    """
    def __init__(self, audio_files, labels, audio_transforms=None,
                 duration=5, sample_rate=32000):
        self.audio_files = audio_files
        self.labels = labels  # Multi-hot labels: (num_samples, num_classes)
        self.audio_transforms = audio_transforms
        self.duration = duration
        self.sample_rate = sample_rate

    def __len__(self):
        return len(self.audio_files)

    def __getitem__(self, idx):
        waveform, sr = torchaudio.load(self.audio_files[idx])

        if sr != self.sample_rate:
            resampler = torchaudio.transforms.Resample(sr, self.sample_rate)
            waveform = resampler(waveform)

        target_length = self.duration * self.sample_rate
        if waveform.shape[1] > target_length:
            start = torch.randint(0, waveform.shape[1] - target_length, (1,)).item()
            waveform = waveform[:, start:start + target_length]
        elif waveform.shape[1] < target_length:
            padding = target_length - waveform.shape[1]
            waveform = torch.nn.functional.pad(waveform, (0, padding))

        label = self.labels[idx]

        if self.audio_transforms is not None:
            waveform = self.audio_transforms(waveform)

        return waveform, label

class AttentionPooling(nn.Module):
    """
    """
    def __init__(self, input_dim, hidden_dim=128):
        super().__init__()
        self.attention = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, 1)
        )

    def forward(self, x):
        """
        Args:
            x: (batch, time_steps, features)

        Returns:
            pooled: (batch, features)
        """
        attn_weights = F.softmax(self.attention(x), dim=1)
        pooled = (x * attn_weights).sum(dim=1)
        return pooled, attn_weights

class WeaklySupervisedBirdcallModel(nn.Module):
    """
    """
    def __init__(self, num_classes=397, pretrained=True):
        super().__init__()

        self.backbone = PANNsCNN14(num_classes=num_classes, pretrained=pretrained)

        self.backbone.fc_audioset = nn.Identity()

        self.attention_pool = AttentionPooling(feature_dim, hidden_dim=128)

        self.classifier = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(feature_dim, 512),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(512, num_classes)
        )

    def forward(self, x, return_attention=False):
        """
        Args:
            x: (batch, time_samples)

        Returns:
            logits: (batch, num_classes)
            attention_weights (optional): (batch, time_steps)
        """
        features = self.extract_features(x)  # (batch, time_steps, feature_dim)

        pooled, attn_weights = self.attention_pool(features)

        logits = self.classifier(pooled)

        if return_attention:
            return logits, attn_weights
        return logits

    def extract_features(self, x):
        """
        """
        with torch.no_grad():
            features = self.backbone.fc1(
                torch.mean(self.backbone.bn0(
                    self.backbone.logmel_extractor(
                        self.backbone.spectrogram_extractor(x)
                    ).transpose(1, 3)
                ), dim=3)
            )
        return features.unsqueeze(1)  # (batch, 1, feature_dim)

def train_weakly_supervised(model, dataloader, criterion, optimizer, device, use_mixup=True):
    model.train()

    for waveforms, labels in dataloader:
        waveforms = waveforms.to(device)
        labels = labels.to(device).float()

        if use_mixup and np.random.rand() < 0.5:
            waveforms, labels_a, labels_b, lam = mixup_data(waveforms, labels, alpha=0.2)

        logits = model(waveforms)

        if use_mixup and np.random.rand() < 0.5:
            loss = mixup_criterion(criterion, logits, labels_a, labels_b, lam)
        else:
            loss = criterion(logits, labels)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

def visualize_attention(model, waveform, bird_name):
    model.eval()
    with torch.no_grad():
        logits, attention = model(waveform.unsqueeze(0), return_attention=True)

    # attention: (1, time_steps)
    attention = attention.squeeze(0).cpu().numpy()

    import matplotlib.pyplot as plt
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 6))

    ax1.plot(waveform.cpu().numpy().T)
    ax1.set_title(f'Audio Waveform - {bird_name}')
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Amplitude')

    ax2.plot(attention)
    ax2.set_title('Attention Weights')
    ax2.set_xlabel('Time Step')
    ax2.set_ylabel('Attention Weight')

    plt.tight_layout()
    plt.savefig('attention_visualization.png')
    plt.close()
```

```python
import torch
import numpy as np

def predict_with_sliding_window(model, audio_path, window_size=5,
                                hop_size=2.5, sample_rate=32000,
                                device='cuda'):
    """

    Args:

    Returns:
        predictions: (num_windows, num_classes)
    """
    model.eval()

    waveform, sr = torchaudio.load(audio_path)
    if sr != sample_rate:
        resampler = torchaudio.transforms.Resample(sr, sample_rate)
        waveform = resampler(waveform)

    window_samples = int(window_size * sample_rate)
    hop_samples = int(hop_size * sample_rate)

    predictions = []
    timestamps = []

    with torch.no_grad():
        for start in range(0, waveform.shape[1] - window_samples + 1, hop_samples):
            end = start + window_samples
            window = waveform[:, start:end].to(device)

            logits = model(window)
            probs = torch.sigmoid(logits).cpu().numpy()

            predictions.append(probs[0])
            timestamps.append(start / sample_rate)

    predictions = np.array(predictions)
    timestamps = np.array(timestamps)

    return predictions, timestamps

def aggregate_predictions(predictions, threshold=0.5, min_duration=3):
    """

    Args:
        predictions: (num_windows, num_classes)

    Returns:
    """
    binary_pred = (predictions > threshold).astype(int)

    final_pred = binary_pred.copy()
    for c in range(binary_pred.shape[1]):
        col = binary_pred[:, c]

        changes = np.diff(col, prepend=0, append=0)
        starts = np.where(changes == 1)[0]
        ends = np.where(changes == -1)[0]

        for s, e in zip(starts, ends):
            if e - s < min_duration:
                final_pred[s:e, c] = 0

    return final_pred

def create_birdclef_submission(predictions, timestamps, audio_id,
                               bird_species, threshold=0.5):
    """

    Args:

    Returns:
    """
    rows = []

    for i, (pred, ts) in enumerate(zip(predictions, timestamps)):
        active_birds = []
        for j, p in enumerate(pred):
            if p > threshold:
                active_birds.append(bird_species[j])

        row_id = f"{audio_id}_{ts:.1f}"

        if active_birds:
            rows.append({
                'row_id': row_id,
                'birds': ' '.join(active_birds)
            })
        else:
            rows.append({
                'row_id': row_id,
                'birds': 'nocall'
            })

    return rows

model = WeaklySupervisedBirdcallModel(num_classes=397)
model = model.to(device)
model.load_state_dict(torch.load('best_model.pth'))

audio_path = 'test_soundscape.wav'
predictions, timestamps = predict_with_sliding_window(
    model, audio_path, window_size=5, hop_size=2.5, device=device
)

final_pred = aggregate_predictions(predictions, threshold=0.5, min_duration=3)

rows = create_birdclef_submission(
    predictions, timestamps, 'soundscape_01', bird_species, threshold=0.5
)

import pandas as pd
submission = pd.DataFrame(rows)
submission.to_csv('submission.csv', index=False)
```

   - Binary Cross-Entropy Loss

---

## BirdCLEF 2022 - Endangered Bird Sounds Classification

  - 1st Place: kdl - "It's not all BirdNet"
  - 2nd Place: Leon Shangguan
  - 3rd Place: uemu-slime

#### 1st Place - Beyond BirdNet (kdl)

  - TTA（Test Time Augmentation）

#### 2nd Place - SED + CNN with 7 Models Ensemble (Leon Shangguan)

  - ResNet50/ResNeSt50 backbone
- **TTA**：
  - SpecAugment
  - Mixup

#### 3rd Place - 18 Checkpoints Ensemble (uemu-slime)

  - ResNet50
  - ResNeSt50
  - EfficientNet-B0/B3
  - SpecAugment
  - Mixup

#### 4th Place - CNN-based Ensemble (Kramarenko Vladislav)

  - ResNet50
  - ResNeSt50
  - DenseNet-121
  - Mel-spectrogram
  - Early stopping

#### 5th Place - Reimplementation of 2021 2nd Place (common-kestrel)

  - ResNet50
  - ResNeSt50
  - EfficientNet-B0
  - DenseNet-121

```python
import torch
import torch.nn as nn
import torch.nn.functional as F

class SEDModel(nn.Module):
    """

    """
    def __init__(self, num_classes=152, backbone='resnet50',
                 sample_rate=32000, window_size=5, hop_size=512):
        super().__init__()

        self.num_classes = num_classes
        self.window_size = window_size
        self.sample_rate = sample_rate

        self.mel_extractor = MelSpectrogramExtractor(
            sample_rate=sample_rate,
            n_mels=128,
            n_fft=2048,
            hop_length=hop_size
        )

        if backbone == 'resnet50':
            import torchvision.models as models
            self.backbone = models.resnet50(pretrained=True)
            self.backbone.conv1 = nn.Conv2d(
                1, 64, kernel_size=7, stride=2, padding=3, bias=False
            )
            feature_dim = 2048
        elif backbone == 'resnest50':
            feature_dim = 2048

        self.backbone.fc = nn.Identity()

        self.fc = nn.Linear(feature_dim, num_classes)

    def forward(self, waveform, return_frames=False):
        """
        Args:
            waveform: (batch, time_samples)

        Returns:
        """
        batch_size = waveform.shape[0]

        mel_spec = self.mel_extractor.extract(waveform)  # (batch, 1, mel_bins, time_frames)

        features = self.extract_features_with_time(mel_spec)  # (batch, time_frames, feature_dim)

        framewise_output = self.fc(features)  # (batch, time_frames, num_classes)

        if return_frames:
            return framewise_output

        output, _ = torch.max(framewise_output, dim=1)  # (batch, num_classes)

        return output

    def extract_features_with_time(self, mel_spec):
        """

        """
        batch, channels, mel_bins, time_frames = mel_spec.shape

        # Reshape: (batch * time_frames, channels, mel_bins, 1)
        mel_spec_reshaped = mel_spec.permute(0, 3, 1, 2).reshape(
            batch * time_frames, channels, mel_bins, 1
        )

        features = self.backbone(mel_spec_reshaped)  # (batch * time_frames, feature_dim)

        features = features.reshape(batch, time_frames, -1)

        return features

class MultiScaleSEDModel(nn.Module):
    """

    """
    def __init__(self, num_classes=152, short_duration=5, long_duration=10):
        super().__init__()

        self.num_classes = num_classes

        self.short_model = SEDModel(
            num_classes=num_classes,
            window_size=short_duration
        )

        self.long_model = SEDModel(
            num_classes=num_classes,
            window_size=long_duration
        )

    def forward(self, waveform_short, waveform_long, use_and_rule=True):
        """
        Args:

        Returns:
            output: (batch, num_classes)
        """
        output_short = self.short_model(waveform_short)  # (batch, num_classes)
        prob_short = torch.sigmoid(output_short)

        output_long = self.long_model(waveform_long)  # (batch, num_classes)
        prob_long = torch.sigmoid(output_long)

        if use_and_rule:
            prob_final = prob_short * prob_long
        else:
            prob_final = torch.clamp(prob_short + prob_long, 0, 1)

        return prob_final

model = MultiScaleSEDModel(num_classes=152, short_duration=5, long_duration=10)

waveform_short = torch.randn(4, 5 * 32000)  # 4 samples, 5 seconds
waveform_long = torch.randn(4, 10 * 32000)   # 4 samples, 10 seconds

with torch.no_grad():
    prob = model(waveform_short, waveform_long, use_and_rule=True)
print(prob.shape)  # (4, 152)
```

#### TTA（Test Time Augmentation）
```python
import torch
import numpy as np

def predict_with_tta(model, audio_path, window_size=5, tta_shifts=[0, 1, 2],
                     sample_rate=32000, device='cuda'):
    """

    Args:

    Returns:
    """
    model.eval()

    waveform, sr = torchaudio.load(audio_path)
    if sr != sample_rate:
        resampler = torchaudio.transforms.Resample(sr, sample_rate)
        waveform = resampler(waveform)

    window_samples = int(window_size * sample_rate)

    all_tta_predictions = []

    for shift in tta_shifts:
        shift_samples = int(shift * sample_rate)

        start_positions = list(range(shift_samples, waveform.shape[1] - window_samples + 1,
                                    int(window_size * sample_rate)))

        predictions = []

        with torch.no_grad():
            for start in start_positions:
                end = start + window_samples
                window = waveform[:, start:end].to(device)

                logits = model(window)
                probs = torch.sigmoid(logits).cpu().numpy()
                predictions.append(probs[0])

        predictions = np.array(predictions)
        all_tta_predictions.append(predictions)

    all_tta_predictions = np.array(all_tta_predictions)  # (num_shifts, num_windows, num_classes)

    avg_predictions = np.mean(all_tta_predictions, axis=0)

    return avg_predictions

model = SEDModel(num_classes=152)
model = model.to(device)
model.load_state_dict(torch.load('best_model.pth'))

audio_path = 'test_soundscape.wav'
predictions = predict_with_tta(
    model, audio_path, window_size=5, tta_shifts=[0, 1, 2], device=device
)

threshold = 0.5
binary_pred = (predictions > threshold).astype(int)
```

```python
import numpy as np

def and_rule_post_process(short_pred, long_pred, threshold=0.5):
    """

    Args:

    Returns:
    """
    binary_short = (short_pred > threshold).astype(int)
    binary_long = (long_pred > threshold).astype(int)

    scale_factor = len(short_pred) / len(long_pred)

    final_pred = np.zeros_like(binary_short)

    for i in range(len(short_pred)):
        long_idx = int(i / scale_factor)

        if long_idx < len(binary_long):
            final_pred[i] = binary_short[i] & binary_long[long_idx]
        else:
            final_pred[i] = binary_short[i]

    return final_pred

final_pred = and_rule_post_process(short_pred, long_pred, threshold=0.5)
```

```python
import torch
import numpy as np

class EnsembleModel:
    """
    """
    def __init__(self, models, weights=None, device='cuda'):
        """
        Args:
        """
        self.models = models
        self.device = device

        if weights is None:
            self.weights = [1.0 / len(models)] * len(models)
        else:
            total = sum(weights)
            self.weights = [w / total for w in weights]

        for model in self.models:
            model.to(device)
            model.eval()

    def predict(self, waveform):
        """

        Args:

        Returns:
        """
        all_predictions = []

        with torch.no_grad():
            for model in self.models:
                logits = model(waveform)
                probs = torch.sigmoid(logits).cpu().numpy()
                all_predictions.append(probs)

        all_predictions = np.array(all_predictions)  # (num_models, batch, num_classes)

        ensemble_pred = np.zeros_like(all_predictions[0])
        for i, pred in enumerate(all_predictions):
            ensemble_pred += self.weights[i] * pred

        return ensemble_pred

    def predict_from_files(self, model_paths, ModelClass, model_kwargs, waveform):
        """

        Args:

        Returns:
        """
        all_predictions = []

        for path in model_paths:
            model = ModelClass(**model_kwargs)
            model.load_state_dict(torch.load(path))
            model.to(self.device)
            model.eval()

            with torch.no_grad():
                logits = model(waveform)
                probs = torch.sigmoid(logits).cpu().numpy()
                all_predictions.append(probs)

        all_predictions = np.array(all_predictions)

        ensemble_pred = np.zeros_like(all_predictions[0])
        for i, pred in enumerate(all_predictions):
            ensemble_pred += self.weights[i] * pred

        return ensemble_pred

models = [
    SEDModel(num_classes=152, backbone='resnet50'),
    SEDModel(num_classes=152, backbone='resnest50'),
    SEDModel(num_classes=152, backbone='efficientnet_b0'),
]

for i, model in enumerate(models):
    model.load_state_dict(torch.load(f'model_{i}.pth'))

ensemble = EnsembleModel(models, weights=None, device=device)

waveform = torch.randn(4, 5 * 32000).to(device)
predictions = ensemble.predict(waveform)
print(predictions.shape)  # (4, 152)
```

```python
"""

"""

class BirdNetModel(nn.Module):
    """

    """
    def __init__(self, num_classes=152, pretrained_path=None):
        super().__init__()

        import torchvision.models as models
        self.backbone = models.resnet50(pretrained=True)

        self.backbone.conv1 = nn.Conv2d(
            1, 64, kernel_size=7, stride=2, padding=3, bias=False
        )

        feature_dim = 2048

        self.classifier = nn.Sequential(
            nn.Dropout(0.5),
            nn.Linear(feature_dim, num_classes)
        )

        if pretrained_path is not None:
            self.load_pretrained(pretrained_path)

    def load_pretrained(self, path):
        state_dict = torch.load(path, map_location='cpu')

        model_state = self.state_dict()
        pretrained_state = {
            k: v for k, v in state_dict.items()
            if k in model_state and v.shape == model_state[k].shape
        }

        model_state.update(pretrained_state)
        self.load_state_dict(model_state)
        print(f"Loaded pretrained weights from {path}")

    def forward(self, mel_spec):
        """
        Args:
            mel_spec: (batch, 1, mel_bins, time_frames)

        Returns:
            logits: (batch, num_classes)
        """
        features = self.backbone(mel_spec)
        logits = self.classifier(features)
        return logits

# model = BirdNetModel(num_classes=152, pretrained_path='birdnet.pth')
# model.eval()
# with torch.no_grad():
#     logits = model(mel_spec)
#     probs = torch.sigmoid(logits)
```

6. **TTA（Test Time Augmentation）**：

---

## Rainforest Connection Species Audio Detection 2021

  - 1st Place: watercooled
  - 7th Place: Beluga & Peter
  - 11th Place: cpmp
  - 13th Place: Ryan Epp

#### 1st Place - Image Classification Approach (watercooled)

  - EfficientNet-B3
  - Mel-spectrogram（128 Mel bins）

#### 7th Place - Strong Baseline with Ensemble (Beluga & Peter)

  - EfficientNet-B3
  - DenseNet-121
  - SpecAugment
  - Mixup

#### 11th Place - The 0.931 Magic Explained (cpmp)

#### 13th Place - Mean Co-Teachers and Noisy Students (Ryan Epp)

   - Label-Weighted Label-Ranking Average Precision

   - Mixup

---

## AMP®-Parkinson's Disease Progression Prediction 2023

  - 1st Place: Connecting Dotts
  - 2nd Place: No Luck All Skill
  - 3rd Place: Hajime Tamura

#### 1st Place - Feature Engineering + Gradient Boosting (Connecting Dotts)

  - XGBoost/LightGBM
  - CatBoost

#### 2nd Place - Strong Feature Engineering (No Luck All Skill)

#### 3rd Place - Robust Modeling Approach (Hajime Tamura)

  - XGBoost/LightGBM

   - Gradient Boosting (XGBoost, LightGBM, CatBoost)

   - SMAPE (Symmetric MAPE)
