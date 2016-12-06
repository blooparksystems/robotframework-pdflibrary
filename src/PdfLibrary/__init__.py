import os
import uuid
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from cStringIO import StringIO
from pydmtx import DataMatrix
from PIL import Image as Img
from wand.image import Image


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
execfile(os.path.join(THIS_DIR, 'version.py'))

__version__ = VERSION


class PdfLibrary(object):
    
    ROBOT_LIBRARY_VERSION = VERSION
    ROBOT_LIBRARY_SCOPE = 'GLOBAL'
    
    def create_profile(self, path):
        from selenium import webdriver
        fp = webdriver.FirefoxProfile()
        fp.set_preference("browser.download.folderList", 2)
        fp.set_preference("browser.download.manager.showWhenStarting", False)
        fp.set_preference("browser.download.dir", path)
        fp.set_preference("browser.helperApps.neverAsk.saveToDisk", 'application/pdf')
        fp.set_preference("pdfjs.disabled", True)
        fp.update_preferences()
        return fp.path

    def pdf_should_contain_value(self, path, value):
        rsrcmgr = PDFResourceManager()
        laparams = LAParams()
        codec = 'utf-8'

        retstr = StringIO()
        device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)

        fp = file(path, 'rb')
        for page in PDFPage.get_pages(fp, set(), maxpages=0, password="", caching=True, check_extractable=True):
            interpreter.process_page(page)
        fp.close()
        device.close()
        content = retstr.getvalue()
        retstr.close()
        if not value.encode('utf-8') in content:
            message = "PDF '%s' should have contained text '%s' but did not" % (path, value)
            raise AssertionError(message)

    def pdf_should_not_contain_value(self, path, value):
        rsrcmgr = PDFResourceManager()
        laparams = LAParams()
        codec = 'utf-8'

        retstr = StringIO()
        device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)

        fp = file(path, 'rb')
        for page in PDFPage.get_pages(fp, set(), maxpages=0, password="", caching=True, check_extractable=True):
            interpreter.process_page(page)
        fp.close()
        device.close()
        content = retstr.getvalue()
        retstr.close()
        if value.encode('utf-8') in content:
            message = "PDF '%s' shouldn't have contained text '%s' but it has" % (path, value)
            raise AssertionError(message)

    def pdf_should_contain_datamatrix_with(self, path, btext):
        path_list = path.split('/')
        path_list.pop()
        image_folder = '/'.join(path_list)
        uuid_set = str(uuid.uuid4().fields[-1])[:5]
        try:
            with Image(filename=path, resolution=200) as img:
                img.compression_quality = 80
                img.save(filename="%s/temp%s.jpg" % (image_folder, uuid_set))
        except Exception, err:
            message = "PDF '%s' could not be processed" % (path)
            raise AssertionError(message)

        barcode_value = False
        for file in os.listdir(image_folder):
            image_path = os.path.join(image_folder, file)
            if os.path.isfile(image_path) and image_path.endswith('.jpg'):
                dm_read = DataMatrix()
                img = Img.open(image_path)
                content = dm_read.decode(img.size[0], img.size[1], buffer(img.tostring()))
                if content.startswith(btext):
                    barcode_value = True
                break

        for file in os.listdir(image_folder):
            image_path = os.path.join(image_folder, file)
            if os.path.isfile(image_path) and image_path.endswith('.jpg'):
                os.remove(image_path)

        if not barcode_value:
            message = "PDF '%s' should have contained datamatrix with value '%s' but did not" % (path, btext)
            raise AssertionError(message)
