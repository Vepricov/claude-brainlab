# BirdCLEF\+ 2025
> Last updated: 2026-01-23
> Source count: 1
---

```python
import torch
import torchaudio
import torch.nn as nn
import numpy as np

class MelSpectrogramExtractor:

    def __init__(
        self,
        sample_rate: int = 32000,
        n_mels: int = 128,
        n_fft: int = 2048,
        hop_length: int = 512,
        fmin: float = 0.0,
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
        "fmin": 0.0,
        "fmax": 16000.0,
    },
        "n_mels": 96,
        "n_fft": 2048,
        "hop_length": 512,
        "fmin": 0.0,
        "fmax": 16000.0,
    },
        "n_mels": 256,
        "n_fft": 4096,
        "hop_length": 1024,
        "fmin": 0.0,
        "fmax": 16000.0,
    },
}

extractor = MelSpectrogramExtractor(**CONFIGS["config_128"])
waveform, sr = torchaudio.load("audio.wav")
```

```python
import torch
import torch.nn as nn
import numpy as np
from pathlib import Path

class PseudoLabelGenerator:

    def __init__(
        self,
        model: nn.Module,
        threshold: float = 0.4,
        use_segmentwise: bool = True,
        power_transform: float = 1.0,
    ):
        """
        Args:
        """
        self.model = model
        self.model.eval()
        self.threshold = threshold
        self.use_segmentwise = use_segmentwise
        self.power_transform = power_transform

    @torch.no_grad()
    def generate_pseudo_labels(
        self,
        audio_path: str,
        segment_duration: int = 5,
        overlap: float = 0.5,
    ) -> list[dict]:
        """

        Returns:
            List of {"start": float, "end": float, "labels": np.ndarray}
        """
        waveform, sr = torchaudio.load(audio_path)

        samples_per_segment = int(segment_duration * sr)
        hop_length = int(samples_per_segment * (1 - overlap))

        pseudo_labels = []

        for start_idx in range(0, len(waveform) - samples_per_segment, hop_length):
            end_idx = start_idx + samples_per_segment
            segment = waveform[:, start_idx:end_idx]

            mel_spec = self.extract_mel(segment)

            if self.use_segmentwise:
                logits = self.model(mel_spec, return_segmentwise=True)
                logits = logits.mean(dim=1)  # (batch, num_classes)
            else:
                logits = self.model(mel_spec)

            probs = torch.sigmoid(logits).squeeze(0).cpu().numpy()

            if self.power_transform != 1.0:
                probs = np.power(probs, self.power_transform)

            mask = self._apply_threshold(probs)

            if mask.sum() > 0:
                pseudo_labels.append({
                    "start": start_idx / sr,
                    "end": end_idx / sr,
                    "labels": probs,
                    "mask": mask,
                })

        return pseudo_labels

    def _apply_threshold(self, probs: np.ndarray) -> np.ndarray:
        high_threshold = 0.7
        low_threshold = 0.3

        mask = np.zeros_like(probs, dtype=bool)

        return mask

    def extract_mel(self, waveform: torch.Tensor) -> torch.Tensor:
        pass

generator = PseudoLabelGenerator(
    model=model,
    threshold=0.4,
)

pseudo_labels = generator.generate_pseudo_labels("train_soundscape_01.wav")
```

```python
import torch
import torch.nn as nn
import numpy as np

class AudioMixUp:

    def __init__(
        self,
        alpha: float = 0.5,
        probability: float = 0.5,
    ):
        """
        Args:
            mixup_type:
        """
        self.alpha = alpha
        self.mixup_type = mixup_type
        self.probability = probability

    def __call__(
        self,
        batch: dict,
    ) -> dict:
        """

        Args:
            batch: {"mel": (B, C, H, W), "labels": (B, num_classes)}

        Returns:
            Mixed batch
        """
        if torch.rand(1).item() > self.probability:
            return batch

        mel = batch["mel"]
        labels = batch["labels"]

        batch_size = mel.size(0)

        lam = np.random.beta(self.alpha, self.alpha)

        index = torch.randperm(batch_size)

        mixed_mel = lam * mel + (1 - lam) * mel[index]

        if self.mixup_type == "soft":
            mixed_labels = lam * labels + (1 - lam) * labels[index]
        elif self.mixup_type == "hard":
            mixed_labels = torch.maximum(labels, labels[index])
        else:
            raise ValueError(f"Unknown mixup_type: {self.mixup_type}")

        return {
            "mel": mixed_mel,
            "labels": mixed_labels,
        }

class Sumix:

    def __init__(self, alpha: float = 0.5, probability: float = 1.0):
        self.alpha = alpha
        self.probability = probability

    def __call__(
        self,
        waveform: torch.Tensor,
        labels: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """

        Args:
            waveform: (batch, num_samples)
            labels: (batch, num_classes)

        Returns:
            Mixed waveform and labels
        """
        if torch.rand(1).item() > self.probability:
            return waveform, labels

        batch_size = waveform.size(0)
        lam = np.random.beta(self.alpha, self.alpha)
        index = torch.randperm(batch_size)

        mixed_waveform = lam * waveform + (1 - lam) * waveform[index]

        mixed_labels = torch.maximum(labels, labels[index])

        return mixed_waveform, mixed_labels

mixup = AudioMixUp(alpha=0.5, mixup_type="hard", probability=0.5)
sumix = Sumix(alpha=0.5, probability=1.0)

for batch in dataloader:
    waveform, labels = sumix(batch["waveform"], batch["labels"])

    mel = extract_mel(waveform)

    batch = mixup({"mel": mel, "labels": labels})
```

