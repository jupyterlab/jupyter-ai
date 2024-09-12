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
    file9_path = static_test_files_dir / "file9.ipynb"

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
    shutil.copy2(file9_path, job_staging_subdir)

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

    assert len(result) == 4  # Test number of valid files

    filenames = [fp.name for fp in result]
    assert "file0.html" in filenames  # Check that valid file is included
    assert "file3.xyz" not in filenames  # Check that invalid file is excluded

    # test unix wildcard pattern
    pattern_path = os.path.join(staging_dir_filepath, "**/*.*py*")
    results = collect_filepaths(pattern_path, all_files)
    assert len(results) == 2
    condition = lambda p: p.suffix in [".py", ".ipynb"]
    assert all(map(condition, results))

    # test unix wildcard pattern returning only directories
    pattern_path = f"{str(staging_dir_filepath)}*/"
    results = collect_filepaths(pattern_path, all_files)
    assert len(result) == 4
    filenames = [fp.name for fp in result]

    assert "file0.html" in filenames  # Check that valid file is included
    assert "file3.xyz" not in filenames  # Check that invalid file is excluded
