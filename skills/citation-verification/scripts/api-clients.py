#!/usr/bin/env python3
"""
API Clients for Citation Verification

"""

import time
import requests
from typing import Dict, List, Optional
from abc import ABC, abstractmethod

class RateLimiter:

    def __init__(self, calls_per_minute: int):
        self.calls_per_minute = calls_per_minute
        self.last_call = 0
        self.min_interval = 60.0 / calls_per_minute

    def wait_if_needed(self):
        elapsed = time.time() - self.last_call
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_call = time.time()

class APIClient(ABC):

    def __init__(self, rate_limit: int = 20):
        """
        Args:
        """
        self.rate_limiter = RateLimiter(rate_limit)

    @abstractmethod
    def search(self, **kwargs) -> Optional[Dict]:
        pass

    def _retry_request(self, func, max_retries: int = 3):
        for i in range(max_retries):
            try:
                self.rate_limiter.wait_if_needed()
                return func()
            except requests.exceptions.RequestException as e:
                if i == max_retries - 1:
                    raise
        return None

class CrossRefClient(APIClient):

    """

    def __init__(self, rate_limit: int = 50):
        """
        Args:
        """
        super().__init__(rate_limit)
        self.base_url = "https://api.crossref.org"

    def search_by_doi(self, doi: str) -> Optional[Dict]:

        Args:

        Returns:
        """
        def request():
            url = f"{self.base_url}/works/{doi}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()

        try:
            data = self._retry_request(request)
            if data and 'message' in data:
                return self._normalize_result(data['message'])
            return None
        except Exception as e:
            return None

    def search(self, doi: str = None, **kwargs) -> Optional[Dict]:
        if doi:
            return self.search_by_doi(doi)
        return None

    def _normalize_result(self, data: Dict) -> Dict:
        title = data.get('title', [''])[0] if 'title' in data else ''

        authors = []
        if 'author' in data:
            for author in data['author']:
                given = author.get('given', '')
                family = author.get('family', '')
                if given and family:
                    authors.append(f"{given} {family}")
                elif family:
                    authors.append(family)

        year = None
        if 'published' in data:
            date_parts = data['published'].get('date-parts', [[]])[0]
            if date_parts:
                year = date_parts[0]
        elif 'created' in data:
            date_parts = data['created'].get('date-parts', [[]])[0]
            if date_parts:
                year = date_parts[0]

        venue = ''
        if 'container-title' in data:
            venue = data['container-title'][0] if data['container-title'] else ''

        return {
            'title': title,
            'authors': authors,
            'year': year,
            'venue': venue,
            'doi': data.get('DOI', ''),
            'type': data.get('type', ''),
            'source': 'crossref'
        }

    def get_bibtex(self, doi: str) -> Optional[str]:

        Args:

        Returns:
        """
        def request():
            url = f"https://doi.org/{doi}"
            headers = {"Accept": "application/x-bibtex"}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.text

        try:
            return self._retry_request(request)
        except Exception as e:
            return None

class ArXivClient(APIClient):

    """

    def __init__(self, rate_limit: int = 20):
        """
        Args:
        """
        super().__init__(rate_limit)
        try:
            import arxiv
            self.arxiv = arxiv
        except ImportError:

    def search_by_id(self, arxiv_id: str) -> Optional[Dict]:

        Args:

        Returns:
        """
        def request():
            search = self.arxiv.Search(id_list=[arxiv_id])
            paper = next(search.results())
            return paper

        try:
            self.rate_limiter.wait_if_needed()
            paper = request()
            return self._normalize_result(paper)
        except StopIteration:
            return None
        except Exception as e:
            return None

    def search_by_title(self, title: str, max_results: int = 5) -> Optional[Dict]:

        Args:

        Returns:
        """
        def request():
            search = self.arxiv.Search(
                query=f'ti:"{title}"',
                max_results=max_results,
                sort_by=self.arxiv.SortCriterion.Relevance
            )
            results = list(search.results())
            return results[0] if results else None

        try:
            self.rate_limiter.wait_if_needed()
            paper = request()
            if paper:
                return self._normalize_result(paper)
            return None
        except Exception as e:
            return None

    def search(self, arxiv_id: str = None, title: str = None, **kwargs) -> Optional[Dict]:
        if arxiv_id:
            return self.search_by_id(arxiv_id)
        elif title:
            return self.search_by_title(title)
        return None

    def _normalize_result(self, paper) -> Dict:
        arxiv_id = paper.entry_id.split('/')[-1]

        return {
            'title': paper.title,
            'authors': [a.name for a in paper.authors],
            'year': paper.published.year,
            'venue': 'arXiv',
            'arxiv_id': arxiv_id,
            'doi': paper.doi if hasattr(paper, 'doi') else None,
            'abstract': paper.summary,
            'pdf_url': paper.pdf_url,
            'source': 'arxiv'
        }

    @staticmethod
    def extract_arxiv_id(text: str) -> Optional[str]:

        Args:

        Returns:
        """
        import re

        match = re.search(r'\d{4}\.\d{4,5}', text)
        if match:
            return match.group()

        match = re.search(r'[a-z-]+/\d{7}', text)
        if match:
            return match.group()

        return None

class SemanticScholarClient(APIClient):

    """

    def __init__(self, rate_limit: int = 20):
        """
        Args:
        """
        super().__init__(rate_limit)
        try:
            from semanticscholar import SemanticScholar
            self.sch = SemanticScholar()
        except ImportError:

    def search_by_title(self, title: str, max_results: int = 5) -> Optional[Dict]:

        Args:

        Returns:
        """
        try:
            self.rate_limiter.wait_if_needed()
            results = self.sch.search_paper(title, limit=max_results)

            if not results:
                return None

            paper = results[0]
            return self._normalize_result(paper)
        except Exception as e:
            return None

    def search_by_doi(self, doi: str) -> Optional[Dict]:

        Args:

        Returns:
        """
        try:
            self.rate_limiter.wait_if_needed()
            paper = self.sch.get_paper(f"DOI:{doi}")
            if paper:
                return self._normalize_result(paper)
            return None
        except Exception as e:
            return None

    def search(self, title: str = None, doi: str = None, **kwargs) -> Optional[Dict]:
        if doi:
            return self.search_by_doi(doi)
        elif title:
            return self.search_by_title(title)
        return None

    def _normalize_result(self, paper) -> Dict:
        authors = []
        if paper.authors:
            authors = [a.name for a in paper.authors]

        external_ids = paper.externalIds if hasattr(paper, 'externalIds') else {}
        doi = external_ids.get('DOI') if external_ids else None
        arxiv_id = external_ids.get('ArXiv') if external_ids else None

        return {
            'title': paper.title,
            'authors': authors,
            'year': paper.year,
            'venue': paper.venue if hasattr(paper, 'venue') else '',
            'paperId': paper.paperId,
            'doi': doi,
            'arxiv_id': arxiv_id,
            'citationCount': paper.citationCount if hasattr(paper, 'citationCount') else 0,
            'abstract': paper.abstract if hasattr(paper, 'abstract') else '',
            'source': 'semantic_scholar'
        }

