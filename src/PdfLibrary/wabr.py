import sys
import base64
import os.path
from xml.dom.minidom import parse, parseString
#version 2 and 3 renaming
if sys.version_info < (3, 0):
    import httplib
else:
    import http.client

import mimetypes
import codecs
import string
import random
import io


class WABarcodeReader(object):
    validtypes = "1d,Code39,Code128,Code93,Codabar,Ucc128,Interleaved2of5," + "Ean13,Ean8,Upca,Upce," + "2d,Pdf417,DataMatrix,QR," + "DrvLic," + "postal,imb,bpo,aust,sing,postnet," + "Code39basic,Patch"
    version = "1.0.0"

    def __init__(self, serverUrl="", authorization=""):
        if (serverUrl != ""):
            self._serverUrl = serverUrl;
        else:
            self._serverUrl = "https://wabr.inliteresearch.com";
        self.__authorization = authorization
        self.types = ""
        self.dirs = ""
        self.tbr = 0


    def Read(self, image_source, types="", directions="", tbr_code=0):
        WAUtils.printDiag("\n================= PROCESSING: " + WAUtils._signature(image_source))
        names = image_source.split('|')
        urls = []
        files = []
        images = []
        for n in range(0, len(names)):
            name1 = names[n]
            name = name1.strip()
            s = name.lower()
            #  string s1 = s1.replace("\r\n", "\r");
            #  s1 = s1.replace("\r", "");
            if s.startswith("http://") or s.startswith("https://") or s.startswith("ftp://") or s.startswith("file://"):
                urls.append(name)
            elif os.path.isfile(name):
                files.append(name)
            elif name.startswith("data:") or WAUtils._isBase64(name):
                images.append(name)
            else:
                raise Exception("Invalid image source: " + name[0:min(len(name), 256)])
        return self.__ReadLocal(self, urls, files, images, types, directions, tbr_code)

    @staticmethod
    def __ParseResponse(txtResponse):
        barcodes = []
        txtResponse = txtResponse.strip() 
        if (len(txtResponse) < 6): return barcodes
        if txtResponse[0] == ('<') or txtResponse[1] == ('<'):
            doc = parseString(txtResponse)
            nodeResults = WAUtils._selectNode(doc, "Results")
            if (nodeResults == None): return barcodes;
            nodeBarcodes = WAUtils._selectNode(nodeResults, "Barcodes")
            if (nodeBarcodes == None): return barcodes;
                    
            for nodeBarcode in  WAUtils._selectNodes(nodeBarcodes, "Barcode"):
                barcode = WABarcode()
                    # XML text is encoded inside of Text node. Parser decoded text
                str = WAUtils._nodeValue(nodeBarcode, "Text", "")
                barcode.Text = str;   
                barcode.Left = WAUtils._nodeValueInt(nodeBarcode, "Left", 0)
                barcode.Right = WAUtils._nodeValueInt(nodeBarcode, "Right", 0)
                barcode.Top = WAUtils._nodeValueInt(nodeBarcode, "Top", 0)
                barcode.Bottom = WAUtils._nodeValueInt(nodeBarcode, "Bottom", 0)
                barcode.Length = WAUtils._nodeValueInt(nodeBarcode, "Length", 0)
                barcode.Data = WAUtils._decodeBase64(WAUtils._nodeValue(nodeBarcode, "Data", ""))
                barcode.Page = WAUtils._nodeValueInt(nodeBarcode, "Page", 0)
                barcode.File = WAUtils._nodeValue(nodeBarcode, "File", "")
                meta = WAUtils._nodeValueXml(nodeBarcode, "Meta")
                if (meta != None):
                    barcode.Meta = meta.toxml()
                barcode.Type = WAUtils._nodeValue(nodeBarcode, "Type", "")
                barcode.Rotation = WAUtils._nodeValue(nodeBarcode, "Rotation", "")

                barcode.Values = {}
                docValues =  WAUtils._nodeValueXml(nodeBarcode, "Values")
                if (docValues != None):
                  values =  WAUtils._selectNode(WAUtils._selectNode(nodeBarcode, ""), "")
                  if (values != None):
                    for node in WAUtils._selectNodes(values, ""):
                        barcode.Values[node.nodeName] = WAUtils._nodeValue(values, node.nodeName, "")

                barcodes.append(barcode)
        return barcodes

    @staticmethod
    def __ReadLocal (self, urls, files, images, types_, dirs_, tbr_):
        server = self._serverUrl
        queries = {}
        url = ""
        for n in range(0, len(urls)):
            s = urls[n]
            if url != "":
                url += "|"
            url += s
        if url != "":
            queries["url"] = url

        image = ""
        for n in range(0, len(images)):
            s = images[n]
            if image != "":
                image += "|"
            image += s
        if image != "":
            queries["image"] = image

        queries["format"] = "xml"
        queries["fields"] = "meta"
        if types_ != "":
            queries["types"] = types_
        if dirs_ != "":
            queries["options"]  = dirs_
        if tbr_ != 0:
            queries["tbr"] =  tbr_.__str__()
        serverUrl = server + "/barcodes"
        barcodes = []
        txtResponse = ""
        txtResponse = _WAHttpRequest._ExecRequest(serverUrl, self.__authorization, files, queries)
        barcodes = WABarcodeReader.__ParseResponse(txtResponse)
        return barcodes


