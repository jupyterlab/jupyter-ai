import os
import shutil
from pathlib import Path
from typing import Tuple

import pytest
from jupyter_ai.document_loaders.directory import collect_filepaths


@pytest.fixture
def staging_dir(static_test_files_dir, jp_ai_staging_dir) -> Path:
    file1_path = static_test_files_dir / ".hidden_file.pdf"
    file2_path = static_test_files_dir / ".hidden_file.txt"
    file3_path = static_test_files_dir / "file0.html"
    file4_path = static_test_files_dir / "file1.txt"
    file5_path = static_test_files_dir / "file2.py"
    file6_path = static_test_files_dir / "file3.csv"
    file7_path = static_test_files_dir / "file3.xyz"
    file8_path = static_test_files_dir / "file4.pdf"

    job_staging_dir = jp_ai_staging_dir / "TestDir"
    job_staging_dir.mkdir()
    job_staging_subdir = job_staging_dir / "subdir"
    job_staging_subdir.mkdir()
    job_staging_hiddendir = job_staging_dir / ".hidden_dir"
    job_staging_hiddendir.mkdir()

    shutil.copy2(file1_path, job_staging_dir)
    shutil.copy2(file2_path, job_staging_subdir)
    shutil.copy2(file3_path, job_staging_dir)
    shutil.copy2(file4_path, job_staging_subdir)
    shutil.copy2(file5_path, job_staging_subdir)
    shutil.copy2(file6_path, job_staging_hiddendir)
    shutil.copy2(file7_path, job_staging_subdir)
    shutil.copy2(file8_path, job_staging_hiddendir)

    return job_staging_dir


def test_collect_filepaths(staging_dir):
    """
    Test that the number of valid files for `/learn` is correct.
    i.e., the `collect_filepaths` function only selects files that are
    1. Not in the the excluded directories and
    2. Are in the  valid file extensions list.
    """
    all_files = False
    staging_dir_filepath = staging_dir
    # Call the function we want to test
    result = collect_filepaths(staging_dir_filepath, all_files)

    assert len(result) == 3  # Test number of valid files

    filenames = [fp.name for fp in result]
    assert "file0.html" in filenames  # Check that valid file is included
    assert "file3.xyz" not in filenames  # Check that invalid file is excluded
