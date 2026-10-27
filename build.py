#!/usr/bin/env python3
"""Generate the bitcoin-data dataset index as a static site.

Reads categories.toml and every datasets/*.toml, validates them, and writes
the site to site/. Uses only the Python standard library (3.11+ for tomllib).

    python3 build.py          # validate and build into site/
    python3 build.py --check  # validate only
    python3 build.py --tags   # validate and list existing tags with counts
"""

import html
import json
import re
import shutil
import sys
import tomllib
from pathlib import Path
from string import Template

ROOT = Path(__file__).resolve().parent
DATASETS_DIR = ROOT / "datasets"
TEMPLATES_DIR = ROOT / "templates"
STATIC_DIR = ROOT / "static"
OUT_DIR = ROOT / "site"

SITE_NAME = "bitcoin-data"
SITE_TAGLINE = "Collection of public Bitcoin related datasets."
ORG_URL = "https://github.com/bitcoin-data"
SOURCE_URL = "https://github.com/bitcoin-data/bitcoin-data.github.io"

# Link types, in the order they are rendered, with their default labels.
LINK_TYPES = {
    "repository": "Repository",
    "website": "Website",
    "download": "Download",
    "documentation": "Documentation",
    "paper": "Paper",
    "other": "Link",
}

SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$")


class EntryError(Exception):
    pass


def load_toml(path):
    with path.open("rb") as f:
        return tomllib.load(f)


def load_categories():
    data = load_toml(ROOT / "categories.toml")
    categories = []
    for cat in data.get("categories", []):
        for key in ("id", "name", "description"):
            if not isinstance(cat.get(key), str) or not cat[key].strip():
                raise EntryError(f"categories.toml: category missing '{key}'")
        if not SLUG_RE.match(cat["id"]):
            raise EntryError(f"categories.toml: bad category id {cat['id']!r}")
        categories.append(cat)
    if not categories:
        raise EntryError("categories.toml: no categories defined")
    return categories


def require_str(entry, key, where, optional=False):
    value = entry.get(key)
    if value is None:
        if optional:
            return None
        raise EntryError(f"{where}: missing required field '{key}'")
    if not isinstance(value, str) or not value.strip():
        raise EntryError(f"{where}: '{key}' must be a non-empty string")
    return value.strip()


def load_dataset(path, category_ids):
    where = path.relative_to(ROOT)
    slug = path.stem
    if not SLUG_RE.match(slug):
        raise EntryError(f"{where}: filename must be lowercase kebab-case")
    entry = load_toml(path)

    known = {"name", "category", "tags", "description", "links", "license", "doi", "author"}
    unknown = set(entry) - known
    if unknown:
        raise EntryError(f"{where}: unknown field(s): {', '.join(sorted(unknown))}")

    dataset = {
        "slug": slug,
        "name": require_str(entry, "name", where),
        "category": require_str(entry, "category", where),
        "description": require_str(entry, "description", where),
        "license": require_str(entry, "license", where),
        "author": require_str(entry, "author", where, optional=True),
        "doi": require_str(entry, "doi", where, optional=True),
    }
    if dataset["category"] not in category_ids:
        raise EntryError(
            f"{where}: unknown category {dataset['category']!r}, "
            f"expected one of: {', '.join(category_ids)}"
        )
    if dataset["doi"] and not DOI_RE.match(dataset["doi"]):
        raise EntryError(f"{where}: 'doi' must be a bare DOI like 10.5281/zenodo.123456")

    tags = entry.get("tags", [])
    if not isinstance(tags, list) or not all(isinstance(t, str) for t in tags):
        raise EntryError(f"{where}: 'tags' must be a list of strings")
    for tag in tags:
        if not SLUG_RE.match(tag):
            raise EntryError(f"{where}: tag {tag!r} must be lowercase kebab-case")
    if len(set(tags)) != len(tags):
        raise EntryError(f"{where}: duplicate tags")
    dataset["tags"] = sorted(tags)

    links = entry.get("links")
    if not isinstance(links, list) or not links:
        raise EntryError(f"{where}: 'links' must contain at least one [[links]] entry")
    dataset["links"] = []
    for i, link in enumerate(links):
        lwhere = f"{where}: links[{i}]"
        if not isinstance(link, dict):
            raise EntryError(f"{lwhere}: must be a table")
        ltype = require_str(link, "type", lwhere)
        if ltype not in LINK_TYPES:
            raise EntryError(
                f"{lwhere}: unknown type {ltype!r}, expected one of: {', '.join(LINK_TYPES)}"
            )
        url = require_str(link, "url", lwhere)
        if not url.startswith(("https://", "http://")):
            raise EntryError(f"{lwhere}: url must start with http:// or https://")
        label = require_str(link, "label", lwhere, optional=True) or LINK_TYPES[ltype]
        dataset["links"].append({"type": ltype, "url": url, "label": label})
    order = list(LINK_TYPES)
    dataset["links"].sort(key=lambda l: order.index(l["type"]))
    return dataset


