import argparse
import os
import shutil
import sys
from pathlib import Path
from urllib.parse import urlparse

from pywebcopy import configs


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
    crawler.get(url)
    crawler.save_complete()

    host = urlparse(url).hostname or "site"
    src_root = Path(conf.get_project_folder()) / host
    if src_root.exists():
        for item in src_root.iterdir():
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


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Enriscador Web - Convert websites into static WordPress themes"
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
