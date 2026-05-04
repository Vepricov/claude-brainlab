# ARC Prize 2025
> Last updated: 2026-01-23
> Source count: 1
---

### ARC Prize 2025 (2025) - 2025-01-22
**Source:** [Kaggle Competition](https://www.kaggle.com/competitions/arc-prize-2025) | [Official Analysis](https://arcprize.org/blog/arc-prize-2025-results-analysis)
**Key Techniques:**

**Results:** NVARC 24.03% (1st), TRM 45% on ARC-AGI-1, SOAR 52% on ARC-AGI-1

**1st Place - NVARC - 24.03% (ARC-AGI-2)**

**2nd Place - the ARChitects - 16.53%**

**3rd Place - MindsAI - 12.64%**

**Paper Awards (ARC-AGI-1):**

**1st Paper Award - Tiny Recursive Model (TRM) - 45%**

**2nd Paper Award - SOAR (Self-Improving Language Models) - 52%**

**3rd Paper Award - CompressARC - 4% (ARC-AGI-2) / 20-34% (ARC-AGI-1)**

### ARC Prize 2025 - Abstraction and Reasoning Corpus

- **ARC-AGI-1**: 800 tasks (400 training + 400 evaluation)

```
    ↓
    ↓
    ↓
```

|------|------|------|---------|
| **2nd** | the ARChitects | 16.53% | Masked-Diffusion LLM |
| **3rd** | MindsAI | 12.64% | TTFT + Augmentation |

**Paper Awards:**

|------|------|------|------|
| **1st** | Alexia Jolicoeur-Martineau | Tiny Recursive Model (TRM) | 45% (ARC-AGI-1) |

---

## Code Templates

```python
import torch
import torch.nn as nn
from typing import List, Tuple, Dict
import numpy as np

class MiRAGEFramework:
    """
    MiRAGE: Misconception detection with Retrieval-guided
            Multi-stage reasoning and Ensemble fusion

    """

    def __init__(self,
                 embedder: nn.Module,
                 reasoner: nn.Module,
                 reranker: nn.Module,
                 alpha: float = 0.7,
                 beta: float = 0.3,
                 top_k: int = 25):
        """
        Args:
        """
        self.embedder = embedder
        self.reasoner = reasoner
        self.reranker = reranker
        self.alpha = alpha
        self.beta = beta
        self.top_k = top_k

        self.embed_db = None
        self.label_db = None

    def build_embedding_index(self, dataset: List[Dict]):
        """

        Args:
            dataset: [{"question": str, "answer": str, "explanation": str, "label": str}, ...]
        """
        embeddings = []
        labels = []

        for item in dataset:
            emb = self.embedder.encode(
                item["question"],
                item["answer"],
                item["explanation"]
            )
            embeddings.append(emb)
            labels.append(item["label"])

        self.embed_db = torch.stack(embeddings)
        self.label_db = labels

    def retrieval_module(self, query: Tuple[str, str, str]) -> List[Tuple[str, float]]:
        """

        Args:
            query: (question, answer, explanation)

        Returns:
        """
        q, a, e = query
        query_emb = self.embedder.encode(q, a, e)

        similarities = torch.matmul(self.embed_db, query_emb)

        label_scores = {}
        for label, sim in zip(self.label_db, similarities):
            if label not in label_scores:
                label_scores[label] = sim
            else:
                label_scores[label] = max(label_scores[label], sim)

        sorted_labels = sorted(label_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_labels[:self.top_k]

    def reasoning_module(self, query: Tuple[str, str, str]) -> str:
        """

        Args:
            query: (question, answer, explanation)

        Returns:
        """
        q, a, e = query
        prompt = f"""
Analyze the following student response to a math problem.

Question: {q}
Student Answer: {a}
Student Explanation: {e}

Think step by step:
1. Is the answer correct?
2. Does the explanation contain any misconceptions?
3. If so, what type of misconception is it?

Provide your reasoning:
"""
        reasoning = self.reasoner.generate(prompt)
        return reasoning

    def reranking_module(self,
                        query: Tuple[str, str, str],
                        reasoning: str,
                        candidates: List[str]) -> List[Tuple[str, float]]:
        """

        Args:
            query: (question, answer, explanation)

        Returns:
        """
        q, a, e = query
        reranked_scores = []

        for label in candidates:
            prompt = f"""
Question: {q}
Student Answer: {a}
Student Explanation: {e}

Reasoning: {reasoning}

Is the misconception "{label}" consistent with the above analysis?
Answer Yes or No:
"""
            logits = self.reranker.get_logits(prompt)

            yes_logit = logits["Yes"]
            no_logit = logits["No"]
            score = yes_logit - no_logit

            reranked_scores.append((label, score.item()))

        reranked_scores.sort(key=lambda x: x[1], reverse=True)
        return reranked_scores

    def ensemble_fusion(self,
                       retrieval_scores: List[Tuple[str, float]],
                       rerank_scores: List[Tuple[str, float]]) -> List[Tuple[str, float]]:
        """

        Args:
            retrieval_scores: [(label, retrieval_score), ...]
            rerank_scores: [(label, rerank_score), ...]

        Returns:
            [(label, fused_score), ...]
        """
        retrieval_dict = dict(retrieval_scores)
        rerank_dict = dict(rerank_scores)

        all_labels = set(retrieval_dict.keys()) | set(rerank_dict.keys())

        fused_scores = []
        for label in all_labels:
            ret_score = retrieval_dict.get(label, 0)
            rerank_score = rerank_dict.get(label, 0)

            fused = self.alpha * rerank_score + self.beta * ret_score
            fused_scores.append((label, fused))

        fused_scores.sort(key=lambda x: x[1], reverse=True)
        return fused_scores

    def predict(self, query: Tuple[str, str, str]) -> List[Tuple[str, float]]:
        """

        Args:
            query: (question, answer, explanation)

        Returns:
        """
        # Stage 1: Retrieval
        retrieval_results = self.retrieval_module(query)
        candidates = [label for label, _ in retrieval_results]

        # Stage 2: Reasoning
        reasoning = self.reasoning_module(query)

        # Stage 3: Reranking
        rerank_results = self.reranking_module(query, reasoning, candidates)

        # Stage 4: Ensemble fusion
        final_results = self.ensemble_fusion(retrieval_results, rerank_results)

        return final_results

if __name__ == "__main__":
    embedder = MathBERTEmbedder()
    reasoner = QwenReasoner()
    reranker = QwenReranker()

    miracle = MiRAGEFramework(
        embedder=embedder,
        reasoner=reasoner,
        reranker=reranker,
        alpha=0.7,
        beta=0.3,
        top_k=25
    )

    train_data = load_training_data()
    miracle.build_embedding_index(train_data)

    query = (
        "What is 2/3 + 1/6?",
        "3/4",
        "I added the numerators and denominators: 2+1=3, 3+6=9, so 3/9=1/3. Wait, that's wrong..."
    )

    predictions = miracle.predict(query)
    print("Top 3 predictions:")
    for label, score in predictions[:3]:
        print(f"{label}: {score:.4f}")
```

### Shared-Prefix Attention (1st Place)

```python
import torch
import torch.nn as nn
import torch.nn.functional as F

class SharedPrefixClassifier(nn.Module):
    """
    Shared-Prefix Attention Classifier
    MAP Competition 1st Place Solution

    """

    def __init__(self, model_name: str, num_labels: int):
        super().__init__()
        self.num_labels = num_labels

        from transformers import AutoModel, AutoTokenizer
        self.model = AutoModel.from_pretrained(model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)

        hidden_size = self.model.config.hidden_size
        self.classifier = nn.Linear(hidden_size, num_labels)

    def create_flex_attention_mask(self,
                                    prefix_len: int,
                                    suffix_len: int,
                                    num_candidates: int) -> torch.Tensor:
        """

        Args:

        Returns:
            attention_mask: [batch, seq_len, seq_len]
        """
        total_len = prefix_len + suffix_len * num_candidates
        device = self.model.device

        mask = torch.zeros(total_len, total_len, device=device)

        mask[:prefix_len, :prefix_len] = 1

        for i in range(num_candidates):
            start = prefix_len + i * suffix_len
            end = start + suffix_len
            mask[start:end, :prefix_len] = 1

        return mask.unsqueeze(0)  # [1, seq_len, seq_len]

    def forward(self,
                question: str,
                answer: str,
                explanation: str,
                candidate_labels: List[str]) -> torch.Tensor:
        """
        Forward pass

        Args:

        Returns:
            logits: [batch, num_labels]
        """
        prefix = f"Question: {question}\nAnswer: {answer}\nExplanation: {explanation}\n\n"

        suffixes = []
        for label in candidate_labels:
            suffixes.append(f"Misconception: {label}")

        full_text = prefix + "".join(suffixes)
        inputs = self.tokenizer(full_text, return_tensors="pt")
        input_ids = inputs["input_ids"].to(self.model.device)

        prefix_len = len(self.tokenizer(prefix)["input_ids"])
        suffix_len = len(self.tokenizer(suffixes[0])["input_ids"])

        attention_mask = self.create_flex_attention_mask(
            prefix_len, suffix_len, len(candidate_labels)
        )

        outputs = self.model(
            input_ids=input_ids,
            attention_mask=attention_mask
        )
        hidden_states = outputs.last_hidden_state  # [batch, seq_len, hidden]

        suffix_last_tokens = []
        for i in range(len(candidate_labels)):
            pos = prefix_len + (i + 1) * suffix_len - 1
            suffix_last_tokens.append(hidden_states[:, pos, :])

        suffix_features = torch.stack(suffix_last_tokens, dim=1)  # [batch, num_labels, hidden]

        logits = self.classifier(suffix_features)  # [batch, num_labels, num_labels]

        batch_size = logits.size(0)
        logits = logits[range(batch_size), range(len(candidate_labels)), :]

        return logits

if __name__ == "__main__":
    classifier = SharedPrefixClassifier("microsoft/deberta-v3-large", num_labels=2587)

    question = "What is 2/3 + 1/6?"
    answer = "3/4"
    explanation = "I added the numerators and denominators."

    candidates = [
        "Adds denominators when adding fractions",
        "Incorrectly adds numerators and denominators",
        "Misunderstands fraction addition",
        # ... more candidates
    ]

    logits = classifier(question, answer, explanation, candidates)
    probs = F.softmax(logits, dim=-1)

    top3_probs, top3_indices = torch.topk(probs, 3)
    for prob, idx in zip(top3_probs[0], top3_indices[0]):
        print(f"{candidates[idx]}: {prob:.4f}")
```

### Multi-Loss Training with Soft Labels (2nd Place)

```python
import torch
import torch.nn as nn
from typing import List, Dict

class MultiLossTrainer:
    """
    Multi-Loss Training with Soft Labels
    MAP Competition 2nd Place Solution

    """

    def __init__(self, model: nn.Module, num_labels: int):
        self.model = model
        self.num_labels = num_labels

        self.ce_loss = nn.CrossEntropyLoss()
        self.kl_loss = nn.KLDivLoss(reduction="batchmean")

    def generate_soft_labels(self,
                            models: List[nn.Module],
                            dataloader: torch.utils.data.DataLoader,
                            device: str) -> torch.Tensor:
        """

        Args:

        Returns:
            soft_labels: [num_samples, num_labels]
        """
        all_soft_labels = []

        for batch in dataloader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)

            all_probs = []
            for model in models:
                with torch.no_grad():
                    outputs = model(input_ids, attention_mask=attention_mask)
                    probs = torch.softmax(outputs.logits, dim=-1)
                    all_probs.append(probs)

            soft_labels = torch.stack(all_probs).mean(dim=0)
            all_soft_labels.append(soft_labels.cpu())

        return torch.cat(all_soft_labels, dim=0)

    def compute_loss(self,
                     logits: torch.Tensor,
                     hard_labels: torch.Tensor,
                     soft_labels: torch.Tensor,
                     alpha: float = 0.5,
                     temperature: float = 2.0) -> torch.Tensor:
        """

        Args:

        Returns:
        """
        hard_loss = self.ce_loss(logits, hard_labels)

        log_probs = torch.log_softmax(logits / temperature, dim=-1)
        soft_labels_smooth = soft_labels / temperature
        soft_loss = self.kl_loss(log_probs, soft_labels_smooth) * (temperature ** 2)

        total_loss = alpha * hard_loss + (1 - alpha) * soft_loss

        return total_loss

    def train_epoch(self,
                    train_loader: torch.utils.data.DataLoader,
                    soft_labels: torch.Tensor,
                    optimizer: torch.optim.Optimizer,
                    device: str):
        """

        Args:
        """
        self.model.train()
        total_loss = 0

        for batch_idx, batch in enumerate(train_loader):
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            hard_labels = batch["labels"].to(device)

            start_idx = batch_idx * train_loader.batch_size
            end_idx = start_idx + len(hard_labels)
            batch_soft_labels = soft_labels[start_idx:end_idx].to(device)

            # Forward
            outputs = self.model(input_ids, attention_mask=attention_mask)
            logits = outputs.logits

            loss = self.compute_loss(logits, hard_labels, batch_soft_labels)

            # Backward
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            total_loss += loss.item()

        return total_loss / len(train_loader)

if __name__ == "__main__":
    from transformers import AutoModelForSequenceClassification

    model = AutoModelForSequenceClassification.from_pretrained(
        "microsoft/deberta-v3-large",
        num_labels=2587
    )

    trainer = MultiLossTrainer(model, num_labels=2587)

    teacher_models = [
        AutoModelForSequenceClassification.from_pretrained("teacher1"),
        AutoModelForSequenceClassification.from_pretrained("teacher2"),
        AutoModelForSequenceClassification.from_pretrained("teacher3"),
    ]

    soft_labels = trainer.generate_soft_labels(teacher_models, train_loader, "cuda")

    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-5)
    for epoch in range(3):
        loss = trainer.train_epoch(train_loader, soft_labels, optimizer, "cuda")
        print(f"Epoch {epoch}, Loss: {loss:.4f}")
```

### Auxiliary Task Training (3rd Place)

```python
import torch
import torch.nn as nn
from typing import Dict, Tuple

class AuxiliaryTaskModel(nn.Module):
    """
    Auxiliary Task Model
    MAP Competition 3rd Place Solution

    """

    def __init__(self,
                 encoder_name: str,
                 num_misconceptions: int,
                 num_error_types: int):
        super().__init__()

        from transformers import AutoModel

        self.encoder = AutoModel.from_pretrained(encoder_name)
        hidden_size = self.encoder.config.hidden_size

        self.misconception_head = nn.Linear(hidden_size, num_misconceptions)
        self.correctness_head = nn.Linear(hidden_size, 2)  # Binary: correct/incorrect
        self.error_type_head = nn.Linear(hidden_size, num_error_types)

        # Dropout
        self.dropout = nn.Dropout(0.1)

    def forward(self,
                input_ids: torch.Tensor,
                attention_mask: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Forward pass with multiple outputs

        Args:
            input_ids: [batch, seq_len]
            attention_mask: [batch, seq_len]

        Returns:
            outputs: {
                "misconception_logits": [batch, num_misconceptions],
                "correctness_logits": [batch, 2],
                "error_type_logits": [batch, num_error_types]
            }
        """
        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        pooled = outputs.last_hidden_state[:, 0, :]  # [CLS] token
        pooled = self.dropout(pooled)

        misconception_logits = self.misconception_head(pooled)
        correctness_logits = self.correctness_head(pooled)
        error_type_logits = self.error_type_head(pooled)

        return {
            "misconception_logits": misconception_logits,
            "correctness_logits": correctness_logits,
            "error_type_logits": error_type_logits
        }

class MultiTaskTrainer:
    """
    Multi-task Training
    """

    def __init__(self,
                 model: AuxiliaryTaskModel,
                 alpha: float = 1.0,
                 beta: float = 0.5,
                 gamma: float = 0.3):
        """
        Args:
        """
        self.model = model
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma

        self.ce_loss = nn.CrossEntropyLoss()

    def compute_loss(self,
                     outputs: Dict[str, torch.Tensor],
                     misconception_labels: torch.Tensor,
                     correctness_labels: torch.Tensor,
                     error_type_labels: torch.Tensor) -> Tuple[torch.Tensor, Dict[str, float]]:
        """

        Args:

        Returns:
        """
        misconception_loss = self.ce_loss(
            outputs["misconception_logits"],
            misconception_labels
        )

        correctness_loss = self.ce_loss(
            outputs["correctness_logits"],
            correctness_labels
        )

        error_type_loss = self.ce_loss(
            outputs["error_type_logits"],
            error_type_labels
        )

        total_loss = (
            self.alpha * misconception_loss +
            self.beta * correctness_loss +
            self.gamma * error_type_loss
        )

        loss_dict = {
            "misconception": misconception_loss.item(),
            "correctness": correctness_loss.item(),
            "error_type": error_type_loss.item(),
            "total": total_loss.item()
        }

        return total_loss, loss_dict

if __name__ == "__main__":
    model = AuxiliaryTaskModel(
        encoder_name="microsoft/deberta-v3-large",
        num_misconceptions=2587,
        num_error_types=10
    )

    trainer = MultiTaskTrainer(model, alpha=1.0, beta=0.5, gamma=0.3)

    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-5)

    for batch in train_loader:
        input_ids = batch["input_ids"].cuda()
        attention_mask = batch["attention_mask"].cuda()
        misconception_labels = batch["misconception_labels"].cuda()
        correctness_labels = batch["correctness_labels"].cuda()
        error_type_labels = batch["error_type_labels"].cuda()

        # Forward
        outputs = model(input_ids, attention_mask)

        # Compute loss
        loss, loss_dict = trainer.compute_loss(
            outputs, misconception_labels, correctness_labels, error_type_labels
        )

        # Backward
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        print(f"Losses: {loss_dict}")
```

```python
import torch
import torch.nn as nn

class TinyRecursiveModel(nn.Module):
    """
    Tiny Recursive Model (TRM)
    Paper: "Less is More: Recursive Reasoning with Tiny Networks"
    Alexia Jolicoeur-Martineau, ARC Prize 2025 Paper Award 1st Place

    """
    def __init__(self, d_model=512, n_heads=8, n_iterations=16):
        super().__init__()
        self.d_model = d_model
        self.n_heads = n_heads
        self.n_iterations = n_iterations

        # Embedding layers
        self.embed_x = nn.Linear(10, d_model)  # input grid embedding (10 colors)
        self.embed_y = nn.Linear(10, d_model)  # output grid embedding
        self.embed_z = nn.Linear(10, d_model)  # latent embedding

        # Single transformer block (iterated, not stacked)
        self.attention = nn.MultiheadAttention(d_model, n_heads, batch_first=True)
        self.ffn = nn.Sequential(
            nn.Linear(d_model, 4 * d_model),
            nn.GELU(),
            nn.Linear(4 * d_model, d_model)
        )
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)

        # Output heads
        self.head_y = nn.Linear(d_model, 10)  # update answer
        self.head_z = nn.Linear(d_model, 10)  # update latent

    def forward(self, x, y_init=None, z_init=None):
        """
        Args:
            x: input grid (batch, seq_len, 10)
            y_init: initial answer (random if None)
            z_init: initial latent (random if None)

        Returns:
            y: refined answer (batch, seq_len, 10)
        """
        batch_size, seq_len, _ = x.shape

        # Initialize
        y = y_init if y_init is not None else torch.randn_like(x)
        z = z_init if z_init is not None else torch.randn(batch_size, seq_len, self.d_model)

        # Embed inputs
        h_x = self.embed_x(x)  # (batch, seq_len, d_model)
        h_y = self.embed_y(y)  # (batch, seq_len, d_model)

        # Iterative refinement
        for iteration in range(self.n_iterations):
            # Combine context: input + current answer + latent
            h = h_x + h_y + self.permute_to_latent(z)

            # Single transformer block
            h_norm = self.norm1(h)
            attn_out, _ = self.attention(h_norm, h_norm, h_norm)
            h = h + attn_out

            h_norm = self.norm2(h)
            ffn_out = self.ffn(h_norm)
            h = h + ffn_out

            # Update latent z (n times)
            for _ in range(3):  # recursive reasoning
                z = z + self.head_z(h)

            # Update answer y (once)
            y_delta = self.head_y(h)
            y = y + y_delta
            h_y = self.embed_y(y)

        return y

    def permute_to_latent(self, z):
        """Permute latent to match input shape"""
        return z  # simplify for example
```

```python
import openai

def generate_synthetic_puzzles(base_descriptions, n_generate=260000):
    """

    Args:

    Returns:
    """
    generated_tasks = []

    for i in range(n_generate):
        desc1 = base_descriptions[i % len(base_descriptions)]
        desc2 = base_descriptions[(i + 1) % len(base_descriptions)]

        combined_prompt = f"""
        Combine these two ARC tasks:

        Task 1: {desc1}
        Task 2: {desc2}

        Generate a new task that combines concepts from both.
        Output format:
        - Input grid generation code
        - Transformation code
        """

        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": combined_prompt}],
            temperature=0.7
        )

        generated_tasks.append(response.choices[0].message.content)

    return generated_tasks

def verify_generated_puzzles(tasks, min_valid_grids=30):
    """

    """
    valid_tasks = []

    for task in tasks:
        input_grids = generate_input_grids(task['input_code'])

        if len(input_grids) < min_valid_grids:
            continue

        transformations = []
        for _ in range(20):
            transform_result = execute_transformation(task['transform_code'], input_grids[0])
            transformations.append(transform_result)

        if check_consensus(transformations, threshold=8):
            valid_tasks.append(task)

    return valid_tasks

def check_consensus(results, threshold=8):
    """
    """
    from collections import Counter
    counts = Counter(results)
    return counts.most_common(1)[0][1] >= threshold
```

```python
from transformers import AutoTokenizer, AutoModelForVision2Seq

def optimize_arc_tokenizer(model_name="Qwen/Qwen2-VL-7B-Instruct"):
    """

    """
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    arc_vocab = {
        '0': 0, '1': 1, '2': 2, '3': 3, '4': 4,
        '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,  # colors
        '\\n': 10,     # newline
        '<IN>': 11,    # input start
        '<OUT>': 12,   # output start
        '<PAD>': 13,   # padding
    }

    # Patch embedding table
    model = AutoModelForVision2Seq.from_pretrained(model_name)
    original_embed = model.model.model.embed_tokens
    new_embed = nn.Embedding(16, original_embed.embedding_dim)

    for token, idx in arc_vocab.items():
        original_idx = tokenizer.convert_tokens_to_ids(token)
        if original_idx is not None:
            new_embed.weight[idx] = original_embed.weight[original_idx]

    model.model.model.embed_tokens = new_embed

    return tokenizer, model
```

### Test-Time Training (TTT)

```python
import torch
import torch.nn as nn

def test_time_training(model, train_examples, test_input, n_steps=100, lr=0.001):
    """
    Test-Time Training (TTT)

    Args:

    Returns:
    """
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.MSELoss()

    for step in range(n_steps):
        total_loss = 0

        for x, y in train_examples:
            pred = model(x)

            loss = criterion(pred, y)
            total_loss += loss

        optimizer.zero_grad()
        total_loss.backward()
        optimizer.step()

    with torch.no_grad():
        prediction = model(test_input)

    return prediction

def tft_with_augmentation(model, train_examples, test_input):
    """
    TTFT + Augmentation Ensemble

    1. Test-Time Fine-Tuning
    3. Tokenizer Dropout
    """
    augmented_examples = []
    for x, y in train_examples:
        for rotation in [0, 90, 180, 270]:
            x_rot = rotate_grid(x, rotation)
            y_rot = rotate_grid(y, rotation)
            augmented_examples.append((x_rot, y_rot))

            x_flip = flip_grid(x_rot)
            y_flip = flip_grid(y_rot)
            augmented_examples.append((x_flip, y_flip))

        color_perms = sample_color_permutations(n=10)
        for perm in color_perms:
            x_perm = apply_color_permutation(x, perm)
            y_perm = apply_color_permutation(y, perm)
            augmented_examples.append((x_perm, y_perm))

    # 2. TTT with augmented data
    predictions = []
    for _ in range(10):  # 10 runs with different augmentation subsets
        subset = random_subset(augmented_examples, size=100)
        pred = test_time_training(model, subset, test_input)
        predictions.append(pred)

    # 3. Ensemble predictions
    final_pred = ensemble_predictions(predictions)

    return final_pred
```

```python
import numpy as np
from itertools import permutations

def augment_arc_task(input_grid, output_grid):
    """

    """
    augmented = []

    rotations = [0, 90, 180, 270]
    flips = [False, True]

    for rotation in rotations:
        for flip in flips:
            x_aug = rotate_grid(input_grid, rotation)
            if flip:
                x_aug = flip_grid(x_aug)

            y_aug = rotate_grid(output_grid, rotation)
            if flip:
                y_aug = flip_grid(y_aug)

            augmented.append((x_aug, y_aug))

    color_perms = sample_color_permutations(n=100)
    for perm in color_perms:
            x_perm = apply_color_permutation(x, perm)
            y_perm = apply_color_permutation(y, perm)
            augmented.append((x_perm, y_perm))

    return augmented

def sample_color_permutations(n=100, seed=42):
    """
    """
    rng = np.random.default_rng(seed)
    colors = np.arange(10)
    perms = []

    for _ in range(n):
        perm = rng.permutation(colors)
        perms.append(perm)

    return perms

def apply_color_permutation(grid, perm):
    """
    """
    permuted = grid.copy()

    mapping = {i: perm[i] for i in range(10)}

    for old_color in range(10):
        new_color = mapping[old_color]
        permuted[grid == old_color] = new_color

    return permuted
```

```python
import openai

class SOAR:
    """
    SOAR: Self-Improving Language Models for Evolutionary Program Synthesis
    Julien Pourcel et al., ARC Prize 2025 Paper Award 2nd Place

    """
    def __init__(self, base_model="gpt-4"):
        self.base_model = base_model
        self.search_trajectory = []

    def evolutionary_search(self, task, n_generations=100):
        """
        """
        population = self.initialize_population(task)

        for gen in range(n_generations):
            evaluated = self.evaluate_population(population, task)

            best = sorted(evaluated, key=lambda x: x['fitness'], reverse=True)[:10]

            offspring = self.mutate_and_crossover(best, task)

            self.search_trajectory.extend([
                {'generation': gen, 'programs': best, 'task': task}
            ])

            population = offspring

        return best[0]

    def fine_tune_on_trajectories(self, n_epochs=10):
        """
        """
        training_data = []
        for trajectory in self.search_trajectory:
            for program in trajectory['programs']:
                prompt = f"""
                Task: {trajectory['task']}
                Program: {program['code']}
                Fitness: {program['fitness']}

                Generate a better program.
                """
                training_data.append({'prompt': prompt, 'completion': program['code']})

        for epoch in range(n_epochs):
            for sample in training_data:
                response = openai.chat.completions.create(
                    model=self.base_model,
                    messages=[{"role": "user", "content": sample['prompt']}],
                    temperature=0.7
                )

                # loss = compute_loss(response, sample['completion'])
                # backward(loss)

        return self.base_model
```

```python
import torch
import torch.nn as nn

class CompressARC(nn.Module):
    """
    CompressARC: ARC-AGI Without Pretraining
    Isaac Liao, ARC Prize 2025 Paper Award 3rd Place

    - VAE loss + decoder regularization
    """
    def __init__(self, latent_dim=64, grid_size=30):
        super().__init__()
        self.latent_dim = latent_dim
        self.grid_size = grid_size

        # Encoder: grid -> latent
        self.encoder = nn.Sequential(
            nn.Linear(10, 128),  # 10 colors
            nn.ReLU(),
            nn.Linear(128, latent_dim * 2)  # mean + logvar
        )

        # Decoder: latent -> grid
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 10)  # 10 colors
        )

    def encode(self, x):
        h = self.encoder(x)  # (batch, latent_dim * 2)
        mu, logvar = h.chunk(2, dim=-1)
        return mu, logvar

    def decode(self, z):
        return self.decoder(z)

    def forward(self, x):
        mu, logvar = self.encode(x)

        # Reparameterization trick
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        z = mu + eps * std

        # Decode
        recon_x = self.decode(z)

        return recon_x, mu, logvar

    def loss_function(self, recon_x, x, mu, logvar, beta=0.1):
        """
        VAE loss + decoder regularization (MDL principle)

        """
        # Reconstruction loss
        recon_loss = nn.functional.cross_entropy(recon_x, x)

        # KL divergence
        kl_loss = -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp())

        # Decoder regularization (MDL)
        decoder_reg = sum(p.pow(2).sum() for p in self.decoder.parameters())

        # Total loss
        total_loss = recon_loss + beta * kl_loss + 0.01 * decoder_reg

        return total_loss

def test_time_train_compressarc(task, n_minutes=20):
    """
    """
    model = CompressARC()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

        total_loss = 0

        for input_grid, output_grid in task['train_examples']:
            recon, mu, logvar = model(input_grid)

            loss = model.loss_function(recon, output_grid, mu, logvar)
            total_loss += loss

        optimizer.zero_grad()
        total_loss.backward()
        optimizer.step()

        if total_loss < 0.01:
            break

    with torch.no_grad():
        test_input = task['test_input']
        recon, mu, logvar = model(test_input)
        prediction = recon.argmax(dim=-1)

    return prediction
```

|------|------|---------|

|------|--------|--------|------|------|

|------|---------------------|------|--------|

**MindsAI TTFT Pipeline：**
1. Test-Time Fine-Tuning
3. Tokenizer Dropout
4. Pretraining Tricks

2. Patch embedding table

- Claude Sonnet: 1.3%
- GPT-4o: 1.9%

- Claude Opus: >30%
- Grok: >30%

|------|------|
