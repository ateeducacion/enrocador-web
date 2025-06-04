import argparse
import subprocess
import os
import shutil
import sys
from pathlib import Path

def download_site(url, dest_dir, user_agent=None, depth=None, exclude=None):
    """Download site using wget."""
    cmd = [
        "wget",
        "--mirror",             # recursive download
        "--convert-links",      # convert links for offline use
        "--page-requisites",    # download all assets
        "--adjust-extension",
        "--no-parent",
    ]
    if depth:
        cmd += ["--level", str(depth)]
    if user_agent:
        cmd += ["--user-agent", user_agent]
    if exclude:
        cmd += ["--exclude-domains", ",".join(exclude)]
    cmd += ["-P", str(dest_dir), url]

    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=True)


def copy_template_files(theme_dir):
    """Copy base PHP template files into the theme."""
    template_dir = Path(__file__).parent / "templates" / "theme"
    for fname in os.listdir(template_dir):
        shutil.copy(template_dir / fname, theme_dir)


def create_wp_theme(theme_name, source_dir, output_dir, url=""):
    """Create WordPress theme from downloaded site."""
    theme_dir = Path(output_dir)
    site_dir = theme_dir / "site"
    if theme_dir.exists():
        shutil.rmtree(theme_dir)
    shutil.copytree(source_dir, site_dir)

    copy_template_files(theme_dir)

    style_css = f"""/*
Theme Name: {theme_name}
Description: Static site generated from {url}
Version: 1.0
*/
"""
    with open(theme_dir / "style.css", "w") as fh:
        fh.write(style_css)

    print(f"WordPress theme created at {theme_dir}")


def parse_args():
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

    pkg = sub.add_parser("package", help="Create WordPress theme from download")
    pkg.add_argument("source", help="Directory with the downloaded site")
    pkg.add_argument(
        "output",
        help="Directory where the WordPress theme will be generated (e.g. themes/mytheme)",
    )
    pkg.add_argument("--theme-name", default=None, help="Name of the WordPress theme")
    pkg.add_argument("--url", help="Original site URL", default="")

    return parser.parse_args()


def main():
    args = parse_args()

    if args.command == "download":
        try:
            download_site(args.url, Path(args.output), args.user_agent, args.depth, args.exclude)
        except subprocess.CalledProcessError as e:
            print("Error during download", e)
            sys.exit(1)
        return

    if args.command == "package":
        theme_name = args.theme_name or Path(args.output).name
        create_wp_theme(theme_name, args.source, args.output, args.url)
        zip_path = shutil.make_archive(args.output, "zip", args.output)
        print(f"Theme archived at {zip_path}")



if __name__ == "__main__":
    main()