### Soft AUC Loss（BirdCLEF+ 2025 - 4th Place）

```python
import torch
import torch.nn as nn
import torch.nn.functional as F

class SoftAUCLoss(nn.Module):
    """

    """

    def __init__(self, reduction: str = "mean"):
        super().__init__()
        self.reduction = reduction

    def forward(
        self,
        predictions: torch.Tensor,
        targets: torch.Tensor,
    ) -> torch.Tensor:
        """
        Args:

        Returns:
            AUC loss
        """
        probs = torch.sigmoid(predictions)

        num_classes = predictions.size(1)
        losses = []

        for c in range(num_classes):
            prob_c = probs[:, c]
            target_c = targets[:, c]

            sorted_indices = torch.argsort(target_c, descending=True)

            positive_scores = prob_c[sorted_indices[:len(sorted_indices)//2]]
            negative_scores = prob_c[sorted_indices[len(sorted_indices)//2:]]

            diff = positive_scores.unsqueeze(1) - negative_scores.unsqueeze(0)
            loss_c = torch.sigmoid(-diff).mean()

            losses.append(loss_c)

        losses = torch.stack(losses)

        if self.reduction == "mean":
            return losses.mean()
        elif self.reduction == "sum":
            return losses.sum()
        else:
            return losses

class ImprovedAUCLoss(nn.Module):
    """
    """

    def __init__(self, margin: float = 1.0):
        super().__init__()
        self.margin = margin

    def forward(
        self,
        predictions: torch.Tensor,
        targets: torch.Tensor,
    ) -> torch.Tensor:
        """
        Args:
            predictions: (batch, num_classes)
        """
        probs = torch.sigmoid(predictions)
        num_classes = predictions.size(1)

        losses = []
        for c in range(num_classes):
            prob_c = probs[:, c]
            target_c = targets[:, c]

            n = prob_c.size(0)
            if n < 2:
                continue

            target_diff = target_c.unsqueeze(1) - target_c.unsqueeze(0)
            prob_diff = prob_c.unsqueeze(1) - prob_c.unsqueeze(0)

            mask = target_diff > 0

            if mask.sum() > 0:
                # Hinge loss: max(0, margin - (prob_i - prob_j))
                loss_c = F.relu(self.margin - prob_diff)[mask].mean()
                losses.append(loss_c)

        if len(losses) == 0:
            return torch.tensor(0.0, device=predictions.device)

        return torch.stack(losses).mean()

criterion = SoftAUCLoss(reduction="mean")

for batch in dataloader:
    predictions = model(batch["mel"])

    loss = criterion(predictions, batch["labels"])

    loss.backward()
    optimizer.step()
```