class WABarcode(object):

    def __init__(self):
        self.Text = ""
        self.Data = []
        self.Type = ""
        self.Page = 0
        self.Top = 0
        self.Left = 0
        self.Right = 0
        self.Bottom = 0
        self.File = ""
        self.Rotation = ""
        self.Meta = ""
        self.Values = {}


class _WAHttpRequest(object):

    @staticmethod
    def __ExecRequestLocal(host, selector, isHTTPS, auth, files, queries):
        content_type, body = _WAHttpRequest.__GetMultipartFormData(queries, files)
        env_auth = 'WABR_AUTH' 
        if (auth == "" and env_auth in os.environ):
            auth = os.environ[env_auth]
        if sys.version_info < (3, 0):
            if (isHTTPS):
                h = httplib.HTTPSConnection(host)
            else:
                h = httplib.HTTPConnection(host)
        else:
            if (isHTTPS):
                h = http.client.HTTPSConnection(host)
            else:
                h = http.client.HTTPConnection(host)
        headers = {
            'Authorization': auth,
            'Content-Type': content_type,
            'Content-length': str(len(body))
            }
          # Encode  body since it might contain non-ascii character
        h.request('POST', selector, body, headers)
        res = h.getresponse()
        return res
        status = res.status
        reason = res.reason
        response = res.read().decode("utf-8")
        if status != 200:
             raise Exception("HttpError " + str(status) + ". "  + reason + ".  " + response)
        return response

    @staticmethod
    def _ExecRequest(serverUrl, auth, files, queries):
        arr = serverUrl.split("/")
        host = ""
        selector = ""
        isHTTPS = False
        for s in arr:
           if (s == ""): continue
           if (s == "http:"): continue
           if (s == "https:"): 
               isHTTPS = True
               continue
           if (host == ""):
               host = s
           else:
               selector = selector + "/" + s
        res = _WAHttpRequest.__ExecRequestLocal(host, selector, isHTTPS, auth, files, queries)
        if (res.status == 301) and (res.reason != "OK") and (isHTTPS == False):  # case of possible HTTP to HTTPS redirect
            res = _WAHttpRequest.__ExecRequestLocal(host, selector, True, auth, files, queries)
        response = res.read().decode("utf-8")
        if res.status != 200 and not (res.status == 301 and res.reason == "OK"):
             raise Exception("HttpError " + str(res.status) + ". "  + res.reason + ".  " + response)
        return response

    @staticmethod
    def __GetMultipartFormData(queries, files):
        form = _MultiPartForm()
        for key in queries.keys():
            form._add_field(key, queries[key])

        for filepath in files:
            form._add_file("file", os.path.basename(filepath),
                fileHandle=codecs.open(filepath, "rb"))

        body = form._get_binary().getvalue();
        content_type = form._get_content_type()
        return content_type, body