def load_datasets(categories):
    category_ids = [c["id"] for c in categories]
    paths = sorted(DATASETS_DIR.glob("*.toml"))
    if not paths:
        raise EntryError("datasets/: no dataset entries found")
    datasets = [load_dataset(p, category_ids) for p in paths]
    datasets.sort(key=lambda d: d["name"].lower())
    return datasets


# --- rendering ---------------------------------------------------------------

e = html.escape


def paragraphs(text):
    parts = [" ".join(p.split()) for p in re.split(r"\n\s*\n", text.strip())]
    return "".join(f"<p>{e(p)}</p>\n" for p in parts if p)


def first_sentence(text):
    text = " ".join(text.split())
    m = re.match(r"(.+?[.!?])(\s|$)", text)
    return m.group(1) if m else text


def render_tags(tags, root):
    if not tags:
        return ""
    items = "".join(
        f'<li><a class="tag" href="{root}tags/{e(t)}/">{e(t)}</a></li>' for t in tags
    )
    return f'<ul class="tags">{items}</ul>'


def render_links(links):
    items = "".join(
        f'<li><a href="{e(l["url"])}" rel="noopener">{e(l["label"])}</a></li>' for l in links
    )
    return f'<ul class="links">{items}</ul>'


def render_dataset_card(d, categories_by_id, root):
    meta = [
        f'<li><span class="label">Category:</span> {e(categories_by_id[d["category"]]["name"])}</li>',
        f'<li><span class="label">License:</span> {e(d["license"])}</li>',
    ]
    if d["author"]:
        meta.append(f'<li><span class="label">Author:</span> {e(d["author"])}</li>')
    if d["doi"]:
        meta.append(
            f'<li><span class="label">DOI:</span> '
            f'<a href="https://doi.org/{e(d["doi"])}">{e(d["doi"])}</a></li>'
        )
    if d["tags"]:
        meta.append(f'<li><span class="label">Tags:</span> {render_tags(d["tags"], root)}</li>')
    return (
        f'<article class="dataset" id="{e(d["slug"])}">\n'
        f'<h3><a href="{root}datasets/{e(d["slug"])}/">{e(d["name"])}</a></h3>\n'
        f'{paragraphs(d["description"])}'
        f'<ul class="meta">{"".join(meta)}</ul>\n'
        f'{render_links(d["links"])}\n'
        f"</article>\n"
    )


def render_index(datasets, categories, categories_by_id):
    root = "./"
    out = [f"<h1>{e(SITE_NAME)}</h1>", f'<p class="lead">{e(SITE_TAGLINE)}</p>']
    for cat in categories:
        members = [d for d in datasets if d["category"] == cat["id"]]
        if not members:
            continue
        out.append(f'<section id="{e(cat["id"])}">')
        out.append(f'<h2>{e(cat["name"])}</h2>')
        out.append(f'<p class="category-description">{e(cat["description"])}</p>')
        out.extend(render_dataset_card(d, categories_by_id, root) for d in members)
        out.append("</section>")
    return "\n".join(out)