```python
import torch
import torch.nn as nn
from scipy.ndimage import gaussian_filter1d

class SlidingWindowInference:
    """

    """

    def __init__(
        self,
        model: nn.Module,
        sample_rate: int = 32000,
        smoothing_sigma: float = 1.0,
    ):
        self.model = model
        self.model.eval()
        self.window_size = window_size
        self.hop_size = hop_size
        self.sample_rate = sample_rate
        self.smoothing_sigma = smoothing_sigma

    @torch.no_grad()
    def predict(
        self,
        audio_path: str,
    ) -> dict[str, float]:
        """

        Returns:
            Dict of {row_id: {species_id: probability}}
        """
        waveform, sr = torchaudio.load(audio_path)

        samples_per_window = int(self.window_size * sr)
        samples_per_hop = int(self.hop_size * sr)

        all_frame_predictions = []

        window_id = 0
        for start_idx in range(0, len(waveform) - samples_per_window, samples_per_hop):
            end_idx = start_idx + samples_per_window
            window = waveform[:, start_idx:end_idx]

            mel_spec = self.extract_mel(window)

            frame_output = self.model(mel_spec)

            if isinstance(frame_output, dict):
                frame_pred = frame_output["clipwise_output"]
            else:
                frame_pred = frame_output

            all_frame_predictions.append(frame_pred.cpu().numpy())

            window_id += 1

        all_frame_predictions = np.array(all_frame_predictions)  # (num_windows, num_classes)

        smoothed_predictions = self._smooth_predictions(all_frame_predictions)

        predictions = {}
        for window_id in range(len(smoothed_predictions)):
            row_id = f"soundscape_{window_id}_{self.window_size}"
            predictions[row_id] = {
                f"species_{i}": float(prob)
                for i, prob in enumerate(smoothed_predictions[window_id])
            }

        return predictions

    def _smooth_predictions(
        self,
        predictions: np.ndarray,
    ) -> np.ndarray:
        """

        Args:
            predictions: (num_windows, num_classes)

        Returns:
            Smoothed predictions
        """
        if self.smoothing_sigma > 0:
            smoothed = gaussian_filter1d(
                predictions,
                sigma=self.smoothing_sigma,
                axis=0,
                mode="nearest",
            )
        else:
            smoothed = predictions

        kernel_size = 3
        if len(smoothed) >= kernel_size:
            # Padding
            padded = np.pad(
                smoothed,
                ((kernel_size // 2, kernel_size // 2), (0, 0)),
                mode="edge",
            )

            kernel = np.ones(kernel_size) / kernel_size
            averaged = np.zeros_like(smoothed)

            for c in range(smoothed.shape[1]):
                averaged[:, c] = np.convolve(
                    padded[:, c],
                    kernel,
                    mode="valid",
                )

            return averaged
        else:
            return smoothed

    def extract_mel(self, waveform: torch.Tensor) -> torch.Tensor:
        pass

inference = SlidingWindowInference(
    model=model,
    window_size=5,
    hop_size=5,
    smoothing_sigma=1.0,
)

predictions = inference.predict("test_soundscape_01.wav")

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
        backbone: str = "tf_efficientnetv2_s.in21k",
        num_classes: int = 206,
        in_channels: int = 1,
        pretrained: bool = True,
    ):
        super().__init__()

        self.num_classes = num_classes

        self.backbone = timm.create_model(
            backbone,
            pretrained=pretrained,
            in_chans=in_channels,
        )

        self.features_dim = self.backbone.num_features

        self.att_block = AttBlockV2(
            self.features_dim,
            num_classes,
            activation="sigmoid",
        )

    def forward(self, x, return_segmentwise=False):
        """
        Args:
            x: (batch, in_channels, n_mels, time)

        Returns:
                clipwise_output: (batch, num_classes)
                dict with:
                    clipwise_output: (batch, num_classes)
                    segmentwise_output: (batch, num_classes, time_frames)
        """
        features = self.backbone(x)  # (batch, features_dim, time_frames)

        pooled_features = features.mean(dim=[2])  # (batch, features_dim)

        clipwise_output = self.att_block(pooled_features)  # (batch, num_classes)

        if not return_segmentwise:
            return clipwise_output

        segmentwise_output = self.att_block(features)  # (batch, num_classes, time_frames)

        return {
            "clipwise_output": clipwise_output,
            "segmentwise_output": segmentwise_output,
        }

class AttBlockV2(nn.Module):
    """

    """

    def __init__(
        self,
        in_features: int,
        out_features: int,
        activation: str = "sigmoid",
    ):
        super().__init__()

        self.activation = activation
        self.att = nn.Conv1d(in_features, out_features, kernel_size=1)
        self.cla = nn.Conv1d(in_features, out_features, kernel_size=1)

        self.apply(self._init_weights)

    def _init_weights(self, m):
        if isinstance(m, nn.Conv1d):
            nn.init.kaiming_normal_(m.weight, mode="fan_out", nonlinearity="relu")
            if m.bias is not None:
                nn.init.constant_(m.bias, 0)

    def forward(self, x):
        """
        Args:

        Returns:
        """
        if x.dim() == 2:
            x = x.unsqueeze(-1)  # (batch, in_features, 1)

        att = self.att(x)

        cla = self.cla(x)

        output = torch.clamp(torch.clamp((cla * att).sum(dim=-1), min=1e-7, max=1-1e-7), min=1e-7)

        if self.activation == "sigmoid":
            output = torch.sigmoid(output)
        elif self.activation == "none":
            pass
        else:
            raise ValueError(f"Unknown activation: {self.activation}")

        return output.squeeze(-1) if output.size(-1) == 1 else output

BACKBONES = {
    "tf_efficientnetv2_s.in21k": {
        "features_dim": 1280,
    },
    "tf_efficientnetv2_b3.in21k": {
        "features_dim": 1536,
    },
    "tf_efficientnetv2_m.in21k": {
        "features_dim": 2048,
    },
    "eca_nfnet_l0": {
        "features_dim": 2304,
    },
}

model = SEDModel(
    backbone="tf_efficientnetv2_s.in21k",
    num_classes=206,
    in_channels=1,
    pretrained=True,
)

clipwise_output = model(mel_spec)
loss = criterion(clipwise_output, labels)

output = model(mel_spec, return_segmentwise=True)
segmentwise_logits = output["segmentwise_output"]  # (batch, 206, time_frames)
segmentwise_probs = torch.sigmoid(segmentwise_logits)
avg_segmentwise_probs = segmentwise_probs.mean(dim=-1)  # (batch, 206)
```

