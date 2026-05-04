>
>

---

---

|------|------|

```python
score = num_correct - C * num_wrong

```

---

|------|--------|--------|----------|----------|

|------|-----------|-----------|-----------|

---

```
┌─────────────────────────────────────────────────────────┐
└─────────────────────────────────────────────────────────┘

       │
       ▼
┌──────────────────┐
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
         │
         ▼
┌──────────────────┐
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
└──────────────────┘
```

```python
def generate_f2p_test(issue: str, code_context: str, model) -> str:
    """

    Args:

    Returns:
    """
    prompt = f"""

GitHub Issue:
{issue}

{code_context}

"""

    test_code = model.generate(prompt)
    return test_code

def validate_f2p_test(
    test_code: str,
    original_code: str,
    patched_code: str
) -> bool:
    """

    Returns:
    """
    original_result = run_test(test_code, original_code)
    if original_result.status != "FAIL":

    patched_result = run_test(test_code, patched_code)
    if patched_result.status != "PASS":

    return True
```

```python
def should_submit_patch(
    patch: str,
    f2p_test_result: dict,
    confidence_metrics: dict
) -> bool:
    """

    """
    if not f2p_test_result['valid_f2p']:
        return False

    if not f2p_test_result['applied_successfully']:
        return False

        return False

    if f2p_test_result['files_modified'] > 2:
        return False

    if confidence_metrics['score'] < 0.9:
        return False

    return True
```

```python
ISSUE_ANALYSIS_PROMPT = """

GitHub Issue:
{issue}

"""
```

```python
PATCH_GENERATION_PROMPT = """

GitHub Issue:
{issue}

{f2p_test}

{code}

"""
```

---

```
┌─────────────────────────────────────────────────────────┐
└─────────────────────────────────────────────────────────┘

       │
       ▼
┌──────────────────┐
         │
         ▼
┌──────────────────┐
         │
         ▼
┌──────────────────┐
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
└──────────────────┘
```

```python
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class TracebackInfo:
    files: List[str]
    lines: List[int]
    functions: List[str]
    error_types: List[str]
    error_messages: List[str]
    raw_traceback: str

class TracebackExtractor:

    PATTERNS = {
        'traceback_header': r'Traceback \(most recent call last\):',
        'frame': r'  File "([^"]+)", line (\d+), in (\w+)',
        'error': r'(\w*Error):\s*(.+)',
        'assertion': r'AssertionError:\s*(.+)',
        'exception_in': r'Exception in (\w+) (.+)',
    }

    def __init__(self):
        self.compiled_patterns = {
            name: re.compile(pattern)
            for name, pattern in self.PATTERNS.items()
        }

    def extract(self, issue_text: str) -> Optional[TracebackInfo]:
        """

        Args:

        Returns:
        """
        if not self.compiled_patterns['traceback_header'].search(issue_text):
            return None

        frames = self.compiled_patterns['frame'].findall(issue_text)
        files = [frame[0] for frame in frames]
        lines = [int(frame[1]) for frame in frames]
        functions = [frame[2] for frame in frames]

        error_match = self.compiled_patterns['error'].search(issue_text)
        if error_match:
            error_types = [error_match.group(1)]
            error_messages = [error_match.group(2)]
        else:
            assertion_match = self.compiled_patterns['assertion'].search(issue_text)
            if assertion_match:
                error_types = ['AssertionError']
                error_messages = [assertion_match.group(1)]
            else:
                error_types = []
                error_messages = []

        traceback_match = re.search(
            r'(Traceback \(most recent call last\):.*?)(?=\n\n|\Z)',
            issue_text,
            flags=re.DOTALL
        )
        raw_traceback = traceback_match.group(1) if traceback_match else ""

        return TracebackInfo(
            files=files,
            lines=lines,
            functions=functions,
            error_types=error_types,
            error_messages=error_messages,
            raw_traceback=raw_traceback
        )

    def prioritize_files(
        self,
        traceback: TracebackInfo,
        all_files: List[str]
    ) -> List[str]:
        """

        Args:

        Returns:
        """
        prioritized = []

        for tb_file in traceback.files:
            normalized = tb_file.replace('/', '.')
            if normalized in all_files:
                prioritized.append((normalized, 1.0))
            elif any(tb_file in f or f in tb_file for f in all_files):
                match = next(f for f in all_files if tb_file in f or f in tb_file)
                prioritized.append((match, 0.9))

        if traceback.files:
            tb_dir = '/'.join(traceback.files[0].split('/')[:-1])
            for f in all_files:
                if f.startswith(tb_dir) and f not in [p[0] for p in prioritized]:
                    prioritized.append((f, 0.7))

        for f in all_files:
            if 'test' in f.lower() and f not in [p[0] for p in prioritized]:
                prioritized.append((f, 0.5))

        prioritized.sort(key=lambda x: x[1], reverse=True)

        return [p[0] for p in prioritized]

    def get_context_lines(
        self,
        traceback: TracebackInfo,
        file_content: str,
        context_window: int = 10
    ) -> str:
        """

        Args:

        Returns:
        """
        if not traceback.lines:

        lines = file_content.split('\n')
        error_line = traceback.lines[0]

        start = max(0, error_line - context_window)
        end = min(len(lines), error_line + context_window + 1)

        context_lines = lines[start:end]

        context_with_line_numbers = [
            f"{i+1:4d}: {line}"
            for i, line in enumerate(context_lines, start=start)
        ]

        if error_line - start < len(context_with_line_numbers):
            idx = error_line - start
            context_with_line_numbers[idx] = f">>> {context_with_line_numbers[idx]}"

        return '\n'.join(context_with_line_numbers)
```

