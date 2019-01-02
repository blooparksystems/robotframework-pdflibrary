# -*- coding: utf-8 -*-
##############################################################################
#
# Odoo, an open source suite of business apps
# This module copyright (C) 2018 bloopark systems (<http://bloopark.de>).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import os
import uuid

from io import StringIO
from subprocess import call

from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.pdfpage import PDFPage

from wand.image import Image
from wand.color import Color

from pylibdmtx import pylibdmtx
from PIL import Image as Img


class PdfDriver(object):

    def __init__(self, path):
        self.path = path

    def extract_pdf_content(self):
        rsrcmgr = PDFResourceManager()
        laparams = LAParams()
        codec = 'utf-8'

        retstr = StringIO()
        device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)

        path_decrypt = self.path.replace('.pdf', '_decrypt.pdf')
        call('qpdf --password=%s --decrypt "%s" "%s"' % (
            '', self.path, path_decrypt
        ), shell=True)

        with open(path_decrypt, 'rb') as fp:
            pages = PDFPage.get_pages(
                fp, set(), maxpages=0, password="",
                caching=True, check_extractable=True
            )
            for page in pages:
                interpreter.process_page(page)
            fp.close()

        device.close()
        content = retstr.getvalue()
        retstr.close()

        os.remove(path_decrypt)

        return content

    def extract_pdf_datamatrix(self):
        uuid_set = str(uuid.uuid4().fields[-1])[:5]
        image_folder = os.path.dirname(self.path)
        image_file = os.path.join(image_folder, 'image%s.png' % uuid_set)

        pages = Image(filename=self.path)
        page = pages.sequence[0]  # Check first page
        with Image(page) as img:
            img.format = 'png'
            img.background_color = Color('white')
            img.alpha_channel = 'remove'
            img.save(filename=image_file)

        datamatrix = pylibdmtx.decode(Img.open(image_file))

        os.remove(image_file)

        return datamatrix and datamatrix[0].data.decode() or False


def pdf_should_contain_value(path, value):
    pdf = PdfDriver(path)
    content = pdf.extract_pdf_content()
    if value not in content:
        raise AssertionError(
            "PDF '%s' should have contained text '%s' but did not" % (
                path, value))


def pdf_should_not_contain_value(path, value):
    pdf = PdfDriver(path)
    content = pdf.extract_pdf_content()
    if value in content:
        raise AssertionError(
            "PDF '%s' shouldn't have contained text '%s' but it has" % (
                path, value))


def pdf_should_contain_datamatrix_with(path, value):
    pdf = PdfDriver(path)
    content = pdf.extract_pdf_datamatrix()
    if not (content and content.startswith(value)):
        raise AssertionError(
            """PDF '%s' should have contained datamatrix with 
            value '%s' but did not.""" % (path, value)
         )