```python
import torch
import torchaudio
import pandas as pd
from pathlib import Path

class XenoCantoPretraining:
    """

    """

    def __init__(
        self,
        species_list: list,
        target_sample_rate: int = 32000,
        segment_duration: int = 5,
    ):
        self.species_list = species_list
        self.target_sample_rate = target_sample_rate
        self.segment_duration = segment_duration

    def download_xeno_canto_data(self, output_dir: str = "data/xeno_canto"):
        """

        """

        xc_species = [s for s in self.species_list if self._should_download(s)]

        for species in xc_species:
            pass

    def _should_download(self, species: str) -> bool:
        competition_species = set(self._get_competition_species())
        return species not in competition_species

    def preprocess_xeno_canto(self, audio_dir: str):
        """

        """
        audio_files = list(Path(audio_dir).rglob("*.mp3"))

        cleaned_data = []

        for audio_file in audio_files:
            waveform, sr = torchaudio.load(audio_file)

            if sr != self.target_sample_rate:
                resampler = torchaudio.transforms.Resample(sr, self.target_sample_rate)
                waveform = resampler(waveform)

            if self._check_quality(waveform):
                segments = self._extract_segments(waveform)

                for segment in segments:
                    cleaned_data.append({
                        "file_path": str(audio_file),
                        "species": audio_file.parent.name,
                        "waveform": segment,
                    })

        return cleaned_data

    def _check_quality(self, waveform: torch.Tensor) -> bool:
        if waveform.shape[1] < self.target_sample_rate * self.segment_duration:
            return False

        # snr = self._calculate_snr(waveform)
        #     return False

        if torch.abs(waveform).max() > 0.99:
            return False

        return True

    def _extract_segments(self, waveform: torch.Tensor) -> list:
        """

        """
        segment_samples = self.segment_duration * self.target_sample_rate

        if waveform.shape[1] <= segment_samples:
            padding = segment_samples - waveform.shape[1]
            waveform = torch.nn.functional.pad(waveform, (0, padding))
            return [waveform]

        max_start = waveform.shape[1] - segment_samples
        start_idx = torch.randint(0, max_start, (1,)).item()

        segment = waveform[:, start_idx:start_idx + segment_samples]
        return [segment]

    def pretrain(self, xc_data, model, save_path: str = "checkpoints/pretrained.pth"):
        """

        - BCE Loss
        - 50-100 epochs
        """
        train_loader = self._create_dataloader(xc_data)

        optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)

        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer, T_max=50, eta_min=1e-6
        )

        criterion = nn.BCEWithLogitsLoss()

        model.train()
        for epoch in range(50):  # 50 epochs
            for batch in train_loader:
                mel_spec = self._extract_mel(batch["waveform"])
                labels = batch["labels"]

                logits = model(mel_spec)
                loss = criterion(logits, labels)

                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

            scheduler.step()

            print(f"Epoch {epoch+1}/50, Loss: {loss.item():.4f}")

        torch.save(model.state_dict(), save_path)
        print(f"Pretrained model saved to {save_path}")

    def finetune(self, model, train_data, val_data, pretrained_path: str):
        """

        """
        model.load_state_dict(torch.load(pretrained_path))

        optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4)

        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer, T_max=30, eta_min=1e-7
        )

        criterion = nn.BCEWithLogitsLoss()

        best_val_score = 0
        best_epoch = 0

        model.train()
        for epoch in range(30):  # 30 epochs
            for batch in train_data:
                mel_spec = self._extract_mel(batch["waveform"])
                labels = batch["labels"]

                logits = model(mel_spec)
                loss = criterion(logits, labels)

                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

            val_score = self._validate(model, val_data)

            print(f"Epoch {epoch+1}/30, Val AUC: {val_score:.4f}")

            if val_score > best_val_score:
                best_val_score = val_score
                best_epoch = epoch
                torch.save(model.state_dict(), f"checkpoints/best_finetuned_epoch{epoch}.pth")

            scheduler.step()

        print(f"Best epoch: {best_epoch}, Best Val AUC: {best_val_score:.4f}")

    def _extract_mel(self, waveform: torch.Tensor) -> torch.Tensor:
        pass

    def _create_dataloader(self, data):
        pass

    def _validate(self, model, val_data):
        pass

    def _get_competition_species(self) -> list:
        pass

    def _calculate_snr(self, waveform: torch.Tensor) -> float:
        pass

"""

"""
```

