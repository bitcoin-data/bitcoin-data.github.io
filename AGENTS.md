# Instructions for agents

This repository generates [bitcoin-data.github.io](https://bitcoin-data.github.io/),
an index of public Bitcoin related datasets. The most common task is adding a
dataset. Follow the steps below; they are written so that a coding agent can
complete the task from a single request like "add the dataset at <url>".

## Repository layout

- `datasets/<slug>.toml`: one file per dataset. This is the only thing to
  create when adding a dataset.
- `categories.toml`: the allowed categories. Do not add a category without
  asking the maintainers; pick the closest existing one.
- `build.py`: validates all entries and generates the site. Python 3.11+,
  standard library only.
- `templates/`, `static/`: page template and stylesheet. Leave them alone when
  adding a dataset.

## Adding a dataset

### 1. Collect facts

Read the dataset's own sources before writing anything. Typically:

- The README of its repository or its website.
- The `LICENSE` file and any data-specific license file such as `LICENSE-DATA`.
  Do not infer a license from the README text alone if a license file exists.
- The data files themselves: format, one or two sample rows, which network
  (mainnet, testnet, signet), the earliest and latest data points.
- How the data is collected and how often it is updated: CI workflows, the
  commit history, scripts in the repository.
- A DOI if the dataset is archived on Zenodo or similar.

Only state facts you verified. If something is unknown, leave the optional
field out or say so in the description rather than guessing.

### 2. Pick a slug, a category, tags and formats

- Slug: lowercase kebab-case, usually the repository name, e.g. `stale-blocks`.
  It becomes the file name `datasets/<slug>.toml` and the URL `/datasets/<slug>/`.
- Category: one `id` from `categories.toml`.
- Tags: reuse existing tags whenever one fits. List them with:

  ```sh
  python3 build.py --tags
  ```

  Good tags describe the subject (`blocks`, `p2p`, `mining`) and the network
  (`mainnet`, `signet`). Use three to seven tags. Tags are lowercase
  kebab-case. The data format is not a tag; it goes in the `format` field.
- Format: one or more of `csv`, `json`, `jsonl`, `parquet`, `sqlite`, `text`,
  `binary`, describing the files a user downloads. Ask the maintainers before
  adding a format to `FORMATS` in `build.py`.

### 3. Write the entry

Copy an existing entry, for example `datasets/stale-blocks.toml`, and fill in
the fields:

| Field         | Required | Content |
| ------------- | -------- | ------- |
| `name`        | yes      | Display name, sentence case, e.g. `Stale blocks`. |
| `category`    | yes      | Category id from `categories.toml`. |
| `tags`        | no       | List of tags, see above. |
| `format`      | yes      | List of data formats, see above. |
| `description` | yes      | Three short sentences, see below. |
| `links`       | yes      | One or more `[[links]]` tables. |
| `license`     | yes      | Free text. Name the data license and, if different, the code license, e.g. `CC0 1.0 (data), MIT (code)`. If there is no license, write `Not specified`. |
| `author`      | no       | The person, group or project publishing the dataset. |
| `doi`         | no       | Bare DOI, e.g. `10.5281/zenodo.22667157`. Prefer the concept DOI that resolves to the latest version. |

The description is exactly three short sentences, about 50 to 70 words in
total. Each answers one question:

1. **What is in it?** What one record represents and the file format.
2. **Where does it come from?** How the data is collected and by whom.
3. **What is it for, and what is the catch?** A typical use, then the main
   caveat a user should know.

Descriptions must be timeless. Do not include dates, time ranges, row or file
counts, sizes, version numbers, update frequencies, or status words such as
"currently", "since", "recently" or "stopped". These facts change and nobody
updates them. Describe what the dataset is, not its state today.

Write plainly for someone who knows Bitcoin but not this dataset. No marketing
language, no "comprehensive" or "powerful". The index page shows every
description in full, so keep it short.

Links use these types, in this order of preference: `repository`, `website`,
`download`, `documentation`, `paper`, `other`. Include the repository, the
website or dashboard if one exists, and a direct `download` link to the main
data file or directory. Give `download` and `documentation` links a `label`
that names the file or document. Use `https://` URLs and the repository's
default branch for raw file links.

### 4. Validate

```sh
python3 build.py --check
```

Fix every error it reports. The validator rejects unknown fields, unknown
categories and link types, tags that are not kebab-case, malformed DOIs and
entries without links. Optionally run `python3 build.py` and open
`site/datasets/<slug>/index.html` to see the result.

### 5. Commit and open a pull request

- Add only the new file under `datasets/`. Do not edit other entries, the
  build script or the templates as part of adding a dataset.
- Commit message: `Add <name> dataset`.
- In the pull request description, list the sources you used for each claim
  in the description and the license, so a reviewer can check them quickly.
  Mention anything you could not verify.

## Updating a dataset

Edit its file under `datasets/`, keep the three-sentence structure, run
`python3 build.py --check`, and open a pull request titled `Update <name> dataset`
that says what changed and why.
