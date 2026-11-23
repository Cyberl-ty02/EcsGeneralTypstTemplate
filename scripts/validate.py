"""Local acceptance checks. Requires Typst 0.15.1 and pypdf 7.1.1.

Run from any directory: python scripts/validate.py
Only build/validation is generated. No network or original research is accessed.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import pypdf
from pypdf import PdfReader
from pypdf.generic import IndirectObject, StreamObject

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build" / "validation"
TIMESTAMP = "0"


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def compile_pdf(source, destination, *, inputs=(), failure=None):
    command = ["typst", "compile", "--root", str(ROOT), "--ignore-system-fonts",
               "--creation-timestamp", TIMESTAMP, "--diagnostic-format", "short"]
    for item in inputs:
        command += ["--input", item]
    result = subprocess.run(command + [str(source), str(destination)],
                            capture_output=True, text=True, encoding="utf-8")
    if failure is not None:
        check(result.returncode != 0 and failure in result.stderr,
              f"Expected diagnostic {failure!r}: {result.stderr}")
        return
    check(result.returncode == 0, result.stderr)
    check(not result.stderr.strip(), f"Unexpected compiler diagnostic: {result.stderr}")


def fixture(name, content):
    path = OUT / (name + ".typ")
    path.write_text('#import "../../template.typ": dissertation\n' + content,
                    encoding="utf-8")
    return path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decoded_objects(reader):
    """Inspect reachable and unreferenced parsed objects and decoded streams."""
    for generation, entries in reader.xref.items():
        for number in entries:
            if number == 0:
                continue
            obj = reader.get_object(IndirectObject(number, generation, reader))
            yield str(obj)
            if isinstance(obj, StreamObject):
                yield obj.get_data().decode("latin-1", errors="replace")
    for number in reader.xref_objStm:
        yield str(reader.get_object(IndirectObject(number, 0, reader)))


def all_text(reader):
    return "\n".join(page.extract_text() for page in reader.pages).replace("\u00a0", " ")


def page_with(reader, starts):
    found = [(i, p.extract_text().replace("\u00a0", " ")) for i, p in enumerate(reader.pages)
             if p.extract_text().replace("\u00a0", " ").startswith(starts)]
    check(len(found) == 1, f"Expected exactly one page starting {starts!r}")
    return found[0]


def embedded_fonts(reader):
    fonts = {}
    for page in reader.pages:
        for font_ref in page["/Resources"].get("/Font", {}).values():
            font = font_ref.get_object()
            entries = font.get("/DescendantFonts", [font])
            for entry in entries:
                entry = entry.get_object()
                name = str(entry.get("/BaseFont", "unknown"))
                descriptor = entry.get("/FontDescriptor")
                embedded = descriptor is not None and any(
                    key in descriptor.get_object() for key in ("/FontFile", "/FontFile2", "/FontFile3"))
                fonts[name] = bool(embedded)
    check(fonts and all(fonts.values()), "A PDF font is not embedded")
    return fonts


def linked_pages(reader):
    page_ids = {p.indirect_reference.idnum: i for i, p in enumerate(reader.pages)}
    internal = 0
    checked_labels = 0
    for page in reader.pages:
        for ref in page.get("/Annots", []):
            annotation = ref.get_object()
            destination = annotation.get("/Dest")
            if destination is None:
                continue
            if isinstance(destination, str):
                check(destination in reader.named_destinations, "Unresolved named PDF link")
                target = reader.get_destination_page_number(reader.named_destinations[destination])
            else:
                check(destination[0].idnum in page_ids, "PDF link targets a missing page")
                target = page_ids[destination[0].idnum]
            internal += 1
            hint = str(annotation.get("/Contents", ""))
            match = re.search(r"page\s+([0-9ivxlcdm]+)$", hint)
            if match:
                check(match.group(1) == reader.page_labels[target], "Contents/list page number disagrees with link")
                checked_labels += 1
    return {"internal_links": internal, "labels_checked": checked_labels}


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    version = subprocess.check_output(["typst", "--version"], text=True).strip()
    check(version.startswith("typst 0.15.1 "), "This acceptance baseline requires Typst 0.15.1")
    records = {"typst": version, "python": sys.version.split()[0], "pypdf": pypdf.__version__,
               "creation_timestamp": TIMESTAMP, "system_fonts": False, "checks": {}}

    for mode in ("normal", "anonymous"):
        inputs = ("anonymous=true",) if mode == "anonymous" else ()
        a, b = (OUT / f"{mode}-{i}.pdf" for i in (1, 2))
        compile_pdf(ROOT / "main.typ", a, inputs=inputs)
        compile_pdf(ROOT / "main.typ", b, inputs=inputs)
        check(digest(a) == digest(b), mode + " repeat PDF hashes differ")
        reader = PdfReader(a)
        text = all_text(reader)
        check(reader.trailer["/Root"].get("/StructTreeRoot") is not None, "Missing structure tree")
        check(not reader.attachments, "Unexpected attached file")
        check(not reader.is_encrypted, "Unexpected encryption")
        check(reader.page_labels[0] == "", "Cover must not have a logical page label")
        for phrase in ("Introduction", "Methodology", "Conclusion", "References",
                       "Supplementary Synthetic Material", "Manning", "Robertson", "Table 1", "Figure 1"):
            check(phrase in text, "Missing sample content: " + phrase)
        check("Equation\u00a01" in text or "Equation 1" in text, "Missing equation reference")
        _, abstract = page_with(reader, "Abstract")
        check(abstract.rstrip().endswith("\ni"), "Abstract must show roman i")
        body_index, body = page_with(reader, "1 Introduction")
        check(body.rstrip().endswith("\n1"), "First body page must visibly show 1")
        appendix_index, appendix = page_with(reader, "A Supplementary")
        check(appendix.rstrip().endswith("\n" + str(appendix_index - body_index + 1)),
              "Appendix page counter must continue from body")
        check(not re.search(r"\n(?:i|1)\s*$", reader.pages[0].extract_text()), "Cover has a visible number")
        for index, page in enumerate(reader.pages[1:], 1):
            check(len(page.extract_text().strip()) > 5, f"Unexpected empty sample page {index + 1}")
        metadata = dict(reader.metadata or {})
        if mode == "normal":
            check(metadata.get("/Author") == "Alex Example", "Missing normal author metadata")
            check("Acknowledgements" in text, "Normal acknowledgements missing")
        else:
            blob = "\n".join(decoded_objects(reader)) + text
            for token in ("Alex Example", "author@example.invalid", "Example Institute",
                          "Dr Morgan Example", "Example Acknowledgement Team", "mailto:"):
                check(token not in blob, "Anonymous sample identity remains: " + token)
            check(not metadata.get("/Author") and not metadata.get("/Keywords"), "Anonymous metadata remains")
            check("Acknowledgements" not in text, "Anonymous acknowledgements remain")
        records["checks"][mode] = {"pages": len(reader.pages), "sha256": digest(a),
                                    "repeat_identical": True, "metadata": metadata,
                                    "embedded_fonts": embedded_fonts(reader),
                                    "pdf_links": linked_pages(reader)}

    # Isolate identity suppression from friendly sample values, including XMP/URI objects.
    tokens = ["IDENTITY_AUTHOR_9F72", "identity9f72@example.invalid", "IDENTITY_INSTITUTE_9F72",
              "IDENTITY_PROGRAMME_9F72", "IDENTITY_SUPERVISOR_9F72", "IDENTITY_KEYWORD_9F72",
              "IDENTITY_ACK_9F72", "IDENTITY_DECLARATION_9F72"]
    canary = fixture("identity", '''
#show: dissertation.with(
  config: (title: "Identity suppression fixture", author: "IDENTITY_AUTHOR_9F72",
    email: "identity9f72@example.invalid", institution: "IDENTITY_INSTITUTE_9F72",
    programme: "IDENTITY_PROGRAMME_9F72", supervisor: "IDENTITY_SUPERVISOR_9F72",
    keywords: ("IDENTITY_KEYWORD_9F72",),
    anonymous: sys.inputs.at("anonymous", default: "false") == "true"),
  acknowledgements: [IDENTITY_ACK_9F72], declaration: [IDENTITY_DECLARATION_9F72],
)
= Public Body
Only public fixture content.
''')
    for anonymous in (False, True):
        path = OUT / ("identity-anonymous.pdf" if anonymous else "identity-normal.pdf")
        compile_pdf(canary, path, inputs=("anonymous=true",) if anonymous else ())
        reader = PdfReader(path)
        text = all_text(reader)
        blob = text + "\n" + "\n".join(decoded_objects(reader))
        for token in tokens:
            check((token not in blob) if anonymous else (token in blob),
                  f"Identity fixture failed for {token}, anonymous={anonymous}")
    records["checks"]["identity_canaries"] = "all 8 present normally and absent anonymously"

    empty = fixture("empty", '''
#show: dissertation.with(config: (title: "Minimal document", author: "Example"),
  acknowledgements: [], declaration: [], appendices: [])
Body without headings, figures, tables or optional sections.
''')
    compile_pdf(empty, OUT / "empty.pdf")
    empty_reader = PdfReader(OUT / "empty.pdf")
    check(len(empty_reader.pages) == 2, "Empty optional sections generated pages")
    empty_text = all_text(empty_reader)
    check(all(s not in empty_text for s in ("Contents", "List of", "Acknowledgements", "Declaration")),
          "Empty optional section remains")
    records["checks"]["empty_sections"] = "2 pages: cover and body only"

    valid_minimal = '(title: "Fixture", author: "Example")'
    invalid = [
        ("missing-title", '(author: "Example",)', "title is required"),
        ("missing-author", '(title: "Fixture",)', "author is required"),
        ("unknown-key", valid_minimal[:-1] + ', anonymous-typo: true)', "Unknown configuration key"),
        ("wrong-bool", valid_minimal[:-1] + ', anonymous: "true")', "anonymous must be a boolean"),
        ("negative-size", valid_minimal[:-1] + ', font-size: -1pt)', "positive absolute length"),
        ("bad-depth", valid_minimal[:-1] + ', contents-depth: 0)', "integer from 1 to 6"),
        ("bad-keywords", valid_minimal[:-1] + ', keywords: "word")', "array of strings"),
        ("invalid-paper", valid_minimal[:-1] + ', paper: "not-a-paper")', "paper"),
        ("invalid-margins", valid_minimal[:-1] + ', margins: "wide")', "non-negative absolute lengths"),
        ("negative-margins", valid_minimal[:-1] + ', margins: -2mm)', "non-negative absolute lengths"),
    ]
    for name, config, diagnostic in invalid:
        source = fixture(name, f'#show: dissertation.with(config: {config})\nBody.')
        compile_pdf(source, OUT / (name + ".pdf"), failure=diagnostic)
    compile_pdf(ROOT / "main.typ", OUT / "invalid-cli.pdf", inputs=("anonymous=maybe",),
                failure="anonymous input must be true or false")
    missing = fixture("anonymous-without-author", '#show: dissertation.with(config: (title: "Anonymous", anonymous: true))\nBody.')
    compile_pdf(missing, OUT / "anonymous-without-author.pdf")
    records["checks"]["configuration"] = "11 invalid configurations rejected; anonymous without author accepted"

    stress = fixture("stress", '''
#show: dissertation.with(
  config: (title: "A Deliberately Long Synthetic Title for Inspecting Line Wrapping, Cover Layout and Readable Academic Typography Across Multiple Lines Without Institution-Specific Branding",
    author: "Layout Example", contents-depth: 2),
  abstract: [Synthetic stress fixture.],
  acknowledgements: [],
  appendices: [
    = Stress Appendix
    Appendix marker: APPENDIX_END_724.
  ],
)
= Extended Layout Exercise
#for n in range(1, 76) [
  #heading(level: 2)[Synthetic subsection #n with a descriptive title for a multi-page contents list]
  This paragraph is invented layout filler. It carries no research information.
  It exists to check running text, heading wrapping and contents pagination.
  #parbreak()
]
= A Long Table with Repeated Column Headings and a Caption Explaining That Every Row Is Synthetic
#figure(
  table(columns: (1fr, 2fr),
    table.header([*Synthetic row*], [*Illustrative value*]),
    ..range(1, 131).map(n => ([Row #n], [Invented value #n])).flatten(),
  ),
  caption: [A deliberately long original caption for a synthetic table, used to verify that the caption and the first rows remain readable and that the table can continue across multiple pages with repeated header cells.],
)
= Extended Prose
#for n in range(1, 13) [
  Synthetic paragraph #n. #lorem(100)
  #parbreak()
]
''')
    compile_pdf(stress, OUT / "stress.pdf")
    reader = PdfReader(OUT / "stress.pdf")
    texts = [p.extract_text() for p in reader.pages]
    text = "\n".join(texts)
    contents_index, _ = page_with(reader, "Contents")
    body_index, first_body = page_with(reader, "1 Extended Layout Exercise")
    check(body_index - contents_index >= 2, "Contents is not multi-page")
    check(first_body.rstrip().endswith("\n1"), "Stress body first page must show 1")
    for n in range(1, 131):
        check(re.search(rf"Row\s+{n}\b", text), f"Long table lost row {n}")
    header_pages = sum("Synthetic row" in t and "Illustrative value" in t for t in texts)
    check(header_pages >= 2, "Long table headers were not repeated")
    check("APPENDIX_END_724" in text and "Synthetic paragraph 12" in text, "Stress ending missing")
    check(all(len(t.strip()) > 5 for t in texts), "Unexpected blank stress page")
    records["checks"]["stress"] = {"pages": len(reader.pages),
                                     "contents_pages": body_index - contents_index - 1,
                                     "repeated_table_header_pages": header_pages,
                                     "rows_present": 130, "pdf_links": linked_pages(reader)}
    # Library use with a non-default paper, margins and font.
    alternate = fixture("alternate", '''
#show: dissertation.with(config: (title: "Alternate layout", author: "Example",
  paper: "a5", margins: 18mm, font: "New Computer Modern", font-size: 10pt,
  leading: 0.6em, paragraph-spacing: 0.5em, contents: false))
= Alternate body
An alternate layout with a visible first page number.
''')
    compile_pdf(alternate, OUT / "alternate.pdf")
    alternate_reader = PdfReader(OUT / "alternate.pdf")
    check(abs(float(alternate_reader.pages[0].mediabox.width) - 419.53) < 1, "Alternate paper ignored")
    embedded_fonts(alternate_reader)
    records["checks"]["alternate_layout"] = "A5, 18mm margins, New Computer Modern, 10pt compiled"

    (OUT / "results.json").write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(records, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    run()
