"""Setup script for BSW AUTOSAR Spec Checker."""
from setuptools import setup, find_packages

setup(
    name="bsw-checker",
    version="1.0.0",
    description="BSW AUTOSAR Spec Verification Tool",
    packages=find_packages(),
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "bsw-checker=bsw_checker.main:main",
        ],
    },
)