```python
import torch
import torch.nn as nn
import numpy as np

class SelfDistillationTrainer:
    """

    """

    def __init__(
        self,
        model: nn.Module,
        num_classes: int = 206,
    ):
        self.model = model
        self.num_classes = num_classes

    def stage1_initial_training(self, train_loader, val_loader, epochs=30):
        """

        """
        print("=== Stage 1: Initial Training ===")

        optimizer = torch.optim.AdamW(self.model.parameters(), lr=1e-3)
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer, T_max=epochs, eta_min=1e-6
        )
        criterion = nn.BCEWithLogitsLoss()

        best_val_loss = float('inf')

        for epoch in range(epochs):
            self.model.train()
            train_loss = 0

            for batch in train_loader:
                mel_spec = batch['mel_spec']
                labels = batch['labels']

                logits = self.model(mel_spec)
                loss = criterion(logits, labels)

                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

                train_loss += loss.item()

            val_loss = self._validate(self.model, val_loader, criterion)

            scheduler.step()

            print(f"Epoch {epoch+1}/{epochs}, Train Loss: {train_loss/len(train_loader):.4f}, "
                  f"Val Loss: {val_loss:.4f}")

            if val_loss < best_val_loss:
                best_val_loss = val_loss
                torch.save(self.model.state_dict(), "checkpoints/stage1_best.pth")

        print(f"Stage 1 complete. Best Val Loss: {best_val_loss:.4f}")

        self.model.load_state_dict(torch.load("checkpoints/stage1_best.pth"))

    def stage2_self_distillation_train_audio(
        self,
        train_loader,
        epochs=20,
        temperature=3.0,
        alpha=0.7,
    ):
        """

        """
        print("=== Stage 2: Self-Distillation on train_audio ===")

        teacher_model = type(self.model)(
            backbone=self.model.backbone,
            num_classes=self.num_classes,
        )
        teacher_model.load_state_dict(torch.load("checkpoints/stage1_best.pth"))
        teacher_model.eval()

        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer, T_max=epochs, eta_min=1e-7
        )

        distillation_criterion = nn.KLDivLoss(reduction="batchmean")
        bce_criterion = nn.BCEWithLogitsLoss()

        best_val_loss = float('inf')

        for epoch in range(epochs):
            self.model.train()
            train_loss = 0

            for batch in train_loader:
                mel_spec = batch['mel_spec']
                hard_labels = batch['labels']

                with torch.no_grad():
                    teacher_logits = teacher_model(mel_spec)
                    teacher_probs = torch.sigmoid(teacher_logits / temperature)

                student_logits = self.model(mel_spec)
                student_log_probs = torch.log_softmax(student_logits / temperature, dim=-1)

                distill_loss = distillation_criterion(student_log_probs, teacher_probs)

                bce_loss = bce_criterion(student_logits, hard_labels)

                loss = alpha * (temperature ** 2) * distill_loss + (1 - alpha) * bce_loss

                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

                train_loss += loss.item()

            scheduler.step()

            print(f"Epoch {epoch+1}/{epochs}, Train Loss: {train_loss/len(train_loader):.4f}, "
                  f"Val Loss: {val_loss:.4f}")

            if val_loss < best_val_loss:
                best_val_loss = val_loss
                torch.save(self.model.state_dict(), "checkpoints/stage2_best.pth")

        print(f"Stage 2 complete. Best Val Loss: {best_val_loss:.4f}")

        self.model.load_state_dict(torch.load("checkpoints/stage2_best.pth"))

    def stage3_self_distillation_soundscape(
        self,
        train_audio_loader,
        soundscape_files,
        epochs=20,
        temperature=3.0,
    ):
        """

        """
        print("=== Stage 3: Self-Distillation with soundscape ===")

        teacher_model = type(self.model)(
            backbone=self.model.backbone,
            num_classes=self.num_classes,
        )
        teacher_model.load_state_dict(torch.load("checkpoints/stage2_best.pth"))
        teacher_model.eval()

        optimizer = torch.optim.AdamW(self.model.parameters(), lr=3e-4)
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer, T_max=epochs, eta_min=1e-7
        )

        distillation_criterion = nn.KLDivLoss(reduction="batchmean")
        bce_criterion = nn.BCEWithLogitsLoss()

        soundscape_pseudo_labels = self._generate_pseudo_labels(
            teacher_model, soundscape_files
        )

        # 50% train_audio + 50% soundscape

        best_val_loss = float('inf')

        for epoch in range(epochs):
            self.model.train()
            train_loss = 0

            for batch in train_audio_loader:
                if np.random.rand() > 0.5:

                mel_spec = batch['mel_spec']
                hard_labels = batch['labels']

                with torch.no_grad():
                    teacher_logits = teacher_model(mel_spec)
                    teacher_probs = torch.sigmoid(teacher_logits / temperature)

                student_logits = self.model(mel_spec)
                student_log_probs = torch.log_softmax(student_logits / temperature, dim=-1)

                distill_loss = distillation_criterion(student_log_probs, teacher_probs)
                bce_loss = bce_criterion(student_logits, hard_labels)
                loss = alpha * (temperature ** 2) * distill_loss + (1 - alpha) * bce_loss

                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

                train_loss += loss.item()

            for batch in soundscape_pseudo_labels:
                if np.random.rand() <= 0.5:

                mel_spec = batch['mel_spec']

                with torch.no_grad():
                    teacher_logits = teacher_model(mel_spec)
                    teacher_probs = torch.sigmoid(teacher_logits / temperature)

                student_logits = self.model(mel_spec)
                student_log_probs = torch.log_softmax(student_logits / temperature, dim=-1)

                distill_loss = distillation_criterion(student_log_probs, teacher_probs)

                optimizer.zero_grad()
                distill_loss.backward()
                optimizer.step()

                train_loss += distill_loss.item()

            scheduler.step()

            print(f"Epoch {epoch+1}/{epochs}, Train Loss: {train_loss:.4f}")

            if epoch % 5 == 0:
                torch.save(self.model.state_dict(), f"checkpoints/stage3_epoch{epoch}.pth")

        print("Stage 3 complete")

    def _generate_pseudo_labels(
        self,
        model: nn.Module,
        audio_files: list,
    ) -> list:
        """

        """
        model.eval()
        pseudo_labels = []

        with torch.no_grad():
            for audio_file in audio_files:
                waveform, sr = torchaudio.load(audio_file)

                segments = self._split_audio(waveform, sr)

                for segment in segments:
                    mel_spec = self._extract_mel(segment)

                    output = model(mel_spec, return_segmentwise=True)
                    segmentwise_logits = output["segmentwise_output"]  # (1, 206, time)
                    segmentwise_probs = torch.sigmoid(segmentwise_logits)

                    avg_probs = segmentwise_probs.mean(dim=-1).squeeze(0)  # (206,)

                    pseudo_labels.append({
                        "mel_spec": mel_spec,
                        "labels": avg_probs,
                    })

        return pseudo_labels

    def _split_audio(self, waveform: torch.Tensor, sr: int) -> list:
        segment_samples = 5 * sr
        segments = []

        for i in range(0, waveform.shape[1], segment_samples):
            segment = waveform[:, i:i+segment_samples]
            if segment.shape[1] == segment_samples:
                segments.append(segment)
            else:
                padding = segment_samples - segment.shape[1]
                segment = torch.nn.functional.pad(segment, (0, padding))
                segments.append(segment)

        return segments

    def _extract_mel(self, waveform: torch.Tensor) -> torch.Tensor:
        pass

    def _validate(self, model, val_loader, criterion):
        model.eval()
        total_loss = 0

        with torch.no_grad():
            for batch in val_loader:
                mel_spec = batch['mel_spec']
                labels = batch['labels']

                logits = model(mel_spec)
                loss = criterion(logits, labels)
                total_loss += loss.item()

        return total_loss / len(val_loader)

class SileroVADDataCleaner:
    """

    """

    def __init__(self):
        self.model, utils = torch.hub.load(
            repo_or_dir='snakers4/silero-vad',
            model='silero_vad',
            force_reload=False,
            onnx=False
        )
        self.model.eval()

    def clean_audio(self, audio_path: str, output_path: str):
        """

        Returns:
        """
        waveform, sr = torchaudio.load(audio_path)

        if waveform.shape[0] > 1:
            waveform = waveform.mean(dim=0, keepdim=True)

        if sr != 16000:
            resampler = torchaudio.transforms.Resample(sr, 16000)
            waveform = resampler(waveform)
            sr = 16000

        speech_chunks = self._detect_speech(waveform, sr)

        if speech_chunks:
            cleaned_waveform = self._remove_speech_chunks(waveform, speech_chunks)
        else:
            cleaned_waveform = waveform

        torchaudio.save(output_path, cleaned_waveform, sr)

        return cleaned_waveform

    def _detect_speech(self, waveform: torch.Tensor, sr: int) -> list:
        """

        Returns:
            List of (start_ms, end_ms) tuples
        """
        speech_probs = []
        window_size = 512  # 32ms at 16kHz

        for i in range(0, waveform.shape[1], window_size):
            chunk = waveform[:, i:i+window_size]
            if chunk.shape[1] < window_size:
                continue

            with torch.no_grad():
                speech_prob = self.model(chunk, sr).item()
                speech_probs.append(speech_prob)

        speech_chunks = []
        in_speech = False
        start_idx = 0

        for i, prob in enumerate(speech_probs):
            if prob > 0.5 and not in_speech:
                in_speech = True
                start_idx = i * window_size
            elif prob <= 0.5 and in_speech:
                in_speech = False
                end_idx = i * window_size
                speech_chunks.append((start_idx, end_idx))

        speech_chunks_ms = [(s * 1000 / sr, e * 1000 / sr) for s, e in speech_chunks]

        return speech_chunks_ms

    def _remove_speech_chunks(
        self,
        waveform: torch.Tensor,
        speech_chunks: list,
    ) -> torch.Tensor:
        sr = 16000

        speech_ranges = [(int(s * sr / 1000), int(e * sr / 1000)) for s, e in speech_chunks]

        mask = torch.ones(waveform.shape[1], dtype=torch.bool)

        for start, end in speech_ranges:
            mask[start:end] = False

        cleaned_waveform = waveform[:, mask]

        return cleaned_waveform

"""

"""
```

