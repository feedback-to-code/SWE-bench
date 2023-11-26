import json
import logging
import os
import traceback
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import unidiff
from tqdm.auto import tqdm

try:
    from tokenize_dataset import TOKENIZER_FUNCS
    from utils import AutoContextManager, ingest_directory_contents
except:
    from .tokenize_dataset import TOKENIZER_FUNCS
    from .utils import AutoContextManager, ingest_directory_contents

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

PATCH_EXAMPLE = """--- a/File.java
+++ b/File.java
@@ -3,38 +3,45 @@ import java.util.List;

 public class File {
     public static int euclidean(int a, int b) {
-        while (b != 0) {
-            int temp = b;
-            b = a % b;
-            a = temp;
+        if (b == 0) {
+            return a;
         }
-        return a;
+        return euclidean(b, a % b);
     }

     public static List<Point> bresenham(int x0, int y0, int x1, int y1) {
         List<Point> points = new ArrayList<>();
         int dx = Math.abs(x1 - x0);
         int dy = Math.abs(y1 - y0);
-        int sx = (x0 < x1) ? 1 : -1;
-        int sy = (y0 < y1) ? 1 : -1;
-        int err = dx - dy;
+        int x = x0, y = y0;
+        int sx = (x0 > x1) ? -1 : 1;
+        int sy = (y0 > y1) ? -1 : 1;

-        while (true) {
-            points.add(new Point(x0, y0));
-            if (x0 == x1 && y0 == y1) {
-                break;
-            }
-            int e2 = 2 * err;
-            if (e2 > -dy) {
+        if (dx > dy) {
+            double err = dx / 2.0;
+            while (x != x1) {
+                points.add(new Point(x, y));
                 err -= dy;
-                x0 += sx;
+                if (err < 0) {
+                    y += sy;
+                    err += dx;
+                }
+                x += sx;
             }
-            if (e2 < dx) {
-                err += dx;
-                y0 += sy;
+        } else {
+            double err = dy / 2.0;
+            while (y != y1) {
+                points.add(new Point(x, y));
+                err -= dx;
+                if (err < 0) {
+                    x += sx;
+                    err += dy;
+                }
+                y += sy;
             }
         }

+        points.add(new Point(x, y));
         return points;
     }"""

PYTHON_PATCH_EXAMPLE = """--- a/file.py
+++ b/file.py
@@ -1,27 +1,35 @@
 def euclidean(a, b):
-    while b:
-        a, b = b, a % b
-    return a
+    if b == 0:
+        return a
+    return euclidean(b, a % b)
 
 
 def bresenham(x0, y0, x1, y1):
     points = []
     dx = abs(x1 - x0)
     dy = abs(y1 - y0)
-    sx = 1 if x0 < x1 else -1
-    sy = 1 if y0 < y1 else -1
-    err = dx - dy
+    x, y = x0, y0
+    sx = -1 if x0 > x1 else 1
+    sy = -1 if y0 > y1 else 1
 
-    while True:
-        points.append((x0, y0))
-        if x0 == x1 and y0 == y1:
-            break
-        e2 = 2 * err
-        if e2 > -dy:
+    if dx > dy:
+        err = dx / 2.0
+        while x != x1:
+            points.append((x, y))
             err -= dy
-            x0 += sx
-        if e2 < dx:
-            err += dx
-            y0 += sy
+            if err < 0:
+                y += sy
+                err += dx
+            x += sx
+    else:
+        err = dy / 2.0
+        while y != y1:
+            points.append((x, y))
+            err -= dx
+            if err < 0:
+                x += sx
+                err += dy
+            y += sy
 
+    points.append((x, y))
     return points"""

