"""
Test that the collect_files function only selects files that are
1. Not in the the excluded directories and
2. Are in the  valid file extensions list.
"""

import os
import unittest

from jupyter_ai.document_loaders.directory import collect_files


class TestCollectFiles(unittest.TestCase):
    # Prepare temp directory for test
    os.mkdir("TestDir")
    path = os.path.join(os.getcwd(), "TestDir")
    test_dir_contents = {
        "0": ["file0.html", ".hidden_file.pdf"],  # top level folder, 1 valid file
        "subdir": [
            "file1.txt",
            ".hidden_file.txt",
            "file2.py",
            "file3.xyz",
        ],  # subfolder, 2 valid files
        ".hidden_dir": ["file3.csv", "file4.pdf"],
    }  # hidden subfolder, no valid files
    for folder in test_dir_contents:
        os.chdir(path)
        if folder != "0":
            os.mkdir(folder)
            d = os.path.join(path, folder)
        else:
            d = path
        for file in test_dir_contents[folder]:
            filepath = os.path.join(d, file)
            open(filepath, "a")

    # Test that the number of valid files for `/learn` is correct
    def test_collect_files(self):
        all_files = False
        # Call the function we want to test
        result = collect_files(self.path, all_files)
        self.assertEqual(len(result), 3)  # Number of valid files

        # Clean up temp directory
        from shutil import rmtree

        rmtree(self.path)
        os.chdir(os.path.split(self.path)[0])


if __name__ == "__main__":
    unittest.main()