```python
extractor = TracebackExtractor()

issue_text = """
When I run the model, I get this error:

Traceback (most recent call last):
  File "train.py", line 42, in train_loop
    loss = model(batch)
  File "model.py", line 156, in __call__
    outputs = self.layer(inputs)
TypeError: Layer.__call__() got an unexpected keyword argument 'training'

This happens when I use the new layer type.
"""

traceback = extractor.extract(issue_text)

if traceback:
    print(f"Error Type: {traceback.error_types}")
    print(f"Error Message: {traceback.error_messages}")
    print(f"Files: {traceback.files}")
    print(f"Lines: {traceback.lines}")
    print(f"Functions: {traceback.functions}")

    all_files = ['model.py', 'train.py', 'utils.py', 'test_model.py']
    prioritized = extractor.prioritize_files(traceback, all_files)
    print(f"Prioritized files: {prioritized}")

    model_code = read_file('model.py')
    context = extractor.get_context_lines(traceback, model_code)
    print(f"Context:\n{context}")
```

```python
def generate_traceback_aware_patch(
    issue: str,
    traceback: TracebackInfo,
    code_context: str,
    model
) -> str:
    """

    Args:
        issue: GitHub issue

    Returns:
    """
    prompt = f"""

{issue}

{code_context}

"""

    patch = model.generate(prompt)
    return patch
```

---

|---------|-----------|-----------|----------|

```python
def combined_strategy(issue: str, codebase: dict) -> Optional[str]:
    """

    """
    traceback = extract_traceback(issue)

    if traceback:
        relevant_files = traceback.prioritize_files(codebase.keys())
        context = get_traceback_context(traceback, codebase)
    else:
        relevant_files = analyze_issue(issue, codebase)
        context = get_full_context(issue, codebase)

    f2p_test = generate_f2p_test(issue, context)

    patch = generate_patch(issue, f2p_test, context)

    if validate_f2p_test(f2p_test, patch):
        return patch
    else:
        return None
```

---

