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
            currency_code='test')

        self.request = PaymentRequest(
            params={'test': 'test'},
            config={'mws_access_key': self.mws_access_key,
                    'mws_secret_key': self.mws_secret_key,
                    'api_version': '2013-01-01',
                    'merchant_id': self.merchant_id,
                    'mws_endpoint': self.mws_endpoint,
                    'headers': {'test': 'test'},
                    'handle_throttle': True})

        self.response = PaymentResponse('<test>test</test>')

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
            currency_code='test',
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
        self.assertEqual(self.client.currency_code, 'test')
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
            "User-Agent":'amazon-pay-sdk-python/{0} ({1}Python/{2}; {3}/{4})'.format(
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
            merchant_id='test',
            mws_auth_token='test')
        parameters = {
            'Action': 'GetMerchantAccountStatus',
            'SellerId': 'test',
            'MWSAuthToken': 'test'}
        data_expected = self.request._querystring(parameters)
        self.assertEqual(mock_urlopen.call_args[1]['data'], data_expected)

    @patch('requests.post')
    def test_create_order_reference_for_id(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_requests_post
        self.client.create_order_reference_for_id(
            object_id='test',
            object_id_type='test',
            order_total='test',
            inherit_shipping_address=False,
            confirm_now=True,
            platform_id='test',
            seller_note='test',
            seller_order_id='test',
            store_name='test',
            custom_information='test',
            merchant_id='test',
            mws_auth_token='test')
        parameters = {
            'Action': 'CreateOrderReferenceForId',
            'Id': 'test',
            'IdType': 'test',
            'OrderTotal.Amount': 'test',
            'OrderTotal.CurrencyCode': 'test',
            'InheritShippingAddress': 'false',
            'ConfirmNow': 'true',
            'PlatformId': 'test',
            'SellerNote': 'test',
            'SellerOrderId': 'test',
            'StoreName': 'test',
            'CustomInformation': 'test',
            'SellerId': 'test',
            'MWSAuthToken': 'test'}
        data_expected = self.request._querystring(parameters)
        self.assertEqual(mock_urlopen.call_args[1]['data'], data_expected)

    @patch('requests.post')
    def test_get_billing_agreement_details(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_requests_post
        self.client.get_billing_agreement_details(
            amazon_billing_agreement_id='test',
            address_consent_token='test',
            merchant_id='test',
            mws_auth_token='test')
        parameters = {
            'Action': 'GetBillingAgreementDetails',
            'AmazonBillingAgreementId': 'test',
            'AddressConsentToken': 'test',
            'SellerId': 'test',
            'MWSAuthToken': 'test'}
        data_expected = self.request._querystring(parameters)
        self.assertEqual(mock_urlopen.call_args[1]['data'], data_expected)

    @patch('requests.post')
    def test_set_billing_agreement_details(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_requests_post
        self.client.set_billing_agreement_details(
            amazon_billing_agreement_id='test',
            platform_id='test',
            seller_note='test',
            seller_billing_agreement_id='test',
            store_name='test',
            custom_information='test',
            merchant_id='test',
            mws_auth_token='test')
        parameters = {
            'Action': 'SetBillingAgreementDetails',
            'AmazonBillingAgreementId': 'test',
            'BillingAgreementAttributes.PlatformId': 'test',
            'BillingAgreementAttributes.SellerNote': 'test',
            'BillingAgreementAttributes.SellerBillingAgreementAttributes.SellerBillingAgreementId': 'test',
            'BillingAgreementAttributes.SellerBillingAgreementAttributes.StoreName': 'test',
            'BillingAgreementAttributes.SellerBillingAgreementAttributes.CustomInformation': 'test',
            'SellerId': 'test',
            'MWSAuthToken': 'test'}
        data_expected = self.request._querystring(parameters)
        self.assertEqual(mock_urlopen.call_args[1]['data'], data_expected)

    @patch('requests.post')
    def test_confirm_billing_agreement(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_requests_post
        self.client.confirm_billing_agreement(
            amazon_billing_agreement_id='test',
            merchant_id='test',
            mws_auth_token='test')
        parameters = {
            'Action': 'ConfirmBillingAgreement',
            'AmazonBillingAgreementId': 'test',
            'SellerId': 'test',
            'MWSAuthToken': 'test'}
        data_expected = self.request._querystring(parameters)
        self.assertEqual(mock_urlopen.call_args[1]['data'], data_expected)

    @patch('requests.post')
    def test_validate_billing_agreement(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_requests_post
        self.client.validate_billing_agreement(
            amazon_billing_agreement_id='test',
            merchant_id='test',
            mws_auth_token='test')
        parameters = {
            'Action': 'ValidateBillingAgreement',
            'AmazonBillingAgreementId': 'test',
            'SellerId': 'test',
            'MWSAuthToken': 'test'}
        data_expected = self.request._querystring(parameters)
        self.assertEqual(mock_urlopen.call_args[1]['data'], data_expected)

    @patch('requests.post')
    def test_authorize_on_billing_agreement(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_requests_post
        self.client.authorize_on_billing_agreement(
            amazon_billing_agreement_id='test',
            authorization_reference_id='test',
            authorization_amount='test',
            seller_authorization_note='test',
            transaction_timeout=0,
            capture_now=True,
            soft_descriptor='test',
            seller_note='test',
            platform_id='test',
            seller_order_id='test',
            store_name='test',
            custom_information='test',
            inherit_shipping_address=False,
            merchant_id='test',
            mws_auth_token='test')
        parameters = {
            'Action': 'AuthorizeOnBillingAgreement',
            'AmazonBillingAgreementId': 'test',
            'TransactionTimeout': '0',
            'AuthorizationReferenceId': 'test',
            'AuthorizationAmount.Amount': 'test',
            'AuthorizationAmount.CurrencyCode': 'test',
            'CaptureNow': 'true',
            'SellerAuthorizationNote': 'test',
            'SoftDescriptor': 'test',
            'SellerNote': 'test',
            'PlatformId': 'test',
            'InheritShippingAddress': 'false',
            'SellerOrderAttributes.SellerOrderId': 'test',
            'SellerOrderAttributes.StoreName': 'test',
            'SellerOrderAttributes.CustomInformation': 'test',
            'SellerId': 'test',
            'MWSAuthToken': 'test'}
        data_expected = self.request._querystring(parameters)
        self.assertEqual(mock_urlopen.call_args[1]['data'], data_expected)

    @patch('requests.post')
    def test_close_billing_agreement(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_requests_post
        self.client.close_billing_agreement(
            amazon_billing_agreement_id='test',
            closure_reason='test',
            merchant_id='test',
            mws_auth_token='test')
        parameters = {
            'Action': 'CloseBillingAgreement',
            'AmazonBillingAgreementId': 'test',
            'ClosureReason': 'test',
            'SellerId': 'test',
            'MWSAuthToken': 'test'}
        data_expected = self.request._querystring(parameters)
        self.assertEqual(mock_urlopen.call_args[1]['data'], data_expected)

    @patch('requests.post')
    def test_set_order_reference_details(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_requests_post
        self.client.set_order_reference_details(
            amazon_order_reference_id='test',
            order_total='test',
            platform_id='test',
            seller_note='test',
            seller_order_id='test',
            store_name='test',
            custom_information='test',
            merchant_id='test',
            mws_auth_token='test')
        parameters = {
            'Action': 'SetOrderReferenceDetails',
            'AmazonOrderReferenceId': 'test',
            'OrderReferenceAttributes.OrderTotal.Amount': 'test',
            'OrderReferenceAttributes.OrderTotal.CurrencyCode': 'test',
            'OrderReferenceAttributes.PlatformId': 'test',
            'OrderReferenceAttributes.SellerNote': 'test',
            'OrderReferenceAttributes.SellerOrderAttributes.SellerOrderId': 'test',
            'OrderReferenceAttributes.SellerOrderAttributes.StoreName': 'test',
            'OrderReferenceAttributes.SellerOrderAttributes.CustomInformation': 'test',
            'SellerId': 'test',
            'MWSAuthToken': 'test'}
        data_expected = self.request._querystring(parameters)
        self.assertEqual(mock_urlopen.call_args[1]['data'], data_expected)
        
    @patch('requests.post')
    def test_set_order_attributes(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_requests_post
        self.client.set_order_attributes(
            amazon_order_reference_id='test',
            currency_code='test',
            amount='test',
            seller_order_id='test',
            payment_service_provider_id='test',
            payment_service_provider_order_id='test',
            platform_id='test',
            seller_note='test',
            request_payment_authorization='test',
            store_name='test',
            list_order_item_categories=['test'],
            custom_information='test',
            merchant_id='test',
            mws_auth_token='test')
        
        parameters = {
            'Action': 'SetOrderAttributes',
            'AmazonOrderReferenceId': 'test',
            'OrderAttributes.OrderTotal.Amount': 'test',
            'OrderAttributes.OrderTotal.CurrencyCode': 'test',
            'OrderAttributes.SellerOrderAttributes.CustomInformation': 'test',
            'OrderAttributes.SellerOrderAttributes.OrderItemCategories.OrderItemCategory.1': 'test',
            'OrderAttributes.PaymentServiceProviderAttributes.PaymentServiceProviderId': 'test',
            'OrderAttributes.PaymentServiceProviderAttributes.PaymentServiceProviderOrderId': 'test',
            'OrderAttributes.PlatformId': 'test',
            'OrderAttributes.RequestPaymentAuthorization': 'test',
            'OrderAttributes.SellerNote': 'test',
            'OrderAttributes.SellerOrderAttributes.SellerOrderId': 'test',
            'OrderAttributes.SellerOrderAttributes.StoreName': 'test',
            'SellerId': 'test',
            'MWSAuthToken': 'test'}
        data_expected = self.request._querystring(parameters)
        self.assertEqual(mock_urlopen.call_args[1]['data'], data_expected)


    @patch('requests.post')
    def test_get_order_reference_details(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_requests_post
        self.client.get_order_reference_details(
            amazon_order_reference_id='test',
            address_consent_token='test',
            access_token='test',
            merchant_id='test',
            mws_auth_token='test')
        parameters = {
            'Action': 'GetOrderReferenceDetails',
            'AmazonOrderReferenceId': 'test',
            'AddressConsentToken': 'test',
            'AccessToken': 'test',
            'SellerId': 'test',
            'MWSAuthToken': 'test'}
        data_expected = self.request._querystring(parameters)
        self.assertEqual(mock_urlopen.call_args[1]['data'], data_expected)

    @patch('requests.post')
    def test_confirm_order_reference(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_requests_post
        self.client.confirm_order_reference(
            amazon_order_reference_id='test',
            merchant_id='test',
            mws_auth_token='test')
        parameters = {
            'Action': 'ConfirmOrderReference',
            'AmazonOrderReferenceId': 'test',
            'SellerId': 'test',
            'MWSAuthToken': 'test'}
        data_expected = self.request._querystring(parameters)
        self.assertEqual(mock_urlopen.call_args[1]['data'], data_expected)

    @patch('requests.post')
    def test_cancel_order_reference(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_requests_post
        self.client.cancel_order_reference(
            amazon_order_reference_id='test',
            cancelation_reason='test',
            merchant_id='test',
            mws_auth_token='test')
        parameters = {
            'Action': 'CancelOrderReference',
            'AmazonOrderReferenceId': 'test',
            'CancelationReason': 'test',
            'SellerId': 'test',
            'MWSAuthToken': 'test'}
        data_expected = self.request._querystring(parameters)
        self.assertEqual(mock_urlopen.call_args[1]['data'], data_expected)

    @patch('requests.post')
    def test_close_order_reference(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_requests_post
        self.client.close_order_reference(
            amazon_order_reference_id='test',
            closure_reason='test',
            merchant_id='test',
            mws_auth_token='test')
        parameters = {
            'Action': 'CloseOrderReference',
            'AmazonOrderReferenceId': 'test',
            'ClosureReason': 'test',
            'SellerId': 'test',
            'MWSAuthToken': 'test'}
        data_expected = self.request._querystring(parameters)
        self.assertEqual(mock_urlopen.call_args[1]['data'], data_expected)

    @patch('requests.post')
    def test_list_order_reference(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_requests_post
        self.client.list_order_reference(
            query_id='test',
            query_id_type='test',
            created_time_range_start='test',
            created_time_range_end='test',
            sort_order='test',
            page_size=1,
            merchant_id='test',
            mws_auth_token='test',
            order_reference_status_list_filter=['test','test'])
        
        if self.client.region in ('na'):
            payment_domain = 'NA_USD'
        elif self.client.region in ('uk', 'gb'):
            payment_domain = 'EU_GBP'
        elif self.client.region in ('jp', 'fe'):
            payment_domain = 'FE_JPY' 
        elif self.client.region in ('eu', 'de', 'fr', 'it', 'es', 'cy'):
            payment_domain = 'EU_EUR'
        else:
            raise ValueError("Error. The current region code does not match our records")


        parameters = {
            'Action': 'ListOrderReference',
            'QueryId': 'test',
            'QueryIdType': 'test',
            'PaymentDomain': payment_domain,
            'CreatedTimeRange.StartTime': 'test',
            'CreatedTimeRange.EndTime': 'test',
            'SortOrder': 'test',
            'PageSize': 1,
            'SellerId': 'test',
            'MWSAuthToken': 'test',
            'OrderReferenceStatusListFilter.OrderReferenceStatus.1': 'test',
            'OrderReferenceStatusListFilter.OrderReferenceStatus.2': 'test'}
        data_expected = self.request._querystring(parameters)
        self.assertEqual(mock_urlopen.call_args[1]['data'], data_expected)

    @patch('requests.post')
    def test_list_order_reference_time_check_error(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_requests_generic_error_post
        self.client.list_order_reference(
            query_id='test',
            query_id_type='test',
            created_time_range_start='test',
            created_time_range_end=None,
            sort_order=None,
            page_size=None,
            merchant_id='test',
            mws_auth_token='test',
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
            raise ValueError("Error. The current region code does not match our records")

         
        parameters = {
            'Action': 'ListOrderReference',
            'QueryId': 'test',
            'QueryIdType': 'test',
            'PaymentDomain': payment_domain,
            'SellerId': 'test',
            'MWSAuthToken': 'test',
            'CreatedTimeRange.StartTime': 'test'}
        data_expected = self.request._querystring(parameters)
        self.assertEqual(mock_urlopen.call_args[1]['data'], data_expected)
        
    @patch('requests.post')
    def test_list_order_reference_by_next_token(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_requests_post
        self.client.list_order_reference_by_next_token(
            next_page_token='test',
            merchant_id='test',
            mws_auth_token='test')
        parameters= {
            'Action': 'ListOrderReferenceByNextToken',
            'NextPageToken': 'test',
            'SellerId': 'test',
            'MWSAuthToken': 'test'}
        data_expected = self.request._querystring(parameters)
        self.assertEqual(mock_urlopen.call_args[1]['data'], data_expected)
        
    @patch('requests.post')
    def test_authorize(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_requests_post
        self.client.authorize(
            amazon_order_reference_id='test',
            authorization_reference_id='test',
            authorization_amount='test',
            seller_authorization_note='test',
            transaction_timeout=0,
            capture_now=True,
            soft_descriptor='test',
            merchant_id='test',
            mws_auth_token='test')
        parameters = {
            'Action': 'Authorize',
            'AmazonOrderReferenceId': 'test',
            'TransactionTimeout': '0',
            'AuthorizationReferenceId': 'test',
            'AuthorizationAmount.Amount': 'test',
            'AuthorizationAmount.CurrencyCode': 'test',
            'SellerAuthorizationNote': 'test',
            'TransactionTimeout': '0',
            'CaptureNow': 'true',
            'SoftDescriptor': 'test',
            'SellerId': 'test',
            'MWSAuthToken': 'test'}
        data_expected = self.request._querystring(parameters)
        self.assertEqual(mock_urlopen.call_args[1]['data'], data_expected)

    @patch('requests.post')
    def test_get_authorization_details(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_requests_post
        self.client.get_authorization_details(
            amazon_authorization_id='test',
            merchant_id='test',
            mws_auth_token='test')
        parameters = {
            'Action': 'GetAuthorizationDetails',
            'AmazonAuthorizationId': 'test',
            'SellerId': 'test',
            'MWSAuthToken': 'test'}
        data_expected = self.request._querystring(parameters)
        self.assertEqual(mock_urlopen.call_args[1]['data'], data_expected)

    @patch('requests.post')
    def test_capture(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_requests_post
        self.client.capture(
            amazon_authorization_id='test',
            capture_reference_id='test',
            capture_amount='test',
            seller_capture_note='test',
            soft_descriptor='test',
            merchant_id='test',
            mws_auth_token='test')
        parameters = {
            'Action': 'Capture',
            'AmazonAuthorizationId': 'test',
            'CaptureReferenceId': 'test',
            'CaptureAmount.Amount': 'test',
            'CaptureAmount.CurrencyCode': 'test',
            'SellerCaptureNote': 'test',
            'SoftDescriptor': 'test',
            'SellerId': 'test',
            'MWSAuthToken': 'test'}
        data_expected = self.request._querystring(parameters)
        self.assertEqual(mock_urlopen.call_args[1]['data'], data_expected)

    @patch('requests.post')
    def test_get_capture_details(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_requests_post
        self.client.get_capture_details(
            amazon_capture_id='test',
            merchant_id='test',
            mws_auth_token='test')
        parameters = {
            'Action': 'GetCaptureDetails',
            'AmazonCaptureId': 'test',
            'SellerId': 'test',
            'MWSAuthToken': 'test'}
        data_expected = self.request._querystring(parameters)
        self.assertEqual(mock_urlopen.call_args[1]['data'], data_expected)

    @patch('requests.post')
    def test_close_authorization(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_requests_post
        self.client.close_authorization(
            amazon_authorization_id='test',
            closure_reason='test',
            merchant_id='test',
            mws_auth_token='test')
        parameters = {
            'Action': 'CloseAuthorization',
            'AmazonAuthorizationId': 'test',
            'ClosureReason': 'test',
            'SellerId': 'test',
            'MWSAuthToken': 'test'}
        data_expected = self.request._querystring(parameters)
        self.assertEqual(mock_urlopen.call_args[1]['data'], data_expected)

    @patch('requests.post')
    def test_refund(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_requests_post
        self.client.refund(
            amazon_capture_id='test',
            refund_reference_id='test',
            refund_amount='test',
            seller_refund_note='test',
            soft_descriptor='test',
            merchant_id='test',
            mws_auth_token='test')
        parameters = {
            'Action': 'Refund',
            'AmazonCaptureId': 'test',
            'RefundReferenceId': 'test',
            'RefundAmount.Amount': 'test',
            'RefundAmount.CurrencyCode': 'test',
            'SellerRefundNote': 'test',
            'SoftDescriptor': 'test',
            'SellerId': 'test',
            'MWSAuthToken': 'test'}
        data_expected = self.request._querystring(parameters)
        self.assertEqual(mock_urlopen.call_args[1]['data'], data_expected)

    @patch('requests.post')
    def test_get_refund_details(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_requests_post
        self.client.get_refund_details(
            amazon_refund_id='test',
            merchant_id='test',
            mws_auth_token='test')
        parameters = {
            'Action': 'GetRefundDetails',
            'AmazonRefundId': 'test',
            'SellerId': 'test',
            'MWSAuthToken': 'test'}
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