FULL_GENERATION_EXAMPLE = """[start of /src/Bresenham.java]
import java.util.ArrayList;
import java.util.List;

import geometry.Point;

public class Bresenham {
    public static List<Point> bresenham(int x0, int y0, int x1, int y1) {
        List<Point> points = new ArrayList<>();
        int dx = Math.abs(x1 - x0);
        int dy = Math.abs(y1 - y0);
        int x = x0, y = y0;
        int sx = (x0 > x1) ? -1 : 1;
        int sy = (y0 > y1) ? -1 : 1;

        if (dx > dy) {
            double err = dx / 2.0;
            while (x != x1) {
                points.add(new Point(x, y));
                err -= dy;
                if (err < 0) {
                    y += sy;
                    err += dx;
                }
                x += sx;
            }
        } else {
            double err = dy / 2.0;
            while (y != y1) {
                points.add(new Point(x, y));
                err -= dx;
                if (err < 0) {
                    x += sx;
                    err += dy;
                }
                y += sy;
            }
        }

        points.add(new Point(x, y));
        return points;
    }
}
[end of /src/Bresenham.java]
[start of /src/geometry/Point.java]
public class Point {
    int x, y;

    public Point(int x, int y) {
        this.x = x;
        this.y = y;
    }
}
[end of /src/geometry/Point.java]"""

PYTHON_FULL_GENERATION_EXAMPLE = """[start of /src/this_file.py]
import os

def euclidean(a, b):
    if b == 0:
        return a
    return euclidean(b, a % b)
[end of /src/this_file.py]
[start of /src/another_file.py]
def bresenham(x0, y0, x1, y1):
    points = []
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    x, y = x0, y0
    sx = -1 if x0 > x1 else 1
    sy = -1 if y0 > y1 else 1
    if dx > dy:
        err = dx / 2.0
        while x != x1:
            points.append((x, y))
            err -= dy
            if err < 0:
                y += sy
                err += dx
            x += sx
    else:
        err = dy / 2.0
        while y != y1:
            points.append((x
            err -= dx
            if err < 0:
                x += sx
                err += dy
            y += sy
    points.append((x, y))
    return points
[end of /src/another_file.py]"""


def add_lines_list(content):
    content_with_lines = list()
    for ix, line in enumerate(content.split("\n"), start=1):
        content_with_lines.append(f"{ix} {line}")
    return content_with_lines


def add_lines(content):
    return "\n".join(add_lines_list(content))


def make_code_text(files_dict, add_line_numbers=True):
    all_text = ""
    for filename, contents in sorted(files_dict.items()):
        all_text += f"[start of {filename}]\n"
        if add_line_numbers:
            all_text += add_lines(contents)
        else:
            all_text += contents
        all_text += f"\n[end of {filename}]\n"
    return all_text.strip("\n")


def make_code_text_edits_only(files_dict, patch, add_line_numbers=True):
    files = dict()
    patch = unidiff.PatchSet(patch)
    for patched_file in patch:
        source_file = patched_file.source_file.split("a/", 1)[-1]
        files[source_file] = list()
        for hunk in patched_file:
            start = hunk.source_start - 15
            end = start + hunk.source_length + 15
            files[source_file].append((start, end))
    all_text = ""
    for filename, content in files_dict.items():
        all_text += f"[start of {filename}]\n"
        content_with_lines = add_lines_list(content)
        for start, end in files[filename]:
            if start > 0:
                all_text += "...\n"
            all_text += "\n".join(content_with_lines[start:end])
            all_text += "\n"
            if end < len(content_with_lines):
                all_text += "...\n"
        all_text = all_text.strip("\n")
        all_text += f"\n[end of {filename}]\n"
    return all_text.strip("\n")


def prompt_style_2(instance):
    premise = "You will be provided with a partial code base and an issue statement explaining a problem to resolve."
    readmes_text = make_code_text(instance["readmes"])
    code_text = make_code_text(instance["file_contents"])
    instructions = (
        f"I need you to solve this issue by generating a single patch file that I can apply "
        + f"directly to this repository using git apply. Please respond with a single patch "
        + f"file in the following format."
    )
    problem_statement = instance["problem_statement"]
    final_text = [
        premise,
        "<issue>",
        problem_statement,
        "</issue>",
        "<code>",
        readmes_text,
        code_text,
        "</code>",
        instructions,
        "<patch>",
        PATCH_EXAMPLE,
        "</patch>",
    ]
    final_text = "\n".join(final_text)
    return final_text