def render_dataset_page(d, categories_by_id):
    root = "../../"
    cat = categories_by_id[d["category"]]
    rows = [
        ("Category", f'<a href="{root}#{e(cat["id"])}">{e(cat["name"])}</a>'),
        ("License", e(d["license"])),
    ]
    if d["author"]:
        rows.append(("Author", e(d["author"])))
    if d["doi"]:
        rows.append(("DOI", f'<a href="https://doi.org/{e(d["doi"])}">{e(d["doi"])}</a>'))
    if d["tags"]:
        rows.append(("Tags", render_tags(d["tags"], root)))
    rows.append(("Links", render_links(d["links"])))
    details = "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in rows)
    return (
        f'<h1>{e(d["name"])}</h1>\n'
        f'{paragraphs(d["description"])}'
        f'<dl class="details">{details}</dl>\n'
    )


def render_tags_index(tag_counts):
    items = "".join(
        f'<li><a class="tag" href="./{e(t)}/">{e(t)}</a> '
        f'<span class="count">{n} dataset{"s" if n != 1 else ""}</span></li>'
        for t, n in sorted(tag_counts.items())
    )
    return f"<h1>Tags</h1>\n<ul class=\"tag-list\">{items}</ul>\n"


def render_tag_page(tag, datasets, categories_by_id):
    root = "../../"
    cards = "".join(render_dataset_card(d, categories_by_id, root) for d in datasets)
    n = len(datasets)
    return (
        f"<h1>Tag: {e(tag)}</h1>\n"
        f'<p class="lead">{n} dataset{"s" if n != 1 else ""}</p>\n{cards}'
    )


def write_page(path, template, *, title, content, root, description=SITE_TAGLINE):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        template.substitute(
            title=e(title),
            meta_description=e(description),
            content=content,
            root=root,
            site_name=e(SITE_NAME),
            org_url=e(ORG_URL),
            source_url=e(SOURCE_URL),
        ),
        encoding="utf-8",
    )


def build(datasets, categories):
    categories_by_id = {c["id"]: c for c in categories}
    template = Template((TEMPLATES_DIR / "base.html").read_text(encoding="utf-8"))

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir()
    for static in STATIC_DIR.iterdir():
        shutil.copy(static, OUT_DIR / static.name)

    write_page(
        OUT_DIR / "index.html",
        template,
        title=f"{SITE_NAME}: Bitcoin datasets",
        content=render_index(datasets, categories, categories_by_id),
        root="./",
    )

    for d in datasets:
        write_page(
            OUT_DIR / "datasets" / d["slug"] / "index.html",
            template,
            title=f"{d['name']} | {SITE_NAME}",
            content=render_dataset_page(d, categories_by_id),
            root="../../",
            description=first_sentence(d["description"]),
        )

    tag_counts = {}
    for d in datasets:
        for t in d["tags"]:
            tag_counts[t] = tag_counts.get(t, 0) + 1
    write_page(
        OUT_DIR / "tags" / "index.html",
        template,
        title=f"Tags | {SITE_NAME}",
        content=render_tags_index(tag_counts),
        root="../",
    )
    for tag in tag_counts:
        tagged = [d for d in datasets if tag in d["tags"]]
        write_page(
            OUT_DIR / "tags" / tag / "index.html",
            template,
            title=f"Tag: {tag} | {SITE_NAME}",
            content=render_tag_page(tag, tagged, categories_by_id),
            root="../../",
            description=f"Bitcoin datasets tagged {tag}.",
        )

    # Machine-readable copy of all entries.
    (OUT_DIR / "datasets.json").write_text(
        json.dumps({"categories": categories, "datasets": datasets}, indent=2) + "\n",
        encoding="utf-8",
    )
    (OUT_DIR / ".nojekyll").touch()


def main(argv):
    try:
        categories = load_categories()
        datasets = load_datasets(categories)
    except EntryError as err:
        print(f"error: {err}", file=sys.stderr)
        return 1
    if "--tags" in argv:
        counts = {}
        for d in datasets:
            for t in d["tags"]:
                counts[t] = counts.get(t, 0) + 1
        for t, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
            print(f"{n:3d}  {t}")
        return 0
    print(f"ok: {len(datasets)} dataset(s), {len(categories)} categories")
    if "--check" in argv:
        return 0
    build(datasets, categories)
    print(f"built site/ ({sum(1 for _ in OUT_DIR.rglob('*.html'))} pages)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
