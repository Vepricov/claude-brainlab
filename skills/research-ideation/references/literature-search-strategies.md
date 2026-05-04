# Literature Search Strategies

Systematic literature search methods to help researchers efficiently find relevant papers.

## 1. Keyword Construction

### 1.1 Core Concept Identification

Extract core concepts from research interests:

**Example**: Research interest "Interpretability of Transformer models"
- Core concept 1: Transformer
- Core concept 2: Interpretability / Explainability

### 1.2 Synonyms and Variants

List synonyms and variants for each core concept:

| Core Concept | Synonyms/Variants |
|-------------|------------------|
| Transformer | Attention mechanism, Self-attention, BERT, GPT |
| Interpretability | Explainability, Transparency, Understanding |

### 1.3 Boolean Operators

Use Boolean operators to combine keywords:

```
(Transformer OR "attention mechanism" OR BERT OR GPT)
AND
(interpretability OR explainability OR transparency)
```

### 1.4 Domain-Specific Terms

Add domain-specific terminology:

- **Method terms**: probing, attention visualization, saliency maps
- **Application domains**: NLP, computer vision, speech recognition
- **Evaluation metrics**: faithfulness, plausibility, human evaluation

## 2. Academic Database Selection

### 2.1 Main Databases

| Database | Characteristics | Best Use Case |
|----------|----------------|---------------|
| **arXiv** | Preprints, fast updates | Latest research developments |
| **Semantic Scholar** | AI-driven, citation analysis | Discovering related papers, analyzing influence |
| **Google Scholar** | Broad coverage | Comprehensive search, finding missed papers |
| **ACL Anthology** | NLP-specialized | Deep search in NLP domain |
| **IEEE Xplore** | Engineering/technology | Computer vision, hardware-related topics |

### 2.2 Search Strategies

**arXiv search**:
```
cat:cs.LG AND (transformer OR attention) AND (interpretability OR explainability)
```

**Semantic Scholar search**:
- Use natural language queries
- Filter by "Highly Influential Citations"
- Check "Related Papers" to discover related work

**Google Scholar search**:
- Use quotes for exact match: "transformer interpretability"
- Restrict time range: 2020-2024
- Exclude patents: -patent

## 3. Search Techniques

### 3.1 Iterative Search

1. **Initial search** — use core keywords
2. **Analyze results** — examine keywords in highly-cited papers
3. **Refine query** — add newly discovered terms
4. **Repeat** — until sufficient relevant papers are found

### 3.2 Citation Tracking

**Forward citation**:
- Find which newer papers cite a given paper
- Understand subsequent developments

**Backward citation**:
- Find which papers a given paper cites
- Understand the foundational background

### 3.3 Author Tracking

- Identify key researchers in the field
- Review their other related work
- Follow their latest research

## 4. Paper Screening Criteria

### 4.1 Initial Screening (based on title and abstract)

**Inclusion criteria**:
- Directly relevant to the research topic
- Published at top conferences/journals (NeurIPS, ICML, ICLR, ACL, AAAI)
- High citation count (relative to publication date)
- Authors from recognized institutions or research groups

**Exclusion criteria**:
- Unrelated to the research topic
- Published in low-quality conferences/journals
- Clearly outdated methods (unless a classic paper)

### 4.2 Deep Screening (based on full text)

**Quality assessment**:
1. **Method novelty** — does it propose a new method or perspective?
2. **Experimental rigor** — is the experimental design sound and results credible?
3. **Writing quality** — is the paper clear and understandable?
4. **Reproducibility** — does it provide code and data?

**Relevance assessment**:
1. **Directly relevant** — core method or problem is directly related
2. **Indirectly relevant** — related techniques or application scenarios
3. **Background knowledge** — provides necessary background and foundations

### 4.3 Literature Management

**Integrated tools**:
- **Zotero** (primary tool, integrated via MCP)
  - Use `add_items_by_doi` to automatically add papers with full metadata
  - Use `create_collection` to automatically create and organize collections
  - Use `find_and_attach_pdfs` to automatically attach OA PDFs
  - Use `get_item_fulltext` to read PDF full text for analysis
  - Use `search_library` to search existing papers and avoid duplicate imports
- Mendeley — social features, PDF annotation (alternative)
- Papers — Mac-specific, elegant interface (alternative)

**Organization strategy**:

Use Zotero collection structure to organize literature:

```
Research-{topic}-{date}
  Core Papers
  Methods
  Applications
  Baselines
  To-Read
```

- Core Papers: directly relevant, highly cited key papers
- Methods: technical method references, reusable methodologies
- Applications: application scenario references, domain practices
- Baselines: experimental comparison baselines, work to reproduce
- To-Read: initially screened, pending deeper reading

## 5. DOI Extraction and Automated Import

### 5.1 DOI Extraction Methods

Common ways to extract DOIs from WebSearch results:

**DOIs in URLs**:
- `https://doi.org/10.xxxx/xxxxx` — direct DOI link
- `https://dl.acm.org/doi/10.xxxx/xxxxx` — ACM Digital Library
- `https://ieeexplore.ieee.org/document/xxxxx` — IEEE (extract from page)
- `https://arxiv.org/abs/xxxx.xxxxx` — arXiv (DOI format: `10.48550/arXiv.xxxx.xxxxx`)

**Common DOI formats**:
- `10.xxxx/xxxxx` — standard DOI prefix
- Starts with `10.`, contains `/` separator
- Example: `10.1038/s41586-023-06747-5` (Nature)
- Example: `10.48550/arXiv.2301.00234` (arXiv)

### 5.2 Automated Import Workflow

```
WebSearch for papers
    |
    v
Extract DOIs from search results
    |
    v
add_items_by_doi to batch-add to Zotero
    |
    v
find_and_attach_pdfs to automatically attach OA PDFs
    |
    v
get_item_fulltext to read full text for analysis
```

**Example workflow**:

1. Use WebSearch to search `"transformer interpretability" site:arxiv.org OR site:doi.org`
2. Collect DOI list from results
3. Call `add_items_by_doi` for batch import (recommend no more than 10 per batch to avoid API rate limits)
4. Call `find_and_attach_pdfs` to attach PDFs for imported papers
5. Use `get_item_fulltext` to read key papers in full

### 5.3 Handling Papers Without DOI

Some papers may not have a standard DOI:
- **arXiv preprints**: Use `10.48550/arXiv.{id}` format
- **Conference proceedings**: Try to get DOI from publisher page
- **Cannot get DOI**: Use `add_web_item` to save webpage link, or use `import_pdf_to_zotero` to import PDF directly
