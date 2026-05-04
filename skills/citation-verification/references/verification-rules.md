```python
def check_bibtex_structure(entry):
    errors = []

    if not entry.get('ENTRYTYPE'):
        errors.append("Missing entry type")

    if not entry.get('ID'):
        errors.append("Missing citation key")

    required = get_required_fields(entry.get('ENTRYTYPE'))
    for field in required:
        if not entry.get(field):
            errors.append(f"Missing required field: {field}")

    return errors
```

```python
def check_field_format(entry):
    errors = []

    if 'year' in entry:
        year = entry['year']
        if not year.isdigit() or len(year) != 4:
            errors.append(f"Invalid year format: {year}")
        if int(year) < 1900 or int(year) > 2030:
            errors.append(f"Year out of reasonable range: {year}")

    if 'doi' in entry:
        doi = entry['doi']
        if not doi.startswith('10.'):
            errors.append(f"Invalid DOI format: {doi}")

    return errors
```

```python
def check_latex_citations(tex_content):
    import re

    cite_pattern = r'\\cite(?:\[[^\]]*\])?\{([^}]+)\}'
    citations = re.findall(cite_pattern, tex_content)

    all_keys = []
    for cite in citations:
        keys = [k.strip() for k in cite.split(',')]
        all_keys.extend(keys)

    return all_keys
```

```python
def check_citation_consistency(tex_keys, bib_keys):
    tex_set = set(tex_keys)
    bib_set = set(bib_keys)

    undefined = tex_set - bib_set

    unused = bib_set - tex_set

    return {
        'undefined': list(undefined),
        'unused': list(unused)
    }
```

```python
def verify_existence(citation_info):
    if citation_info.get('doi'):
        result = verify_with_crossref(citation_info['doi'])
        if result['status'] == 'success':
            return {'exists': True, 'source': 'crossref', 'data': result['data']}

    # arXiv ID
    if citation_info.get('arxiv_id'):
        result = verify_with_arxiv(citation_info['arxiv_id'])
        if result['status'] == 'success':
            return {'exists': True, 'source': 'arxiv', 'data': result['data']}

    if citation_info.get('title'):
        result = verify_with_semantic_scholar(citation_info['title'])
        if result['status'] == 'success' and result['data']:
            return {'exists': True, 'source': 'semantic_scholar', 'data': result['data']}

    return {'exists': False, 'source': None}
```

```python
from difflib import SequenceMatcher

def match_title(title1, title2, threshold=0.85):
    def normalize(text):
        import re
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        return ' '.join(text.split())

    t1 = normalize(title1)
    t2 = normalize(title2)

    ratio = SequenceMatcher(None, t1, t2).ratio()

    return {
        'match': ratio >= threshold,
        'similarity': ratio
    }
```

```python
def match_authors(authors1, authors2, threshold=0.7):
    def normalize_name(name):
        parts = name.replace(',', '').split()
        return ' '.join(sorted(parts)).lower()

    names1 = [normalize_name(a) for a in authors1]
    names2 = [normalize_name(a) for a in authors2]

    set1 = set(names1)
    set2 = set(names2)
    intersection = len(set1 & set2)
    union = len(set1 | set2)

    if union == 0:
        return {'match': False, 'similarity': 0}

    ratio = intersection / union

    return {
        'match': ratio >= threshold,
        'similarity': ratio
    }
```

```python
def match_year(year1, year2, tolerance=1):
    try:
        y1 = int(year1)
        y2 = int(year2)
        diff = abs(y1 - y2)
        return {
            'match': diff <= tolerance,
            'difference': diff
        }
    except (ValueError, TypeError):
        return {'match': False, 'difference': None}
```

```python
def calculate_match_score(citation, api_data):
    scores = {}
    weights = {
        'title': 0.4,
        'authors': 0.3,
        'year': 0.2,
        'venue': 0.1
    }

    if citation.get('title') and api_data.get('title'):
        result = match_title(citation['title'], api_data['title'])
        scores['title'] = result['similarity']

    if citation.get('authors') and api_data.get('authors'):
        result = match_authors(citation['authors'], api_data['authors'])
        scores['authors'] = result['similarity']

    if citation.get('year') and api_data.get('year'):
        result = match_year(citation['year'], api_data['year'])
        scores['year'] = 1.0 if result['match'] else 0.0

    total_score = 0
    total_weight = 0
    for key, weight in weights.items():
        if key in scores:
            total_score += scores[key] * weight
            total_weight += weight

    if total_weight == 0:
        return 0

    return total_score / total_weight
```

```python
def judge_verification_result(match_score):
    if match_score >= 0.9:
        return {
            'status': 'verified',
            'level': 'high_confidence',
        }
    elif match_score >= 0.7:
        return {
            'status': 'partial_match',
            'level': 'medium_confidence',
        }
    elif match_score >= 0.5:
        return {
            'status': 'low_match',
            'level': 'low_confidence',
        }
    else:
        return {
            'status': 'failed',
            'level': 'no_confidence',
        }
```

```python
def verify_citation_complete(citation):
    result = {
        'citation_key': citation.get('ID'),
        'layers': {}
    }

    format_errors = check_bibtex_structure(citation)
    format_errors.extend(check_field_format(citation))
    result['layers']['format'] = {
        'passed': len(format_errors) == 0,
        'errors': format_errors
    }

    existence = verify_existence(citation)
    result['layers']['existence'] = existence

    if not existence['exists']:
        result['final_status'] = 'not_found'
        return result

    api_data = existence['data']
    match_score = calculate_match_score(citation, api_data)
    judgment = judge_verification_result(match_score)

    result['layers']['matching'] = {
        'score': match_score,
        'judgment': judgment
    }

    result['final_status'] = judgment['status']
    result['confidence'] = judgment['level']

    return result
```

```python
VERIFICATION_THRESHOLDS = {

    'weights': {
        'title': 0.4,
        'authors': 0.3,
        'year': 0.2,
        'venue': 0.1
    }
}
```

- title_similarity: 0.90
- author_similarity: 0.80
- high_confidence: 0.95

- title_similarity: 0.80
- author_similarity: 0.60
- high_confidence: 0.85
