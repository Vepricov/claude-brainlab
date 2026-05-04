## Semantic Scholar API

```
GET https://api.semanticscholar.org/graph/v1/paper/{paper_id}
```

```
GET https://api.semanticscholar.org/graph/v1/paper/search?query={query}
```

```bash
pip install semanticscholar
```

```python
from semanticscholar import SemanticScholar

sch = SemanticScholar()

results = sch.search_paper("Attention is All You Need", limit=5)
for paper in results:
    print(f"Title: {paper.title}")
    print(f"Authors: {[a.name for a in paper.authors]}")
    print(f"Year: {paper.year}")
    print(f"DOI: {paper.externalIds.get('DOI', 'N/A')}")
    print("---")
```

```python
paper = sch.get_paper("DOI:10.48550/arXiv.1706.03762")
print(f"Title: {paper.title}")
print(f"Citations: {paper.citationCount}")
```

```python
try:
    paper = sch.get_paper("invalid_id")
except Exception as e:
    print(f"Error: {e}")
```

## arXiv API

```
GET http://export.arxiv.org/api/query?search_query={query}&start={start}&max_results={max}
```

```bash
pip install arxiv
```

```python
import arxiv

paper = next(arxiv.Search(id_list=["1706.03762"]).results())
print(f"Title: {paper.title}")
print(f"Authors: {[a.name for a in paper.authors]}")
print(f"Published: {paper.published}")
print(f"PDF URL: {paper.pdf_url}")

search = arxiv.Search(
    query="Attention is All You Need",
    max_results=5,
    sort_by=arxiv.SortCriterion.Relevance
)

for result in search.results():
    print(f"Title: {result.title}")
    print(f"arXiv ID: {result.entry_id.split('/')[-1]}")
    print("---")
```

```python
import re

def extract_arxiv_id(text):
    match = re.search(r'\d{4}\.\d{4,5}', text)
    if match:
        return match.group()
    match = re.search(r'[a-z-]+/\d{7}', text)
    if match:
        return match.group()
    return None
```

## CrossRef API

```
GET https://api.crossref.org/works/{doi}
```

```
GET https://doi.org/{doi}
Headers: Accept: application/x-bibtex
```

```python
import requests

def get_crossref_metadata(doi):
    url = f"https://api.crossref.org/works/{doi}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data['message']
    return None

doi = "10.48550/arXiv.1706.03762"
metadata = get_crossref_metadata(doi)
if metadata:
    print(f"Title: {metadata['title'][0]}")
    print(f"Authors: {[f\"{a['given']} {a['family']}\" for a in metadata['author']]}")
    print(f"Published: {metadata['published']['date-parts'][0]}")
```

```python
def doi_to_bibtex(doi):
    url = f"https://doi.org/{doi}"
    headers = {"Accept": "application/x-bibtex"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.text
    return None

bibtex = doi_to_bibtex("10.48550/arXiv.1706.03762")
print(bibtex)
```

```python
import re

def extract_doi(text):
    match = re.search(r'10\.\d{4,}/[^\s]+', text)
    if match:
        return match.group()
    return None
```

```
```

```python
def verify_citation(citation_info):
    """

    Args:
        citation_info: dict with keys: doi, arxiv_id, title, authors

    Returns:
    """
    if citation_info.get('doi'):
        return verify_with_crossref(citation_info['doi'])

    if citation_info.get('arxiv_id'):
        return verify_with_arxiv(citation_info['arxiv_id'])

    if citation_info.get('title'):
        return verify_with_semantic_scholar(
            citation_info['title'],
            citation_info.get('authors')
        )

    return {'status': 'insufficient_info'}
```

```python
import time
from requests.exceptions import RequestException

def api_call_with_retry(func, max_retries=3):
    for i in range(max_retries):
        try:
            return func()
        except RequestException as e:
            if i == max_retries - 1:
                raise
```

```python
import time

class RateLimiter:
    def __init__(self, calls_per_minute):
        self.calls_per_minute = calls_per_minute
        self.last_call = 0

    def wait_if_needed(self):
        elapsed = time.time() - self.last_call
        min_interval = 60.0 / self.calls_per_minute
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        self.last_call = time.time()

limiter = RateLimiter(calls_per_minute=20)
limiter.wait_if_needed()
result = api_call()
```

```python
import json
from pathlib import Path

class APICache:
    def __init__(self, cache_dir=".cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def get(self, key):
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            return json.loads(cache_file.read_text())
        return None

    def set(self, key, value):
        cache_file = self.cache_dir / f"{key}.json"
        cache_file.write_text(json.dumps(value))
```

|-----|------|------|----------|
