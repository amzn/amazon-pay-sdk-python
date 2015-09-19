import re
import json
import xml.etree.ElementTree as et
from collections import defaultdict


class PaymentResponse(object):

    """Base class for all OffAmazonPayments responses

    Parameters
    ----------
    xml : string
        XML response from Amazon.


    Properties
    ----------
    root : string
        Root XML node.

    ns : string
        XML namespace.

    success : boolean
        Success or failure of the API call.

    response : Response
        Holds the response type for the API call.

    xml : string
        XML response from Amazon.
    """

    def __init__(self, xml):
        """Initialize response"""
        self.success = True
        self._xml = xml
        try:
            self._root = et.fromstring(xml)
            self._ns = self._namespace(self._root)
            self._response_type = self._root.tag.replace(self._ns, '')
        except:
            raise ValueError('Invalid XML.')

        """There is a bug where 'eu' endpoint returns ErrorResponse XML node
        'RequestID' with capital 'ID'. 'na' endpoint returns 'RequestId'
        """
        try:
            if self._root.find('.//{0}RequestId'.format(self._ns)) is None:
                self.request_id = self._root.find(
                    './/{0}RequestID'.format(self._ns)).text
            else:
                self.request_id = self._root.find(
                    './/{0}RequestId'.format(self._ns)).text
        except:
            self.request_id = None

    def _namespace(self, element):
        """Get XML namespace"""
        ns = re.match('\{.*\}', element.tag)
        return ns.group(0) if ns else ''

    def to_xml(self):
        """Return XML"""
        return self._xml

    def to_json(self):
        """Return JSON"""
        return json.dumps(self._etree_to_dict(self._root))

    def to_dict(self):
        """Return Dictionary"""
        return self._etree_to_dict(self._root)

    def _etree_to_dict(self, t):
        """Convert XML to Dictionary"""
        d = {t.tag.replace(self._ns, ''): {} if t.attrib else None}
        children = list(t)
        if children:
            dd = defaultdict(list)
            for dc in map(self._etree_to_dict, children):
                for k, v in dc.items():
                    dd[k].append(v)
            d = {t.tag.replace(self._ns, ''): dict(
                (k, v[0] if len(v) == 1 else v)
                for k, v in dd.items()
            )}
        if t.attrib:
            d[t.tag.replace(self._ns, '')].update(('@' + k, v)
                                                  for k, v in t.attrib.items())
        if t.text:
            text = t.text.strip()
            if children or t.attrib:
                if text:
                    d[t.tag.replace(self._ns, '')]['#text'] = text
            else:
                d[t.tag.replace(self._ns, '')] = text
        return d


class PaymentErrorResponse(PaymentResponse):

    """Error response subclass"""

    def __init__(self, xml):

        super(PaymentErrorResponse, self).__init__(xml)
        self.success = False