```python
from typing import Optional, Dict, Any
import subprocess
import tempfile
import os

class F2PTestGenerator:

    def __init__(self, model):
        self.model = model

    def generate(self, issue: str, code_context: str) -> str:
        prompt = f"""

Issue:
{issue}

{code_context}

"""
        return self.model.generate(prompt)

    def validate(
        self,
        test_code: str,
        original_code: str,
        patched_code: str
    ) -> Dict[str, Any]:
        results = {
            'valid_f2p': False,
            'original_result': None,
            'patched_result': None,
            'error': None
        }

        try:
            results['original_result'] = self._run_test(
                test_code, original_code
            )

            if results['original_result']['status'] != 'FAIL':
                results['error'] = "Test did not fail on original code"
                return results

            results['patched_result'] = self._run_test(
                test_code, patched_code
            )

            if results['patched_result']['status'] != 'PASS':
                results['error'] = "Test did not pass on patched code"
                return results

            results['valid_f2p'] = True
            return results

        except Exception as e:
            results['error'] = str(e)
            return results

    def _run_test(self, test_code: str, code: str) -> Dict[str, Any]:
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, 'test_fix.py')
            with open(test_file, 'w') as f:
                f.write(test_code)
                f.write('\n\n')
                f.write(code)

            result = subprocess.run(
                ['pytest', test_file, '-v'],
                capture_output=True,
                text=True,
                timeout=10
            )

            return {
                'status': 'PASS' if result.returncode == 0 else 'FAIL',
                'stdout': result.stdout,
                'stderr': result.stderr
            }

def solve_issue_with_f2p(
    issue: str,
    codebase: Dict[str, str],
    model
) -> Optional[str]:
    """
    """
    test_gen = F2PTestGenerator(model)
    test_code = test_gen.generate(issue, codebase)

    patch = generate_patch(issue, test_code, codebase, model)

    validation = test_gen.validate(
        test_code,
        codebase,
        apply_patch(codebase, patch)
    )

    if validation['valid_f2p']:
        return patch
    else:
        return None
```

```python
import re
from typing import Optional, List, Tuple
from dataclasses import dataclass

@dataclass
class TracebackInfo:
    files: List[str]
    lines: List[int]
    functions: List[str]
    error_type: Optional[str]
    error_message: Optional[str]
    full_traceback: str

class TracebackAnalyzer:

    def __init__(self):
        self.patterns = {
            'header': re.compile(r'Traceback \(most recent call last\):'),
            'frame': re.compile(r'  File "([^"]+)", line (\d+), in (\w+)'),
            'error': re.compile(r'(\w*Error):\s*(.+)'),
        }

    def extract(self, text: str) -> Optional[TracebackInfo]:
        if not self.patterns['header'].search(text):
            return None

        frames = self.patterns['frame'].findall(text)

        error_match = self.patterns['error'].search(text)
        error_type = error_match.group(1) if error_match else None
        error_message = error_match.group(2) if error_match else None

        tb_match = re.search(
            r'(Traceback \(most recent call last\):.*?)(?=\n\n|\Z)',
            text,
            flags=re.DOTALL
        )
        full_traceback = tb_match.group(1) if tb_match else ""

        return TracebackInfo(
            files=[f[0] for f in frames],
            lines=[int(f[1]) for f in frames],
            functions=[f[2] for f in frames],
            error_type=error_type,
            error_message=error_message,
            full_traceback=full_traceback
        )

    def get_error_location(self, traceback: TracebackInfo) -> Tuple[str, int]:
        if traceback.files and traceback.lines:
            return (traceback.files[0], traceback.lines[0])
        return (None, None)

    def get_context(
        self,
        traceback: TracebackInfo,
        file_content: str,
        window: int = 5
    ) -> str:
        if not traceback.lines:
            return file_content[:500]

        lines = file_content.split('\n')
        error_line = traceback.lines[0]

        start = max(0, error_line - window)
        end = min(len(lines), error_line + window + 1)

        context = lines[start:end]
        return '\n'.join(
            f"{i+1:4d}: {line}"
            for i, line in enumerate(context, start=start)
        )

def solve_issue_with_traceback(
    issue: str,
    codebase: Dict[str, str],
    model
) -> Optional[str]:
    """
    """
    analyzer = TracebackAnalyzer()
    traceback = analyzer.extract(issue)

    if not traceback:
        return solve_issue_without_traceback(issue, codebase, model)

    file_path, line_no = analyzer.get_error_location(traceback)

    if file_path in codebase:
        context = analyzer.get_context(
            traceback,
            codebase[file_path]
        )
    else:
        return None

    prompt = f"""

Issue: {issue}

{context}

"""
    patch = model.generate(prompt)

    # ...

    return patch
```

