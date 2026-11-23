# Generic Academic Dissertation Template for Typst

An independently maintained generic dissertation template for Typst.

**Version: v0.1.0.** A small, configurable starting point for MSc dissertations
and research reports.
The included manuscript is a synthetic typesetting example, not an empirical
study. The identities, institution, collection and table values are fictional;
the two cited publications are real.

This is an independently maintained, unofficial academic writing template.
Users are responsible for checking the current dissertation and submission
requirements of their own institution.

The `Ecs` in the repository name is a historical personal-project name. It does
not mean this is an official University of Southampton or ECS template, and the
project is not endorsed by the University or School.

## Requirements and quick start

Tested with **Typst 0.15.1**. Install the CLI from the
[official Typst downloads](https://typst.app/open-source/). There are no Universe
packages, scripts, API credentials or network services required to compile.
Run these commands from this directory:

```sh
mkdir build
typst compile --root . main.typ build/sample.pdf
typst compile --root . --input anonymous=true main.typ build/sample-anonymous.pdf
```

If `build` already exists, skip `mkdir`. On PowerShell, `New-Item -ItemType
Directory -Force build` also works. To reproduce the tested font selection and
creation time, use:

```sh
typst compile --root . --ignore-system-fonts --creation-timestamp 0 main.typ build/sample.pdf
typst compile --root . --ignore-system-fonts --creation-timestamp 0 --input anonymous=true main.typ build/sample-anonymous.pdf
```

The supplied date is an explicit string in `config.typ`; the template sets PDF
document dates to `none`. The timestamp flag also stabilises the build environment.
The reproducibility check compares two builds on one tested machine, not all
operating systems or future compiler versions. `--ignore-system-fonts` selects
the compiler's bundled fonts and prevents an installed font from overriding them.
If you choose a custom font, supply an authorised font with `--font-path` or omit
that flag and verify the resulting font selection yourself.

## Files and normal use

| File | Purpose |
| --- | --- |
| `main.typ` | Imports the template, configuration, three chapters and appendix |
| `template.typ` | One public document wrapper: `dissertation` |
| `config.typ` | Metadata, layout, abstract, optional acknowledgements and declaration |
| `chapters/` | Three independent illustrative chapter files |
| `appendix.typ` | A fictional appendix |
| `references.bib` | Two manually entered public bibliography records |
| `scripts/validate.py` | Optional local acceptance checks |
| `THIRD_PARTY.md` | Compiler, fonts, bibliography and test-tool provenance |
| `release-files.txt` | Explicit allowlist of reviewed source files |
| `build/` | Ignored local PDFs, rendering and validation results |

Edit `config.typ` and the chapter files for ordinary use. Add a chapter by creating
a `.typ` file under `chapters/` and adding an `#include` in `main.typ`. Use `=` for
chapter headings, `==` for sections and `===` for subsections. Do not put a
document wrapper or another `#show: dissertation...` inside a chapter.

The template provides title and abstract pages, optional acknowledgements and
declaration, contents, optional figure/table lists, numbered headings and
equations, figures, tables, cross-references, references and appendices.

## Template design and a minimal document

The design follows Typst's official
[Making a Template tutorial](https://typst.app/docs/tutorial/making-a-template/):
`template.typ` exports a document wrapper, its last positional argument receives
the body, and an everything show rule applies it to the rest of the manuscript.
`.with(...)` supplies named arguments without an extra closure. The wrapper's
local `set` and `show` rules style its content; `config.typ` keeps repeated values
in one place. The configuration dictionary groups related settings, while
abstract and optional front matter remain separate content arguments.

A minimal document, saved alongside `template.typ`, is:

```typst
#import "template.typ": dissertation

#show: dissertation.with(
  config: (title: "An Illustrative Report", author: "Example Author"),
  abstract: [A short, fictional example.],
)

= Introduction
Write your own content here.
```

For a full dissertation, start from `main.typ` and edit `config.typ` and the
chapter files. The template sets PDF metadata from the same configuration used
on the cover, so title and author values do not need to be entered twice.
This is a local reusable template; a Typst Universe package manifest is not
required to use it.

## Configuration

The `config` dictionary rejects unknown keys. The only required metadata is a
nonempty `title` and, outside anonymous mode, a nonempty `author`. Optional text
fields default to empty strings. Additional native Typst validation applies to
paper names and layout values.

| Key | Default | Meaning |
| --- | --- | --- |
| `title`, `author` | `""` | Document title and normal-mode author |
| `email` | `""` | Normal-mode cover email and `mailto:` link |
| `institution`, `programme`, `supervisor` | `""` | Optional normal-mode cover fields |
| `submission-date` | `""` | Explicit cover date; no automatic current date |
| `keywords` | `()` | Array of strings for normal-mode PDF metadata |
| `anonymous` | `false` | Suppress template-controlled identity output |
| `paper` | `"a4"` | A native Typst paper name, e.g. `"a5"` |
| `margins` | `(x: 25mm, y: 25mm)` | Absolute nonnegative length or native margin dictionary of such lengths |
| `font`, `font-size` | `"Libertinus Serif"`, `11pt` | Body family and positive absolute size |
| `leading` | `0.7em` | Extra space between line boxes, not a Word line-spacing multiplier |
| `paragraph-spacing` | `0.8em` | Space between paragraphs |
| `contents`, `contents-depth` | `true`, `3` | Heading contents and maximum depth (1–6) |
| `list-of-figures`, `list-of-tables` | `true`, `true` | Generate only when matching outlined elements exist |
| `bibliography-file` | `none` | Relative path, resolved from `template.typ`; sample uses `"references.bib"` |
| `citation-style` | `"ieee"` | Built-in Typst bibliography style |

`abstract`, `acknowledgements`, `declaration` and `appendices` are content
arguments to `dissertation`, not dictionary keys. In the sample, the first three
are defined in `config.typ` and the appendix is included by `main.typ`. Set an
optional section to `none` or `[]` to omit it without an empty page. No prescribed
institutional declaration is supplied. Use your programme's current wording only
when you have the right to use it and it accurately describes your work.

## Page numbering and layout policy

The cover has no printed number or PDF page label. It is physically the first
page, but it is excluded from the following logical numbering. Front matter
starts at visible roman **i** (normally the abstract); the body restarts at visible
Arabic **1**, including the first chapter's first page. References and appendices
continue the Arabic sequence. Appendix headings restart at **A**, **A.1**, etc.
Equations and each kind of figure/table keep their own global numbering.

Each chapter, nonempty front section, generated list, bibliography and appendix
begins on a new page. A page can therefore contain only a short example section.
Empty lists and empty optional sections are omitted. No running header is used;
page numbers are centered in the footer. This is a generic design choice, not an
institutional rule. The template is intended for ordinary portrait documents;
landscape inserts and specialised two-sided binding layouts require additional
layout work and validation.

## Figures, tables, equations and citations

The sample uses native `grid`, `block` and `table` elements rather than image
assets. The original diagram is explicitly `kind: image` so it appears in the
figure list; it includes `alt` text. Captioned tables use a separate counting
track and `table.header` for repeated header cells. Table figures are breakable
across pages. The acceptance fixture checks 130 rows over four pages.

Add a label after an element, such as `<scores>`, and reference it using `@scores`.
Use numbered display mathematics for equation references. Table captions appear
above tables; other figure captions appear below the figure.

Add only the records you need to `references.bib`, then cite their keys using
`@manning2008`, for example. Do not export local attachment paths, private notes
or a full research library. Change `citation-style` in `config.typ` to a supported
built-in style. IEEE is a sample choice, not a requirement for any university.
Set `bibliography-file: none` only when the manuscript has no bibliography
citations. Public facts about the two records were verified with the
[publisher](https://www.cambridge.org/highereducation/books/introduction-to-information-retrieval/669D108D20F556C5C30957D63B5AB65C)
and [Microsoft Research](https://www.microsoft.com/en-us/research/publication/okapi-at-trec-3/).
No publication text, illustration or bibliography export is bundled.

## Anonymous mode and its limits

The sample reads `--input anonymous=true` in `config.typ`. Any value other than
`true` or `false` is rejected. Library callers can set the boolean directly.
Anonymous mode emits an anonymous author on the cover and removes the template's
author, email link, institution, programme, supervisor, acknowledgements,
declaration, PDF author and PDF keywords. These values are omitted from the
output content, not painted over or hidden. Tests inspect extracted text, parsed
PDF objects and decoded streams using eight distinct synthetic identity markers.

**It does not anonymise arbitrary manuscript content.** The title, date, abstract,
chapters, references, figures, external images, appendix and filenames are kept.
Remove self-identifying prose, self-citations, identifying titles, asset metadata
and private links yourself. The source files still contain your configuration;
never distribute them as an anonymous submission. Do not treat this feature as a
guarantee of blind review anonymity.

## Validation and accessibility

PDF compilation requires only Typst. Optional local checks use Python 3.10+ and
`pypdf==7.1.1`; this run used Python 3.14.2. In a separate virtual environment:

```sh
python -m pip install -r scripts/requirements.txt
python scripts/validate.py
```

The script requires the recorded Typst 0.15.1 baseline, generates files only in
`build/validation/`, and makes no network requests. It checks normal and anonymous
builds, byte reproducibility, PDF metadata and identity markers, embedded fonts,
link targets and linked contents page labels, empty sections, invalid
configurations, a different page/font configuration, a multi-page contents list,
long title/body text, a 130-row table and an appendix. Results are recorded in
`build/validation/results.json`. Render pages with `typst compile --format png`
for manual visual review after changing layout.

The sample has a tagged PDF structure, a diagram alternative description,
semantic table headers, selectable text, linked contents and embedded fonts.
Reading order was inspected structurally and visually, but no screen-reader
acceptance or independent standards validator was run. **No PDF/A, PDF/UA or
accessibility certification is claimed.** Mathematics may require additional
natural-language descriptions for an accessible submission. Check your own
content, language, colour contrast, tables and final output.

## Institution-specific requirements

Default dimensions, fonts, spacing and section order are generic design choices.
This project provides no official ECS preset. The public
[ECSP6003 2026–27 module overview](https://www.southampton.ac.uk/courses/2026-27/modules/ecsp6003)
does not provide a complete formatting specification. The
[2010 ECS writing guide record](https://edshare.soton.ac.uk/5940/) is historical
teaching guidance, not a current MSc compliance certificate. Southampton's
[research thesis guidance](https://www.southampton.ac.uk/~assets/doc/quality-handbook/Producing%20and%20submitting%20your%20thesis%20-%20student%20guidance.pdf)
explicitly concerns Doctoral/MPhil degrees; it is not automatically applicable to
a taught MSc. These sources were checked on 23 November 2026. No separate
school-specific notes file is needed until current applicable requirements are
verified.

## Licence and maintenance

The newly written template, example prose/diagram/data and helper code are under
the MIT licence in `LICENSE`. Keep that notice with redistributed copies. No
third-party template source, school logo, private declaration, research asset,
font file or original project history is included. Compiler fonts, optional test
tools and the publications have their own provenance; see `THIRD_PARTY.md`.

The maintainable baseline is deliberately small. Recheck references, licences,
privacy and rendered output when upgrading Typst, changing fonts or adding
packages. There is no automatic CI, publication or deployment workflow. The
source allowlist is `release-files.txt`; generated PDFs, local build output and
private audit records are excluded from the source repository. Version v0.1.0
uses the documented local acceptance checks; CI remains a possible later addition.
