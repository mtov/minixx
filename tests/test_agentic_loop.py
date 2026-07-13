from __future__ import annotations

from minixx.agentic_loop import print_final_result


def test_print_final_result_skips_unified_diff_patches(capsys) -> None:
    print_final_result("--- a/file.py\n+++ b/file.py\n@@ -1 +1 @@\n-old\n+new\n")

    captured = capsys.readouterr()

    assert captured.out == ""


def test_print_final_result_prints_non_patch_results(capsys) -> None:
    print_final_result("Task completed successfully.")

    captured = capsys.readouterr()

    assert captured.out == "Task completed successfully.\n"