```python
import torch
import torch.nn as nn
import numpy as np

class MultiIterativeNoisyStudent:
    """

    """

    def __init__(
        self,
        model: nn.Module,
        num_classes: int = 206,
        num_iterations: int = 3,
    ):
        self.model = model
        self.num_classes = num_classes
        self.num_iterations = num_iterations

        self.mixup_alpha = 0.5

    def train_iteration(
        self,
        train_audio_loader,
        train_soundscape_files,
        iteration: int,
        epochs=30,
    ):
        """

        Args:
        """
        print(f"=== Noisy Student Iteration {iteration + 1} ===")

        if iteration == 0:
            train_loader = train_audio_loader
        else:
            train_loader = self._prepare_mixed_data(
                train_audio_loader,
                train_soundscape_files,
                iteration,
            )

        optimizer = torch.optim.AdamW(self.model.parameters(), lr=1e-3)
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer, T_max=epochs, eta_min=1e-6
        )
        criterion = nn.BCEWithLogitsLoss()

        best_val_loss = float('inf')

        for epoch in range(epochs):
            self.model.train()
            train_loss = 0

            for batch in train_loader:
                mel_spec = batch['mel_spec']
                labels = batch['labels']

                    mel_spec, labels = self._apply_mixup(mel_spec, labels)

                logits = self.model(mel_spec)
                loss = criterion(logits, labels)

                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

                train_loss += loss.item()

            val_loss = self._quick_validate(train_audio_loader, criterion)

            scheduler.step()

            print(f"Iteration {iteration+1}, Epoch {epoch+1}/{epochs}, "
                  f"Train Loss: {train_loss/len(train_loader):.4f}, "
                  f"Val Loss: {val_loss:.4f}")

            if val_loss < best_val_loss:
                best_val_loss = val_loss
                torch.save(self.model.state_dict(),
                          f"checkpoints/noisy_student_iter{iteration}_best.pth")

        print(f"Iteration {iteration+1} complete. Best Val Loss: {best_val_loss:.4f}")

    def _prepare_mixed_data(
        self,
        train_audio_loader,
        soundscape_files,
        iteration: int,
    ):
        """

        """
        pseudo_labels = self._generate_pseudo_labels_power_transform(
            soundscape_files,
            self.power_transform,
        )

        mixed_data = []

        for batch in train_audio_loader:
            mixed_data.append(batch)

        for item in pseudo_labels:
            mixed_data.append(item)

        np.random.shuffle(mixed_data)

        return mixed_data

    def _generate_pseudo_labels_power_transform(
        self,
        audio_files: list,
        power: float = 1.5,
    ) -> list:
        """

        """
        self.model.eval()
        pseudo_labels = []

        with torch.no_grad():
            for audio_file in audio_files:
                waveform, sr = torchaudio.load(audio_file)

                segments = self._split_audio(waveform, sr)

                for segment in segments:
                    mel_spec = self._extract_mel(segment)

                    logits = self.model(mel_spec)
                    probs = torch.sigmoid(logits).squeeze(0).cpu().numpy()  # (206,)

                    probs_transformed = np.power(probs, power)

                    pseudo_labels.append({
                        "mel_spec": mel_spec,
                        "labels": torch.tensor(probs_transformed, dtype=torch.float32),
                    })

        return pseudo_labels

    def _apply_mixup(
        self,
        mel_spec: torch.Tensor,
        labels: torch.Tensor,
    ) -> tuple:
        """

        """
        batch_size = mel_spec.size(0)

        lam = np.random.beta(self.mixup_alpha, self.mixup_alpha)
        # lam = 0.5

        index = torch.randperm(batch_size)

        mixed_mel = lam * mel_spec + (1 - lam) * mel_spec[index]

        mixed_labels = torch.maximum(labels, labels[index])

        return mixed_mel, mixed_labels

    def _split_audio(self, waveform: torch.Tensor, sr: int) -> list:
        segment_samples = 5 * sr
        segments = []

        for i in range(0, waveform.shape[1], segment_samples):
            segment = waveform[:, i:i+segment_samples]
            if segment.shape[1] == segment_samples:
                segments.append(segment)
            else:
                padding = segment_samples - segment.shape[1]
                segment = torch.nn.functional.pad(segment, (0, padding))
                segments.append(segment)

        return segments

    def _extract_mel(self, waveform: torch.Tensor) -> torch.Tensor:
        pass

    def _quick_validate(self, val_loader, criterion):
        self.model.eval()
        total_loss = 0
        count = 0

        with torch.no_grad():
            for i, batch in enumerate(val_loader):
                    break

                mel_spec = batch['mel_spec']
                labels = batch['labels']

                logits = self.model(mel_spec)
                loss = criterion(logits, labels)
                total_loss += loss.item()
                count += 1

        return total_loss / max(count, 1)

"""

"""

def train_noisy_student_full_pipeline():
    """
    """
    model = SEDModel(num_classes=206)
    trainer = MultiIterativeNoisyStudent(model, num_iterations=3)

    print("=== Iteration 0: Training on train_audio only ===")
    trainer.train_iteration(train_audio_loader, soundscape_files, iteration=0, epochs=30)

    print("=== Iteration 1: Adding pseudo-labeled soundscape ===")
    trainer.train_iteration(train_audio_loader, soundscape_files, iteration=1, epochs=30)

    print("=== Iteration 2: Refreshing pseudo labels ===")
    trainer.train_iteration(train_audio_loader, soundscape_files, iteration=2, epochs=30)

    model_iter0 = SEDModel(num_classes=206)
    model_iter0.load_state_dict(torch.load("checkpoints/noisy_student_iter0_best.pth"))

    model_iter1 = SEDModel(num_classes=206)
    model_iter1.load_state_dict(torch.load("checkpoints/noisy_student_iter1_best.pth"))

    model_iter2 = SEDModel(num_classes=206)
    model_iter2.load_state_dict(torch.load("checkpoints/noisy_student_iter2_best.pth"))

    def ensemble_predict(mel_spec):
        pred0 = torch.sigmoid(model_iter0(mel_spec))
        pred1 = torch.sigmoid(model_iter1(mel_spec))
        pred2 = torch.sigmoid(model_iter2(mel_spec))

        ensemble_pred = (pred0 + pred1 + pred2) / 3
        return ensemble_pred

    return ensemble_predict
```

