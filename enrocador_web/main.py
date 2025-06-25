import argparse
import os
import shutil
import sys

if not (3, 8) <= sys.version_info < (3, 13):
    sys.exit("ERROR: enrocador Web requires Python >=3.8 and <3.13")

from pathlib import Path
from urllib.parse import urlparse

from pywebcopy import configs
import threading
import time


def _patch_html2image_py38():
    """Modify html2image for Python 3.8 compatibility if needed."""
    import importlib.util
    from pathlib import Path

    spec = importlib.util.find_spec("html2image")
    if not spec or not spec.origin:
        return

    path = Path(spec.origin)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return

    if "list[str]" not in text:
        return

    if "from typing import List" not in text:
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if line.startswith("import") or line.startswith("from"):
                last_import = i
        lines.insert(last_import + 1, "from typing import List")
        text = "\n".join(lines)

    text = text.replace("list[str]", "List[str]")
    try:
        path.write_text(text, encoding="utf-8")
    except OSError:
        return
    import importlib
    importlib.invalidate_caches()
    importlib.reload(importlib.import_module("html2image"))


def _spinner(message, stop_event):
    """Simple CLI spinner shown while stop_event isn't set."""
    chars = ['|', '/', '-', '\\']
    idx = 0
    while not stop_event.is_set():
        print(f"\r{message} {chars[idx % len(chars)]}", end='', flush=True)
        time.sleep(0.1)
        idx += 1
    print(f"\r{message} listo.      ")

def download_site(url, dest_dir, user_agent=None, depth=None, exclude=None, sanitize=False, theme_name=None):
    """Download site using pywebcopy and generate theme files."""
    dest_dir = Path(dest_dir).resolve()
    static_dir = dest_dir / "static"
    static_dir.mkdir(parents=True, exist_ok=True)

    # Configure pywebcopy
    conf = configs.get_config(url, str(static_dir), "", bypass_robots=True)
    if user_agent:
        headers = conf["http_headers"]
        headers["User-Agent"] = user_agent
        conf["http_headers"] = headers

    crawler = conf.create_crawler()
    stop = threading.Event()
    t = threading.Thread(target=_spinner, args=('Descargando...', stop))
    t.start()
    try:
        crawler.get(url)
        crawler.save_complete()
    finally:
        stop.set()
        t.join()

    host = urlparse(url).hostname or "site"
    src_root = Path(conf.get_project_folder()) / host
    if src_root.exists():
        parts = [p for p in Path(urlparse(url).path).parts if p not in ('', '/')]
        source = src_root
        if parts:
            candidate = src_root.joinpath(*parts)
            if candidate.exists():
                source = candidate
        for item in source.iterdir():
            target = static_dir / item.name
            if target.exists():
                if item.is_dir():
                    shutil.rmtree(target)
                else:
                    target.unlink()
            shutil.move(str(item), target)
        shutil.rmtree(Path(conf.get_project_folder()))

    tn = theme_name or Path(dest_dir).name
    copy_template_files(dest_dir, tn, url)
    convert_html_to_utf8(static_dir)
    strip_index_from_urls(static_dir)
    capture_screenshot(url, dest_dir)


def copy_template_files(theme_dir, theme_name, url=""):
    """Copy base PHP template files and style.css into the theme."""
    template_dir = Path(__file__).parent / "theme_template"
    for fname in os.listdir(template_dir):
        src = template_dir / fname
        dst = theme_dir / fname
        if fname == "style.css":
            text = src.read_text()
            text = text.replace("{{THEME_NAME}}", theme_name)
            text = text.replace("{{URL}}", url)
            dst.write_text(text)
        else:
            shutil.copy(src, dst)


def convert_html_to_utf8(root_dir):
    """Re-encode all HTML files inside ``root_dir`` to UTF-8."""
    for path in Path(root_dir).rglob('*.htm*'):
        data = path.read_bytes()
        for enc in ('utf-8', 'latin-1'):
            try:
                text = data.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        else:
            text = data.decode('utf-8', errors='replace')
        path.write_text(text, encoding='utf-8')


def strip_index_from_urls(root_dir):
    """Remove 'index.html' from href/src attributes in HTML files."""
    import re
    pattern = re.compile(r'(href|src)=(\"|\')(.*?)/?index\.html(?=[\"\'])', re.IGNORECASE)
    for path in Path(root_dir).rglob('*.htm*'):
        text = path.read_text(encoding='utf-8')

        def repl(match):
            url = match.group(3)
            if url and not url.endswith('/'):
                url += '/'
            elif url == '':
                url = './'
            return f"{match.group(1)}={match.group(2)}{url}"

        new_text = pattern.sub(repl, text)
        if new_text != text:
            path.write_text(new_text, encoding='utf-8')


def capture_screenshot(url, theme_dir):
    """Generate ``screenshot.png`` for the theme using html2image."""
    output_dir = Path(theme_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        _patch_html2image_py38()
        from html2image import Html2Image
        hti = Html2Image(output_path=str(output_dir), disable_logging=True)
        hti.screenshot(url=url, save_as="screenshot.png")
    except Exception as e:
        print(f"Could not capture screenshot: {e}")
        fallback = Path(__file__).parent / "theme_template" / "screenshot.png"
        try:
            shutil.copy(fallback, output_dir / "screenshot.png")
        except Exception as copy_error:
            print(f"Could not copy fallback screenshot: {copy_error}")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="enrocador Web - Convert websites into static WordPress themes"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    dl = sub.add_parser("download", help="Download a website")
    dl.add_argument("url", help="URL to download")
    dl.add_argument("output", help="Directory to store the download")
    dl.add_argument("--user-agent", default=None, help="Custom User-Agent")
    dl.add_argument("--depth", type=int, help="Maximum crawl depth")
    dl.add_argument("--exclude", nargs="*", help="Domains to exclude")
    dl.add_argument(
        "--sanitize",
        action="store_true",
        help="Sanitize file names (no effect when using pywebcopy)",
    )
    dl.add_argument("--theme-name", help="Name for the generated theme")

    pkg = sub.add_parser("package", help="Compress a downloaded theme directory")
    pkg.add_argument("path", help="Directory with the theme ready to zip")
    pkg.add_argument(
        "--output",
        help="Path to the resulting ZIP (defaults to <path>.zip)",
        default=None,
    )

    return parser.parse_args(argv)


def main(argv=None):
    # If called without subcommand, default to 'download'
    if argv is None:
        argv = sys.argv[1:]
    if argv and not argv[0].startswith('-') and argv[0] not in {'download', 'package'}:
        argv = ['download'] + argv
    args = parse_args(argv)

    if args.command == "download":
        try:
            download_site(
                args.url,
                Path(args.output),
                args.user_agent,
                args.depth,
                args.exclude,
                sanitize=args.sanitize,
                theme_name=args.theme_name,
            )
        except Exception as e:
            print("Error during download", e)
            sys.exit(1)
        return

    if args.command == "package":
        target = Path(args.path)
        zip_out = Path(args.output) if args.output else target.with_suffix(".zip")
        zip_path = shutil.make_archive(str(zip_out.with_suffix("")), "zip", target)
        print(f"Theme archived at {zip_path}")


if __name__ == "__main__":
    main()
