#!/usr/bin/env python3
"""
Citation Verification Script

    python verify-citations.py references.bib
    python verify-citations.py paper.tex --check-latex
    python verify-citations.py references.bib --verbose --output report.md
"""

import argparse
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import re
from difflib import SequenceMatcher

try:
    import bibtexparser
    from bibtexparser.bparser import BibTexParser
except ImportError:
    sys.exit(1)

try:
    from semanticscholar import SemanticScholar
except ImportError:

try:
    import arxiv
except ImportError:

try:
    import requests
except ImportError:
    sys.exit(1)

@dataclass
class VerificationResult:
    citation_key: str
    status: str  # verified, partial_match, low_match, failed, not_found
    confidence: str  # high_confidence, medium_confidence, low_confidence, no_confidence
    match_score: float
    format_errors: List[str]
    api_source: Optional[str]  # crossref, arxiv, semantic_scholar
    message: str

def parse_arguments():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
  %(prog)s references.bib
  %(prog)s paper.tex --check-latex
  %(prog)s references.bib --verbose --output report.md
  %(prog)s references.bib --api-only
        """
    )

    parser.add_argument(
        'input_file',
        type=str,
    )

    parser.add_argument(
        '--check-latex',
        action='store_true',
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
    )

    parser.add_argument(
        '--output',
        type=str,
    )

    parser.add_argument(
        '--api-only',
        action='store_true',
    )

    parser.add_argument(
        '--format-only',
        action='store_true',
    )

    parser.add_argument(
        '--threshold',
        type=float,
        default=0.85,
    )

    return parser.parse_args()

def load_bibtex(file_path: str) -> List[Dict]:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            parser = BibTexParser(common_strings=True)
            bib_database = bibtexparser.load(f, parser)
            return bib_database.entries
    except FileNotFoundError:
        sys.exit(1)
    except Exception as e:
        sys.exit(1)

def extract_latex_citations(tex_file: str) -> List[str]:
    try:
        with open(tex_file, 'r', encoding='utf-8') as f:
            content = f.read()

        cite_pattern = r'\\cite(?:\[[^\]]*\])?\{([^}]+)\}'
        citations = re.findall(cite_pattern, content)

        all_keys = []
        for cite in citations:
            keys = [k.strip() for k in cite.split(',')]
            all_keys.extend(keys)

    except FileNotFoundError:
        sys.exit(1)
    except Exception as e:
        sys.exit(1)

# ============================================================================
# ============================================================================

def get_required_fields(entry_type: str) -> List[str]:
    required_fields = {
        'article': ['author', 'title', 'journal', 'year'],
        'inproceedings': ['author', 'title', 'booktitle', 'year'],
        'book': ['title', 'publisher', 'year'],
        'misc': ['title'],
        'phdthesis': ['author', 'title', 'school', 'year'],
        'mastersthesis': ['author', 'title', 'school', 'year'],
        'techreport': ['author', 'title', 'institution', 'year'],
    }
    return required_fields.get(entry_type.lower(), ['title'])

def check_bibtex_format(entry: Dict) -> List[str]:

    Returns:
    """
    errors = []

    if 'ENTRYTYPE' not in entry:
        return errors

    if 'ID' not in entry:

    entry_type = entry.get('ENTRYTYPE', '')
    required = get_required_fields(entry_type)
    for field in required:
        if field not in entry or not entry[field].strip():

    if 'year' in entry:
        year = entry['year'].strip()
        if not year.isdigit() or len(year) != 4:
        else:
            year_int = int(year)
            if year_int < 1900 or year_int > 2030:

    if 'doi' in entry:
        doi = entry['doi'].strip()
        if not doi.startswith('10.'):

    return errors

def check_citation_consistency(tex_keys: List[str], bib_keys: List[str]) -> Dict:

    Returns:
        {'undefined': [...], 'unused': [...]}
    """
    tex_set = set(tex_keys)
    bib_set = set(bib_keys)

    return {
        'undefined': list(tex_set - bib_set),
        'unused': list(bib_set - tex_set)
    }

# ============================================================================
# ============================================================================

def verify_with_crossref(doi: str) -> Optional[Dict]:
    try:
        url = f"https://api.crossref.org/works/{doi}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('message')
        return None
    except Exception as e:
        return None

def verify_with_arxiv(arxiv_id: str) -> Optional[Dict]:
    try:
        search = arxiv.Search(id_list=[arxiv_id])
        paper = next(search.results())
        return {
            'title': paper.title,
            'authors': [a.name for a in paper.authors],
            'year': paper.published.year,
            'arxiv_id': arxiv_id
        }
    except Exception as e:
        return None

def verify_with_semantic_scholar(title: str, authors: Optional[List[str]] = None) -> Optional[Dict]:
    try:
        sch = SemanticScholar()
        results = sch.search_paper(title, limit=5)

        if not results:
            return None

        paper = results[0]
        return {
            'title': paper.title,
            'authors': [a.name for a in paper.authors] if paper.authors else [],
            'year': paper.year,
            'paperId': paper.paperId
        }
    except Exception as e:
        return None

def verify_existence(entry: Dict) -> Tuple[bool, Optional[str], Optional[Dict]]:

    Returns:
        (exists, api_source, api_data)
    """
    if 'doi' in entry:
        data = verify_with_crossref(entry['doi'])
        if data:
            return True, 'crossref', data

    if 'eprint' in entry or 'arxiv' in entry.get('note', '').lower():
        arxiv_id = entry.get('eprint', '')
        if not arxiv_id:
            match = re.search(r'arXiv:(\d{4}\.\d{4,5})', entry.get('note', ''))
            if match:
                arxiv_id = match.group(1)

        if arxiv_id:
            data = verify_with_arxiv(arxiv_id)
            if data:
                return True, 'arxiv', data

    if 'title' in entry:
        authors = entry.get('author', '').split(' and ') if 'author' in entry else None
        data = verify_with_semantic_scholar(entry['title'], authors)
        if data:
            return True, 'semantic_scholar', data

    return False, None, None

