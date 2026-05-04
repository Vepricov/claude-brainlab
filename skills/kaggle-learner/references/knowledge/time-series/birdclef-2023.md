# BirdCLEF 2023
> Last updated: 2026-01-25
> Source count: 10+
---

### BirdCLEF 2023 - Bird Sound Identification (2023)

|------|----------|------------|----------|
| **2nd** | Griffith | ~0.75+ | SED + CNN with 7 models ensemble |
| **3rd** | ADSR | ~0.75 | SED with attention on Mel frequency bands |

|--------|---------------|---------------|-----------------|

---

---

### 1st Place - Volodymyr Sydorskyi (Volodymyr)

   - Checkpoint averaging

- GitHub: [VSydorskyy/BirdCLEF_2023_1st_place](https://github.com/VSydorskyy/BirdCLEF_2023_1st_place)
- Kaggle Writeup: [1st place solution: Correct Data is All You Need](https://www.kaggle.com/competitions/birdclef-2023/writeups/volodymyr-1st-place-solution-correct-data-is-all-y)

---

### 2nd Place - Griffith

   - BCE Loss（Binary Cross Entropy）
   - Label Smoothing

- EfficientNetV2-s backbone

- GitHub: [LIHANG-HONG/birdclef2023-2nd-place-solution](https://github.com/LIHANG-HONG/birdclef2023-2nd-place-solution)
- Kaggle Writeup: [2nd place solution: SED + CNN with 7 models ensemble](https://www.kaggle.com/competitions/birdclef-2023/writeups/griffith-2nd-place-solution-sed-cnn-with-7-models-)

---

### 3rd Place - ADSR

- Kaggle Writeup: [3rd place solution: SED with attention on Mel frequency bands](https://www.kaggle.com/competitions/birdclef-2023/writeups/adsr-3rd-place-solution-sed-with-attention-on-mel-)

---

### 4th Place - ATFujita

   - Checkpoint averaging

- BaseModel + Knowledge Distillation

- GitHub: [AtsunoriFujita/BirdCLEF-2023-Identify-bird-calls-in-soundscapes](https://github.com/AtsunoriFujita/BirdCLEF-2023-Identify-bird-calls-in-soundscapes)
- Kaggle Writeup: [4th Place Solution: Knowledge Distillation Is All You Need](https://www.kaggle.com/competitions/birdclef-2023/writeups/atfujita-4th-place-solution-knowledge-distillation)

---

### 5th Place - Yevhenii Maslov

- EfficientNetV2 backbone

- GitHub: [yevmaslov](https://github.com/yevmaslov)
- Kaggle Writeup: [5th place solution](https://www.kaggle.com/competitions/birdclef-2023/writeups/yevhenii-maslov-5th-place-solution)

---

### 8th Place - FURU-NAG

- Kaggle Writeup: [8th Place Solution: Implementing Multimodal Data Augmentation Methods](https://www.kaggle.com/competitions/birdclef-2023/writeups/furu-nag-8th-place-solution-implementing-multimoda)

---

### 18th Place - SED with Attention

- Kaggle Writeup: [18th place solution: SED with attention](https://www.kaggle.com/competitions/birdclef-2023/writeups/18th-place-solution-sed-with-attention)

---

```python
import torch
import torchaudio
import torch.nn as nn
import numpy as np
import librosa

class MelSpectrogramExtractor:

    def __init__(
        self,
        sample_rate: int = 32000,
        n_mels: int = 128,
        n_fft: int = 2048,
        hop_length: int = 512,
        fmin: float = 64.0,
        fmax: float = 16000.0,
        power: float = 2.0,
        normalize: bool = True,
    ):
        self.sample_rate = sample_rate
        self.n_mels = n_mels
        self.n_fft = n_fft
        self.hop_length = hop_length
        self.fmin = fmin
        self.fmax = fmax

        self.mel_transform = torchaudio.transforms.MelSpectrogram(
            sample_rate=sample_rate,
            n_fft=n_fft,
            hop_length=hop_length,
            n_mels=n_mels,
            f_min=fmin,
            f_max=fmax,
            power=power,
            normalized=normalize,
        )

    def extract(self, waveform: torch.Tensor) -> torch.Tensor:
        """

        Args:

        Returns:
        """
        if waveform.dim() == 1:
            waveform = waveform.unsqueeze(0)

        mel_spec = self.mel_transform(waveform)

        mel_spec = torch.log(mel_spec + 1e-9)

        return mel_spec

    def extract_fixed_length(
        self, waveform: torch.Tensor, target_length: int
    ) -> torch.Tensor:
        """

        Args:
            waveform: (num_samples,)

        Returns:
            mel_spec: (n_mels, target_length)
        """
        mel_spec = self.extract(waveform).squeeze(0)

        if mel_spec.shape[1] < target_length:
            pad_length = target_length - mel_spec.shape[1]
            mel_spec = nn.functional.pad(mel_spec, (0, pad_length))
        else:
            start = (mel_spec.shape[1] - target_length) // 2
            mel_spec = mel_spec[:, start:start + target_length]

        return mel_spec

CONFIGS = {
        "n_mels": 128,
        "n_fft": 2048,
        "hop_length": 512,
        "fmin": 64.0,
        "fmax": 16000.0,
    },
        "n_mels": 256,
        "n_fft": 4096,
        "hop_length": 1024,
        "fmin": 64.0,
        "fmax": 16000.0,
    },
}

extractor = MelSpectrogramExtractor(**CONFIGS["config_128"])
waveform, sr = torchaudio.load("audio.wav")
if sr != 32000:
    waveform = torchaudio.transforms.Resample(sr, 32000)(waveform)
```

```python
import torch
import torch.nn as nn
import timm

class SEDModel(nn.Module):
    """
    """

    def __init__(
        self,
        model_name: str = "tf_efficientnetv2_s",
        num_classes: int = 264,
        pretrained: bool = True,
        in_channels: int = 1,
        rnn_layers: int = 1,
        rnn_hidden: int = 128,
    ):
        super().__init__()

        # Backbone（EfficientNetV2）
        self.backbone = timm.create_model(
            model_name,
            pretrained=pretrained,
            in_chans=in_channels,
        )

        backbone_features = self.backbone.num_features

        self.rnn = nn.LSTM(
            input_size=backbone_features,
            hidden_size=rnn_hidden,
            num_layers=rnn_layers,
            batch_first=True,
            bidirectional=True,
        )

        self.classifier = nn.Sequential(
            nn.Linear(rnn_hidden * 2, rnn_hidden),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(rnn_hidden, num_classes),
        )

    def forward(self, x, return_segmentwise=False):
        """
        Args:
            x: (batch, channels, n_mels, time)

        Returns:
        """
        batch_size = x.size(0)

        # (batch, channels, n_mels, time) -> (batch, features, time')
        features = self.backbone(x)

        features = features.permute(0, 2, 1)

        # (batch, time', features) -> (batch, time', rnn_hidden * 2)
        rnn_out, _ = self.rnn(features)

        if return_segmentwise:
            segmentwise_logits = self.classifier(rnn_out)
            return segmentwise_logits
        else:
            global_features = rnn_out.mean(dim=1)  # (batch, rnn_hidden * 2)
            logits = self.classifier(global_features)
            return logits

model = SEDModel(
    model_name="tf_efficientnetv2_s",
    num_classes=264,
    pretrained=True,
    in_channels=1,
    rnn_layers=1,
    rnn_hidden=128,
)

mel_spec = torch.randn(4, 1, 128, 313)  # (batch, channels, n_mels, time)
logits = model(mel_spec)  # (batch, 264)
segmentwise_logits = model(mel_spec, return_segmentwise=True)  # (batch, time, 264)
```

```python
import torch
import torch.nn as nn
import torch.nn.functional as F
import timm

class MelFrequencyAttention(nn.Module):

    def __init__(self, n_mels: int, reduction: int = 8):
        super().__init__()
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.max_pool = nn.AdaptiveMaxPool2d(1)

        self.fc = nn.Sequential(
            nn.Linear(n_mels, n_mels // reduction, bias=False),
            nn.ReLU(inplace=True),
            nn.Linear(n_mels // reduction, n_mels, bias=False),
        )
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        """
        Args:
            x: (batch, channels, n_mels, time)

        Returns:
            attention: (batch, channels, n_mels, 1)
        """
        avg_out = self.avg_pool(x).squeeze(-1).squeeze(-1)  # (batch, channels)
        max_out = self.max_pool(x).squeeze(-1).squeeze(-1)  # (batch, channels)

        avg_out = self.fc(avg_out)
        max_out = self.fc(max_out)

        attention = self.sigmoid(avg_out + max_out)
        attention = attention.unsqueeze(-1).unsqueeze(-1)  # (batch, channels, n_mels, 1)

        return attention

class SEDWithMelAttention(nn.Module):

    def __init__(
        self,
        model_name: str = "tf_efficientnetv2_s",
        num_classes: int = 264,
        pretrained: bool = True,
        n_mels: int = 128,
        rnn_hidden: int = 128,
    ):
        super().__init__()

        # Backbone
        self.backbone = timm.create_model(
            model_name,
            pretrained=pretrained,
            in_chans=1,
            num_classes=0,
            global_pool="",
        )

        backbone_features = self.backbone.num_features

        self.mel_attention = MelFrequencyAttention(n_mels=n_mels)

        self.rnn = nn.LSTM(
            input_size=backbone_features,
            hidden_size=rnn_hidden,
            num_layers=1,
            batch_first=True,
            bidirectional=True,
        )

        self.classifier = nn.Sequential(
            nn.Linear(rnn_hidden * 2, rnn_hidden),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(rnn_hidden, num_classes),
        )

    def forward(self, x, return_segmentwise=False):
        """
        Args:
            x: (batch, 1, n_mels, time)

        Returns:
            logits: (batch, num_classes)
        """
        features = self.backbone(x)  # (batch, features, time')

        mel_att = self.mel_attention(features)  # (batch, features, n_mels, 1)
        features = features * mel_att

        features = features.permute(0, 2, 1)  # (batch, time', features)

        # RNN
        rnn_out, _ = self.rnn(features)

        if return_segmentwise:
            segmentwise_logits = self.classifier(rnn_out)
            return segmentwise_logits
        else:
            global_features = rnn_out.mean(dim=1)
            logits = self.classifier(global_features)
            return logits

model = SEDWithMelAttention(
    model_name="tf_efficientnetv2_s",
    num_classes=264,
    pretrained=True,
    n_mels=128,
    rnn_hidden=128,
)
```

```python
import torch
import torchaudio
import numpy as np

class AudioAugmentation:

    def __init__(
        self,
        sample_rate: int = 32000,
        apply_prob: float = 0.5,
    ):
        self.sample_rate = sample_rate
        self.apply_prob = apply_prob

    def __call__(self, waveform: torch.Tensor) -> torch.Tensor:
        if torch.rand(1).item() > self.apply_prob:
            return waveform

        augmentations = [
            self._pitch_shift,
            self._time_stretch,
            self._add_noise,
            self._gain,
        ]

        np.random.shuffle(augmentations)

        num_augment = np.random.randint(1, 3)
        for aug in augmentations[:num_augment]:
            waveform = aug(waveform)

        return waveform

    def _pitch_shift(self, waveform: torch.Tensor) -> torch.Tensor:
        if torch.rand(1).item() > 0.5:
            return waveform

        waveform_np = waveform.numpy()

        shifted = librosa.effects.pitch_shift(
            waveform_np,
            sr=self.sample_rate,
            n_steps=n_steps,
        )

        return torch.from_numpy(shifted).float()

    def _time_stretch(self, waveform: torch.Tensor) -> torch.Tensor:
        if torch.rand(1).item() > 0.5:
            return waveform

        rate = np.random.uniform(0.8, 1.2)
        waveform_np = waveform.numpy()

        stretched = librosa.effects.time_stretch(
            waveform_np,
            rate=rate,
        )

        return torch.from_numpy(stretched).float()

    def _add_noise(self, waveform: torch.Tensor) -> torch.Tensor:
        if torch.rand(1).item() > 0.5:
            return waveform

        noise = torch.randn_like(waveform)

        signal_power = waveform.mean() ** 2
        noise_power = noise.mean() ** 2

        noise = noise * torch.sqrt(signal_power / (noise_power * (10 ** (snr / 10))))

        return waveform + noise

    def _gain(self, waveform: torch.Tensor) -> torch.Tensor:
        if torch.rand(1).item() > 0.5:
            return waveform

        gain = np.random.uniform(0.8, 1.2)
        return waveform * gain

class SpecAugment:

    def __init__(
        self,
        time_mask_param: int = 50,
        freq_mask_param: int = 16,
        num_time_masks: int = 2,
        num_freq_masks: int = 2,
        apply_prob: float = 0.5,
    ):
        self.time_mask_param = time_mask_param
        self.freq_mask_param = freq_mask_param
        self.num_time_masks = num_time_masks
        self.num_freq_masks = num_freq_masks
        self.apply_prob = apply_prob

    def __call__(self, spec: torch.Tensor) -> torch.Tensor:
        """
        Args:
            spec: (channels, n_mels, time)

        Returns:
            augmented_spec: (channels, n_mels, time)
        """
        if torch.rand(1).item() > self.apply_prob:
            return spec

        for _ in range(self.num_time_masks):
            t = np.random.randint(0, self.time_mask_param)
            t0 = np.random.randint(0, max(1, spec.size(-1) - t))
            spec[:, :, t0:t0 + t] = 0

        for _ in range(self.num_freq_masks):
            f = np.random.randint(0, self.freq_mask_param)
            f0 = np.random.randint(0, max(1, spec.size(-2) - f))
            spec[:, f0:f0 + f, :] = 0

        return spec

class MixUp:

    def __init__(self, alpha: float = 0.5, apply_prob: float = 0.5):
        self.alpha = alpha
        self.apply_prob = apply_prob

    def __call__(
        self,
        mel_spec: torch.Tensor,
        labels: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """
        Args:
            mel_spec: (batch, channels, n_mels, time)
            labels: (batch, num_classes)

        Returns:
            mixed_mel, mixed_labels
        """
        if torch.rand(1).item() > self.apply_prob:
            return mel_spec, labels

        batch_size = mel_spec.size(0)

        lam = np.random.beta(self.alpha, self.alpha)

        index = torch.randperm(batch_size)

        mixed_mel = lam * mel_spec + (1 - lam) * mel_spec[index]
        mixed_labels = lam * labels + (1 - lam) * labels[index]

        return mixed_mel, mixed_labels

audio_aug = AudioAugmentation(sample_rate=32000, apply_prob=0.8)
spec_aug = SpecAugment(
    time_mask_param=50,
    freq_mask_param=16,
    num_time_masks=2,
    num_freq_masks=2,
    apply_prob=0.8,
)
mixup = MixUp(alpha=0.5, apply_prob=0.5)

waveform = torchaudio.load("audio.wav")[0]
augmented_waveform = audio_aug(waveform)

mel_spec = torch.randn(4, 1, 128, 313)
augmented_spec = spec_aug(mel_spec)

# MixUp
labels = torch.randint(0, 2, (4, 264)).float()
mixed_spec, mixed_labels = mixup(mel_spec, labels)
```

```python
import torch
import torch.nn as nn
import torch.nn.functional as F

class FocalLoss(nn.Module):

    def __init__(
        self,
        alpha: float = 0.25,
        gamma: float = 2.0,
        reduction: str = "mean",
    ):
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.reduction = reduction

    def forward(self, inputs: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        """
        Args:
            inputs: (batch, num_classes) - logits
            targets: (batch, num_classes) - one-hot or multi-hot labels

        Returns:
            loss
        """
        bce_loss = F.binary_cross_entropy_with_logits(
            inputs, targets, reduction="none"
        )

        pt = torch.exp(-bce_loss)
        focal_loss = self.alpha * (1 - pt) ** self.gamma * bce_loss

        if self.reduction == "mean":
            return focal_loss.mean()
        elif self.reduction == "sum":
            return focal_loss.sum()
        else:
            return focal_loss

class CombinedLoss(nn.Module):

    def __init__(
        self,
        bce_weight: float = 0.5,
        focal_weight: float = 0.5,
        focal_alpha: float = 0.25,
        focal_gamma: float = 2.0,
        label_smoothing: float = 0.0,
    ):
        super().__init__()
        self.bce_weight = bce_weight
        self.focal_weight = focal_weight

        self.focal_loss = FocalLoss(
            alpha=focal_alpha,
            gamma=focal_gamma,
        )

        self.label_smoothing = label_smoothing

    def forward(
        self,
        inputs: torch.Tensor,
        targets: torch.Tensor,
    ) -> torch.Tensor:
        """
        Args:
            inputs: (batch, num_classes) - logits
            targets: (batch, num_classes) - multi-hot labels

        Returns:
            loss
        """
        # Label smoothing
        if self.label_smoothing > 0:
            targets = targets * (1 - self.label_smoothing) + \
                      self.label_smoothing / targets.size(-1)

        # BCE Loss
        bce_loss = F.binary_cross_entropy_with_logits(inputs, targets)

        # Focal Loss
        focal_loss = self.focal_loss(inputs, targets)

        loss = self.bce_weight * bce_loss + self.focal_weight * focal_loss

        return loss

class KnowledgeDistillationLoss(nn.Module):

    def __init__(
        self,
        temperature: float = 4.0,
    ):
        super().__init__()
        self.temperature = temperature
        self.alpha = alpha

    def forward(
        self,
        student_logits: torch.Tensor,
        teacher_logits: torch.Tensor,
        targets: torch.Tensor,
    ) -> torch.Tensor:
        """
        Args:

        Returns:
            loss
        """
        T = self.temperature

        # Soft targets
        soft_teacher = F.softmax(teacher_logits / T, dim=-1)
        soft_student = F.log_softmax(student_logits / T, dim=-1)

        distillation_loss = F.kl_div(
            soft_student,
            soft_teacher,
            reduction="batchmean",
        ) * (T ** 2)

        student_loss = F.binary_cross_entropy_with_logits(
            student_logits,
            targets,
        )

        loss = self.alpha * distillation_loss + (1 - self.alpha) * student_loss

        return loss

criterion = CombinedLoss(
    bce_weight=0.5,
    focal_weight=0.5,
    focal_alpha=0.25,
    focal_gamma=2.0,
    label_smoothing=0.1,
)

logits = torch.randn(4, 264)
targets = torch.randint(0, 2, (4, 264)).float()

loss = criterion(logits, targets)
print(f"Combined Loss: {loss.item()}")

kd_criterion = KnowledgeDistillationLoss(
    temperature=4.0,
    alpha=0.7,
)

student_logits = torch.randn(4, 264)

kd_loss = kd_criterion(student_logits, teacher_logits, targets)
print(f"KD Loss: {kd_loss.item()}")
```

---

```python
import librosa
import numpy as np

def calculate_snr(audio: np.ndarray, sample_rate: int) -> float:
    frame_length = 2048
    frames = librosa.util.frame(audio, frame_length=frame_length, hop_length=512)

    energies = np.mean(frames ** 2, axis=0)

    signal_energy = np.percentile(energies, 90)
    noise_energy = np.percentile(energies, 10)

    snr = 10 * np.log10(signal_energy / (noise_energy + 1e-9))
    return snr

def filter_audio_by_quality(
    audio_path: str,
    min_snr: float = 10.0,
    max_duration: float = 60.0,
) -> bool:
    try:
        audio, sr = librosa.load(audio_path, sr=32000)

        snr = calculate_snr(audio, sr)
        if snr < min_snr:
            return False

        duration = len(audio) / sr
        if duration > max_duration:
            return False

        rms = librosa.feature.rms(y=audio)[0]
        if np.mean(rms) < 0.01:
            return False

        return True

    except Exception as e:
        print(f"Error loading {audio_path}: {e}")
        return False

is_good_quality = filter_audio_by_quality("audio.wav", min_snr=10.0)
```

```python
from pathlib import Path
import pandas as pd

def load_external_data(
    data_dir: str,
    species_list: list[str],
    min_samples_per_species: int = 5,
) -> pd.DataFrame:
    data_dir = Path(data_dir)

    all_records = []

    for species in species_list:
        species_dir = data_dir / species
        if not species_dir.exists():
            continue

        audio_files = list(species_dir.glob("*.wav")) + \
                      list(species_dir.glob("*.mp3"))

        if len(audio_files) < min_samples_per_species:
            continue

        for audio_file in audio_files:
            all_records.append({
                "filename": str(audio_file),
                "species": species,
                "source": "xeno_canto",
            })

    return pd.DataFrame(all_records)

species_list = ["bird_a", "bird_b", "bird_c"]
external_df = load_external_data(
    "data/xeno_canto",
    species_list,
    min_samples_per_species=5,
)
```

```python
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

def two_stage_training(
    model: nn.Module,
    train_loader_external: DataLoader,
    train_loader_competition: DataLoader,
    val_loader: DataLoader,
    num_epochs_stage1: int = 10,
    num_epochs_stage2: int = 20,
    lr_stage1: float = 1e-3,
    lr_stage2: float = 1e-4,
):

    print("Stage 1: Pre-training on external data")
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr_stage1)
    criterion = nn.BCEWithLogitsLoss()

    for epoch in range(num_epochs_stage1):
        model.train()
        for batch in train_loader_external:
            mel_spec = batch["mel_spec"].cuda()
            labels = batch["labels"].cuda()

            logits = model(mel_spec)
            loss = criterion(logits, labels)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

        val_loss = validate(model, val_loader, criterion)
        print(f"Epoch {epoch+1}/{num_epochs_stage1}, Val Loss: {val_loss:.4f}")

    print("Stage 2: Fine-tuning on competition data")
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr_stage2)

    for epoch in range(num_epochs_stage2):
        model.train()
        for batch in train_loader_competition:
            mel_spec = batch["mel_spec"].cuda()
            labels = batch["labels"].cuda()

            logits = model(mel_spec)
            loss = criterion(logits, labels)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

        val_loss = validate(model, val_loader, criterion)
        print(f"Epoch {epoch+1}/{num_epochs_stage2}, Val Loss: {val_loss:.4f}")

    return model

def validate(model: nn.Module, val_loader: DataLoader, criterion: nn.Module):
    model.eval()
    total_loss = 0

    with torch.no_grad():
        for batch in val_loader:
            mel_spec = batch["mel_spec"].cuda()
            labels = batch["labels"].cuda()

            logits = model(mel_spec)
            loss = criterion(logits, labels)

            total_loss += loss.item()

    return total_loss / len(val_loader)
```

#### 2.2 Checkpoint Averaging（2nd/4th Place）

```python
import torch
from pathlib import Path

def average_checkpoints(
    checkpoint_paths: list[str],
    output_path: str,
):
    checkpoints = []
    for path in checkpoint_paths:
        ckpt = torch.load(path, map_location="cpu")
        checkpoints.append(ckpt)

    avg_state_dict = checkpoints[0]["model_state_dict"].copy()

    for key in avg_state_dict.keys():
        tensors = [ckpt["model_state_dict"][key] for ckpt in checkpoints]
        avg_state_dict[key] = torch.stack(tensors).mean(dim=0)

    torch.save({
        "model_state_dict": avg_state_dict,
        "epoch": sum([ckpt["epoch"] for ckpt in checkpoints]) // len(checkpoints),
    }, output_path)

    print(f"Averaged checkpoint saved to {output_path}")

checkpoint_dir = Path("checkpoints")
checkpoint_paths = [
    str(checkpoint_dir / "model_epoch_13.pt"),
    str(checkpoint_dir / "model_epoch_15.pt"),
    str(checkpoint_dir / "model_epoch_17.pt"),
    str(checkpoint_dir / "model_epoch_19.pt"),
    str(checkpoint_dir / "model_epoch_20.pt"),
]

average_checkpoints(
    checkpoint_paths,
    "checkpoints/model_averaged.pt",
)
```

```python
import torch
import torch.nn as nn

def quantize_model(
    model: nn.Module,
    calibration_loader: DataLoader,
):
    quantized_model = torch.quantization.quantize_dynamic(
        model,
        {nn.Linear, nn.Conv2d},
        dtype=torch.qint8,
    )

    # quantized_model.eval()
    # with torch.no_grad():
    #     for batch in calibration_loader:
    #         _ = quantized_model(batch["mel_spec"])

    return quantized_model

quantized_model = quantize_model(model, val_loader)
torch.save(quantized_model.state_dict(), "model_quantized.pt")
```

```python
import torch
import torch.onnx
import onnxruntime as ort

def export_to_onnx(
    model: nn.Module,
    output_path: str,
    input_shape: tuple = (1, 1, 128, 313),
    opset_version: int = 13,
):
    model.eval()

    dummy_input = torch.randn(*input_shape)

    torch.onnx.export(
        model,
        dummy_input,
        output_path,
        opset_version=opset_version,
        input_names=["mel_spec"],
        output_names=["logits"],
        dynamic_axes={
            "mel_spec": {0: "batch_size"},
            "logits": {0: "batch_size"},
        },
    )

    print(f"Model exported to {output_path}")

    sess_options = ort.SessionOptions()
    sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

    session = ort.InferenceSession(
        output_path,
        sess_options,
        providers=["CPUExecutionProvider"],
    )

    return session

onnx_session = export_to_onnx(
    model,
    "model.onnx",
    input_shape=(1, 1, 128, 313),
)

def predict_onnx(session: ort.InferenceSession, mel_spec: np.ndarray):
    inputs = {session.get_inputs()[0].name: mel_spec}
    outputs = session.run(None, inputs)

    return outputs[0]

def batch_predict_onnx(
    session: ort.InferenceSession,
    mel_specs: np.ndarray,
    batch_size: int = 32,
):
    predictions = []

    for i in range(0, len(mel_specs), batch_size):
        batch = mel_specs[i:i+batch_size]
        batch_pred = predict_onnx(session, batch)
        predictions.append(batch_pred)

    return np.concatenate(predictions, axis=0)
```

```python
import numpy as np
from scipy.optimize import minimize

def find_optimal_weights(
    predictions: np.ndarray,
    targets: np.ndarray,
) -> np.ndarray:
    """

    Args:
        predictions: (num_models, num_samples, num_classes)
        targets: (num_samples, num_classes)

    Returns:
        weights: (num_models,)
    """
    num_models = predictions.shape[0]

    def objective(weights):
        weighted_pred = np.average(predictions, axis=0, weights=weights)
        auc = compute_auc(weighted_pred, targets)

    constraints = {"type": "eq", "fun": lambda w: np.sum(w) - 1}
    bounds = [(0, 1) for _ in range(num_models)]

    initial_weights = np.ones(num_models) / num_models

    result = minimize(
        objective,
        initial_weights,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
    )

    return result.x

def compute_auc(predictions: np.ndarray, targets: np.ndarray) -> float:
    from sklearn.metrics import roc_auc_score
    return roc_auc_score(targets, predictions, average="macro")

# predictions: (num_models, num_samples, num_classes)
predictions = np.random.rand(5, 1000, 264)
targets = np.random.randint(0, 2, (1000, 264))

optimal_weights = find_optimal_weights(predictions, targets)
print(f"Optimal weights: {optimal_weights}")

final_predictions = np.average(predictions, axis=0, weights=optimal_weights)
```

```python
import numpy as np

def min_ensemble(predictions: np.ndarray) -> np.ndarray:
    """

    Args:
        predictions: (num_models, num_samples, num_classes)

    Returns:
        ensemble: (num_samples, num_classes)
    """
    return np.min(predictions, axis=0)

def max_ensemble(predictions: np.ndarray) -> np.ndarray:
    """

    Args:
        predictions: (num_models, num_samples, num_classes)

    Returns:
        ensemble: (num_samples, num_classes)
    """
    return np.max(predictions, axis=0)

def rank_ensemble(
    predictions: np.ndarray,
    method: str = "geometric",
) -> np.ndarray:
    """

    Args:
        predictions: (num_models, num_samples, num_classes)
        method: "geometric" or "arithmetic"

    Returns:
        ensemble: (num_samples, num_classes)
    """
    ranks = np.zeros_like(predictions)
    for i in range(predictions.shape[0]):
        ranks[i] = scipy.stats.rankdata(predictions[i], axis=-1)

    if method == "geometric":
        avg_ranks = np.exp(np.mean(np.log(ranks + 1), axis=0)) - 1
    else:  # arithmetic
        avg_ranks = np.mean(ranks, axis=0)

    ensemble = avg_ranks / avg_ranks.sum(axis=-1, keepdims=True)

    return ensemble

predictions = np.random.rand(5, 1000, 264)

min_pred = min_ensemble(predictions)
max_pred = max_ensemble(predictions)
rank_pred = rank_ensemble(predictions, method="geometric")
```

```python
import numpy as np
from scipy.ndimage import gaussian_filter1d

def temporal_smoothing(
    predictions: np.ndarray,
    sigma: float = 1.0,
) -> np.ndarray:
    """

    Args:

    Returns:
        smoothed: (num_samples, num_classes)
    """
    smoothed = np.zeros_like(predictions)

    for i in range(predictions.shape[1]):
        smoothed[:, i] = gaussian_filter1d(predictions[:, i], sigma=sigma)

    return smoothed

def neighbor_window_smoothing(
    predictions: np.ndarray,
    window_size: int = 5,
    neighbor_weight: float = 0.5,
) -> np.ndarray:
    """

    Args:
        predictions: (num_samples, num_classes)

    Returns:
        smoothed: (num_samples, num_classes)
    """
    half_window = window_size // 2
    smoothed = np.zeros_like(predictions)

    for i in range(len(predictions)):
        start = max(0, i - half_window)
        end = min(len(predictions), i + half_window + 1)

        window = predictions[start:end]

        weights = np.ones(len(window))
        weights[weights == 1] = neighbor_weight
        weights[len(window) // 2] = 1.0

        smoothed[i] = np.average(window, axis=0, weights=weights)

    return smoothed

smoothed_gaussian = temporal_smoothing(predictions, sigma=1.5)
smoothed_neighbor = neighbor_window_smoothing(
    predictions,
    window_size=5,
    neighbor_weight=0.5,
)
```

```python
import numpy as np
import pandas as pd

def species_time_filtering(
    predictions: pd.DataFrame,
    time_info: pd.DataFrame,
    species_activity: dict,
) -> pd.DataFrame:
    """

    Args:
        species_activity: {species: {active_hours: [start, end]}}

    Returns:
        filtered_predictions
    """
    filtered = predictions.copy()

    for species, activity in species_activity.items():
        if species not in predictions.columns:
            continue

        active_hours = activity["active_hours"]  # [start, end]

        hours = pd.to_datetime(time_info["time"]).dt.hour

        mask = (hours < active_hours[0]) | (hours > active_hours[1])
        filtered.loc[mask, species] *= 0.5

    return filtered

predictions_df = pd.DataFrame({
    "bird_a": np.random.rand(100),
    "bird_b": np.random.rand(100),
})

time_info_df = pd.DataFrame({
    "time": pd.date_range("2023-01-01 00:00", periods=100, freq="5min"),
})

species_activity = {
}

filtered_predictions = species_time_filtering(
    predictions_df,
    time_info_df,
    species_activity,
)
```

---

|------|---------------|---------------|----------------|

---

### Kaggle Writeups

1. **[1st place solution: Correct Data is All You Need](https://www.kaggle.com/competitions/birdclef-2023/writeups/volodymyr-1st-place-solution-correct-data-is-all-y)** - Volodymyr Sydorskyi
2. **[2nd place solution: SED + CNN with 7 models ensemble](https://www.kaggle.com/competitions/birdclef-2023/writeups/griffith-2nd-place-solution-sed-cnn-with-7-models-)** - Griffith
3. **[3rd place solution: SED with attention on Mel frequency bands](https://www.kaggle.com/competitions/birdclef-2023/writeups/adsr-3rd-place-solution-sed-with-attention-on-mel-)** - ADSR
4. **[4th Place Solution: Knowledge Distillation Is All You Need](https://www.kaggle.com/competitions/birdclef-2023/writeups/atfujita-4th-place-solution-knowledge-distillation)** - ATFujita
5. **[5th place solution](https://www.kaggle.com/competitions/birdclef-2023/writeups/yevhenii-maslov-5th-place-solution)** - Yevhenii Maslov
6. **[8th Place Solution: Implementing Multimodal Data Augmentation Methods](https://www.kaggle.com/competitions/birdclef-2023/writeups/furu-nag-8th-place-solution-implementing-multimoda)** - FURU-NAG
7. **[18th place solution: SED with attention](https://www.kaggle.com/competitions/birdclef-2023/writeups/18th-place-solution-sed-with-attention)**

### GitHub Repositories

3. **[Bird Species Recognition using Convolutional Neural Networks with Attention on Frequency Bands](https://www.researchgate.net/publication/389264675_Bird_Species_Recognition_using_Convolutional_Neural_Networks_with_Attention_on_Frequency_Bands)**

---
