from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="erpnext_amex",
    version="0.0.1",
    author="Your Company",
    author_email="support@yourcompany.com",
    description="AMEX expense classification and import system for ERPNext",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/glamcor/erpnext-amex",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.10",
    install_requires=[
        "frappe",
        "erpnext",
        "pandas>=2.0.0",
        "boto3>=1.26.0",
        "requests>=2.28.0",
    ],
    include_package_data=True,
    zip_safe=False,
)