class WAUtils(object):
    bShowDiag = False

    @staticmethod
    def printDiag(var):
        if (WAUtils.bShowDiag):
            WAUtils.printUTF8(var + "\n")

    @staticmethod
    def _signature(image):
       if (image == ""): return "";
       if (image.startswith("data:image")):
          ind = image.find(":::")
          s = image[0:40] + "..."
          if (ind > 4):
            s  = s + image[ind:-1]
       else:
          s = image[0:min(len(image), 80)]
       return " [" + s + "] "
 
    @staticmethod
    def _nodeValue(nodeParent, name, defValue):
        sout = defValue
        node = WAUtils._selectNode(nodeParent, name)
        if (node != None):
            nodeText = WAUtils._selectNode(node, "#text")
            if (nodeText != None):
               sout = nodeText.nodeValue
        return sout

    @staticmethod
    def _selectNode(nodeParent, name):
        if (nodeParent == None) : return None
        for node in nodeParent.childNodes:
            if (node.nodeName == name  or (node.nodeName[0] != "#" and name == "")) : return node
        return None

    @staticmethod
    def _selectNodes(nodeParent, name):
        nodes = []
        if (nodeParent == None) : return nodes
        for node in nodeParent.childNodes:
            if (node.nodeName == name or (node.nodeName[0] != "#" and name == "")) : nodes.append(node)
        return nodes

    @staticmethod
    def _nodeValueInt(nodeParent, name, defValue):
        nout = defValue
        sout =  WAUtils._nodeValue(nodeParent, name, "")
        if sout != "":
            nout = int(sout)
        return nout

    @staticmethod
    def _decodeBase64(strBase64):
        try:
            arr = base64.b64decode(strBase64)
            return arr;
        except:
            return None

    @staticmethod
    def fileToBase64(file):
        image_file = open(file, "rb")
        bBase64 = base64.b64encode(image_file.read())
        image_file.close()
        if sys.version_info < (3, 0):
            strBase64 = str(bBase64)
        else:
            strBase64 = str(bBase64, 'ASCII')
        ext = os.path.splitext(file)[1][1:].strip() 
        strBase64 = "data:image/" + ext + ";base64," + strBase64
        # Optionally attach suffix with reference file name to be placed in Barcode.File property
        strBase64 = strBase64 + ":::" + os.path.basename(file)
        return strBase64

    @staticmethod
    def _nodeValueXml(nodeParent, name):
        sout = ""
        node = WAUtils._selectNode(nodeParent, name)
        if node != None:
            sout = node.toxml()
        if (sout == ""): return None
        try:
            doc = parseString(sout)
            return doc
        except:
            return None

    @staticmethod
    def _isBase64(value): # IsBase64String
        v = value
        # replace formating characters
        v = v.replace("\r\n", "")
        v = v.replace("\r", "")
        # remove reference file name, if  present
        ind = v.find(":::")
        if ind > 0:
           v = v[0:ind]
        if v == None or len(v) == 0 or (len(v) % 4) != 0:
            return False
        index = len(v) - 1
        if v[index] == '=':
            index -= 1
        if v[index] == '=':
            index -= 1
        i = 0
        while i <= index:
            if WAUtils.__IsInvalidBase64char(v[i]):
                return False
            i += 1
        return True


    @staticmethod
    def __IsInvalidBase64char(value):
        intValue = ord(value)
        if intValue >= 48 and intValue <= 57:
            return False
        if intValue >= 65 and intValue <= 90:
            return False
        if intValue >= 97 and intValue <= 122:
            return False
        return intValue != 43 and intValue != 47

    #method is required if file names or barcode data use non-ascii characters
    @staticmethod
    def SetStdoutUTF8():
      print ("Content-Type: text/plain\n")
      if hasattr(sys.stdout, 'buffer'):
         sys.stdout.buffer.write(codecs.BOM_UTF8)
      else:
         reload(sys)
         enc1  = sys.getdefaultencoding()
         sys.setdefaultencoding("utf-8")
         enc2  = sys.getdefaultencoding()
         sys.stdout.write('\xef\xbb\xbf')  # not defined in 2.2 codecs.BOM_UTF8
    
    #method required if print string in DOS
    @staticmethod
    def printUTF8(var):
      if hasattr(sys.stdout, 'buffer'):
        sys.stdout.buffer.write(var.encode('utf8'))
        print("")
      else:
        sys.stdout.write(var.encode('utf8'))
        print("")


class _MultiPartForm(object):
    """Accumulate the data to be used when posting a form."""

    def __init__(self):
        self.form_fields = []
        self.files = []
        # self.boundary = mimetools.choose_boundary()  # not in Python.3
        _BOUNDARY_CHARS = string.digits + string.ascii_letters
        self.boundary = ''.join(random.choice(_BOUNDARY_CHARS) for i in range(30))

        return

    def _get_content_type(self):
        return 'multipart/form-data; boundary=%s' % self.boundary

    def _add_field(self, name, value):
        """Add a simple field to the form data."""
        self.form_fields.append((name, value))
        return

    def _add_file(self, fieldname, filename, fileHandle, mimetype=None):
        """Add a file to be uploaded."""
        body = fileHandle.read()
        if mimetype is None:
            mimetype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        self.files.append((fieldname, filename, mimetype, body))
        return

    def __write_string(self, binary, str):
        if sys.version_info < (3, 0):
            binary.write(str)
        else:
            binary.write(bytes(str, 'UTF-8'))

    def _get_binary(self):
        """Return a binary buffer containing the form data, including attached files."""
        part_boundary = '--' + self.boundary

        binary = io.BytesIO()
        needsCLRF = False
        # Add the form fields
        for name, value in self.form_fields:
            if needsCLRF:
                self.__write_string(binary, '\r\n')
            needsCLRF = True

            block = [part_boundary,
              'Content-Disposition: form-data; name="%s"' % name,
              '',
              value
            ]
            self.__write_string(binary, '\r\n'.join(block))

        # Add the files to upload
        for field_name, filename, content_type, body in self.files:
            if needsCLRF:
                self.__write_string(binary, '\r\n')
            needsCLRF = True

            block = [part_boundary,
              str('Content-Disposition: file; name="%s"; filename="%s"' % \
              (field_name, filename)),
              'Content-Type: %s' % content_type,
              ''
              ]
            self.__write_string(binary, '\r\n'.join(block))
            self.__write_string(binary, '\r\n')
            binary.write(body)

        # add closing boundary marker,
        self.__write_string(binary, '\r\n--' + self.boundary + '--\r\n')
        return binary
