from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="qase-victoria-metrics",
    version="1.0.0",
    description="A Qase-Pytest plugin to extract test results and push metrics to Victoria Metrics",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Didit Setiawan",
    author_email="didit@pintu.co.id",
    url="https://github.com/dsetiawan230294/qase-victoria-metrics",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pytest>=8.3.5",
        "qase-pytest>=6.2.0",
        "allure-pytest>=2.13.5",
    ],
    classifiers=[
        "Framework :: Pytest",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={"pytest11": ["pytest_metrics = pytest_metrics.metrics"]},
    python_requires=">=3.10",
    keywords=["pytest", "qase", "metrics", "victoria-metrics", "pytest-plugin"],
    license="MIT",
    include_package_data=True,
)
