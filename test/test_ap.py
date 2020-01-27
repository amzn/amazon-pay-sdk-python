import os
import sys
import json
import platform
import unittest
import xml.etree.ElementTree as et
import amazon_pay.ap_region as ap_region
import amazon_pay.version as ap_version
from unittest.mock import Mock, patch
from amazon_pay.client import AmazonPayClient
from amazon_pay.payment_request import PaymentRequest
from amazon_pay.payment_response import PaymentResponse, PaymentErrorResponse
from symbol import parameters


class AmazonPayClientTest(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None
        self.mws_access_key = 'mws_access_key'
        self.mws_secret_key = 'mws_secret_key'
        self.merchant_id = 'merchant_id'
        self.service_version = '2013-01-01'
        self.mws_endpoint = \
            'https://mws.amazonservices.com/OffAmazonPayments_Sandbox/{}'.format(
                self.service_version)

        self.client = AmazonPayClient(
            mws_access_key=self.mws_access_key,
            mws_secret_key=self.mws_secret_key,
            merchant_id=self.merchant_id,
            handle_throttle=False,
            sandbox=True,
            region='na',
            currency_code='USD'
        )

        self.request = PaymentRequest(
            params={'test': 'test'},
            config={'mws_access_key': self.mws_access_key,
                    'mws_secret_key': self.mws_secret_key,
                    'api_version': '2013-01-01',
                    'merchant_id': self.merchant_id,
                    'mws_endpoint': self.mws_endpoint,
                    'headers': {'test': 'test'},
                    'handle_throttle': True})

        self.response = PaymentResponse('<test>الفلانية فلا</test>')
        self.supplementary_data = '{"AirlineMetaData" : {"version": 1.0, "airlineCode": "PAX", "flightDate": "2018-03-24T20:29:19.22Z", "departureAirport": "CDG", "destinationAirport": "LUX", "bookedLastTime": -1, "classOfTravel": "F", "passengers": {"numberOfPassengers": 4, "numberOfChildren": 1, "numberOfInfants": 1 }}, "AccommodationMetaData": {"version": 1.0, "startDate": "2018-03-24T20:29:19.22Z", "endDate": "2018-03-24T20:29:19.22Z", "lengthOfStay": 5, "numberOfGuests": 4, "class": "Standard", "starRating": 5, "bookedLastTime": -1 }, "OrderMetaData": {"version": 1.0, "numberOfItems": 3, "type": "Digital" }, "BuyerMetaData": {"version" : 1.0, "isFirstTimeCustomer" : true, "numberOfPastPurchases" : 2, "numberOfDisputedPurchases" : 3, "hasOpenDispute" : true, "riskScore" : 0.75 }}'

    def mock_requests_post(self, url, data=None, headers=None, verify=False):
        mock_response = Mock()
        mock_response.text = '<GetBillingAgreementDetailsResponse>\
            <GetBillingAgreementDetailsResult><BillingAgreementDetails>\
            <BillingAgreementStatus><State>Draft</State>\
            </BillingAgreementStatus></BillingAgreementDetails>\
            </GetBillingAgreementDetailsResult>\
            </GetBillingAgreementDetailsResponse>'
        mock_response.status_code = 200
        return mock_response

    def mock_requests_500_post(
            self, url, data=None, headers=None, verify=False):
        mock_response = Mock()
        mock_response.text = '<error>test</error>'
        mock_response.status_code = 500
        return mock_response

    def mock_requests_generic_error_post(
            self, url, data=None, headers=None, verify=False):
        mock_response = Mock()
        mock_response.text = '<error>test</error>'
        mock_response.status_code = 502
        return mock_response

    def mock_requests_503_post(
            self, url, data=None, headers=None, verify=False):
        mock_response = Mock()
        mock_response.text = '<error>test</error>'
        mock_response.status_code = 503
        return mock_response

    def mock_get_login_profile(self, url, headers, params, verify):
        mock_response = Mock()
        mock_response.json.return_value = {"aud": "client_id"}
        mock_response.status_code = 200
        return mock_response

    def test_sandbox_setter(self):
        self.client.sandbox = False
        self.assertEqual(
            self.client._mws_endpoint,
            'https://mws.amazonservices.com/OffAmazonPayments/2013-01-01')
        self.client.sandbox = True
        self.assertEqual(
            self.client._mws_endpoint,
            'https://mws.amazonservices.com/OffAmazonPayments_Sandbox/2013-01-01')

    def test_sanitize_response_data(self):
        current_file_dir = os.path.dirname(__file__)
        test_file_path = os.path.join(current_file_dir, "log.txt")
        f = open(test_file_path, "r")
        source_text = f.read()
        f.close()
        text = self.request._sanitize_response_data(source_text)
        test_file_path = os.path.join(current_file_dir, "sanlog.txt")
        f = open(test_file_path, "r")
        san_text = f.read()
        f.close
        self.assertEqual(text, san_text)

    def test_region_exception(self):
        with self.assertRaises(KeyError):
            AmazonPayClient(
                mws_access_key=self.mws_access_key,
                mws_secret_key=self.mws_secret_key,
                merchant_id=self.merchant_id,
                handle_throttle=False,
                sandbox=True,
                region='should_throw_exception',
                currency_code='test')

    def test_set_endpoint(self):
        self.client._set_endpoint()
        self.assertEqual(
            self.client._mws_endpoint,
            'https://mws.amazonservices.com/OffAmazonPayments_Sandbox/2013-01-01')

    def test_sign(self):
        test_signature = self.request._sign('my_test_string')
        self.assertEqual(
            test_signature,
            'JQZYxe8EFlLE3XCAWotsn329rpZF7OFYhA8oo7rUV2E=')

    def test_application_settings(self):
        client = AmazonPayClient(
            mws_access_key=self.mws_access_key,
            mws_secret_key=self.mws_secret_key,
            merchant_id=self.merchant_id,
            handle_throttle=False,
            sandbox=True,
            region='na',
            currency_code='USD',
            application_name='test_application',
            application_version='test_application_version')
        self.assertEqual(client.application_name, 'test_application')
        self.assertEqual(
            client.application_version,
            'test_application_version')

    def test_properties(self):
        self.assertEqual(self.client.mws_access_key, 'mws_access_key')
        self.assertEqual(self.client.mws_secret_key, 'mws_secret_key')
        self.assertEqual(self.client.merchant_id, 'merchant_id')
        self.assertEqual(self.client._region_code, 'na')
        self.assertEqual(self.client.currency_code, 'USD')
        self.assertEqual(self.client.handle_throttle, False)
        self.assertEqual(self.client.sandbox, True)

    @patch('requests.post')
    def test_generic_error_response(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_requests_generic_error_post
        self.request.send_post()
        response = self.request.response
        self.assertEqual(type(response), PaymentErrorResponse)

    @patch('requests.post')
    def test_500_response(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_requests_500_post
        self.request.send_post()
        response = self.request.response.to_dict()
        self.assertEqual(response['error'], '500')

    @patch('requests.post')
    def test_503_response(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_requests_503_post
        self.request.send_post()
        response = self.request.response.to_dict()
        self.assertEqual(response['error'], '503')

    @patch('requests.post')
    def test_headers(self, mock_urlopen):
        py_version = ".".join(map(str, sys.version_info[:3]))
        mock_urlopen.side_effect = self.mock_requests_post
        self.client.get_service_status()
        if sys.version_info[0] == 3 and sys.version_info[1] >= 2:
            py_valid = True

        header_expected = {
            'Content-Type': 'application/x-www-form-urlencoded',
            "User-Agent": 'amazon-pay-sdk-python/{0} ({1}Python/{2}; {3}/{4})'.format(
                str(ap_version.versions['application_version']),
                (''),
                py_version,
                str(platform.system()),
                str(platform.release())
            )
        }
        self.assertEqual(mock_urlopen.call_args[1]['headers'], header_expected)
        self.assertTrue(py_valid, True)

    @patch('requests.post')
    def test_get_merchant_account_status(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_requests_post
        self.client.get_merchant_account_status(
            merchant_id='A2AMGDUDUJFL',
            mws_auth_token='amzn.mws.d8f2d-6a5f-b46293482379')
        parameters = {
            'Action': 'GetMerchantAccountStatus',
            'SellerId': 'A2AMGDUDUJFL',
            'MWSAuthToken': 'amzn.mws.d8f2d-6a5f-b46293482379'}
        data_expected = self.request._querystring(parameters)
        self.assertEqual(mock_urlopen.call_args[1]['data'], data_expected)

    @patch('requests.post')
    def test_create_order_reference_for_id(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_requests_post
        self.client.create_order_reference_for_id(
            object_id='B01-462347-4762387',
            object_id_type='BillingAgreement',
            order_total='1',
            inherit_shipping_address=False,
            confirm_now=True,
            platform_id='testPlatformId123',
            seller_note='testSellerNote2145',
            seller_order_id='testSellerOrderId21434',
            supplementary_data=self.supplementary_data,
            store_name='testStoreName1234',
            custom_information='testCustomInfo12435',
            merchant_id='A2AMR0DUGHIUEHQ',
            mws_auth_token='amzn.mws.d6ac8f2d-6a5f-b06476237468923749823')
        parameters = {
            'Action': 'CreateOrderReferenceForId',
            'Id': 'B01-462347-4762387',
            'IdType': 'BillingAgreement',
            'OrderReferenceAttributes.OrderTotal.Amount': '1',
            'OrderReferenceAttributes.OrderTotal.CurrencyCode': 'USD',
            'InheritShippingAddress': 'false',
            'ConfirmNow': 'true',
            'OrderReferenceAttributes.PlatformId': 'testPlatformId123',
            'OrderReferenceAttributes.SellerNote': 'testSellerNote2145',
            'OrderReferenceAttributes.SellerOrderAttributes.SellerOrderId': 'testSellerOrderId21434',
            'OrderReferenceAttributes.SupplementaryData': self.supplementary_data,
            'OrderReferenceAttributes.SellerOrderAttributes.StoreName': 'testStoreName1234',
            'OrderReferenceAttributes.SellerOrderAttributes.CustomInformation': 'testCustomInfo12435',
            'SellerId': 'A2AMR0DUGHIUEHQ',
            'MWSAuthToken': 'amzn.mws.d6ac8f2d-6a5f-b06476237468923749823'}

        data_expected = self.request._querystring(parameters)
        self.assertEqual(mock_urlopen.call_args[1]['data'], data_expected)

    @patch('requests.post')
    def test_get_billing_agreement_details(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_requests_post
        self.client.get_billing_agreement_details(
            amazon_billing_agreement_id='B01-47236478-46253862',
            address_consent_token='AFYDFWIGHUIP',
            merchant_id='ADEIUYIOQUIOW',
            mws_auth_token='amzn.mws.d6ac8f2d-6a5f-7462348237498')
        parameters = {
            'Action': 'GetBillingAgreementDetails',
            'AmazonBillingAgreementId': 'B01-47236478-46253862',
            'AddressConsentToken': 'AFYDFWIGHUIP',
            'SellerId': 'ADEIUYIOQUIOW',
            'MWSAuthToken': 'amzn.mws.d6ac8f2d-6a5f-7462348237498'}
        data_expected = self.request._querystring(parameters)
        self.assertEqual(mock_urlopen.call_args[1]['data'], data_expected)

    @patch('requests.post')
    def test_set_billing_agreement_details(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_requests_post
        self.client.set_billing_agreement_details(
            amazon_billing_agreement_id='B01-47236478-462863428',
            platform_id='testPlatformId89',
            seller_note='testSellerNote3251',
            seller_billing_agreement_id='testBillingAgreement1213',
            store_name='testStoreName5237',
            custom_information='testCustomInfo32365',
            merchant_id='AGDUIEJOQEOPQWIKO',
            mws_auth_token='amzn.mws.d6ac8f2d-6a5f-b06a-bc12-4623862')
        parameters = {
            'Action': 'SetBillingAgreementDetails',
            'AmazonBillingAgreementId': 'B01-47236478-462863428',
            'BillingAgreementAttributes.PlatformId': 'testPlatformId89',
            'BillingAgreementAttributes.SellerNote': 'testSellerNote3251',
            'BillingAgreementAttributes.SellerBillingAgreementAttributes.SellerBillingAgreementId': 'testBillingAgreement1213',
            'BillingAgreementAttributes.SellerBillingAgreementAttributes.StoreName': 'testStoreName5237',
            'BillingAgreementAttributes.SellerBillingAgreementAttributes.CustomInformation': 'testCustomInfo32365',
            'SellerId': 'AGDUIEJOQEOPQWIKO',
            'MWSAuthToken': 'amzn.mws.d6ac8f2d-6a5f-b06a-bc12-4623862'}
        data_expected = self.request._querystring(parameters)
        self.assertEqual(mock_urlopen.call_args[1]['data'], data_expected)

    @patch('requests.post')
    def test_confirm_billing_agreement(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_requests_post
        self.client.confirm_billing_agreement(
            amazon_billing_agreement_id='B01-47236478-46284638789',
            merchant_id='AGFUHWIEJLMLK',
            mws_auth_token='amzn.mws.d6ac8f2d-6a5f-b06a-bc12-4263289')
        parameters = {
            'Action': 'ConfirmBillingAgreement',
            'AmazonBillingAgreementId': 'B01-47236478-46284638789',
            'SellerId': 'AGFUHWIEJLMLK',
            'MWSAuthToken': 'amzn.mws.d6ac8f2d-6a5f-b06a-bc12-4263289'}
        data_expected = self.request._querystring(parameters)
        self.assertEqual(mock_urlopen.call_args[1]['data'], data_expected)

    @patch('requests.post')
    def test_validate_billing_agreement(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_requests_post
        self.client.validate_billing_agreement(
            amazon_billing_agreement_id='B01-47236478-46287462347823490',
            merchant_id='AGFUHWHYDIIJQWL',
            mws_auth_token='amzn.mws.d6ac8f2d-6a5f-b06a-bc12-457267342897')
        parameters = {
            'Action': 'ValidateBillingAgreement',
            'AmazonBillingAgreementId': 'B01-47236478-46287462347823490',
            'SellerId': 'AGFUHWHYDIIJQWL',
            'MWSAuthToken': 'amzn.mws.d6ac8f2d-6a5f-b06a-bc12-457267342897'}
        data_expected = self.request._querystring(parameters)
        self.assertEqual(mock_urlopen.call_args[1]['data'], data_expected)

    @patch('requests.post')
    def test_authorize_on_billing_agreement(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_requests_post
        self.client.authorize_on_billing_agreement(
            amazon_billing_agreement_id='B01-4653268-47632947',
            authorization_reference_id='testAuthRefId31253',
            authorization_amount='1',
            seller_authorization_note='testSellerAuthNote3612367',
            transaction_timeout=0,
            capture_now=True,
            soft_descriptor='testSoftDescriptor42837',
            seller_note='testSellerNote4721893',
            platform_id='testPlatformId47237',
            seller_order_id='testSellerOrderId4237',
            store_name='testStoreName842398',
            custom_information='testCustomInfo623',
            supplementary_data=self.supplementary_data,
            inherit_shipping_address=False,
            merchant_id='A2AMR0FDYHGHJD',
            mws_auth_token='amzn.mws.d6ac8f2d-463286-fhegsdj46238')
        parameters = {
            'Action': 'AuthorizeOnBillingAgreement',
            'AmazonBillingAgreementId': 'B01-4653268-47632947',
            'TransactionTimeout': '0',
            'AuthorizationReferenceId': 'testAuthRefId31253',
            'AuthorizationAmount.Amount': '1',
            'AuthorizationAmount.CurrencyCode': 'USD',
            'CaptureNow': 'true',
            'SellerAuthorizationNote': 'testSellerAuthNote3612367',
            'SoftDescriptor': 'testSoftDescriptor42837',
            'SellerNote': 'testSellerNote4721893',
            'PlatformId': 'testPlatformId47237',
            'InheritShippingAddress': 'false',
            'SellerOrderAttributes.SellerOrderId': 'testSellerOrderId4237',
            'SellerOrderAttributes.StoreName': 'testStoreName842398',
            'SellerOrderAttributes.CustomInformation': 'testCustomInfo623',
            'SellerOrderAttributes.SupplementaryData': self.supplementary_data,
            'SellerId': 'A2AMR0FDYHGHJD',
            'MWSAuthToken': 'amzn.mws.d6ac8f2d-463286-fhegsdj46238'}
        data_expected = self.request._querystring(parameters)
        self.assertEqual(mock_urlopen.call_args[1]['data'], data_expected)

    @patch('requests.post')
    def test_close_billing_agreement(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_requests_post
        self.client.close_billing_agreement(
            amazon_billing_agreement_id='B01-4236278-3761372',
            closure_reason='testClosureReason',
            merchant_id='A2AMR0DGUQHWIJQWL',
            mws_auth_token='amzn.mws.d6ac8f2d-463286-fhegsdj46238')
        parameters = {
            'Action': 'CloseBillingAgreement',
            'AmazonBillingAgreementId': 'B01-4236278-3761372',
            'ClosureReason': 'testClosureReason',
            'SellerId': 'A2AMR0DGUQHWIJQWL',
            'MWSAuthToken': 'amzn.mws.d6ac8f2d-463286-fhegsdj46238'}
        data_expected = self.request._querystring(parameters)
        self.assertEqual(mock_urlopen.call_args[1]['data'], data_expected)

    @patch('requests.post')
    def test_set_order_reference_details(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_requests_post
        self.client.set_order_reference_details(
            amazon_order_reference_id='P01-1234567-7654897',
            order_total='1',
            platform_id='platformId4673',
            seller_note='sellerNote38278',
            seller_order_id='sellerOrderId123',
            store_name='testStoreName387289',
            custom_information='customInfo34278',
            merchant_id='A2AMR0CLHYUTGH',
            mws_auth_token='amzn.mws.d8f2d-6a5f-b06a4628',
            supplementary_data=self.supplementary_data)
        parameters = {
            'Action': 'SetOrderReferenceDetails',
            'AmazonOrderReferenceId': 'P01-1234567-7654897',
            'OrderReferenceAttributes.OrderTotal.Amount': '1',
            'OrderReferenceAttributes.OrderTotal.CurrencyCode': 'USD',
            'OrderReferenceAttributes.PlatformId': 'platformId4673',
            'OrderReferenceAttributes.SellerNote': 'sellerNote38278',
            'OrderReferenceAttributes.SellerOrderAttributes.SellerOrderId': 'sellerOrderId123',
            'OrderReferenceAttributes.SellerOrderAttributes.StoreName': 'testStoreName387289',
            'OrderReferenceAttributes.SellerOrderAttributes.CustomInformation': 'customInfo34278',
            'SellerId': 'A2AMR0CLHYUTGH',
            'MWSAuthToken': 'amzn.mws.d8f2d-6a5f-b06a4628',
            'OrderReferenceAttributes.SellerOrderAttributes.SupplementaryData': self.supplementary_data}
        data_expected = self.request._querystring(parameters)
        self.assertEqual(mock_urlopen.call_args[1]['data'], data_expected)

    @patch('requests.post')
    def test_set_order_attributes(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_requests_post
        self.client.set_order_attributes(
            amazon_order_reference_id='P01-1234567-4827348237',
            currency_code='USD',
            amount='1',
            seller_order_id='testSellerOrderId5371',
            payment_service_provider_id='AGHJHHJKJHL',
            payment_service_provider_order_id='testPSPOrderId',
            platform_id='testPlatformId472',
            seller_note='testSellerNote4628',
            request_payment_authorization='true',
            store_name='testStoreName26157',
            list_order_item_categories=['test'],
            custom_information='testCustomInfo35273',
            merchant_id='AGHJHHJKJHL',
            mws_auth_token='amzn.mws.d8f2d-6a5f-b06a4628',
            supplementary_data=self.supplementary_data)

        parameters = {
            'Action': 'SetOrderAttributes',
            'AmazonOrderReferenceId': 'P01-1234567-4827348237',
            'OrderAttributes.OrderTotal.Amount': '1',
            'OrderAttributes.OrderTotal.CurrencyCode': 'USD',
            'OrderAttributes.SellerOrderAttributes.CustomInformation': 'testCustomInfo35273',
            'OrderAttributes.SellerOrderAttributes.OrderItemCategories.OrderItemCategory.1': 'test',
            'OrderAttributes.PaymentServiceProviderAttributes.PaymentServiceProviderId': 'AGHJHHJKJHL',
            'OrderAttributes.PaymentServiceProviderAttributes.PaymentServiceProviderOrderId': 'testPSPOrderId',
            'OrderAttributes.PlatformId': 'testPlatformId472',
            'OrderAttributes.RequestPaymentAuthorization': 'true',
            'OrderAttributes.SellerNote': 'testSellerNote4628',
            'OrderAttributes.SellerOrderAttributes.SellerOrderId': 'testSellerOrderId5371',
            'OrderAttributes.SellerOrderAttributes.StoreName': 'testStoreName26157',
            'SellerId': 'AGHJHHJKJHL',
            'MWSAuthToken': 'amzn.mws.d8f2d-6a5f-b06a4628',
            'OrderAttributes.SellerOrderAttributes.SupplementaryData': self.supplementary_data}
        data_expected = self.request._querystring(parameters)
        self.assertEqual(mock_urlopen.call_args[1]['data'], data_expected)

    @patch('requests.post')
    def test_get_order_reference_details(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_requests_post
        self.client.get_order_reference_details(
            amazon_order_reference_id='P01-476238-47238',
            address_consent_token='ADUHIQILPLP',
            access_token='AHJJOKJJHNJNJK',
            merchant_id='ADGJUHJWKJKJ',
            mws_auth_token='amzn.mws.d8f2d-6a5f-b427489234798')
        parameters = {
            'Action': 'GetOrderReferenceDetails',
            'AmazonOrderReferenceId': 'P01-476238-47238',
            'AddressConsentToken': 'ADUHIQILPLP',
            'AccessToken': 'AHJJOKJJHNJNJK',
            'SellerId': 'ADGJUHJWKJKJ',
            'MWSAuthToken': 'amzn.mws.d8f2d-6a5f-b427489234798'
        }
        data_expected = self.request._querystring(parameters)
        self.assertEqual(mock_urlopen.call_args[1]['data'], data_expected)

    @patch('requests.post')
    def test_confirm_order_reference(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_requests_post
        self.client.confirm_order_reference(
            amazon_order_reference_id='P01-476238-47263849238',
            merchant_id='AHDGJHDJKFJIIIJ',
            mws_auth_token='amzn.mws.d8f2d-6a5f-b42rwe74237489',
            success_url='https://www.success.com',
            failure_url='https://www.failure.com',
            authorization_amount='5',
            currency_code='USD'
        )

        parameters = {
            'Action': 'ConfirmOrderReference',
            'AmazonOrderReferenceId': 'P01-476238-47263849238',
            'SellerId': 'AHDGJHDJKFJIIIJ',
            'MWSAuthToken': 'amzn.mws.d8f2d-6a5f-b42rwe74237489',
            'SuccessUrl': 'https://www.success.com',
            'FailureUrl': 'https://www.failure.com',
            'AuthorizationAmount.Amount': '5',
            'AuthorizationAmount.CurrencyCode': 'USD'
        }

        data_expected = self.request._querystring(parameters)

        self.assertEqual(mock_urlopen.call_args[1]['data'], data_expected)

    @patch('requests.post')
    def test_cancel_order_reference(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_requests_post
        self.client.cancel_order_reference(
            amazon_order_reference_id='P01-476238-472642737489',
            cancelation_reason='testCancelReason',
            merchant_id='AJHDELWJEKELW',
            mws_auth_token='amzn.mws.d8f2d-6a5f-b42rw72372897893')
        parameters = {
            'Action': 'CancelOrderReference',
            'AmazonOrderReferenceId': 'P01-476238-472642737489',
            'CancelationReason': 'testCancelReason',
            'SellerId': 'AJHDELWJEKELW',
            'MWSAuthToken': 'amzn.mws.d8f2d-6a5f-b42rw72372897893'}
        data_expected = self.request._querystring(parameters)
        self.assertEqual(mock_urlopen.call_args[1]['data'], data_expected)

    @patch('requests.post')
    def test_close_order_reference(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_requests_post
        self.client.close_order_reference(
            amazon_order_reference_id='P01-476238-472642737489',
            closure_reason='testClosureReason24156',
            merchant_id='AJHYJHJLYFYGTUHK',
            mws_auth_token='amzn.mws.d8f2d-6a5f-b42ryurueruio3uio87')
        parameters = {
            'Action': 'CloseOrderReference',
            'AmazonOrderReferenceId': 'P01-476238-472642737489',
            'ClosureReason': 'testClosureReason24156',
            'SellerId': 'AJHYJHJLYFYGTUHK',
            'MWSAuthToken': 'amzn.mws.d8f2d-6a5f-b42ryurueruio3uio87'}
        data_expected = self.request._querystring(parameters)
        self.assertEqual(mock_urlopen.call_args[1]['data'], data_expected)

    @patch('requests.post')
    def test_list_order_reference(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_requests_post
        self.client.list_order_reference(
            query_id='testSellerOrderId124',
            query_id_type='SellerOrderId',
            created_time_range_start='testStart',
            created_time_range_end='testEnd',
            sort_order='ascending',
            page_size=1,
            merchant_id='AFHRWKJEKJLJKL',
            mws_auth_token='amzn.mws.d8f2d-6a5f-b42ryurueruio3uio87',
            order_reference_status_list_filter=['test1', 'test2'])

        if self.client.region in ('na'):
            payment_domain = 'NA_USD'
        elif self.client.region in ('uk', 'gb'):
            payment_domain = 'EU_GBP'
        elif self.client.region in ('jp', 'fe'):
            payment_domain = 'FE_JPY'
        elif self.client.region in ('eu', 'de', 'fr', 'it', 'es', 'cy'):
            payment_domain = 'EU_EUR'
        else:
            raise ValueError(
                "Error. The current region code does not match our records")

        parameters = {
            'Action': 'ListOrderReference',
            'QueryId': 'testSellerOrderId124',
            'QueryIdType': 'SellerOrderId',
            'PaymentDomain': payment_domain,
            'CreatedTimeRange.StartTime': 'testStart',
            'CreatedTimeRange.EndTime': 'testEnd',
            'SortOrder': 'ascending',
            'PageSize': 1,
            'SellerId': 'AFHRWKJEKJLJKL',
            'MWSAuthToken': 'amzn.mws.d8f2d-6a5f-b42ryurueruio3uio87',
            'OrderReferenceStatusListFilter.OrderReferenceStatus.1': 'test1',
            'OrderReferenceStatusListFilter.OrderReferenceStatus.2': 'test2'}
        data_expected = self.request._querystring(parameters)
        self.assertEqual(mock_urlopen.call_args[1]['data'], data_expected)

    @patch('requests.post')
    def test_list_order_reference_time_check_error(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_requests_generic_error_post
        self.client.list_order_reference(
            query_id='testSellerOrderId12444',
            query_id_type='SellerOrderId',
            created_time_range_start='testStart',
            created_time_range_end=None,
            sort_order=None,
            page_size=None,
            merchant_id='AGDJHKWJLHHK',
            mws_auth_token='amzn.mws.d8f2d-6a5f-b42r23564783492380',
            order_reference_status_list_filter=None)

        if self.client.region in ('na'):
            payment_domain = 'NA_USD'
        elif self.client.region in ('uk', 'gb'):
            payment_domain = 'EU_GBP'
        elif self.client.region in ('jp', 'fe'):
            payment_domain = 'FE_JPY'
        elif self.client.region in ('eu', 'de', 'fr', 'it', 'es', 'cy'):
            payment_domain = 'EU_EUR'
        else:
            raise ValueError(
                "Error. The current region code does not match our records")

        parameters = {
            'Action': 'ListOrderReference',
            'QueryId': 'testSellerOrderId12444',
            'QueryIdType': 'SellerOrderId',
            'PaymentDomain': payment_domain,
            'SellerId': 'AGDJHKWJLHHK',
            'MWSAuthToken': 'amzn.mws.d8f2d-6a5f-b42r23564783492380',
            'CreatedTimeRange.StartTime': 'testStart'}
        data_expected = self.request._querystring(parameters)
        self.assertEqual(mock_urlopen.call_args[1]['data'], data_expected)

    @patch('requests.post')
    def test_list_order_reference_by_next_token(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_requests_post
        self.client.list_order_reference_by_next_token(
            next_page_token='yrtewyy4823749329482394023940',
            merchant_id='AHFUHWJELWJELEJW',
            mws_auth_token='amzn.mws.d8f2d-6a5f-b42r23436248623748')
        parameters = {
            'Action': 'ListOrderReferenceByNextToken',
            'NextPageToken': 'yrtewyy4823749329482394023940',
            'SellerId': 'AHFUHWJELWJELEJW',
            'MWSAuthToken': 'amzn.mws.d8f2d-6a5f-b42r23436248623748'}
        data_expected = self.request._querystring(parameters)
        self.assertEqual(mock_urlopen.call_args[1]['data'], data_expected)

    @patch('requests.post')
    def test_authorize(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_requests_post
        self.client.authorize(
            amazon_order_reference_id='P01-351-461238848937',
            authorization_reference_id='testAuthId123',
            authorization_amount='1',
            seller_authorization_note='testAuthNote123',
            transaction_timeout=0,
            capture_now=True,
            soft_descriptor='testSoftDescriptor12',
            merchant_id='A2AMR0CUYDHYIOW',
            mws_auth_token='amzn.mws.d6ac8f2d-6a5f-b06a-bc3276378843298-fgeswyd')
        parameters = {
            'Action': 'Authorize',
            'AmazonOrderReferenceId': 'P01-351-461238848937',
            'AuthorizationReferenceId': 'testAuthId123',
            'AuthorizationAmount.Amount': '1',
            'AuthorizationAmount.CurrencyCode': 'USD',
            'SellerAuthorizationNote': 'testAuthNote123',
            'TransactionTimeout': '0',
            'CaptureNow': 'true',
            'SoftDescriptor': 'testSoftDescriptor12',
            'SellerId': 'A2AMR0CUYDHYIOW',
            'MWSAuthToken': 'amzn.mws.d6ac8f2d-6a5f-b06a-bc3276378843298-fgeswyd'}
        data_expected = self.request._querystring(parameters)
        self.assertEqual(mock_urlopen.call_args[1]['data'], data_expected)

    @patch('requests.post')
    def test_get_authorization_details(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_requests_post
        self.client.get_authorization_details(
            amazon_authorization_id='P01-351-461238848937-A42374987239849',
            merchant_id='AGDFHGWEHGWJH',
            mws_auth_token='amzn.mws.d6ac8f2d-6a5f-b06a-bc412328378')
        parameters = {
            'Action': 'GetAuthorizationDetails',
            'AmazonAuthorizationId': 'P01-351-461238848937-A42374987239849',
            'SellerId': 'AGDFHGWEHGWJH',
            'MWSAuthToken': 'amzn.mws.d6ac8f2d-6a5f-b06a-bc412328378'}
        data_expected = self.request._querystring(parameters)
        self.assertEqual(mock_urlopen.call_args[1]['data'], data_expected)

    @patch('requests.post')
    def test_capture(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_requests_post
        self.client.capture(
            amazon_authorization_id='P01-1234567-7654321-A467823648',
            capture_reference_id='testCaptureRefId123',
            capture_amount='1',
            seller_capture_note='testCaptureNote124',
            soft_descriptor='testSoftDescriptor123',
            merchant_id='A2AMR8YRGWKHK',
            mws_auth_token='amzn.mws.d6ac8f2d-6a5f-b06a-472637-753648')
        parameters = {
            'Action': 'Capture',
            'AmazonAuthorizationId': 'P01-1234567-7654321-A467823648',
            'CaptureReferenceId': 'testCaptureRefId123',
            'CaptureAmount.Amount': '1',
            'CaptureAmount.CurrencyCode': 'USD',
            'SellerCaptureNote': 'testCaptureNote124',
            'SoftDescriptor': 'testSoftDescriptor123',
            'SellerId': 'A2AMR8YRGWKHK',
            'MWSAuthToken': 'amzn.mws.d6ac8f2d-6a5f-b06a-472637-753648'}
        data_expected = self.request._querystring(parameters)
        self.assertEqual(mock_urlopen.call_args[1]['data'], data_expected)

    @patch('requests.post')
    def test_get_capture_details(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_requests_post
        self.client.get_capture_details(
            amazon_capture_id='P01-4763247-C6472482379',
            merchant_id='A2AYDGTIQUYOHO',
            mws_auth_token='amzn.mws.d6ac8f2d-6a5f-b645234782374903')
        parameters = {
            'Action': 'GetCaptureDetails',
            'AmazonCaptureId': 'P01-4763247-C6472482379',
            'SellerId': 'A2AYDGTIQUYOHO',
            'MWSAuthToken': 'amzn.mws.d6ac8f2d-6a5f-b645234782374903'}
        data_expected = self.request._querystring(parameters)
        self.assertEqual(mock_urlopen.call_args[1]['data'], data_expected)

    @patch('requests.post')
    def test_close_authorization(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_requests_post
        self.client.close_authorization(
            amazon_authorization_id='P01-4763247-A6568472482379',
            closure_reason='testClosure',
            merchant_id='A2ATTYIUHBUMTYU',
            mws_auth_token='amzn.mws.d6ac8f2d-6a5f-b645234782374903')
        parameters = {
            'Action': 'CloseAuthorization',
            'AmazonAuthorizationId': 'P01-4763247-A6568472482379',
            'ClosureReason': 'testClosure',
            'SellerId': 'A2ATTYIUHBUMTYU',
            'MWSAuthToken': 'amzn.mws.d6ac8f2d-6a5f-b645234782374903'}
        data_expected = self.request._querystring(parameters)
        self.assertEqual(mock_urlopen.call_args[1]['data'], data_expected)

    @patch('requests.post')
    def test_refund(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_requests_post
        self.client.refund(
            amazon_capture_id='P01-4763247-C645749',
            refund_reference_id='testRefundRefId125',
            refund_amount='1',
            seller_refund_note='testRefundNote123',
            soft_descriptor='testSoftDescriptor167',
            merchant_id='A2ATGUHFHWDJEOPW',
            mws_auth_token='amzn.mws.d6ac8f2d-6a5f-b645234782374903')
        parameters = {
            'Action': 'Refund',
            'AmazonCaptureId': 'P01-4763247-C645749',
            'RefundReferenceId': 'testRefundRefId125',
            'RefundAmount.Amount': '1',
            'RefundAmount.CurrencyCode': 'USD',
            'SellerRefundNote': 'testRefundNote123',
            'SoftDescriptor': 'testSoftDescriptor167',
            'SellerId': 'A2ATGUHFHWDJEOPW',
            'MWSAuthToken': 'amzn.mws.d6ac8f2d-6a5f-b645234782374903'}
        data_expected = self.request._querystring(parameters)
        self.assertEqual(mock_urlopen.call_args[1]['data'], data_expected)

    @patch('requests.post')
    def test_get_refund_details(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_requests_post
        self.client.get_refund_details(
            amazon_refund_id='P01-4763247-R643927483',
            merchant_id='A2ATGUYIOUHIJL',
            mws_auth_token='amzn.mws.d6ac8f2d-6a5f-b6447623479')
        parameters = {
            'Action': 'GetRefundDetails',
            'AmazonRefundId': 'P01-4763247-R643927483',
            'SellerId': 'A2ATGUYIOUHIJL',
            'MWSAuthToken': 'amzn.mws.d6ac8f2d-6a5f-b6447623479'}
        data_expected = self.request._querystring(parameters)
        self.assertEqual(mock_urlopen.call_args[1]['data'], data_expected)

    @patch('requests.post')
    def test_get_service_status(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_requests_post
        self.client.get_service_status()
        parameters = {
            'Action': 'GetServiceStatus'}
        data_expected = self.request._querystring(parameters)
        self.assertEqual(mock_urlopen.call_args[1]['data'], data_expected)

    def test_is_order_reference_id(self):
        self.assertTrue(self.client.is_order_reference_id('P'))
        self.assertTrue(self.client.is_order_reference_id('S'))
        self.assertFalse(self.client.is_order_reference_id('X'))

    def test_is_billing_agreement_id(self):
        self.assertTrue(self.client.is_billing_agreement_id('B'))
        self.assertTrue(self.client.is_billing_agreement_id('C'))
        self.assertFalse(self.client.is_billing_agreement_id('X'))

    def test_response_invalid_xml(self):
        with self.assertRaises(ValueError):
            PaymentResponse('<invalid></xml>')

    @patch('requests.post')
    def test_response_to_xml(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_requests_post
        response = self.client.get_service_status()
        self.assertTrue(et.fromstring(response.to_xml()))

    @patch('requests.post')
    def test_response_to_json(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_requests_post
        response = self.client.get_service_status()
        self.assertTrue(json.loads(response.to_json()))

    def test_response_to_json_utf8(self):
        text = self.response.to_json()
        utf8_text = '{"test": "الفلانية فلا"}'
        self.assertEqual(text, utf8_text)

    @patch('requests.post')
    def test_response_to_dict(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_requests_post
        response = self.client.get_service_status()
        self.assertEqual(type(response.to_dict()), dict)

    @patch('requests.get')
    def test_get_login_profile(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_get_login_profile
        response = self.client.get_login_profile('access_token', 'client_id')

    def test_environment_variables(self):
        os.environ['AP_REGION'] = 'na'
        os.environ['AP_MWS_ACCESS_KEY'] = 'AP_MWS_ACCESS_KEY'
        os.environ['AP_MERCHANT_ID'] = 'AP_MERCHANT_ID'
        os.environ['AP_CURRENCY_CODE'] = 'AP_CURRENCY_CODE'
        os.environ['AP_MWS_SECRET_KEY'] = 'AP_MWS_SECRET_KEY'

        client = AmazonPayClient(sandbox=True)
        self.assertEqual(client.region, 'na')
        self.assertEqual(client.mws_access_key, 'AP_MWS_ACCESS_KEY')
        self.assertEqual(client.mws_secret_key, 'AP_MWS_SECRET_KEY')
        self.assertEqual(client.merchant_id, 'AP_MERCHANT_ID')
        self.assertEqual(client.currency_code, 'AP_CURRENCY_CODE')

        os.environ['AP_REGION'] = 'AP_REGION'
        with self.assertRaises(KeyError):
            client = AmazonPayClient()


if __name__ == "__main__":
    unittest.main()
