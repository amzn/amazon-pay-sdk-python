import re
import json
import base64
import logging
from urllib import request
from OpenSSL import crypto
from urllib.error import HTTPError
from urllib.parse import urlparse
from amazon_pay.payment_response import PaymentResponse


class IpnHandler():

    logger = logging.getLogger('__amazon_pay_sdk__')
    logger.addHandler(logging.NullHandler())

    """Instant Payment Notifications (IPN) can be used to monitor the state
    transition of payment objects.

    Amazon sends you a notification when the state of any of the payment
    objects or the Order Reference object changes. These notifications are
    always sent without any action required on your part and can be used to
    update any internal tracking or fulfillment systems you might be using to
    manage the order.

    After you receive an IPN, a best practice is to perform a get operation for
    the respective object for which you have received the notification. You can
    use the response of the get operation to update your systems.

    With each notification you receive, you should configure your endpoint to
    send Amazon a '200 OK' response immediately after receipt. If you do not
    send this response or if your server is down when the SNS message is sent,
    Amazon SNS will perform retries every hour for 14 days.

    Amazon Simple Notification Service (Amazon SNS) is a fast, flexible, fully
    managed push notification service.
    """

    def __init__(self, body, headers):
        """
        Parameters
        ----------
        body : string
            The body of the SNS message.

        headers : dictionary
            The headers of the SNS message.


        Properties
        ----------
        error : string
            Holds the latest error, if any.
        """

        self.error = None

        self._root = None
        self._ns = None
        self._response_type = None
        self._headers = headers
        self._payload = json.loads(body.decode('utf-8'))
        self._pem = None

        self._message_encoded = self._payload['Message']
        self._message = json.loads(self._payload['Message'])
        self._message_id = self._payload['MessageId']
        self._topic_arn = self._payload['TopicArn']
        self._notification_data = self._message['NotificationData']
        self._signing_cert_url = self._payload['SigningCertURL']
        self._signature = self._payload['Signature']
        self._timestamp = self._payload['Timestamp']
        self._type = self._payload['Type']
        self._xml = self._notification_data.replace(
            '<?xml version="1.0" encoding="UTF-8"?>\n',
            '')
        self.logger.debug('IPN Response: %s',
                          self._sanitize_response_data(self._xml))

    def authenticate(self):
        """Attempt to validate a SNS message received from Amazon
        From release version 2.7.9/3.4.3 on, Python by default attempts to
        perform certificate validation. Returns True on success.

        https://docs.python.org/2/library/httplib.html#httplib.HTTPSConnection

        Changed in version 3.4.3: This class now performs all the necessary
        certificate and hostname checks by default.
        """
        self._validate_header()
        self._validate_cert_url()
        self._get_cert()
        self._validate_signature()

        return True

    def _validate_header(self):
        """Compare the header topic_arn to the body topic_arn """
        if 'X-Amz-Sns-Topic-Arn' in self._headers:
            if self._topic_arn != self._headers.get(
                    'X-Amz-Sns-Topic-Arn'):
                self.error = 'Invalid TopicArn.'
                raise ValueError('Invalid TopicArn')
        else:
            self.error = 'Invalid TopicArn'
            raise ValueError('Invalid TopicArn')

        return True

    def _validate_cert_url(self):
        """Checks to see if the certificate URL points to a AWS endpoint and
        validates the signature using the .pem from the certificate URL.
        """
        try:
            url_object = urlparse(self._signing_cert_url)
        except:
            raise ValueError('Invalid signing cert URL.')

        if url_object.scheme != 'https':
            raise ValueError('Invalid certificate.')

        if not re.search(
                '^sns\.[a-zA-Z0-9\-]{3,}\.amazonaws\.com(\.cn)?$', url_object.netloc):
            raise ValueError('Invalid certificate.')

        if not re.search('^\/(.*)\.pem$', url_object.path):
            raise ValueError('Invalid certificate.')

        return True

    def _get_cert(self):
        try:
            cert_req = request.urlopen(
                url=request.Request(self._signing_cert_url))
        except HTTPError as ex:
            self.error = 'Error retrieving certificate.'
            raise ValueError(
                'Error retrieving certificate. {}'.format(
                    ex.reason))

        self._pem = str(cert_req.read(), encoding='utf-8')
        return True

    def _validate_signature(self):
        """Generate signing string and validate signature"""
        signing_string = '{}\n{}\n{}\n{}\n{}\n{}\n{}\n{}\n{}\n{}\n'.format(
            'Message',
            self._message_encoded,
            'MessageId',
            self._message_id,
            'Timestamp',
            self._timestamp,
            'TopicArn',
            self._topic_arn,
            'Type',
            self._type)

        crt = crypto.load_certificate(crypto.FILETYPE_PEM, self._pem)
        signature = base64.b64decode(self._signature)

        try:
            crypto.verify(
                crt,
                signature,
                signing_string.encode('utf-8'),
                'sha1')
        except:
            self.error = 'Invalid signature.'
            raise ValueError('Invalid signature.')

        return True

    def to_json(self):
        """Retuns notification message as JSON"""
        return PaymentResponse(self._xml).to_json()

    def to_xml(self):
        """Retuns notification message as XML"""
        return PaymentResponse(self._xml).to_xml()

    def _sanitize_response_data(self, text):
        editText = text
        patterns = []
        patterns.append(r'(?s)(<SellerNote>).*(<\/SellerNote>)')
        patterns.append(
            r'(?s)(<AuthorizationBillingAddress>).*(<\/AuthorizationBillingAddress>)')
        patterns.append(
            r'(?s)(<SellerAuthorizationNote>).*(<\/SellerAuthorizationNote>)')
        patterns.append(r'(?s)(<SellerCaptureNote>).*(<\/SellerCaptureNote>)')
        patterns.append(r'(?s)(<SellerRefundNote>).*(<\/SellerRefundNote>)')
        replacement = r'\1 REMOVED \2'

        for pattern in patterns:
            editText = re.sub(pattern, replacement, editText)
        return editText
