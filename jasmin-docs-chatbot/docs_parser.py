import os
import json
import requests
from bs4 import BeautifulSoup

import git
import pandas as pd


GIT_REPO_URL = "https://github.com/cedadev/jasmin-help-hugo-hinode"
GIT_REPO_PATH = "./jasmin-help-hugo-hinode"
CSV_PATH = "./ceda_jasmin_docs.csv"
CEDA_DOCS_PATH = "./ceda-docs-2024-10-25"

# MOLES related variables
moles_key_map = {"time": "time_period", "phenomena": "variables",
           "projects": "associated_projects", "bbox": "bounding_box"}
moles_key_order = ["title", "uuid", "abstract", "keywords", "time", "bbox", "phenomena", "projects"]


def clone_repo(url=GIT_REPO_URL, path=GIT_REPO_PATH, force=False):
    if force and os.path.isdir(path):
        print(f"Removing existing repo at {path}.")
        os.system(f"rm -rf {path}")

    if not os.path.isdir(path):
        print(f"Cloning {url} to {path}.")
        git.Repo.clone_from(url, path)
    else:
        print(f"Repo already exists at {path}.")


def check_url(url):
    response = requests.get(url)
    response.raise_for_status()


def parse_md_file_jasmin(file_path, docs_url="https://help.jasmin.ac.uk"):
    """
    Parse a markdown file and return a list of sections.
    
    Args:
        file_path (str): The path to the markdown file.
        docs_url (str): The base URL for the documentation site.
        
    Returns:
        list: A list of sections, each represented as a list with three elements:
            - The section title.
            - The section content.
            - The section URL.
    """
    print(f"Parsing {file_path}")

    with open(file_path, "r", encoding="utf-8") as file:
        lines = file.readlines()

    page_slug_search = [line.split(":")[-1].strip() for line in lines[:20] 
                       if line.startswith("slug:")]
    if page_slug_search:
        page_slug = page_slug_search[0]
    else:
        page_slug = file_path.split(os.path.sep)[-1][:-3]

    url_parts = file_path.split(os.path.sep)[3:]
    url_base = docs_url + "/" + "/".join(url_parts)[:-3]

    if url_base.endswith("_index"):
        url_base = url_base[:-6]
    else:
        url_base = "/".join(url_base.split("/")[:-1] + [page_slug])

    check_url(url_base)

    try:
        section_separator = sorted(set(
                [line.strip().split()[0] for line in lines if line.startswith("#")]
            ))[0]
    except IndexError:
        print(f"No sections found in {file_path}.")
        return []

    sections = []
    current_section = None

    in_code_block = False
    triple_dash_count = 0

    for line in lines:
        if line.strip() == "---":
            triple_dash_count += 1
            continue

        if triple_dash_count == 1 and line.startswith("title:"):
            page_title = line.split(":")[1].strip()
            continue

        if triple_dash_count < 2:
            continue

        if not line.strip():
            continue

        if line.startswith("```"):
            in_code_block = not in_code_block
            continue

        if line.startswith(section_separator) and not in_code_block:
            if current_section:
                sections.append(current_section)

            title = line.strip("#").strip()
            slug = title.lower().replace(" ", "-")
            current_section = [line.strip("#").strip(), "", f"{url_base}#{slug}"]
        else:
            if not current_section:
                current_section = [page_title, "", url_base]
            current_section[1] += line

    if not sections or sections[-1] != current_section:
        sections.append(current_section)

    return sections


def resolve_ceda_docs_search_url(title):
    "Resolves a URL from the CEDA Docs content, based on the title."
    search_url = "https://help.ceda.ac.uk/search?collectionId=564b4f2490336002f86de436&query="
    url = search_url + "+".join(title.split())
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")

    def _simple_str(x): 
        reps = [" ", ":", "-", "_", "'", '"', ",", ";", ".", "&"]
        for rep in reps: 
            x = x.replace(rep, "")
        return x

    url_path = [li.a.get("href", "") for li in soup.find("ul", class_="articleList"). \
                find_all("li") if _simple_str(li.text.strip().split("\n")[0]) == _simple_str(title)]

    if url_path:
        return url_path[0]
    else:
        return None


