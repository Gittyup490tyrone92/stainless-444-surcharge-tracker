#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="stainless-444-surcharge-tracker",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Track and analyze stainless steel 444 alloy surcharges",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Gittyup490tyrone92/stainless-444-surcharge-tracker",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "ss444_collect=src.collect_data:collect_and_save_data",
            "ss444_visualize=src.visualize:generate_all_visualizations",
            "ss444_report=src.generate_report:generate_all_reports",
            "ss444_update=src.monthly_update:run_monthly_update",
        ],
    },
    include_package_data=True,
)