```python
import torch
import torch.nn as nn
import torch.nn.functional as F

class SoftAUCLoss_v4(nn.Module):
    """

    """

    def __init__(
        self,
        margin: float = 1.0,
        reduction: str = "mean",
    ):
        super().__init__()
        self.margin = margin
        self.reduction = reduction

    def forward(
        self,
        predictions: torch.Tensor,
        targets: torch.Tensor,
    ) -> torch.Tensor:
        """
        Args:

        Returns:
            AUC loss
        """
        probs = torch.sigmoid(predictions)
        num_classes = predictions.size(1)
        losses = []

        for c in range(num_classes):
            prob_c = probs[:, c]      # (batch,)
            target_c = targets[:, c]  # (batch,)

            target_diff = target_c.unsqueeze(1) - target_c.unsqueeze(0)  # (batch, batch)
            prob_diff = prob_c.unsqueeze(1) - prob_c.unsqueeze(0)        # (batch, batch)

            mask = target_diff > 0

            if mask.sum() > 0:
                # Hinge loss: max(0, margin - (prob_i - prob_j))

                loss_c = F.relu(self.margin - prob_diff)[mask].mean()

                # weight = target_diff[mask]
                # weighted_loss = F.relu(self.margin - prob_diff)[mask] * weight
                # loss_c = weighted_loss.sum() / weight.sum()

                losses.append(loss_c)

        if len(losses) == 0:
            return torch.tensor(0.0, device=predictions.device, requires_grad=True)

        losses = torch.stack(losses)

        if self.reduction == "mean":
            return losses.mean()
        elif self.reduction == "sum":
            return losses.sum()
        else:
            return losses

class SoftAUCLoss_Advanced(nn.Module):
    """

    """

    def __init__(
        self,
        margin: float = 1.0,
        temperature: float = 1.0,
        use_class_weighting: bool = True,
    ):
        super().__init__()
        self.margin = margin
        self.temperature = temperature
        self.use_class_weighting = use_class_weighting

    def forward(
        self,
        predictions: torch.Tensor,
        targets: torch.Tensor,
    ) -> torch.Tensor:
        """
        Args:
            predictions: (batch, num_classes)
        """
        probs = torch.sigmoid(predictions / self.temperature)
        num_classes = predictions.size(1)

        losses = []

        for c in range(num_classes):
            prob_c = probs[:, c]
            target_c = targets[:, c]

            target_diff = target_c.unsqueeze(1) - target_c.unsqueeze(0)
            prob_diff = prob_c.unsqueeze(1) - prob_c.unsqueeze(0)

            # mask: target_i > target_j
            mask = target_diff > 0

            if mask.sum() > 0:
                # Hinge loss
                base_loss = F.relu(self.margin - prob_diff)[mask]

                weights = target_diff[mask]
                weighted_loss = base_loss * weights

                loss_c = weighted_loss.sum() / weights.sum()

                if self.use_class_weighting:
                    class_weight = self._get_class_weight(c, num_classes)
                    loss_c = loss_c * class_weight

                losses.append(loss_c)

        if len(losses) == 0:
            return torch.tensor(0.0, device=predictions.device, requires_grad=True)

        return torch.stack(losses).mean()

    def _get_class_weight(self, class_idx: int, num_classes: int) -> float:
        """

        """

"""

   - Hinge loss: max(0, margin - (prob_i - prob_j))

"""

def train_with_soft_auc_loss():

    model = SEDModel(num_classes=206)

    criterion_bce = nn.BCEWithLogitsLoss()

    criterion_soft_auc = SoftAUCLoss_v4(margin=1.0)

    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)

    for epoch in range(30):
        model.train()

        for batch in train_loader:
            mel_spec = batch['mel_spec']

                loss = criterion_soft_auc(model(mel_spec), labels)
                loss = criterion_bce(model(mel_spec), labels)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

        print(f"Epoch {epoch+1}/30, Loss: {loss.item():.4f}")
```

---

## Best Practices

|------|---------|------|

|------|------|------|---------|

|------|------|------|

**Scalogram/Spectrogram (2D):**
- Mixup

- 1D CNN + GRU
- Transformer (Time-series Transformer)
- LSTM/GRU

**Scalogram (2D):**
- MaxVIT: maxvit_base_tf_512
- ConvNeXt: convnextv2_atto

|------|------|

|------|---------|
