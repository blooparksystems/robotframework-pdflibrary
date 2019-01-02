#!/usr/bin/env python

from os.path import join, dirname

execfile(join(dirname(__file__), 'src', 'PdfLibrary', 'version.py'))

from distutils.core import setup

CLASSIFIERS = """
Programming Language :: Python
Topic :: Software Development :: Testing
"""[1:-1]

long_description=open(join(dirname(__file__), 'README.md',)).read()

setup(
  name             = 'robotframework-pdflibrary',
  version          = VERSION,
  description      = 'Robot Framework PDF Inspect Library',
  long_description = long_description,
  author           = 'bloopark systems GmbH & Co. KG',
  author_email     = 'info@bloopark.com',
  url              = 'https://github.com/blooparksystems/robotframework-pdflibrary',
  license          = 'Apache License 2.0',
  keywords         = 'robotframework checking testautomation pdf reports',
  platforms        = 'any',
  zip_safe         = False,
  classifiers      = CLASSIFIERS.splitlines(),
  package_dir      = {'' : 'src'},
  install_requires = ['robotframework', 'pdfminer', 'pylibdmtx', 'wand'],
  packages         = ['PdfLibrary'],
)
