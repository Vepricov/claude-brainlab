> 
> **📝 Important Notice**: This repository is improved based on the official AAAI 2026 template with the assistance of Cursor. If you encounter any issues or conflicts, please actively submit issues.

---

**📖 Online View and Test Template**: [https://cn.overleaf.com/read/wyhcnvcrtpyt#cd4a07](https://cn.overleaf.com/read/wyhcnvcrtpyt#cd4a07)

- English: You can view, edit, and compile the template directly in Overleaf using the link above, without needing a local LaTeX installation

---

```latex
\def\aaaianonymous{true}
```

```latex
% \def\aaaianonymous{true}
```

```latex
\ifdefined\aaaianonymous
\else
\fi

\ifdefined\aaaianonymous
    \title{AAAI Press Anonymous Submission\\Instructions for Authors Using \LaTeX{}}
\else
    \title{AAAI Press Formatting Instructions \\for Authors Using \LaTeX{} --- A Guide}
\fi

\ifdefined\aaaianonymous
\else
\fi
```

```latex
\def\aaaianonymous{true}

% \def\aaaianonymous{true}
```

```bash
pdflatex aaai2026-unified-template.tex
bibtex aaai2026-unified-template
pdflatex aaai2026-unified-template.tex
pdflatex aaai2026-unified-template.tex
```

---

## English Version

### Overview ✅

I have **completely merged** the two AAAI 2026 versions (anonymous submission and camera-ready) into a single unified template file `aaai2026-unified-template.tex`.

This template contains **all complete content** from both original templates (886 lines total, more comprehensive than the original files), including:
- All formatting instructions and requirements
- Complete example codes and tables
- Image processing guidelines
- Reference formatting requirements
- All sections and appendix content
- Version-specific Acknowledgments sections

### Key Differences Analysis

By comparing the two original templates, the main differences are:

#### 1. Package Loading Method
- **Anonymous version**: `\usepackage[submission]{aaai2026}`
- **Camera-ready version**: `\usepackage{aaai2026}`

#### 2. Title Differences
- **Anonymous version**: "AAAI Press Anonymous Submission Instructions for Authors Using LaTeX"
- **Camera-ready version**: "AAAI Press Formatting Instructions for Authors Using LaTeX --- A Guide"

#### 3. Links Environment Handling
- **Anonymous version**: Links environment commented out to prevent identity disclosure
- **Camera-ready version**: Links environment displayed normally

#### 4. Content Section Differences
- **Anonymous version**: Contains special instructions in "Preparing an Anonymous Submission" section
- **Camera-ready version**: Contains complete formatting instructions and copyright information

### Dependency Files Verification

✅ **Files verified and copied to main directory**:

- `aaai2026.sty` - AAAI 2026 style file (identical in both versions)
- `aaai2026.bst` - Bibliography style file (identical in both versions)
- `aaai2026.bib` - Sample bibliography file
- `figure1.pdf` and `figure2.pdf` - Sample image files

All these files are identical in both versions, so the unified template works properly.

### How to Use the Unified Template

#### Switch to Anonymous Submission Version
On line 11 of the template file, **uncomment** this line:
```latex
\def\aaaianonymous{true}
```

#### Switch to Camera-ready Version
On line 11 of the template file, **comment out** or **delete** this line:
```latex
% \def\aaaianonymous{true}
```

### Core Mechanism of One-Click Switching

The unified template uses LaTeX conditional compilation:

```latex
% Conditional package loading
\ifdefined\aaaianonymous
    \usepackage[submission]{aaai2026}  % Anonymous version
\else
    \usepackage{aaai2026}              % Camera-ready version
\fi

% Conditional title setting
\ifdefined\aaaianonymous
    \title{AAAI Press Anonymous Submission\\Instructions for Authors Using \LaTeX{}}
\else
    \title{AAAI Press Formatting Instructions \\for Authors Using \LaTeX{} --- A Guide}
\fi

% Conditional content display
\ifdefined\aaaianonymous
    % Anonymous version specific content
\else
    % Camera-ready version specific content
\fi
```

### File List

The main directory now contains the following files:

- `aaai2026-unified-template.tex` - Unified main paper template file
- `aaai2026-unified-supp.tex` - Unified supplementary material template file
- `aaai2026.sty` - AAAI 2026 LaTeX style file
- `aaai2026.bst` - Bibliography style file
- `aaai2026.bib` - Sample bibliography file
- `figure1.pdf` - Sample image 1
- `figure2.pdf` - Sample image 2
- `README.md` - This documentation

### Supplementary Material Template

#### Overview
`aaai2026-unified-supp.tex` is a unified template specifically designed for AAAI 2026 supplementary materials, using the same version switching mechanism as the main paper template.

#### Key Features
- **Version Switching**: Switch between anonymous submission and camera-ready versions by modifying one line of code
- **Supplementary Content Support**: Supports additional experiments, derivations, data, figures, algorithms, etc.
- **Format Consistency**: Maintains complete format consistency with the main paper template
- **Code Examples**: Includes examples for algorithms, code listings, and other supplementary materials

#### Usage
Same as the main paper template, just modify line 11:
```latex
% Anonymous submission version
\def\aaaianonymous{true}

% Camera-ready version
% \def\aaaianonymous{true}
```

#### Supplementary Material Content Suggestions
- Additional experimental results and ablation studies
- Detailed mathematical derivations and proofs
- More figures and visualizations
- Algorithm pseudocode and implementation details
- Dataset descriptions and preprocessing steps
- Hyperparameter settings and experimental configurations
- Failure case analysis
- Computational complexity analysis

### Usage Checklist

#### 📋 Pre-Submission Checklist

**Version Setup**:
- [ ] Set `\def\aaaianonymous{true}` (anonymous submission)
- [ ] Commented out all information that could reveal identity
- [ ] Anonymized references (removed author names)

**Content Completeness**:
- [ ] Title, abstract, and keywords filled
- [ ] All sections complete
- [ ] Figure and table numbers consecutive and correct
- [ ] Reference format correct
- [ ] Supplementary materials prepared (if any)

**Format Check**:
- [ ] Page margins meet requirements
- [ ] Font and font size correct
- [ ] Line spacing meets standards
- [ ] Figure and table positions and sizes appropriate
- [ ] Mathematical formula format correct

**Technical Check**:
- [ ] LaTeX compilation error-free
- [ ] References generated correctly
- [ ] PDF output normal
- [ ] File size within limits

#### 📋 Post-Acceptance Checklist

**Version Switch**:
- [ ] Commented out `\def\aaaianonymous{true}` (camera-ready)
- [ ] Added complete author information
- [ ] Added all author affiliation information
- [ ] Restored all commented content

**Content Updates**:
- [ ] Modified content according to reviewer comments
- [ ] Updated all figures and experiments
- [ ] Completed supplementary materials
- [ ] Checked all links and citations

**Final Check**:
- [ ] Final PDF quality check
- [ ] All files backed up
- [ ] Meets conference final submission requirements
- [ ] Supplementary materials submitted separately (if needed)

#### 📋 Supplementary Material Checklist

**Content Organization**:
- [ ] Supplementary materials correspond to main paper content
- [ ] Chapter structure clear and reasonable
- [ ] Figure and table numbers don't conflict with main paper
- [ ] Reference format consistent

**Technical Details**:
- [ ] Algorithm pseudocode clear and complete
- [ ] Experimental setup explained in detail
- [ ] Data preprocessing steps clear
- [ ] Hyperparameter configuration complete

**Format Requirements**:
- [ ] Using unified supp template
- [ ] Page settings consistent with main paper
- [ ] Font and format meet requirements
- [ ] File size within limits

### Practical Usage Recommendations

1. **Submission Stage**: 
   - Uncomment `\def\aaaianonymous{true}` 
   - Ensure no information that could reveal identity is included
   - Check that references are anonymized

2. **Preparing final version after acceptance**:
   - Comment out or delete the `\def\aaaianonymous{true}` line
   - Add complete author information and affiliations
   - Uncomment links environment (if needed)

3. **Compilation Testing**:
   - Compile in both modes to ensure proper functionality
   - Check if the output PDF meets requirements
   - Verify reference formatting is correct

4. **Dependency File Confirmation**:
   - Ensure all dependency files are in the same directory
   - Remember to move dependency files when moving the template file

### Important Notes

⚠️ **About Bibliography Style**:
- The `aaai2026.sty` file automatically sets `\bibliographystyle{aaai2026}`
- **Do NOT** add `\bibliographystyle{aaai2026}` command again in your document
- Otherwise you'll get "`Illegal, another \bibstyle command`" error
- Just use the `\bibliography{aaai2026}` command

### Compilation Commands Example

```bash
# Compile LaTeX document
pdflatex aaai2026-unified-template.tex
bibtex aaai2026-unified-template
pdflatex aaai2026-unified-template.tex
pdflatex aaai2026-unified-template.tex
```

### Common Issues and Solutions

#### 1. "Illegal, another \bibstyle command" Error
**Cause**: Duplicate bibliography style setting  
**Solution**: Remove the `\bibliographystyle{aaai2026}` command from your document, `aaai2026.sty` handles it automatically

#### 2. Incorrect Reference Format
**Cause**: Missing natbib package or BibTeX file issues  
**Solution**: Follow the standard LaTeX compilation process: pdflatex → bibtex → pdflatex → pdflatex

---

---

🎉 **Now you only need to modify one line of code to switch between the two versions, with all necessary dependency files ready to use!**
