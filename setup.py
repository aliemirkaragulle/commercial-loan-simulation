from setuptools import setup, find_packages

setup(
    name="loan_calculators",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "streamlit",
        "plotly",
        "pandas",
        "numpy",
        "holidays",
        "python-dateutil"
    ]
)