# ============================================================================
# ============================================================================

def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    return ' '.join(text.split())

def match_title(title1: str, title2: str, threshold: float = 0.85) -> Dict:
    t1 = normalize_text(title1)
    t2 = normalize_text(title2)

    ratio = SequenceMatcher(None, t1, t2).ratio()

    return {
        'match': ratio >= threshold,
        'similarity': ratio
    }

def normalize_author_name(name: str) -> str:
    parts = name.replace(',', '').split()
    return ' '.join(sorted(parts)).lower()

def match_authors(authors1: List[str], authors2: List[str], threshold: float = 0.7) -> Dict:
    names1 = [normalize_author_name(a) for a in authors1]
    names2 = [normalize_author_name(a) for a in authors2]

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

def match_year(year1: str, year2: int, tolerance: int = 1) -> Dict:
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

def calculate_match_score(entry: Dict, api_data: Dict, threshold: float) -> float:
    scores = {}
    weights = {
        'title': 0.4,
        'authors': 0.3,
        'year': 0.2,
        'venue': 0.1
    }

    if 'title' in entry and 'title' in api_data:
        result = match_title(entry['title'], api_data['title'], threshold)
        scores['title'] = result['similarity']

    if 'author' in entry and 'authors' in api_data:
        entry_authors = entry['author'].split(' and ')
        result = match_authors(entry_authors, api_data['authors'])
        scores['authors'] = result['similarity']

    if 'year' in entry and 'year' in api_data:
        result = match_year(entry['year'], api_data['year'])
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

def judge_verification_result(match_score: float) -> Dict:
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

def verify_citation(entry: Dict, args) -> VerificationResult:
    citation_key = entry.get('ID', 'unknown')

    format_errors = []
    if not args.api_only:
        format_errors = check_bibtex_format(entry)

    if args.format_only:
        return VerificationResult(
            citation_key=citation_key,
            status='format_checked',
            confidence='n/a',
            match_score=0.0,
            format_errors=format_errors,
            api_source=None,
        )

    exists, api_source, api_data = verify_existence(entry)

    if not exists:
        return VerificationResult(
            citation_key=citation_key,
            status='not_found',
            confidence='no_confidence',
            match_score=0.0,
            format_errors=format_errors,
            api_source=None,
        )

    match_score = calculate_match_score(entry, api_data, args.threshold)
    judgment = judge_verification_result(match_score)

    return VerificationResult(
        citation_key=citation_key,
        status=judgment['status'],
        confidence=judgment['level'],
        match_score=match_score,
        format_errors=format_errors,
        api_source=api_source,
        message=judgment['message']
    )

# ============================================================================
# ============================================================================

def print_summary(results: List[VerificationResult], verbose: bool = False):
    total = len(results)
    verified = sum(1 for r in results if r.status == 'verified')
    partial = sum(1 for r in results if r.status == 'partial_match')
    low = sum(1 for r in results if r.status == 'low_match')
    failed = sum(1 for r in results if r.status in ['failed', 'not_found'])

    print("\n" + "="*60)
    print("="*60)
    print("="*60)

    if verbose:
        for result in results:
            print(f"[{result.citation_key}]")
            if result.api_source:
            if result.format_errors:
            print()

def generate_markdown_report(results: List[VerificationResult], output_file: str):
    total = len(results)
    verified = sum(1 for r in results if r.status == 'verified')
    partial = sum(1 for r in results if r.status == 'partial_match')
    low = sum(1 for r in results if r.status == 'low_match')
    failed = sum(1 for r in results if r.status in ['failed', 'not_found'])

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Citation Verification Report\n\n")

        for status, emoji, title in [
        ]:
            status_results = [r for r in results if r.status == status]
            if status_results:
                f.write(f"### {emoji} {title} ({len(status_results)})\n\n")
                for result in status_results:
                    f.write(f"#### `{result.citation_key}`\n\n")
                    if result.api_source:
                    if result.format_errors:
                        for error in result.format_errors:
                            f.write(f"  - {error}\n")
                    f.write("\n")

        if failed > 0:
            failed_results = [r for r in results if r.status in ['failed', 'not_found']]
            for result in failed_results:
                f.write(f"- `{result.citation_key}`: {result.message}\n")
            f.write("\n")

        if partial > 0 or low > 0:
            check_results = [r for r in results if r.status in ['partial_match', 'low_match']]
            for result in check_results:
                f.write(f"- `{result.citation_key}`: {result.message}\n")
            f.write("\n")

# ============================================================================
# ============================================================================

def main():
    args = parse_arguments()

    entries = load_bibtex(args.input_file)

    if args.check_latex:
        tex_file = args.input_file.replace('.bib', '.tex')
        if Path(tex_file).exists():
            tex_keys = extract_latex_citations(tex_file)
            bib_keys = [e['ID'] for e in entries]
            consistency = check_citation_consistency(tex_keys, bib_keys)

            if consistency['undefined']:
            if consistency['unused']:
            if not consistency['undefined'] and not consistency['unused']:

    results = []
    for i, entry in enumerate(entries, 1):
        citation_key = entry.get('ID', 'unknown')

        result = verify_citation(entry, args)
        results.append(result)

        if result.status == 'verified':
            print("✅")
        elif result.status == 'partial_match':
            print("⚠️")
        else:
            print("❌")

    print_summary(results, args.verbose)

    if args.output:
        generate_markdown_report(results, args.output)

    failed_count = sum(1 for r in results if r.status in ['failed', 'not_found'])
    return 0 if failed_count == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
