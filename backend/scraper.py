import json
import re
from urllib.parse import urldefrag, urljoin, urlparse

import requests
from bs4 import BeautifulSoup


SKIP_EXTENSIONS = (
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".svg",
    ".webp",
    ".woff",
    ".woff2",
    ".ttf",
    ".map",
    ".zip",
    ".rar",
)
DATA_EXTENSIONS = (".json", ".csv", ".txt", ".md")
JS_DATA_RE = re.compile(r"""["']([^"']+\.(?:json|csv|txt|md))["']""", re.IGNORECASE)
JS_ASSET_RE = re.compile(r"""["']([^"']+\.js)["']""", re.IGNORECASE)
FETCH_RE = re.compile(r"""fetch\(\s*[^"']*["']([^"']+)["']""", re.IGNORECASE)


def _clean_url(url):
    cleaned, _ = urldefrag(url)
    return cleaned


def _same_site(url, root_url):
    return urlparse(url).netloc == urlparse(root_url).netloc


def _join_site_url(current_url, ref):
    parsed_ref = urlparse(ref)
    if parsed_ref.scheme or ref.startswith("/"):
        return urljoin(current_url, ref)

    current_path = urlparse(current_url).path
    if current_path.startswith("/assets/") and not ref.startswith(("./", "../")):
        parsed_current = urlparse(current_url)
        site_root = f"{parsed_current.scheme}://{parsed_current.netloc}/"
        return urljoin(site_root, ref)

    return urljoin(current_url, ref)


def _should_skip(url):
    path = urlparse(url).path.lower()
    return path.endswith(SKIP_EXTENSIONS)


def _looks_like_data(url):
    return urlparse(url).path.lower().endswith(DATA_EXTENSIONS)


def _json_value_to_text(value, prefix=""):
    parts = []
    if isinstance(value, dict):
        for key, nested in value.items():
            label = f"{prefix}.{key}" if prefix else str(key)
            parts.extend(_json_value_to_text(nested, label))
    elif isinstance(value, list):
        if all(not isinstance(item, (dict, list)) for item in value):
            parts.append(f"{prefix}: {', '.join(map(str, value))}")
        else:
            for index, nested in enumerate(value, 1):
                label = f"{prefix}[{index}]" if prefix else f"item[{index}]"
                parts.extend(_json_value_to_text(nested, label))
    elif value is not None and value != "":
        parts.append(f"{prefix}: {value}")
    return parts


def _documents_from_json(data, source, section=""):
    documents = []
    if isinstance(data, list):
        for index, item in enumerate(data, 1):
            label = f"{section} record {index}" if section else f"record {index}"
            text = " | ".join(_json_value_to_text(item))
            if text:
                documents.append({"source": f"{source}#{label}", "content": f"{label} | {text}"})
            return documents

    if isinstance(data, dict):
        for key, value in data.items():
            documents.extend(_documents_from_json(value, source, str(key)))
        if documents:
            return documents

    text = " | ".join(_json_value_to_text(data))
    if text:
        documents.append({"source": source, "content": text})
    return documents


def _documents_from_data_response(url, response):
    content_type = response.headers.get("content-type", "").lower()
    path = urlparse(url).path.lower()

    if "json" in content_type or path.endswith(".json"):
        try:
            return _documents_from_json(response.json(), url)
        except json.JSONDecodeError:
            pass

    text = response.text.strip()
    if not text:
        return []
    return [{"source": url, "content": text}]


def _extract_links_from_html(url, html):
    soup = BeautifulSoup(html, "html.parser")
    links = set()
    for tag in soup.find_all(["a", "link", "script"], href=True):
        links.add(urljoin(url, tag["href"]))
    for tag in soup.find_all(["script", "img", "iframe"], src=True):
        links.add(urljoin(url, tag["src"]))
    return {_clean_url(link) for link in links}


def _extract_data_links_from_js(url, text):
    links = set()
    for pattern in (JS_DATA_RE, FETCH_RE):
        for match in pattern.findall(text):
            link = _join_site_url(url, match)
            if _looks_like_data(link):
                links.add(link)
    return {_clean_url(link) for link in links}


def _extract_js_links_from_js(url, text):
    links = set()
    for match in JS_ASSET_RE.findall(text):
        link = _join_site_url(url, match)
        if urlparse(link).path.lower().endswith(".js"):
            links.add(link)
    return {_clean_url(link) for link in links}


def scrape_url(url, depth=1, max_pages=200):
    root_url = _clean_url(url)
    visited = set()
    documents = []

    def crawl(current_url, remaining_depth):
        current_url = _clean_url(current_url)
        if (
            current_url in visited
            or len(visited) >= max_pages
            or _should_skip(current_url)
            or not _same_site(current_url, root_url)
        ):
            return

        visited.add(current_url)
        try:
            response = requests.get(
                current_url,
                timeout=20,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            response.raise_for_status()
        except Exception as exc:
            print(f"Failed {current_url}: {exc}")
            return

        content_type = response.headers.get("content-type", "").lower()
        path = urlparse(current_url).path.lower()

        if _looks_like_data(current_url):
            documents.extend(_documents_from_data_response(current_url, response))
            return

        if "javascript" in content_type or path.endswith(".js"):
            for link in _extract_data_links_from_js(current_url, response.text):
                crawl(link, remaining_depth)
            for link in _extract_js_links_from_js(current_url, response.text):
                crawl(link, remaining_depth)
            return

        if "text/html" not in content_type:
            return

        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text(separator=" ", strip=True)
        if text:
            documents.append({"source": current_url, "content": text})

        for link in _extract_links_from_html(current_url, response.text):
            if _looks_like_data(link) or link.lower().endswith(".js"):
                crawl(link, remaining_depth)
            elif remaining_depth > 0:
                crawl(link, remaining_depth - 1)

    crawl(root_url, depth)
    print(f"Scraped {len(visited)} website URLs from {root_url}")
    return documents
