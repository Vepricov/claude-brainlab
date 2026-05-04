```bibtex
@article{smith2020,
  title={Deep Learning for NLP},
  year={2020}
}
```

```bibtex
@article{smith2020,
  author={Smith, John and Doe, Jane},
  title={Deep Learning for NLP},
  journal={Nature},
  year={2020}
}
```

```bibtex
```

```bibtex
```

```bibtex
```

```bibtex
```

```bibtex
```

```bibtex
```

```bibtex
```

```bibtex
```

```bibtex
```

```bibtex
```

```python
if not crossref_found and not arxiv_found and not semantic_scholar_found:
```

```bibtex
@article{smith2020deep,
  author={Smith, John},
  title={Deep Learning for NLP},
  journal={Nature},
  year={2020}
}
```

```bibtex
@article{vaswani2017attention,
  author={Vaswani, Ashish and others},
  title={Attention is All You Need},
  year={2017}
}
```

```bibtex
@inproceedings{vaswani2017attention,
  author={Vaswani, Ashish and others},
  title={Attention is All You Need},
  booktitle={Advances in Neural Information Processing Systems},
  year={2017}
}
```

```latex
\cite{smith2020deep}
```

```bibtex
  author={Smith, John},
  title={Deep Learning for NLP},
  year={2020}
}
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

```bibtex
@article{paper1,
  ...
}

@article{paper2,
  ...
}

@article{paper3,
  ...
}
```

```bibtex
@article{vaswani2017,
  author={Vaswani, Ashish and others},
  title={Attention is All You Need},
  booktitle={NeurIPS},
  year={2017}
}

@inproceedings{vaswani2017attention,
  author={Vaswani, A. and others},
  title={Attention is All You Need},
  booktitle={Advances in Neural Information Processing Systems},
  year={2017}
}
```

- Citation verification scripts

|---------|---------|---------|---------|
