"""The calciner's reserved envelope, as text. Builds no geometry.

    python3 -m geometry.calciner
"""

from .ilc_spec import ilc_report


if __name__ == "__main__":
    print(ilc_report())
