# bitcoin-data.github.io

Index of public Bitcoin related datasets, published at
[bitcoin-data.github.io](https://bitcoin-data.github.io/).

The site is generated from one TOML file per dataset in [`datasets/`](./datasets)
by [`build.py`](./build.py), which only needs Python 3.11 or newer.
Datasets do not have to live in the bitcoin-data organisation; external
datasets are welcome.

## Adding a dataset

If you use a coding agent, point it at this repository and ask it to add the
dataset; [`AGENTS.md`](./AGENTS.md) contains step-by-step instructions it will
follow. By hand:

1. Copy an existing file in `datasets/`, for example
   [`datasets/stale-blocks.toml`](./datasets/stale-blocks.toml), to
   `datasets/<slug>.toml`. The slug is lowercase kebab-case and becomes the
   dataset's URL, `/datasets/<slug>/`.
2. Fill in the fields described below.
3. Run `python3 build.py --check` (or just open a pull request, CI runs it).

### Fields

| Field         | Required | Description |
| ------------- | -------- | ----------- |
| `name`        | yes      | Display name of the dataset. |
| `category`    | yes      | One of the ids in [`categories.toml`](./categories.toml). |
| `tags`        | no       | List of lowercase kebab-case tags, e.g. `["blocks", "mainnet"]`. Reuse existing tags where possible, see the [tags page](https://bitcoin-data.github.io/tags/). |
| `format`      | yes      | List of data formats: `csv`, `json`, `jsonl`, `parquet`, `sqlite`, `text`, `binary`. |
| `description` | yes      | Three short sentences, see below. |
| `links`       | yes      | One or more `[[links]]` tables with `type`, `url` and an optional `label`. Types: `repository`, `website`, `download`, `documentation`, `paper`, `other`. |
| `license`     | yes      | Free text, e.g. `CC0 1.0` or `CC0 1.0 (data), MIT (code)`. |
| `author`      | no       | Person, group or project that publishes the dataset. |
| `doi`         | no       | Bare DOI like `10.5281/zenodo.22667157`, rendered as a doi.org link. |

### Writing the description

Three short sentences, about 50 to 70 words in total. Each answers one
question:

1. **What is in it?** What one record represents and the file format.
2. **Where does it come from?** How the data is collected and by whom.
3. **What is it for, and what is the catch?** A typical use, then the main
   caveat.

Descriptions are timeless: no dates, counts, sizes, version numbers, update
frequencies or status words such as "currently" or "since". Those change, and
nobody updates them. Describe what the dataset is, not how big it is today.

### Example

```toml
name = "Stale blocks"
category = "blocks"
tags = ["blocks", "headers", "forks", "mainnet"]
format = ["csv", "binary"]
author = "0xB10C and contributors"
license = "CC0 1.0 (data), MIT (code)"
doi = "10.5281/zenodo.22667157"
description = """
One row per stale block observed on the Bitcoin mainnet ...
"""

[[links]]
type = "repository"
url = "https://github.com/bitcoin-data/stale-blocks"

[[links]]
type = "download"
label = "stale-blocks.csv"
url = "https://raw.githubusercontent.com/bitcoin-data/stale-blocks/master/stale-blocks.csv"
```

## Building locally

```sh
python3 build.py            # writes the site to site/
python3 build.py --check    # only validates the entries
python3 build.py --tags     # lists the tags in use, with counts
```

With Nix: `nix-shell -p python3 --run "python3 build.py"`.

Besides the HTML pages, the generated site contains:

- `datasets.json`: all entries as JSON.
- `llms.txt` and `llms-full.txt`: a plain-text index of the datasets for AI
  agents, short and with full descriptions.
- `sitemap.xml` and `robots.txt` for search engines, and schema.org `Dataset`
  JSON-LD on every dataset page for Google Dataset Search.

The site's base URL is a constant at the top of `build.py`.

## Deployment

[`.github/workflows/build.yml`](./.github/workflows/build.yml) validates and
builds the site on every pull request and deploys it to GitHub Pages on every
push to `main`. In the repository settings, set Pages to deploy from
"GitHub Actions".
