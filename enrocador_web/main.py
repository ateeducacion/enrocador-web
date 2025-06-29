import argparse
import os
import re
import shutil
import sys
import locale
from typing import Iterable

if not (3, 8) <= sys.version_info < (3, 13):
    sys.exit("ERROR: enrocador Web requires Python >=3.8 and <3.13")

# Ensure UTF-8 locale so file operations don't fail on systems with ASCII locale
if sys.getfilesystemencoding().lower() == "ascii":
    try:
        locale.setlocale(locale.LC_ALL, "C.UTF-8")
    except locale.Error:
        pass
    try:
        if not hasattr(sys, "setdefaultencoding"):
            import importlib
            importlib.reload(sys)
        if hasattr(sys, "setdefaultencoding"):
            sys.setdefaultencoding("utf-8")
    except Exception:
        pass

from pathlib import Path
from urllib.parse import urlparse

from pywebcopy import configs
import threading
import time


def _patch_html2image_py38():
    """Modify html2image for Python 3.8 compatibility if installed."""
    import importlib
    import importlib.util
    from pathlib import Path

    spec = importlib.util.find_spec("html2image")
    if not spec or not spec.origin:
        return

    pkg_dir = Path(spec.origin).resolve().parent
    candidates = [Path(spec.origin), pkg_dir / "html2image.py"]
    changed = False

    for path in candidates:
        if not path.exists():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue

        if "list[str]" not in text:
            continue

        if "from typing import List" not in text:
            lines = text.splitlines()
            last_import = 0
            for i, line in enumerate(lines):
                if line.startswith("import") or line.startswith("from"):
                    last_import = i
            lines.insert(last_import + 1, "from typing import List")
            text = "\n".join(lines)

        text = text.replace("list[str]", "List[str]")
        try:
            path.write_text(text, encoding="utf-8")
            changed = True
        except OSError:
            continue

    if changed:
        importlib.invalidate_caches()
        importlib.reload(importlib.import_module("html2image"))


def _patch_pywebcopy_unicode():
    """Relax pywebcopy decoding to avoid ASCII errors."""
    import importlib
    import importlib.util
    from pathlib import Path
    spec = importlib.util.find_spec("pywebcopy")
    if not spec or not spec.origin:
        return
    pkg_dir = Path(spec.origin).resolve().parent
    elements = pkg_dir / "elements.py"
    urls = pkg_dir / "urls.py"
    changed = False

    if elements.exists():
        try:
            text = elements.read_text(encoding="utf-8")
        except OSError:
            text = ""
        new_text = text.replace(".decode(encoding)", ".decode(encoding, errors='ignore')")
        if new_text != text:
            try:
                elements.write_text(new_text, encoding="utf-8")
                changed = True
            except OSError:
                pass

    if urls.exists():
        try:
            text = urls.read_text(encoding="utf-8")
        except OSError:
            text = ""
        if "_implicit_encoding = 'ascii'" in text:
            text = text.replace("_implicit_encoding = 'ascii'", "_implicit_encoding = 'utf-8'")
            try:
                urls.write_text(text, encoding="utf-8")
                changed = True
            except OSError:
                pass

    if changed:
        importlib.invalidate_caches()
        importlib.reload(importlib.import_module("pywebcopy.urls"))
        importlib.reload(importlib.import_module("pywebcopy.elements"))


def _spinner(message, stop_event):
    """Simple CLI spinner shown while stop_event isn't set."""
    chars = ['|', '/', '-', '\\']
    idx = 0
    while not stop_event.is_set():
        print(f"\r{message} {chars[idx % len(chars)]}", end='', flush=True)
        time.sleep(0.1)
        idx += 1
    print(f"\r{message} listo.      ")


def sanitize_folder_name(name: str) -> str:
    """Return a safe folder name (lowercase, trimmed, no invalid chars)."""
    name = name.strip().lower()
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r"[\\/:*?\"<>|]", "", name)
    name = re.sub(r"[^a-z0-9._-]", "", name)
    return name or "theme"


def safe_listdir(path: Path) -> Iterable[Path]:
    """List directory entries even on systems with non-UTF8 locales."""
    try:
        return list(path.iterdir())
    except UnicodeDecodeError:
        entries = []
        for name in os.listdir(os.fsencode(str(path))):
            try:
                decoded = os.fsdecode(name)
            except Exception:
                continue
            entries.append(path / decoded)
        return entries


def safe_rglob(root: Path, pattern: str) -> Iterable[Path]:
    """Yield files matching pattern without decoding errors."""
    import fnmatch
    root_b = os.fsencode(str(root))
    for dirpath_b, dirnames_b, filenames_b in os.walk(root_b):
        dirpath = Path(os.fsdecode(dirpath_b))
        for fname_b in filenames_b:
            name = os.fsdecode(fname_b)
            if fnmatch.fnmatch(name, pattern):
                yield dirpath / name

def download_site(url, dest_dir, user_agent=None, depth=None, exclude=None, sanitize=False, theme_name=None):
    """Download site using pywebcopy and generate theme files."""
    _patch_pywebcopy_unicode()
    orig = Path(dest_dir).resolve()
    dest_dir = orig.parent / sanitize_folder_name(orig.name)
    if dest_dir != orig and orig.exists() and not dest_dir.exists():
        try:
            orig.rename(dest_dir)
        except OSError:
            pass
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
        entries = safe_listdir(source)
        for item in entries:
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
            text = src.read_text(encoding="utf-8")
            text = text.replace("{{THEME_NAME}}", theme_name)
            text = text.replace("{{URL}}", url)
            dst.write_text(text, encoding="utf-8")
        else:
            shutil.copy(src, dst)


def convert_html_to_utf8(root_dir):
    """Re-encode all HTML files inside ``root_dir`` to UTF-8."""
    for path in safe_rglob(Path(root_dir), '*.htm*'):
        try:
            data = path.read_bytes()
        except (UnicodeDecodeError, OSError):
            continue
        for enc in ('utf-8', 'latin-1'):
            try:
                text = data.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        else:
            text = data.decode('utf-8', errors='replace')
        try:
            path.write_text(text, encoding='utf-8')
        except (UnicodeDecodeError, OSError):
            continue


def strip_index_from_urls(root_dir):
    """Remove 'index.html' from href/src attributes in HTML files."""
    import re
    pattern = re.compile(r'(href|src)=(\"|\')(.*?)/?index\.html(?=[\"\'])', re.IGNORECASE)
    for path in safe_rglob(Path(root_dir), '*.htm*'):
        try:
            text = path.read_text(encoding='utf-8')
        except (UnicodeDecodeError, OSError):
            continue

        def repl(match):
            url = match.group(3)
            if url and not url.endswith('/'):
                url += '/'
            elif url == '':
                url = './'
            return f"{match.group(1)}={match.group(2)}{url}"

        new_text = pattern.sub(repl, text)
        if new_text != text:
            try:
                path.write_text(new_text, encoding='utf-8')
            except (UnicodeDecodeError, OSError):
                pass


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
            out_path = Path(args.output)
            out_path = out_path.parent / sanitize_folder_name(out_path.name)

            theme = args.theme_name
            if theme is None:
                theme = sanitize_folder_name(out_path.name)
            else:
                theme = sanitize_folder_name(theme)

            download_site(
                args.url,
                out_path,
                args.user_agent,
                args.depth,
                args.exclude,
                sanitize=args.sanitize,
                theme_name=theme,
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
