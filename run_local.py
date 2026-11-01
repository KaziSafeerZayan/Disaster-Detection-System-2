"""Launch the dashboard; interactive Earth Engine setup lives in authenticate.bat."""
import os
import sys
from pathlib import Path

from streamlit.web import cli


def main():
    root = Path(__file__).resolve().parent
    os.chdir(root)
    sys.path.insert(0, str(root))
    if os.getenv("GEE_PROJECT_ID"):
        import config
        config.GEE_PROJECT_ID = os.environ["GEE_PROJECT_ID"]
    sys.argv = ["streamlit", "run", str(root / "app" / "app.py"), *sys.argv[1:]]
    return cli.main()


if __name__ == "__main__":
    sys.exit(main())
