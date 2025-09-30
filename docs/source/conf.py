# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
sys.path.insert(0, os.path.abspath('../../src'))
sys.path.insert(0, os.path.abspath('.'))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'HW_CAM'
copyright = '2025, Pakfat50'
author = 'Pakfat50'
release = '4.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'myst_parser',
    'japanesesupport',
    'sphinxcontrib.plantuml',
    'sphinx.ext.mathjax'
    ]

plantuml_jar = "plantuml-mit-1.2025.7.jar"
plantuml_java_options=" ".join([
             "-DPLANTUML_LIMIT_SIZE=8192",
             "-Djava.awt.headless=true"
])

# sphinxcontrib-plantumlのオプション
plantuml = f"java {plantuml_java_options} -jar {plantuml_jar}"
plantuml_output_format="svg_img"
plantuml_latex_output_format="png"
# plantuml_epstopdf="epstopdf", # TeXLive
# plantuml_cache_path="_plantuml" ,

templates_path = ['_templates']
exclude_patterns = []

language = 'ja'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