def parse_md_file_cedadocs(file_path, docs_url="https://help.ceda.ac.uk"):
    """
    Parse a markdown file and return a list of sections.

    Args:
        file_path (str): The path to the markdown file.
        docs_url (str): The base URL for the documentation site.

    Returns:
        list: A list of sections, each represented as a list with three elements:
            - The section title.
            - The section content.
            - The section URL.
    """
    print(f"Parsing {file_path}")

    with open(file_path, "r", encoding="utf-8") as file:
        lines = file.readlines()

    page_title = os.path.basename(file_path)[:-3].replace("-", " ")
    url_path = resolve_ceda_docs_search_url(page_title)

    if not url_path:
        print(f"[WARNING] Failed to get path for: {file_path}")
        url_base = docs_url
    else:
        url_base = docs_url + url_path
        print(f"[INFO] Located URL at: {url_base}")

    check_url(url_base)

    try:
        section_separator = sorted(set(
                [line.strip().split()[0] for line in lines if line.startswith("#")]
            ))[0]
    except IndexError:
        print(f"[WARNING] No sections found in {file_path}.")
        return []

    sections = []
    current_section = None

    in_code_block = False

    for line in lines:
        if not line.strip():
            continue

        if line.startswith("```"):
            in_code_block = not in_code_block
            continue

        if line.startswith(section_separator) and not in_code_block:
            if current_section:
                sections.append(current_section)

            title = line.strip("#").strip()
            slug = title.lower().replace(" ", "-")
            current_section = [line.strip("#").strip(), "", f"{url_base}#{slug}"]
        else:
            if not current_section:
                current_section = [page_title, "", url_base]
            current_section[1] += line

    if not sections or sections[-1] != current_section:
        sections.append(current_section)

    return sections


def package_moles_record(rec):
    "Repackage a MOLES observation dictionary, ready for putting into DataFrame."
    uuid = rec["uuid"]
    title = f"Catalogue record: {uuid}"
    page_url = f"https://catalogue.ceda.ac.uk/uuid/{uuid}"

    # Construct content - with ordered keys and pretty-printed
    content = {moles_key_map.get(key, key): rec[key] for key in moles_key_order}
    content = json.dumps(content, indent=2, sort_keys=False)
    return [title, content, page_url]


def parse_moles_records(moles_json="moles.json"):
    "Parse MOLES records and return a list of [[title, content, page_url]]."
    print(f"Loading MOLES data from: {moles_json}")
    data = json.load(open(moles_json))
    print(f"Parsed {len(data)} files.")
    sections = [package_moles_record(rec) for rec in data]
    return sections


def parse_docs(git_repo_url=GIT_REPO_URL, 
               repo_path=GIT_REPO_PATH, 
               ceda_docs_path=CEDA_DOCS_PATH,
               csv_path=CSV_PATH, max_docs=5000, force=False):

    exclude_files = ["centos7-sci-login-xfer-servers.md"]

    if os.path.isfile(csv_path) and not force:
        print(f"Loading {csv_path}.")
        return pd.read_csv(csv_path)

    clone_repo(git_repo_url, repo_path)

    jasmin_docs_path = os.path.join(repo_path, "content", "docs")
    sections = []

    # First, parse the documentation from walking directories
    to_walk = [("JASMIN Docs", jasmin_docs_path, parse_md_file_jasmin), 
               ("CEDA Docs", ceda_docs_path, parse_md_file_cedadocs)]

    count = 0

    for docs_name, docs_path, docs_parser in to_walk:
        print(f"Parsing {docs_name} if found.")
        for root, dirs, files in os.walk(docs_path):
            for file in files:
                if count > max_docs: 
                    break

                if file.endswith(".md") and file not in exclude_files:
                    new_sections = docs_parser(os.path.join(root, file))

                if new_sections:
                    sections.extend(new_sections)
                    count += 1

    print(f"Parsed {count} files.")

    # Next, add the MOLES content from a CSV file
    sections.extend(parse_moles_records())

    df = pd.DataFrame(sections, columns=["title", "contents", "page_url"])

    df["char_count"] = df["contents"].apply(len)
    df["word_count"] = df["contents"].apply(lambda x: len(x.split()))
    df.to_csv(csv_path, index=False)
    return df


if __name__ == "__main__":

    df = parse_docs(csv_path="test_ceda_jasmin_docs.csv", force=True)
    print(df.shape)
    print(df.head(3))

