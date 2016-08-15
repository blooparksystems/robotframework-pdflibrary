import os
from .wabr import  WAUtils, WABarcodeReader, WABarcode
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from cStringIO import StringIO


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

    def pdf_should_contain_barcode_with(self, path, btype, btext):
        WAUtils.SetStdoutUTF8()
        serverUrl = ""  #  Your server URL (default is wanr.inliteresearch.com)
        auth = ""       #  Your Authorization code or  WABR_AUTH environment variable is used
        reader = WABarcodeReader(serverUrl, auth)
        barcode_founded = False
        barcodes = reader.Read(path)
        for n in range(0, len(barcodes)):
            barcode = barcodes[n]
            if barcode.Type == btype and barcode.Text.startswith(btext):
                barcode_founded = True
                break
        if not barcode_founded:
            message = "PDF '%s' should have contained barcode type '%s' and text '%s' but did not" % (path, btype, btext)
            raise AssertionError(message)