```python
class HybridIssueSolver:
    """

    """

    def __init__(self, model):
        self.model = model
        self.traceback_analyzer = TracebackAnalyzer()
        self.f2p_generator = F2PTestGenerator(model)

    def solve(
        self,
        issue: str,
        codebase: Dict[str, str]
    ) -> Optional[str]:
        """
        """
        traceback = self.traceback_analyzer.extract(issue)

        if traceback:
            return self._solve_with_traceback(issue, traceback, codebase)
        else:
            return self._solve_with_f2p(issue, codebase)

    def _solve_with_traceback(
        self,
        issue: str,
        traceback: TracebackInfo,
        codebase: Dict[str, str]
    ) -> Optional[str]:
        """
        """
        file_path, line_no = self.traceback_analyzer.get_error_location(traceback)

        if file_path and file_path in codebase:
            context = self.traceback_analyzer.get_context(
                traceback,
                codebase[file_path]
            )
        else:
            return None

        test_code = self.f2p_generator.generate(issue, context)

        patch = self._generate_traceback_aware_patch(
            issue, traceback, context, test_code
        )

        validation = self.f2p_generator.validate(
            test_code,
            codebase[file_path],
            apply_patch(codebase[file_path], patch)
        )

        return patch if validation['valid_f2p'] else None

    def _solve_with_f2p(
        self,
        issue: str,
        codebase: Dict[str, str]
    ) -> Optional[str]:
        """
        """
        context = self._analyze_issue(issue, codebase)

        test_code = self.f2p_generator.generate(issue, context)

        patch = self._generate_patch(issue, test_code, context)

        return patch

    def _generate_traceback_aware_patch(
        self,
        issue: str,
        traceback: TracebackInfo,
        context: str,
        test_code: str
    ) -> str:
        prompt = f"""

Issue: {issue}

{context}

{test_code}

"""
        return self.model.generate(prompt)

    def _generate_patch(
        self,
        issue: str,
        test_code: str,
        context: str
    ) -> str:
        prompt = f"""

Issue:
{issue}

{test_code}

{context}

"""
        return self.model.generate(prompt)
```

---

```python
CONFIDENCE_THRESHOLD = 0.9
MAX_PATCH_SIZE = 500
MAX_FILES_MODIFIED = 2

def should_submit(patch, validation_result):
    return (
        validation_result['valid_f2p'] and
        len(patch) < MAX_PATCH_SIZE and
        validation_result['confidence'] > CONFIDENCE_THRESHOLD
    )
```

```python
def minimal_f2p(issue, code, model):
    test = generate_test(issue, code, model)

    if not test_fails_on_original(test, code):

    patch = generate_patch(issue, test, code, model)

    if not test_passes_on_patched(test, patch, code):

    return patch
```

```python
def minimal_traceback_analysis(issue):
    import re

    pattern = r'File "([^"]+)", line (\d+)'
    matches = re.findall(pattern, issue)

    if matches:
        return {
            'file': matches[0][0],
            'line': int(matches[0][1]),
            'has_traceback': True
        }

    return {'has_traceback': False}
```

```python
def conservative_submit(patch, validation):
    checks = [
        validation['valid_f2p'],
        len(patch) < 500,
        validation['confidence'] > 0.9,
        validation['files_modified'] <= 2
    ]

    return all(checks)
```

|------|----------|------|

```python
from concurrent.futures import ThreadPoolExecutor

def parallel_verify(patches, issue, model, num_workers=4):
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = [
            executor.submit(verify_patch, patch, issue, model)
            for patch in patches
        ]
        results = [f.result() for f in futures]
    return results
```

```python
if verify(patch) == "Yes":

verifications = [verify(patch) for _ in range(5)]
if sum(v == "Yes" for v in verifications) >= 4:
    submit(patch)
```

```python
if is_valid_patch(patch):

if is_valid_patch(patch) and len(patch) < 500:
    submit(patch)
```

```python
if llm_says_good(patch):
    submit(patch)

if test_fails_on_original(test, code) and test_passes_on_patched(test, patch, code):
    submit(patch)
```

---

---

- SWE-bench: https://www.swebench.com/
