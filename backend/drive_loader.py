import os
import re
import shutil
import tempfile
from pathlib import Path

import gdown
import pandas as pd

from content_extractors import documents_from_dataframe, extract_from_bytes


def _normalize_drive_folder_url(folder_url):
    match = re.search(r"/folders/([a-zA-Z0-9_-]+)", folder_url)
    if match:
        folder_id = match.group(1)
        return f"https://drive.google.com/drive/folders/{folder_id}"
    return folder_url


def _is_drive_folder_url(url):
    return "/folders/" in url


def load_excel_with_links(
    excel_path,
    follow_links_depth=1,
    follow_urls_in_text=True,
    max_urls=20,
):
    df = pd.read_excel(excel_path)
    return documents_from_dataframe(df, "excel", follow_links_depth, follow_urls_in_text, max_urls)


def load_drive_folder_public(
    folder_url,
    follow_links_depth=1,
    follow_urls_in_text=True,
    max_urls=20,
    enable_ocr=True,
    enable_audio_video=True,
    whisper_model="base",
    whisper_device="cpu",
    whisper_compute_type="int8",
    archive_depth=1,
    cache=None,
):
    if not folder_url:
        return []

    folder_url = _normalize_drive_folder_url(folder_url)
    print(f"Drive folder URL (normalized): {folder_url}")
    temp_dir = tempfile.mkdtemp(prefix="drive_ingest_")
    try:
        gdown.download_folder(
            url=folder_url,
            output=temp_dir,
            quiet=False,
            use_cookies=False,
        )
        documents = []
        file_count = 0
        skipped = 0
        for root, _, files in os.walk(temp_dir):
            for name in files:
                path = os.path.join(root, name)
                rel_path = os.path.relpath(path, temp_dir)
                with open(path, "rb") as handle:
                    content = handle.read()
                cache_key = f"drive:{rel_path}"
                if cache:
                    file_hash = cache.hash_bytes(content)
                    if cache.file_unchanged(cache_key, file_hash):
                        skipped += 1
                        continue

                documents += extract_from_bytes(
                    name,
                    content,
                    follow_links_depth=follow_links_depth,
                    follow_urls_in_text=follow_urls_in_text,
                    max_urls=max_urls,
                    enable_ocr=enable_ocr,
                    enable_audio_video=enable_audio_video,
                    whisper_model=whisper_model,
                    whisper_device=whisper_device,
                    whisper_compute_type=whisper_compute_type,
                    archive_depth=archive_depth,
                )
                if cache:
                    cache.update_file_hash(cache_key, file_hash)
                file_count += 1
        print(f"Drive files downloaded: {file_count}, skipped unchanged: {skipped}")
        return documents
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def load_drive_public(
    url,
    follow_links_depth=1,
    follow_urls_in_text=True,
    max_urls=20,
    enable_ocr=True,
    enable_audio_video=True,
    whisper_model="base",
    whisper_device="cpu",
    whisper_compute_type="int8",
    archive_depth=1,
    cache=None,
):
    if _is_drive_folder_url(url):
        return load_drive_folder_public(
            url,
            follow_links_depth=follow_links_depth,
            follow_urls_in_text=follow_urls_in_text,
            max_urls=max_urls,
            enable_ocr=enable_ocr,
            enable_audio_video=enable_audio_video,
            whisper_model=whisper_model,
            whisper_device=whisper_device,
            whisper_compute_type=whisper_compute_type,
            archive_depth=archive_depth,
            cache=cache,
        )

    temp_dir = tempfile.mkdtemp(prefix="drive_file_")
    old_cwd = os.getcwd()
    try:
        os.chdir(temp_dir)
        downloaded = gdown.download(url=url, output=None, quiet=False, fuzzy=True)
        os.chdir(old_cwd)
        if not downloaded:
            return []

        downloaded_path = Path(downloaded)
        if not downloaded_path.is_absolute():
            downloaded_path = Path(temp_dir) / downloaded_path

        with open(downloaded_path, "rb") as handle:
            content = handle.read()

        cache_key = f"drive:{url}"
        if cache:
            file_hash = cache.hash_bytes(content)
            if cache.file_unchanged(cache_key, file_hash):
                print("Drive file skipped unchanged: 1")
                return []

        documents = extract_from_bytes(
            downloaded_path.name or "google_drive_file",
            content,
            follow_links_depth=follow_links_depth,
            follow_urls_in_text=follow_urls_in_text,
            max_urls=max_urls,
            enable_ocr=enable_ocr,
            enable_audio_video=enable_audio_video,
            whisper_model=whisper_model,
            whisper_device=whisper_device,
            whisper_compute_type=whisper_compute_type,
            archive_depth=archive_depth,
        )
        if cache:
            cache.update_file_hash(cache_key, file_hash)
        return documents
    finally:
        os.chdir(old_cwd)
        shutil.rmtree(temp_dir, ignore_errors=True)
