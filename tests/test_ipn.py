from future.standard_library import install_aliases
install_aliases()

import os
import unittest
from pay_with_amazon.ipn_handler import IpnHandler


class IpnHandlerTest(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None

        with open(
                '{0}/test.pem'.format(os.path.dirname(os.path.realpath(__file__)))) as pemfile:
            self.pem = pemfile.read()

        self.body_valid = b'{\n  "Type" : "Notification",\n  "MessageId" : "15e7412b-e9ac-5f6a-b6df-0c909df567a0",\n  "TopicArn" : "arn:aws:sns:us-east-1:291180941288:A3BXB0YN3XH17HAQR8184NJXADU",\n  "Message" : "{\\"NotificationReferenceId\\":\\"1111111-1111-11111-1111-11111EXAMPLE\\",\\"MarketplaceID\\":\\"A3BXB0YN3XH17H\\",\\"NotificationType\\":\\"OrderReferenceNotification\\",\\"IsSample\\":true,\\"SellerId\\":\\"AQR8184NJXADU\\",\\"ReleaseEnvironment\\":\\"Sandbox\\",\\"Version\\":\\"2013-01-01\\",\\"NotificationData\\":\\"<?xml version=\\\\\\"1.0\\\\\\" encoding=\\\\\\"UTF-8\\\\\\"?>\\\\n            <OrderReferenceNotification xmlns=\\\\\\"https://mws.amazonservices.com/ipn/OffAmazonPayments/2013-01-01\\\\\\">\\\\n                <OrderReference>\\\\n                    <AmazonOrderReferenceId>P01-0000000-0000000-000000<\\\\/AmazonOrderReferenceId>\\\\n                    <OrderTotal>\\\\n                        <Amount>0.0<\\\\/Amount>\\\\n                        <CurrencyCode>USD<\\\\/CurrencyCode>\\\\n                    <\\\\/OrderTotal>\\\\n                    <SellerOrderAttributes />\\\\n                    <OrderReferenceStatus>\\\\n                        <State>Closed<\\\\/State>           \\\\n                        <LastUpdateTimestamp>2013-01-01T01:01:01.001Z<\\\\/LastUpdateTimestamp>\\\\n                        <ReasonCode>AmazonClosed<\\\\/ReasonCode>\\\\n                    <\\\\/OrderReferenceStatus>\\\\n                    <CreationTimestamp>2013-01-01T01:01:01.001Z<\\\\/CreationTimestamp>       \\\\n                    <ExpirationTimestamp>2013-01-01T01:01:01.001Z<\\\\/ExpirationTimestamp>\\\\n                <\\\\/OrderReference>\\\\n            <\\\\/OrderReferenceNotification>\\",\\"Timestamp\\":\\"2015-04-30T00:06:49.370Z\\"}",\n  "Timestamp" : "2015-04-30T00:06:49.434Z",\n  "SignatureVersion" : "1",\n  "Signature" : "FltJb7WvAGpFayYBgzO5RMd5FoiGizURv+TdPnm/tLXE/E3ndwvLa08hYD3tvmggKSX7Qc0a4mSty9EjZFtTgRVT93jEGuXVBT/WjO5s0lD+7AnuWslxzuVtzLLuMTOnfFUIeoXX2V1bpGwNXPxGfRxLcqz7v41ZdvJvAauoIhjo4oAHF4nZOo2MBd6HY7LMIhJPHS0xmbyQ9Z4QFm5iDaDoSyZ5Q2hCM1RJ1Uv5MQMpNjTXdX4cX81C8lis4nMar/ejDJ8cOwiEweUl5F+y7jxI1uc8AgXNoMGXSwNvdVqoj4zgHVKPkb0Oz7HHY0c4LP9s0FMYkhLBmEGFZVKGKA==",\n  "SigningCertURL" : "https://sns.us-east-1.amazonaws.com/SimpleNotificationService-d6d679a1d18e95c2f9ffcf11f4f9e198.pem",\n  "UnsubscribeURL" : "https://sns.us-east-1.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:us-east-1:291180941288:A3BXB0YN3XH17HAQR8184NJXADU:6cab6de5-c2c7-4ef0-9d4f-d6a5db8b1636"\n}'
        self.body_invalid = b'{\n  "Type" : "Notification",\n  "MessageId" : "28908206-3478-5398-bcf7-cfbd41c2a223",\n  "TopicArn" : "invalid",\n  "Message" : "{\\"NotificationReferenceId\\":\\"1111111-1111-11111-1111-11111EXAMPLE\\",\\"MarketplaceID\\":\\"A3BXB0YN3XH17H\\",\\"NotificationType\\":\\"OrderReferenceNotification\\",\\"IsSample\\":true,\\"SellerId\\":\\"AQR8184NJXADU\\",\\"ReleaseEnvironment\\":\\"Sandbox\\",\\"Version\\":\\"2013-01-01\\",\\"NotificationData\\":\\"<?xml version=\\\\\\"1.0\\\\\\" encoding=\\\\\\"UTF-8\\\\\\"?>\\\\n            <OrderReferenceNotification xmlns=\\\\\\"https://invalid.amazonservices.com/ipn/OffAmazonPayments/2013-01-01\\\\\\">\\\\n                <OrderReference>\\\\n                    <AmazonOrderReferenceId>P01-0000000-0000000-000000<\\\\/AmazonOrderReferenceId>\\\\n                    <OrderTotal>\\\\n                        <Amount>0.0<\\\\/Amount>\\\\n                        <CurrencyCode>USD<\\\\/CurrencyCode>\\\\n                    <\\\\/OrderTotal>\\\\n                    <SellerOrderAttributes />\\\\n                    <OrderReferenceStatus>\\\\n                        <State>Closed<\\\\/State>           \\\\n                        <LastUpdateTimestamp>2013-01-01T01:01:01.001Z<\\\\/LastUpdateTimestamp>\\\\n                        <ReasonCode>AmazonClosed<\\\\/ReasonCode>\\\\n                    <\\\\/OrderReferenceStatus>\\\\n                    <CreationTimestamp>2013-01-01T01:01:01.001Z<\\\\/CreationTimestamp>       \\\\n                    <ExpirationTimestamp>2013-01-01T01:01:01.001Z<\\\\/ExpirationTimestamp>\\\\n                <\\\\/OrderReference>\\\\n            <\\\\/OrderReferenceNotification>\\",\\"Timestamp\\":\\"2015-04-30T00:12:42.805Z\\"}",\n  "Timestamp" : "2015-04-30T00:12:42.885Z",\n  "SignatureVersion" : "1",\n  "Signature" : "ZChg+1FlUr8OUfu9kd7B2wzT7G1Z0BWf2mH3MH5MtDqhI4t9j5lvG9YqC20LSXV+x3ajvnEmyt2YO635KIAA+Ig4IKeCgnm/YJNjxqtdaOS01M4+3vw9zaeKPY3FlTBgG3T+J3+K3SLARIeblVJhabA0TXVatqtFbMwV81xxKnLxqE5Ik8MZSBAQdHFm6u2lNIruluQakL1mmDUm/2Szj+DkMFrjsQce7fcbkr5TCJ0YB5oYAtkG2MKODYEXYAAlpUe3G0qtBT8WyOVkMGyVQswpgZbJseCER/5xU1Vjm7UNL+tR5AbOABDX/4wi+5670gqmEumny6CvZTxIVbLmjg==",\n  "SigningCertURL" : "https://invalid.us-east-1.amazonaws.com/SimpleNotificationService-d6d679a1d18e95c2f9ffcf11f4f9e198.pem",\n  "UnsubscribeURL" : "https://sns.us-east-1.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:us-east-1:291180941288:A3BXB0YN3XH17HAQR8184NJXADU:6cab6de5-c2c7-4ef0-9d4f-d6a5db8b1636"\n}'

        self.headers = {
            'Content-Type': 'text/plain; charset=UTF-8',
            'Accept-Encoding': 'gzip,deflate',
            'Host': 'test.me',
            'X-Amz-Sns-Message-Id': '15e7412b-e9ac-5f6a-b6df-0c909df567a0',
            'Connection': 'Keep-Alive',
            'User-Agent': 'Amazon Simple Notification Service Agent',
            'X-Amz-Sns-Message-Type': 'Notification',
            'X-Amz-Sns-Topic-Arn': 'arn:aws:sns:us-east-1:291180941288:A3BXB0YN3XH17HAQR8184NJXADU',
            'Content-Length': '100',
            'X-Amz-Sns-Subscription-Arn': 'arn:aws:sns:us-east-1:291180941288:A3BXB0YN3XH17HAQR8184NJXADU:6cab6de5-c2c7-4ef0-9d4f-d6a5db8b1636'}

        self.ipn_handler = IpnHandler(
            body=self.body_valid,
            headers=self.headers)

    def test_validate_header(self):
        self.assertTrue(self.ipn_handler._validate_header())

        with self.assertRaises(ValueError):
            ipn_handler = IpnHandler(
                body=self.body_invalid,
                headers={'test': 'test'})
            ipn_handler._validate_header()

        with self.assertRaises(ValueError):
            ipn_handler = IpnHandler(
                body=self.body_valid,
                headers={'X-Amz-Sns-Topic-Arn': 'invalid'})
            ipn_handler._validate_header()

    def test_validate_cert_url(self):
        with self.assertRaises(ValueError):
            ipn_handler = IpnHandler(
                body=self.body_invalid,
                headers={'test': 'test'})
            ipn_handler._validate_cert_url()

        ipn_handler = IpnHandler(
            body=self.body_valid,
            headers={'test': 'test'})
        self.assertTrue(ipn_handler._validate_cert_url())

    def test_validate_signature(self):
        self.ipn_handler._pem = self.pem
        self.ipn_handler._validate_signature()

        with self.assertRaises(ValueError):
            ipn_handler = IpnHandler(
                body=self.body_invalid,
                headers=self.headers)
            ipn_handler._pem = self.pem
            ipn_handler._validate_signature()


if __name__ == "__main__":
    unittest.main()
