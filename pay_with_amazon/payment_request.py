try:
    from urllib.parse import urlparse, urlencode
except ImportError:     # Python 2
    from urlparse import urlparse
    from urllib import urlencode

import base64
import datetime
import hashlib
import hmac
import time
from collections import OrderedDict

import requests
from pay_with_amazon.payment_response import (
    PaymentErrorResponse, PaymentResponse
)


class PaymentRequest(object):

    """Parses request, generates signature and parameter string, posts
    request to Amazon, and returns result.
    """

    def __init__(self, params, config):
        """
        Parameters
        ----------
        params : dictionary, required
            Dictionary containing keys passed from the _operation method. Each
            API call fills this dictionary so you shouldn't need to modify this.
            The keys will vary depending on the API call.

        config : dictionary, required
            Dictionary containing configuration information.
            Required keys: mws_access_key, mws_secret_key, api_version,
                merchant_id, mws_endpoint, headers, handle_throttle
        """
        self.success = False
        self.response = None
        self.mws_access_key = config['mws_access_key']
        self.mws_secret_key = config['mws_secret_key']
        self.merchant_id = config['merchant_id']
        self.handle_throttle = config['handle_throttle']

        self._retry_time = 0
        self._params = params
        self._api_version = config['api_version']
        self._mws_endpoint = config['mws_endpoint']
        self._headers = config['headers']
        self._should_throttle = False

    def _sign(self, string_to_sign):
        """Generate the signature for the request"""
        signature = hmac.new(
            self.mws_secret_key.encode('utf_8'),
            msg=string_to_sign.encode('utf_8'),
            digestmod=hashlib.sha256).digest()
        signature = base64.b64encode(signature).decode()
        return signature

    def _querystring(self, params):
        """Generate the querystring to be posted to the MWS endpoint

        Required parameters for every API call.

        AWSAccessKeyId: Your Amazon MWS account is identified by your access key,
            which Amazon MWS uses to look up your secret key.

        SignatureMethod: The HMAC hash algorithm you are using to calculate your
            signature. Both HmacSHA256 and HmacSHA1 are supported hash algorithms,
            but Amazon recommends using HmacSHA256.

        SignatureVersion: Which signature version is being used. This is Amazon
            MWS-specific information that tells Amazon MWS the algorithm you used
            to form the string that is the basis of the signature. For Amazon MWS,
            this value is currently SignatureVersion=2.

        Version: The version of the API section being called.

        Timestamp: Each request must contain the timestamp of the request. The
            Timestamp attribute must contain the client's machine time in
            ISO8601 format; requests with a timestamp significantly different
            (15 minutes) than the receiving machine's clock will be rejected to
            help prevent replay attacks.

        SellerId: Your seller or merchant identifier.
        """
        parameters = {'AWSAccessKeyId': self.mws_access_key,
                      'SignatureMethod': 'HmacSHA256',
                      'SignatureVersion': '2',
                      'Version': self._api_version,
                      'Timestamp': datetime.datetime.utcnow().replace(
                          microsecond=0).isoformat(sep='T') + 'Z'}

        if 'SellerId' not in params:
            parameters['SellerId'] = self.merchant_id

        parameters.update(dict((k, v) for k, v in params.items()))
        parse_results = urlparse(self._mws_endpoint)

        string_to_sign = "POST\n{0}\n{1}\n{2}".format(
            parse_results[1],
            parse_results[2],
            urlencode(
                sorted(parameters.items())).replace(
                    '+', '%20').replace('*', '%2A').replace('%7E', '~'))

        parameters['Signature'] = self._sign(string_to_sign)

        ordered_parameters = OrderedDict(sorted(parameters.items()))
        ordered_parameters['Signature'] = ordered_parameters.pop('Signature')
        return urlencode(ordered_parameters).encode('utf_8')

    def _request(self, retry_time):
        time.sleep(retry_time)
        data = self._querystring(self._params)

        r = requests.post(
            url=self._mws_endpoint,
            data=data,
            headers=self._headers,
            verify=True)
        self._status_code = r.status_code

        if self._status_code == 200:
            self.success = True
            self._should_throttle = False
            self.response = PaymentResponse(r.text)
        elif (self._status_code == 500 or self._status_code ==
              503) and self.handle_throttle:
            self._should_throttle = True
            self.response = PaymentErrorResponse(
                '<error>{0}</error>'.format(r.status_code))
        else:
            self.response = PaymentErrorResponse(r.text)

    def send_post(self):
        """Call request to send to MWS endpoint and handle throttle if set."""
        if self.handle_throttle:
            for retry_time in (0, 1, 4, 10):
                self._request(retry_time)
                if self.success or not self._should_throttle:
                    break
        else:
            self._request(0)