class CitationAPIManager:

    """

    def __init__(self):
        self.crossref = None
        self.arxiv = None
        self.semantic_scholar = None

        try:
            self.crossref = CrossRefClient()
        except Exception as e:

        try:
            self.arxiv = ArXivClient()
        except Exception as e:

        try:
            self.semantic_scholar = SemanticScholarClient()
        except Exception as e:

    def verify_citation(self, citation_info: Dict) -> tuple[bool, Optional[str], Optional[Dict]]:

        2. arXiv ID → arXiv

        Args:

        Returns:
            (exists, api_source, api_data)
        """
        if 'doi' in citation_info and self.crossref:
            data = self.crossref.search_by_doi(citation_info['doi'])
            if data:
                return True, 'crossref', data

        arxiv_id = citation_info.get('arxiv_id')
        if not arxiv_id and 'note' in citation_info:
            arxiv_id = ArXivClient.extract_arxiv_id(citation_info['note'])

        if arxiv_id and self.arxiv:
            data = self.arxiv.search_by_id(arxiv_id)
            if data:
                return True, 'arxiv', data

        if 'title' in citation_info and self.semantic_scholar:
            data = self.semantic_scholar.search_by_title(citation_info['title'])
            if data:
                return True, 'semantic_scholar', data

        return False, None, None

    def get_bibtex(self, doi: str) -> Optional[str]:

        Args:

        Returns:
        """
        if self.crossref:
            return self.crossref.get_bibtex(doi)
        return None

# ============================================================================
# ============================================================================

if __name__ == '__main__':
    print("-" * 60)
    crossref = CrossRefClient()
    result = crossref.search_by_doi("10.48550/arXiv.1706.03762")
    if result:
    print()

    print("-" * 60)
    try:
        arxiv_client = ArXivClient()
        result = arxiv_client.search_by_id("1706.03762")
        if result:
    except ImportError as e:
    print()

    print("-" * 60)
    try:
        ss_client = SemanticScholarClient()
        result = ss_client.search_by_title("Attention is All You Need")
        if result:
    except ImportError as e:
    print()

    print("-" * 60)
    manager = CitationAPIManager()
    citation_info = {
        'title': 'Attention is All You Need',
        'authors': ['Vaswani', 'Shazeer'],
        'year': '2017'
    }
    exists, source, data = manager.verify_citation(citation_info)
    if exists:
