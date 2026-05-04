#!/usr/bin/env python3
"""
BibTeX and LaTeX Format Checker

    python format-checker.py references.bib
    python format-checker.py paper.tex --check-latex
    python format-checker.py references.bib --strict
"""

import argparse
import sys
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

try:
    import bibtexparser
    from bibtexparser.bparser import BibTexParser
    BIBTEX_AVAILABLE = True
except ImportError:
    BIBTEX_AVAILABLE = False

class ErrorLevel(Enum):

@dataclass
class FormatError:
    level: ErrorLevel

def parse_arguments():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
  %(prog)s references.bib
  %(prog)s paper.tex --check-latex
  %(prog)s references.bib --strict --output report.txt
  %(prog)s references.bib --fix-common
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
        '--strict',
        action='store_true',
    )

    parser.add_argument(
        '--output',
        type=str,
    )

    parser.add_argument(
        '--fix-common',
        action='store_true',
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
    )

    parser.add_argument(
        '--entry-type',
        type=str,
    )

    return parser.parse_args()

def load_bibtex_file(file_path: str) -> List[Dict]:

    Args:

    Returns:

    Raises:
    """
    if not BIBTEX_AVAILABLE:

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            parser = BibTexParser(common_strings=True)
            bib_database = bibtexparser.load(f, parser)
            return bib_database.entries
    except FileNotFoundError:
    except Exception as e:

def load_latex_file(file_path: str) -> str:

    Args:

    Returns:

    Raises:
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
    except Exception as e:

# ============================================================================
# ============================================================================

def get_required_fields(entry_type: str) -> List[str]:

    Args:

    Returns:
    """
    required_fields = {
        'article': ['author', 'title', 'journal', 'year'],
        'inproceedings': ['author', 'title', 'booktitle', 'year'],
        'book': ['title', 'publisher', 'year'],
        'incollection': ['author', 'title', 'booktitle', 'publisher', 'year'],
        'inbook': ['author', 'title', 'chapter', 'publisher', 'year'],
        'proceedings': ['title', 'year'],
        'phdthesis': ['author', 'title', 'school', 'year'],
        'mastersthesis': ['author', 'title', 'school', 'year'],
        'techreport': ['author', 'title', 'institution', 'year'],
        'manual': ['title'],
        'misc': ['title'],
        'unpublished': ['author', 'title', 'note'],
    }
    return required_fields.get(entry_type.lower(), ['title'])

def get_optional_fields(entry_type: str) -> List[str]:

    Args:

    Returns:
    """
    optional_fields = {
        'article': ['volume', 'number', 'pages', 'month', 'doi', 'url'],
        'inproceedings': ['editor', 'volume', 'series', 'pages', 'address',
                         'month', 'organization', 'publisher', 'doi', 'url'],
        'book': ['author', 'editor', 'volume', 'series', 'address',
                'edition', 'month', 'isbn', 'doi', 'url'],
    }
    return optional_fields.get(entry_type.lower(), [])

def check_entry_structure(entry: Dict) -> List[FormatError]:

    Args:

    Returns:
    """
    errors = []

    if 'ENTRYTYPE' not in entry:
        errors.append(FormatError(
            level=ErrorLevel.ERROR,
            location=f"entry:{entry.get('ID', 'unknown')}",
            field='ENTRYTYPE',
        ))
        return errors

    if 'ID' not in entry or not entry['ID'].strip():
        errors.append(FormatError(
            level=ErrorLevel.ERROR,
            location="entry:unknown",
            field='ID',
        ))

    entry_type = entry.get('ENTRYTYPE', '')
    required = get_required_fields(entry_type)
    for field in required:
        if field not in entry or not entry[field].strip():
            errors.append(FormatError(
                level=ErrorLevel.ERROR,
                location=f"entry:{entry.get('ID', 'unknown')}",
                field=field,
            ))

    return errors

def check_field_formats(entry: Dict) -> List[FormatError]:

    Args:

    Returns:
    """
    errors = []
    entry_id = entry.get('ID', 'unknown')

    if 'year' in entry:
        year = entry['year'].strip()
        if not year.isdigit():
            errors.append(FormatError(
                level=ErrorLevel.ERROR,
                location=f"entry:{entry_id}",
                field='year',
            ))
        elif len(year) != 4:
            errors.append(FormatError(
                level=ErrorLevel.ERROR,
                location=f"entry:{entry_id}",
                field='year',
            ))
        else:
            year_int = int(year)
            if year_int < 1900 or year_int > 2030:
                errors.append(FormatError(
                    level=ErrorLevel.WARNING,
                    location=f"entry:{entry_id}",
                    field='year',
                ))

    if 'doi' in entry:
        doi = entry['doi'].strip()
        if not doi.startswith('10.'):
            errors.append(FormatError(
                level=ErrorLevel.ERROR,
                location=f"entry:{entry_id}",
                field='doi',
            ))
        if 'doi.org' in doi or 'dx.doi.org' in doi:
            errors.append(FormatError(
                level=ErrorLevel.WARNING,
                location=f"entry:{entry_id}",
                field='doi',
            ))

    if 'author' in entry:
        author = entry['author'].strip()
        if not author:
            errors.append(FormatError(
                level=ErrorLevel.ERROR,
                location=f"entry:{entry_id}",
                field='author',
            ))
        elif ' and ' in author:
            authors = author.split(' and ')
            formats = []
            for a in authors:
                if ',' in a:
                    formats.append('last_first')  # "Last, First"
                else:
                    formats.append('first_last')  # "First Last"

            if len(set(formats)) > 1:
                errors.append(FormatError(
                    level=ErrorLevel.WARNING,
                    location=f"entry:{entry_id}",
                    field='author',
                ))

    if 'pages' in entry:
        pages = entry['pages'].strip()
        if '-' in pages and '--' not in pages:
            errors.append(FormatError(
                level=ErrorLevel.INFO,
                location=f"entry:{entry_id}",
                field='pages',
            ))

    if 'url' in entry:
        url = entry['url'].strip()
        if not url.startswith(('http://', 'https://')):
            errors.append(FormatError(
                level=ErrorLevel.WARNING,
                location=f"entry:{entry_id}",
                field='url',
            ))

    return errors

def check_consistency(entries: List[Dict]) -> List[FormatError]:

    Args:

    Returns:
    """
    errors = []

    ids = [e.get('ID', '') for e in entries]
    duplicates = [id for id in ids if ids.count(id) > 1]
    if duplicates:
        for dup_id in set(duplicates):
            errors.append(FormatError(
                level=ErrorLevel.ERROR,
                location=f"entry:{dup_id}",
                field='ID',
            ))

    author_formats = {}
    for entry in entries:
        if 'author' in entry and ' and ' in entry['author']:
            entry_id = entry.get('ID', 'unknown')
            authors = entry['author'].split(' and ')
            for author in authors:
                if ',' in author:
                    author_formats[entry_id] = 'last_first'
                else:
                    author_formats[entry_id] = 'first_last'
                break

    if len(set(author_formats.values())) > 1:
        errors.append(FormatError(
            level=ErrorLevel.WARNING,
            location="global",
            field='author',
        ))

    return errors

# ============================================================================
# ============================================================================

def extract_latex_citations(tex_content: str) -> List[str]:

    Args:

    Returns:
    """
    cite_pattern = r'\\cite(?:\[[^\]]*\])?(?:\[[^\]]*\])?\{([^}]+)\}'
    citations = re.findall(cite_pattern, tex_content)

    all_keys = []
    for cite in citations:
        keys = [k.strip() for k in cite.split(',')]
        all_keys.extend(keys)

def check_latex_consistency(tex_keys: List[str], bib_keys: List[str]) -> List[FormatError]:

    Args:

    Returns:
    """
    errors = []

    tex_set = set(tex_keys)
    bib_set = set(bib_keys)

    undefined = tex_set - bib_set
    if undefined:
        for key in sorted(undefined):
            errors.append(FormatError(
                level=ErrorLevel.ERROR,
                location=f"latex:cite",
                field=key,
            ))

    unused = bib_set - tex_set
    if unused:
        for key in sorted(unused):
            errors.append(FormatError(
                level=ErrorLevel.WARNING,
                location=f"bibtex:entry",
                field=key,
            ))

    return errors

# ============================================================================
# ============================================================================

def print_errors(errors: List[FormatError], verbose: bool = False):

    Args:
    """
    if not errors:
        return

    errors_by_level = {
        ErrorLevel.ERROR: [],
        ErrorLevel.WARNING: [],
        ErrorLevel.INFO: []
    }

    for error in errors:
        errors_by_level[error.level].append(error)

    print("\n" + "="*60)
    print("="*60)
    print("="*60)

    for level in [ErrorLevel.ERROR, ErrorLevel.WARNING, ErrorLevel.INFO]:
        level_errors = errors_by_level[level]
        if not level_errors:
            continue

        level_symbol = {
            ErrorLevel.ERROR: "❌",
            ErrorLevel.WARNING: "⚠️",
            ErrorLevel.INFO: "ℹ️"
        }[level]

        print(f"\n{level_symbol} {level.value.upper()} ({len(level_errors)}):\n")

        for error in level_errors:
            print(f"  [{error.location}]", end="")
            if error.field:
                print(f" {error.field}:", end="")
            print(f" {error.message}")

            if verbose and error.suggestion:
            print()

def generate_report(errors: List[FormatError], output_file: str):

    Args:
    """
    errors_by_level = {
        ErrorLevel.ERROR: [],
        ErrorLevel.WARNING: [],
        ErrorLevel.INFO: []
    }

    for error in errors:
        errors_by_level[error.level].append(error)

    with open(output_file, 'w', encoding='utf-8') as f:

        for level in [ErrorLevel.ERROR, ErrorLevel.WARNING, ErrorLevel.INFO]:
            level_errors = errors_by_level[level]
            if not level_errors:
                continue

            level_name = {
            }[level]

            f.write(f"## {level_name} ({len(level_errors)})\n\n")

            for error in level_errors:
                f.write(f"### [{error.location}]")
                if error.field:
                    f.write(f" {error.field}")
                f.write("\n\n")
                if error.suggestion:
