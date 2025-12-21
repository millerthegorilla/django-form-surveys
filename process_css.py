#!/usr/bin/env python3
from bs4 import BeautifulSoup
import sys
import hashlib


import os
import re
import subprocess


def is_git_clean():
    """Check if the git working directory is clean (no uncommitted changes)."""
    try:
        result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True, cwd=os.getcwd())
        return result.returncode == 0 and not result.stdout.strip()
    except FileNotFoundError:
        # Git not installed or not in a git repo
        return False


def is_new_branch():
    """Check if the current git branch has local commits not pushed to the remote (i.e., is 'new' or ahead)."""
    try:
        # Get current branch name
        branch_result = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], capture_output=True, text=True, cwd=os.getcwd())
        if branch_result.returncode != 0:
            return False
        branch = branch_result.stdout.strip()
        
        # Check if there are commits ahead of origin/branch
        log_result = subprocess.run(['git', 'log', '--oneline', f'origin/{branch}..HEAD'], capture_output=True, text=True, cwd=os.getcwd())
        if log_result.returncode == 0:
            # If output, there are local commits
            return bool(log_result.stdout.strip())
        else:
            # If remote branch doesn't exist, consider it new
            return True
    except (FileNotFoundError, subprocess.SubprocessError):
        return False


def find_html_files(directory, extra_files=tuple()):
    file_extensions = (".html", ".htm") + extra_files
    html_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(file_extensions):
                html_files.append(os.path.join(root, file))
    return html_files


def style_to_class(style):
    """Generate a unique class name from a style string."""
    return "extracted_" + hashlib.md5(style.encode()).hexdigest()[:8]


def extract_inline_css(html_path, css_path, output_html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    style_map = {}
    for tag in soup.find_all(style=True):
        style = tag["style"].strip()
        class_name = style_to_class(style)
        if class_name not in style_map:
            style_map[class_name] = style
        # Add or append to class attribute
        existing_classes = tag.get("class", [])
        tag["class"] = existing_classes + [class_name]
        del tag["style"]

    # Write CSS file
    with open(css_path, "w", encoding="utf-8") as f:
        for class_name, style in style_map.items():
            f.write(f".{class_name} {{ {style} }}\n")

    # Insert <link> tag if not present
    if not soup.find("link", rel="stylesheet", href=css_path):
        head = soup.head or soup.new_tag("head")
        link_tag = soup.new_tag("link", rel="stylesheet", href=css_path)
        head.append(link_tag)
        if not soup.head:
            soup.insert(0, head)

    with open(output_html_path, "w", encoding="utf-8") as f:
        f.write(str(soup))


def extract_css_classes(css_file_path):
    """Extract class names from a CSS file."""
    with open(css_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # Find all .classname patterns
    # todo add switch to detect if this is tailwind css and remove
    # escape characters - doing it anyway for now
    content = content.replace('\\','')
    classes = set(re.findall(r'\..+?(?=\s{)', content))
    # remove the leading dot
    classes = {cls[1:] for cls in classes}
    return classes


def force_remove_prefix_from_html(html_files, prefix):
    """Remove a specific prefix from class names in HTML files."""
    for html_file in html_files:
        with open(html_file, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')

        for tag in soup.find_all(attrs={'class': True}):
            new_classes = []
            for cls in tag['class']:
                if cls.startswith(prefix + ':'):
                    new_cls = cls[len(prefix) + 1:]
                else:
                    new_cls = cls
                new_classes.append(new_cls)
            tag['class'] = new_classes

        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(str(soup))


def prefix_css_classes_in_html(css_file_path, html_files, prefix, action='add'):
    """
    Scan a CSS file for class definitions, then in the given HTML files,
    add or remove the prefix to those class names in the HTML.

    :param css_file_path: Path to the CSS file to scan for classes.
    :param html_files: List of HTML file paths to modify.
    :param prefix: The prefix to add or remove (e.g., 'tw').
    :param action: 'add' to add the prefix, 'remove' to remove it.
    """
    classes = extract_css_classes(css_file_path)
    for html_file in html_files:
        with open(html_file, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')
        
        for tag in soup.find_all(attrs={'class': True}):
            new_classes = []
            for cls in tag['class']:
                if action == 'add':
                    if cls in classes and not cls.startswith(prefix + ':'):
                        new_cls = prefix + ':' + cls
                    else:
                        new_cls = cls
                elif action == 'remove':
                    if cls.startswith(prefix + ':') and cls[len(prefix) + 1:] in classes:
                        new_cls = cls[len(prefix) + 1:]
                    else:
                        new_cls = cls
                else:
                    new_cls = cls
                new_classes.append(new_cls)
            tag['class'] = new_classes
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(str(soup))


if __name__ == "__main__":
    if not is_new_branch():
        print("It is highly recommended to run this script on a new clean branch.")
        sys.exit(1)
    if not is_git_clean():
        print("Git working directory is not clean. Please commit or stash changes before running this script.")
        sys.exit(1)
    if len(sys.argv) < 4:
        print(
            "Usage: python process_css.py [--extract_css (input_file/directory) (output_file/directory) output.css]" \
            "   [--prefix_css (css_file) (html_file/directory) (prefix) (add|remove)]" \
            "   or [--force-remove-prefix (html_file/directory) (prefix)]"
            "   and [--extra-files (comma separated file extensions)]"
        )
        sys.exit(1)

    if "--extra-files" in sys.argv:
        extra_index = sys.argv.index("--extra-files")
        extra_files = tuple(ext.strip() for ext in sys.argv[extra_index + 1].split(","))
        # Remove these from sys.argv to avoid confusion later
        sys.argv.pop(extra_index)  # Remove --extra-files
        sys.argv.pop(extra_index)  # Remove the extensions argument
    else:
        extra_files = tuple()
    switch = sys.argv[1]
    if switch == "--extract_css":
        in_path = sys.argv[2]
        out_path = sys.argv[3]
        css_file = sys.argv[4]
        if not os.path.exists(out_path):
            if out_path.endswith(".html"):
                with open(out_path, "w") as f:
                    pass
            else:
                os.makedirs(os.path.realpath(out_path), exist_ok=True)

        if os.path.isfile(in_path) and os.path.isfile(out_path):
            extract_inline_css(in_path, css_file, out_path)
        elif os.path.isdir(in_path) and os.path.isdir(out_path):
            html_files = find_html_files(in_path, extra_files=extra_files)
            for html_file in html_files:
                relative_path = os.path.relpath(html_file, in_path)
                output_html_file = os.path.join(out_path, relative_path)
                output_dir = os.path.dirname(output_html_file)
                os.makedirs(output_dir, exist_ok=True)
                extract_inline_css(html_file, css_file, output_html_file)
        elif not os.path.exists(in_path):
            print(f"{in_path} does not exist or is not a regular file/directory.")
            if not os.path.exists(out_path):
                print(f"{out_path} does not exist or is not a regular file/directory.")
            sys.exit(1)
        else:
            print("Input and output paths must both be files or both be directories.")
            sys.exit(1)
    elif switch == "--prefix_css":
        css_file = sys.argv[2]
        html_path = sys.argv[3]
        prefix = sys.argv[4]
        action = sys.argv[5]
        if os.path.isfile(html_path):
            prefix_css_classes_in_html(css_file, [html_path], prefix, action)
        elif os.path.isdir(html_path):
            html_files = find_html_files(html_path, extra_files=extra_files)
            prefix_css_classes_in_html(css_file, html_files, prefix, action)
        else:
            print(f"{html_path} does not exist or is not a regular file/directory.")
            sys.exit(1)
    elif switch == "--force-remove-prefix":
        html_path = sys.argv[2]
        prefix = sys.argv[3]
        if os.path.isfile(html_path):
            force_remove_prefix_from_html([html_path], prefix)
        elif os.path.isdir(html_path):
            html_files = find_html_files(html_path, extra_files=extra_files)
            force_remove_prefix_from_html(html_files, prefix)
        else:
            print(f"{html_path} does not exist or is not a regular file/directory.")
            sys.exit(1)
    else:
        print("Unknown switch. Use --extract_css, --prefix_css, or --force-remove-prefix.")
        sys.exit(1)