def prompt_style_2_edits_only(instance):
    premise = "You will be provided with a partial code base and an issue statement explaining a problem to resolve."
    readmes_text = make_code_text(instance["readmes"])
    code_text = make_code_text_edits_only(instance["file_contents"], instance["patch"])
    instructions = (
        f"I need you to solve this issue by generating a single patch file that I can apply "
        + f"directly to this repository using git apply. Please respond with a single patch "
        + f"file in the following format."
    )
    problem_statement = instance["problem_statement"]
    final_text = [
        premise,
        "<issue>",
        problem_statement,
        "</issue>",
        "<code>",
        readmes_text,
        code_text,
        "</code>",
        instructions,
        "<patch>",
        PATCH_EXAMPLE,
        "</patch>",
    ]
    final_text = "\n".join(final_text)
    return final_text


def prompt_style_3(instance):
    premise = "You will be provided with a partial code base and an issue statement explaining a problem to resolve."
    readmes_text = make_code_text(instance["readmes"])
    code_text = make_code_text(instance["file_contents"])
    example_explanation = (
        f"Here is an example of a patch file. It consists of changes to the code base. "
        + f"It specifies the file names, the line numbers of each change, and the removed and added lines. "
        + f"A single patch file can contain changes to multiple files."
    )
    final_instruction = (
        f"I need you to solve the provded issue by generating a single patch file that I can apply "
        + f"directly to this repository using git apply. Please respond with a single patch "
        + f"file in the format shown above."
    )
    problem_statement = instance["problem_statement"]
    final_text = [
        premise,
        "<issue>",
        problem_statement,
        "</issue>",
        "",
        "<code>",
        readmes_text,
        code_text,
        "</code>",
        "",
        example_explanation,
        "<patch>",
        PATCH_EXAMPLE,
        "</patch>",
        "",
        final_instruction,
        "Respond below:",
    ]
    final_text = "\n".join(final_text)
    return final_text


def full_file_gen(instance):
    premise = "You will be provided with a partial code base and an issue statement explaining a problem to resolve."
    readmes_text = make_code_text(instance["readmes"], add_line_numbers=False)
    code_text = make_code_text(instance["file_contents"], add_line_numbers=False)
    instructions = (
        f"I need you to solve this issue by regenerating the full files in the code base that you would like to change. "
        + f"You can change as many files as you like. "
        + f"Please respond with a list of files and their revised contents in the following format."
    )
    problem_statement = instance["problem_statement"]
    final_text = [
        premise,
        "<issue>",
        problem_statement,
        "</issue>",
        "<code>",
        readmes_text,
        code_text,
        "</code>",
        instructions,
        "<example>",
        FULL_GENERATION_EXAMPLE,
        "</example>",
    ]
    final_text = "\n".join(final_text)
    return final_text


def ingest_files(filenames):
    files_dict = dict()
    for filename in filenames:
        with open(filename, errors='ignore') as f:
            content = f.read()
        files_dict[filename] = content
    return files_dict


PROMPT_FUNCTIONS = {
    "style-2": prompt_style_2,
    "style-3": prompt_style_3,
    "full_file_gen": full_file_gen,
    "style-2-edits-only": prompt_style_2_edits_only,
}


def add_retrieval_results(input_instances, retrieval_dir, k, file_source):
    """
    Adds retrieval results to input_instances in-place
    """
    retrieval_results = dict()
    for instance_id, instance in tqdm(
        input_instances.items(),
        total=len(input_instances),
        desc="Adding retrieval results",
    ):
        retrieval_results_path = Path(
            retrieval_dir,
            instance["repo"].split("/")[-1] + "-task-instances.retrieval.jsonl",
        )
        assert (
            retrieval_results_path.exists()
        ), f"Retrieval results not found at {retrieval_results_path}"
        if retrieval_results_path not in retrieval_results:
            d = [json.loads(line) for line in open(retrieval_results_path)]
            d = {x["instance_id"]: x["hits"] for x in d}
            retrieval_results[retrieval_results_path.as_posix()] = d
        instance["hits"] = retrieval_results[retrieval_results_path.as_posix()][
            instance_id
        ][:k]


def get_oracle_filenames(instance):
    """
    Returns the filenames that are changed in the patch
    """
    source_files = {
        patch_file.source_file.split("a/", 1)[-1]
        for patch_file in unidiff.PatchSet(instance["patch"])
    }
    gold_docs = set()
    for source_file in source_files:
        gold_docs.add(source_file)
    return gold_docs


def add_text_inputs(
    input_instances,
    retrieval_dir,
    k,
    prompt_style,
    file_source,
    max_context_len=None,
    tokenizer_name=None,
    verbose=False,
):
    """Adds text inputs context for prediction in-place.

    Args:
    - input_instances: dictionary with unprocessed input instances.
    - retrieval_dir: if using retrieval method for file_contents, specify retrieval_dir to add retrieval results
    - k: if using retrieval, specifies the maximum number of files to included within context
    - prompt_style: specify the function to generate instructions and prompt provided an instance (from PROMPT_FUNCTIONS)
    - file_source: where to collect file_contents (e.g. oracle or bm25)
    - verbose: set ContextManager verbose to True
    """
    if max_context_len is not None:
        assert (
            tokenizer_name is not None
        ), "Must specify tokenizer_name if using max_context_len"
        tokenizer, tokenizer_func = TOKENIZER_FUNCS[tokenizer_name]
    input_instances_copy = deepcopy(input_instances)
    if file_source in {"bm25"}:
        add_retrieval_results(input_instances_copy, retrieval_dir, k, file_source)
    orig_dir = os.getcwd()
    with TemporaryDirectory(
        dir="/scratch" if os.path.exists("/scratch") else "/tmp"
    ) as root_dir:
        for instance_id, instance in tqdm(
            input_instances_copy.items(),
            total=len(input_instances_copy),
            desc="Adding text inputs",
        ):
            try:
                with AutoContextManager(
                    instance, root_dir, verbose=verbose
                ) as cm:
                    readmes = cm.get_readme_files()
                    instance["readmes"] = ingest_files(readmes)
                    if max_context_len is not None:
                        instance["file_contents"] = dict()
                        base_text_inputs = PROMPT_FUNCTIONS[prompt_style](instance)
                        base_text_input_length = len(
                            tokenizer_func(base_text_inputs, tokenizer)
                        )
                    if file_source in {"oracle"}:
                        instance["file_contents"] = ingest_files(
                            get_oracle_filenames(instance)
                        )
                    elif file_source in {"bm25"}:
                        instance["file_contents"] = ingest_files(
                            [x["docid"] for x in instance["hits"]]
                        )
                    elif file_source in {"all"}:
                        instance["file_contents"] = ingest_directory_contents(
                            cm.repo_path
                        )
                    elif file_source in {"none"}:
                        instance["file_contents"] = dict()
                    else:
                        raise ValueError(f"Invalid file source {file_source}")
                    if max_context_len is not None:
                        cur_input_len = base_text_input_length
                        include_files = list()
                        for filename in [x["docid"] for x in instance["hits"]]:
                            content = make_code_text(
                                {filename: instance["file_contents"][filename]}
                            )
                            if tokenizer_name in {"llama"}:
                                tokens = tokenizer_func("\n" + content, tokenizer)
                                idx = tokens.index(13)
                                assert (
                                    idx <= 2
                                ), "Expected newline token id (13) to be one of the first three tokens"
                                tokens = tokens[idx + 1 :]  # remove newline tokens
                            else:
                                tokens = tokenizer_func(content, tokenizer)
                            if cur_input_len + len(tokens) < max_context_len:
                                include_files.append(filename)
                                cur_input_len += len(tokens)
                        instance["file_contents"] = {
                            filename: instance["file_contents"][filename]
                            for filename in include_files
                        }
                    input_instances[instance_id]["text_inputs"] = PROMPT_FUNCTIONS[
                        prompt_style
                    ](instance)
            except Exception as e:
                print(f"Failed on instance {instance_id}", e)
                traceback.print_exc()
                input_instances[instance_id]["text_inputs"] = None
            finally:
                # if AutoContextManager fails to exit properly future exits will return the wrong directory
                os.chdir(orig_dir)
    os.chdir(orig_dir)
