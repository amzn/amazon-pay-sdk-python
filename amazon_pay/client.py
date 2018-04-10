import re
import os
import sys
import json
import logging
import platform
import amazon_pay.ap_region as ap_region
import amazon_pay.version as ap_version
from amazon_pay.payment_request import PaymentRequest
from fileinput import filename


class AmazonPayClient:

    logger = logging.getLogger('__amazon_pay_sdk__')
    logger.addHandler(logging.NullHandler())

    """This client allows you to make all the necessary API calls to
        integrate with Amazon Pay.
    """
    # pylint: disable=too-many-instance-attributes, too-many-public-methods
    # pylint: disable=too-many-arguments, too-many-lines

    def __init__(
            self,
            mws_access_key=None,
            mws_secret_key=None,
            merchant_id=None,
            region=None,
            currency_code=None,
            sandbox=False,
            handle_throttle=True,
            application_name=None,
            application_version=None,
            log_enabled=False,
            log_file_name=None,
            log_level=None):
    
    
        """
        Parameters
        ----------
        mws_access_key : string, optional
            Your MWS access key. If no value is passed, check environment.
            Environment variable: AP_MWS_ACCESS_KEY
            (mws_access_key must be passed or specified in environment or this
             will result in an error)

        mws_secret_key : string, optional
            Your MWS secret key. If no value is passed, check environment.
            Environment variable: AP_MWS_SECRET_KEY
            (mws_secret_key must be passed or specified in environment or this
             will result in an error)

        merchant_id : string, optional
            Your merchant ID. If you are a marketplace enter the seller's merchant
            ID. If no value is passed, check environment.
            Environment variable: AP_MERCHANT_ID
            (merchant_id must be passed or specified in environment or this
             will result in an error)

        region : string, optional
            The region in which you are conducting business. If no value is
            passed, check environment.
            Environment variable: AP_REGION
            (region must be passed or specified in environment or this
             will result in an error)

        sandbox : string, optional
            Toggle sandbox mode. Default: False.

        currency_code: string, required
            Currency code for your region.
            Environment variable: AP_CURRENCY_CODE

        handle_throttle: boolean, optional
            If requests are throttled, do you want this client to pause and
            retry? Default: True

        application_name: string, optional
            The name of your application. This will get set in the UserAgent.
            Default: None

        application_version: string, optional
            Your application version. This will get set in the UserAgent.
            Default: None

        log_file_name: string, optional
            The name of the file for logging
            Default: None

        log_level: integer, optional
            The level of logging recorded
            Default: "None"
            Levels: "CRITICAL"; "ERROR"; "WARNING"; "INFO"; "DEBUG"; "NOTSET"
        """
        env_param_map = {'mws_access_key': 'AP_MWS_ACCESS_KEY',
                         'mws_secret_key': 'AP_MWS_SECRET_KEY',
                         'merchant_id': 'AP_MERCHANT_ID',
                         'region': 'AP_REGION',
                         'currency_code': 'AP_CURRENCY_CODE'}
        for param in env_param_map:
            if eval(param) is None:
                try:
                    setattr(self, param, os.environ[env_param_map[param]])
                except:
                    raise ValueError('Invalid {}.'.format(param))
            else:
                setattr(self, param, eval(param))

        try:
            self._region = ap_region.regions[self.region]
            # used for Login with Amazon helper
            self._region_code = self.region
        except KeyError:
            raise KeyError('Invalid region code ({})'.format(self.region))

        self.mws_access_key = self.mws_access_key
        self.mws_secret_key = self.mws_secret_key
        self.merchant_id = self.merchant_id
        self.currency_code = self.currency_code
        self.handle_throttle = handle_throttle
        self.application_name = application_name
        self.application_version = application_version

        self._sandbox = sandbox
        self._api_version = ap_version.versions['api_version']
        self._application_library_version = ap_version.versions[
            'application_version']
        self._mws_endpoint = None
        self._set_endpoint()

        if log_enabled is not False:
            numeric_level = getattr(logging, log_level.upper(), None)
            if numeric_level is not None:
                if log_file_name is not None:
                    self.logger.setLevel(numeric_level)
                    fh = logging.FileHandler(log_file_name)
                    self.logger.addHandler(fh)
                    fh.setLevel(numeric_level)
                else:
                    self.logger.setLevel(numeric_level)
                    ch = logging.StreamHandler(sys.stdout)
                    self.logger.addHandler(ch)
                    ch.setLevel(numeric_level)
        
        app_name_and_ver = ''
        
        if application_name not in ['', None]:
            app_name_and_ver = app_name_and_ver + str(application_name)
            if application_version not in ['', None]:
                app_name_and_ver = app_name_and_ver + '/' + str(application_version)

        elif application_version not in ['', None]:
            app_name_and_ver = app_name_and_ver + str(application_version)
        
        if ((application_name not in ['', None]) | (application_version not in ['', None])):
            app_name_and_ver = app_name_and_ver + '; '

        current_py_ver = ".".join(map(str, sys.version_info[:3]))
        
        self._user_agent = 'amazon-pay-sdk-python/{0} ({1}Python/{2}; {3}/{4})'.format(
            str(self._application_library_version),
            str(app_name_and_ver),
            str(current_py_ver),
            str(platform.system()),
            str(platform.release())
        )
        
        self.logger.debug('user agent: %s', self._user_agent)

        self._headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': self._user_agent}

    @property
    def sandbox(self):
        return self._sandbox

    @sandbox.setter
    def sandbox(self, value):
        """Set Sandbox mode"""
        self._sandbox = value
        self._set_endpoint()

    def _set_endpoint(self):
        """Set endpoint for API calls"""
        if self._sandbox:
            self._mws_endpoint = \
                'https://{}/OffAmazonPayments_Sandbox/{}'.format(
                    self._region, self._api_version)
        else:
            self._mws_endpoint = \
                'https://{}/OffAmazonPayments/{}'.format(
                    self._region, self._api_version)

    def get_login_profile(self, access_token, client_id):
        """Get profile associated with LWA user. This is a helper method for
        Login with Amazon (separate service). Added here for convenience.
        """
        from amazon_pay.login_with_amazon import LoginWithAmazon
        lwa_client = LoginWithAmazon(
            client_id=client_id,
            region=self._region_code,
            sandbox=self._sandbox)
        response = lwa_client.get_login_profile(access_token=access_token)
        return response

    def create_order_reference_for_id(
            self,
            object_id,
            object_id_type,
            order_total,
            inherit_shipping_address=True,
            confirm_now=False,
            platform_id=None,
            seller_note=None,
            seller_order_id=None,
            store_name=None,
            custom_information=None,
            merchant_id=None,
            mws_auth_token=None):
        # pylint: disable=too-many-arguments
        """Creates an order reference for the given object.

        Parameters
        ----------
        object_id : string, required
            The identifier of the object to be used to create an order reference.

        object_id_type : string, required
            The type of the object represented by the Id request parameter.

        order_total : string, required
            Specifies the total amount of the order represented by this order
            reference.

        inherit_shipping_address : boolean, optional
            Specifies whether to inherit the shipping address details from the
            object represented by the Id request parameter. Default: True

        confirm_now : boolean, optional
            Indicates whether to directly confirm the requested order reference.
            Default: False

        merchant_id : string, required
            Your merchant ID. If you are a marketplace enter the seller's merchant
            ID.

        mws_auth_token: string, optional
            Your marketplace web service auth token. Default: None

        """
        parameters = {
            'Action': 'CreateOrderReferenceForId',
            'Id': object_id,
            'IdType': object_id_type,
            'OrderTotal.Amount': order_total,
            'OrderTotal.CurrencyCode': self.currency_code}
        optionals = {
            'InheritShippingAddress': str(inherit_shipping_address).lower(),
            'ConfirmNow': str(confirm_now).lower(),
            'PlatformId': platform_id,
            'SellerNote': seller_note,
            'SellerOrderId': seller_order_id,
            'StoreName': store_name,
            'CustomInformation': custom_information,
            'SellerId': merchant_id,
            'MWSAuthToken': mws_auth_token}
        return self._operation(params=parameters, options=optionals)

    def get_billing_agreement_details(
            self,
            amazon_billing_agreement_id,
            address_consent_token=None,
            merchant_id=None,
            mws_auth_token=None):
        """Returns details about the Billing Agreement object and its current
        state.

        Parameters
        ----------
        amazon_billing_agreement_id : string, required
            The billing agreement identifier.

        address_consent_token : string, optional
            The buyer address consent token. You must provide a valid
            AddressConsentToken if you want to get the full shipping address
            before the billing agreement is confirmed. Otherwise you will only
            receive the city, state, postal code, and country before you confirm
            the billing agreement. Default: None

        merchant_id : string, required
            Your merchant ID. If you are a marketplace enter the seller's merchant
            ID.

        mws_auth_token: string, optional
            Your marketplace web service auth token. Default: None
        """
        parameters = {
            'Action': 'GetBillingAgreementDetails',
            'AmazonBillingAgreementId': amazon_billing_agreement_id}
        optionals = {
            'AddressConsentToken': address_consent_token,
            'SellerId': merchant_id,
            'MWSAuthToken': mws_auth_token}
        return self._operation(params=parameters, options=optionals)

    def set_billing_agreement_details(
            self,
            amazon_billing_agreement_id,
            platform_id=None,
            seller_note=None,
            seller_billing_agreement_id=None,
            store_name=None,
            custom_information=None,
            merchant_id=None,
            mws_auth_token=None):
        # pylint: disable=too-many-arguments
        """Sets billing agreement details such as a description of the agreement
        and other information about the seller.

        Parameters
        ----------
        amazon_billing_agreement_id : string, required
            The billing agreement identifier.

        platform_id : string, optional
            Represents the SellerId of the Solution Provider that developed the
            platform. This value should only be provided by solution providers.
            It should not be provided by sellers creating their own custom
            integration.

        seller_note : string, optional
            Represents a description of the billing agreement that is displayed
            in emails to the buyer.

        seller_billing_agreement_id : string, optional
            The seller-specified identifier of this billing agreement.

        store_name : string, optional
            The identifier of the store from which the order was placed. This
            overrides the default value in Seller Central under Settings >
            Account Settings. It is displayed to the buyer in the email they
            receive from Amazon and also in their transaction history on the
            Amazon Pay website.

        custom_information : string, optional
            Any additional information you wish to include with this billing
            agreement.

        merchant_id : string, required
            Your merchant ID. If you are a marketplace enter the seller's merchant
            ID.

        mws_auth_token: string, optional
            Your marketplace web service auth token. Default: None
        """
        parameters = {
            'Action': 'SetBillingAgreementDetails',
            'AmazonBillingAgreementId': amazon_billing_agreement_id}
        optionals = {
            'BillingAgreementAttributes.PlatformId': platform_id,
            'BillingAgreementAttributes.SellerNote': seller_note,
            'BillingAgreementAttributes.SellerBillingAgreementAttributes.SellerBillingAgreementId': seller_billing_agreement_id,
            'BillingAgreementAttributes.SellerBillingAgreementAttributes.StoreName': store_name,
            'BillingAgreementAttributes.SellerBillingAgreementAttributes.CustomInformation': custom_information,
            'SellerId': merchant_id,
            'MWSAuthToken': mws_auth_token}
        return self._operation(params=parameters, options=optionals)

    def confirm_billing_agreement(
            self,
            amazon_billing_agreement_id,
            merchant_id=None,
            mws_auth_token=None):
        """Confirms that the billing agreement is free of constraints and all
        required information has been set on the billing agreement.

        Parameters
        ----------
        amazon_billing_agreement_id : string, required
            The billing agreement identifier.

        merchant_id : string, required
            Your merchant ID. If you are a marketplace enter the seller's merchant
            ID.

        mws_auth_token: string, optional
            Your marketplace web service auth token. Default: None
        """
        parameters = {
            'Action': 'ConfirmBillingAgreement',
            'AmazonBillingAgreementId': amazon_billing_agreement_id}
        optionals = {
            'SellerId': merchant_id,
            'MWSAuthToken': mws_auth_token}
        return self._operation(params=parameters, options=optionals)

    def validate_billing_agreement(
            self,
            amazon_billing_agreement_id,
            merchant_id=None,
            mws_auth_token=None):
        """Validates the status of the BillingAgreement object and the payment
        method associated with it.

        Parameters
        ----------
        amazon_billing_agreement_id : string, required
            The billing agreement identifier.

        merchant_id : string, required
            Your merchant ID. If you are a marketplace enter the seller's merchant
            ID.

        mws_auth_token: string, optional
            Your marketplace web service auth token. Default: None
        """
        parameters = {
            'Action': 'ValidateBillingAgreement',
            'AmazonBillingAgreementId': amazon_billing_agreement_id}
        optionals = {
            'SellerId': merchant_id,
            'MWSAuthToken': mws_auth_token}
        return self._operation(params=parameters, options=optionals)

    def authorize_on_billing_agreement(
            self,
            amazon_billing_agreement_id,
            authorization_reference_id,
            authorization_amount,
            seller_authorization_note=None,
            transaction_timeout=1440,
            capture_now=False,
            soft_descriptor=None,
            seller_note=None,
            platform_id=None,
            seller_order_id=None,
            store_name=None,
            custom_information=None,
            inherit_shipping_address=True,
            merchant_id=None,
            mws_auth_token=None):
        # pylint: disable=too-many-arguments
        """Reserves a specified amount against the payment method(s) stored in
        the billing agreement.

        Parameters
        ----------
        amazon_billing_agreement_id : string, required
            The billing agreement identifier.

        authorization_reference_id : string, required
            The identifier for this authorization transaction that you specify.
            This identifier must be unique for all your transactions
            (authorization, capture, refund, etc.).

        authorization_amount : string, required
            Represents the amount to be authorized.

        seller_authorization_note : string, optional
            A description for the transaction that is displayed in emails to the
            buyer. Default: None

        transaction_timeout : unsigned integer, optional
            The number of minutes after which the authorization will
            automatically be closed and you will not be able to capture funds
            against the authorization. Default: 1440

        capture_now : boolean, optional
            Indicates whether to directly capture the amount specified by the
            AuthorizationAmount request parameter against an order reference
            (without needing to call Capture and without waiting until the order
            ships). The captured amount is disbursed to your account in the next
            disbursement cycle. Default: False

        seller_note : string, optional
            Represents a description of the order that is displayed in emails to
            the buyer. Default: None

        platform_id : string, optional
            Represents the SellerId of the Solution Provider that developed the
            platform. This value should only be provided by Solution Providers.
            It should not be provided by sellers creating their own custom
            integration. Default: None

        seller_order_id : string, optional
            The seller-specified identifier of this order. This is displayed to
            the buyer in the email they receive from Amazon and transaction
            history on the Amazon Pay website. Default: None

        store_name : string, optional
            The identifier of the store from which the order was placed. This
            overrides the default value in Seller Central under Settings >
            Account Settings. It is displayed to the buyer in the email they
            receive from Amazon and also in their transaction history on the
            Amazon Pay website. Default: None

        custom_information : string, optional
            Any additional information you wish to include with this order
            reference. Default: None

        inherit_shipping_address : boolean, optional
            Specifies whether to inherit the shipping address details from the
            object represented by the Id request parameter. Default: True

        merchant_id : string, required
            Your merchant ID. If you are a marketplace enter the seller's merchant
            ID.

        mws_auth_token: string, optional
            Your marketplace web service auth token. Default: None
        """
        parameters = {
            'Action': 'AuthorizeOnBillingAgreement',
            'AmazonBillingAgreementId': amazon_billing_agreement_id,
            'TransactionTimeout': transaction_timeout,
            'AuthorizationReferenceId': authorization_reference_id,
            'AuthorizationAmount.Amount': authorization_amount,
            'AuthorizationAmount.CurrencyCode': self.currency_code}
        optionals = {
            'CaptureNow': str(capture_now).lower(),
            'SellerAuthorizationNote': seller_authorization_note,
            'SoftDescriptor': soft_descriptor,
            'SellerNote': seller_note,
            'PlatformId': platform_id,
            'InheritShippingAddress': str(inherit_shipping_address).lower(),
            'SellerOrderAttributes.SellerOrderId': seller_order_id,
            'SellerOrderAttributes.StoreName': store_name,
            'SellerOrderAttributes.CustomInformation': custom_information,
            'SellerId': merchant_id,
            'MWSAuthToken': mws_auth_token}
        return self._operation(params=parameters, options=optionals)

    def close_billing_agreement(
            self,
            amazon_billing_agreement_id,
            closure_reason=None,
            merchant_id=None,
            mws_auth_token=None):
        """Confirms that you want to terminate the billing agreement with the
        buyer and that you do not expect to create any new order references or
        authorizations on this billing agreement.

        Parameters
        ----------
        amazon_billing_agreement_id : string, required
            The billing agreement identifier.

        closure_reason : string, optional
            Describes the reason for closing the billing agreement.
            Default: None

        merchant_id : string, required
            Your merchant ID. If you are a marketplace enter the seller's merchant
            ID.

        mws_auth_token: string, optional
            Your marketplace web service auth token. Default: None
        """
        parameters = {
            'Action': 'CloseBillingAgreement',
            'AmazonBillingAgreementId': amazon_billing_agreement_id}
        optionals = {
            'ClosureReason': closure_reason,
            'SellerId': merchant_id,
            'MWSAuthToken': mws_auth_token}
        return self._operation(params=parameters, options=optionals)

    def set_order_reference_details(
            self,
            amazon_order_reference_id,
            order_total,
            platform_id=None,
            seller_note=None,
            seller_order_id=None,
            store_name=None,
            custom_information=None,
            merchant_id=None,
            mws_auth_token=None):
        """Sets order reference details such as the order total and a
        description for the order.

        Parameters
        ----------
        amazon_order_reference_id : string, required
            The order reference identifier retrieved from the amazon pay Button
            widget.

        order_total : string, required
            Specifies the total amount of the order represented by this order
            reference.

        platform_id : string, optional
            Represents the SellerId of the Solution Provider that developed the
            platform. This value should only be provided by Solution Providers.
            It should not be provided by sellers creating their own custom
            integration. Default: None

        seller_note : string, optional
            Represents a description of the order that is displayed in emails
            to the buyer. Default: None

        seller_order_id : string, optional
            The seller-specified identifier of this order. This is displayed to
            the buyer in the email they receive from Amazon and also in their
            transaction history on the Amazon Pay website. Default: None

        store_name : string, optional
            The identifier of the store from which the order was placed. This
            overrides the default value in Seller Central under Settings >
            Account Settings. It is displayed to the buyer in the email they
            receive from Amazon and also in their transaction history on the
            Amazon Pay website. Default: None

        custom_information : string, optional
            Any additional information you wish to include with this order
            reference. Default: None

        merchant_id : string, required
            Your merchant ID. If you are a marketplace enter the seller's merchant
            ID.

        mws_auth_token: string, optional
            Your marketplace web service auth token. Default: None
        """
        parameters = {
            'Action': 'SetOrderReferenceDetails',
            'AmazonOrderReferenceId': amazon_order_reference_id,
            'OrderReferenceAttributes.OrderTotal.Amount': order_total,
            'OrderReferenceAttributes.OrderTotal.CurrencyCode': self.currency_code}
        optionals = {
            'OrderReferenceAttributes.PlatformId': platform_id,
            'OrderReferenceAttributes.SellerNote': seller_note,
            'OrderReferenceAttributes.SellerOrderAttributes.SellerOrderId': seller_order_id,
            'OrderReferenceAttributes.SellerOrderAttributes.StoreName': store_name,
            'OrderReferenceAttributes.SellerOrderAttributes.CustomInformation': custom_information,
            'SellerId': merchant_id,
            'MWSAuthToken': mws_auth_token}
        return self._operation(params=parameters, options=optionals)

    def set_order_attributes(
         self,
         amazon_order_reference_id,
         currency_code=None,
         amount=None,
         seller_order_id=None,
         payment_service_provider_id=None,
         payment_service_provider_order_id=None,
         platform_id=None,
         seller_note=None,
         request_payment_authorization=None,
         store_name=None,
         list_order_item_categories=None,
         custom_information=None,
         merchant_id=None,
         mws_auth_token=None):
        '''
        Return and update the information of an order with missing
        or updated information

        Parameters
        ----------
        amazon_order_reference_id : string, required
            The order reference identifier retrieved from the amazon pay Button
            widget.

        merchant_id : string, optional
            Your merchant ID. If you are a marketplace enter the seller's merchant
            ID.

        mws_auth_token: string, optional
            Your marketplace web service auth token. Default: None

        currency_code : string, optional
            The currency you're accepting the order in. A three-digit
            currency code, formatted based on the ISO 4217 standard.
            Default: None

        amount : string, optional
            Specifies the total amount of the order represented by this order
            reference. Default: None

        seller_order_id : string, optional
            The seller-specified identifier of this order. This is displayed to
            the buyer in the email they receive from Amazon and also in their
            transaction history on the Amazon Pay website. Default: None

        payment_service_provider_id : string, optional
            For use with a Payment Service Provider. This is their specific
            ID that is associated with Amazon Pay accounts and services.
            Default: None

        payment_service_provider_order_id : string, optional
            For use with a Payment Service Provider. This is their specific
            ID that is linked to your specific Amazon Pay Order Reference ID.
            Default: None

        platform_id : string, optional
            Represents the SellerId of the Solution Provider that developed the
            platform. This value should only be provided by Solution Providers.
            It should not be provided by sellers creating their own custom
            integration. Default: None

        seller_note : string, optional
            Represents a description of the order that is displayed in
            e-mails to the buyer. Default: None

        request_payment_authorization : boolean (string), optional
            Specifies if the merchants want their buyers to go through
            multi-factor authentication. Default: None

        store_name : string, optional
            The identifier of the store from which the order was placed. This
            overrides the default value in Seller Central under Settings >
            Account Settings. It is displayed to the buyer in the email they
            receive from Amazon and also in their transaction history on the
            Amazon Pay website. Default: None

        list_order_item_categories : list (string), optional
            List the category, or categories, that correlate to the order
            in question. You may set more than one item. Default: None

        custom_information : string, optional
            Any additional information you want your back-end system to
            keep record of. Your customers will not see this, and this
            will not be visible on Seller Central. This can only be
            accessed if your back end system supports calling this variable.
            Default: None
        '''

        parameters = {
            'Action': 'SetOrderAttributes',
            'AmazonOrderReferenceId': amazon_order_reference_id
        }

        optionals = {
            'OrderAttributes.OrderTotal.Amount': amount,
            'OrderAttributes.OrderTotal.CurrencyCode': currency_code,
            'OrderAttributes.SellerOrderAttributes.CustomInformation': custom_information,
            'OrderAttributes.PaymentServiceProviderAttributes.PaymentServiceProviderId':
                payment_service_provider_id,
            'OrderAttributes.PaymentServiceProviderAttributes.PaymentServiceProviderOrderId':
                payment_service_provider_order_id,
            'OrderAttributes.PlatformId': platform_id,
            'OrderAttributes.RequestPaymentAuthorization': request_payment_authorization,
            'OrderAttributes.SellerNote': seller_note,
            'OrderAttributes.SellerOrderAttributes.SellerOrderId': seller_order_id,
            'OrderAttributes.SellerOrderAttributes.StoreName': store_name,
            'SellerId': merchant_id,
            'MWSAuthToken': mws_auth_token
        }

        if list_order_item_categories is not None:
            self._enumerate(
                'OrderAttributes.SellerOrderAttributes.OrderItemCategories.OrderItemCategory.',
                list_order_item_categories, optionals)

        return self._operation(params=parameters, options=optionals)


    def get_order_reference_details(
            self,
            amazon_order_reference_id,
            access_token=None,
            address_consent_token=None,
            merchant_id=None,
            mws_auth_token=None):
        """Returns details about the order reference object and its current
        state.

        Parameters
        ----------
        amazon_order_reference_id : string, optional
            The order reference identifier. This value is retrieved from the
            amazon pay Button widget after the buyer has successfully authenticated
            with Amazon.
                
        access_token : string, optional
            The access token. This value is retrieved from the
            amazon pay Button widget after the buyer has successfully authenticated
            with Amazon. (Note: When using this value, you cannot use the
            address_consent_token at the same time, or this will cause an error.
            The same note applies when using just the address_consent_token)

        address_consent_token : string, optional
            The buyer address consent token. This value is retrieved from the
            amazon pay Button widget after the buyer has successfully authenticated
            with Amazon.

        merchant_id : string, required
            Your merchant ID. If you are a marketplace enter the seller's merchant
            ID.

        mws_auth_token: string, optional
            Your marketplace web service auth token. Default: None
        """
        parameters = {
            'Action': 'GetOrderReferenceDetails',
            'AmazonOrderReferenceId': amazon_order_reference_id
        }
        optionals = {
            'AddressConsentToken': address_consent_token,
            'AccessToken': access_token,
            'SellerId': merchant_id,
            'MWSAuthToken': mws_auth_token}
        return self._operation(params=parameters, options=optionals)

    def confirm_order_reference(
            self,
            amazon_order_reference_id,
            merchant_id=None,
            mws_auth_token=None):
        """Confirms that the order reference is free of constraints and all
        required information has been set on the order reference.

        Parameters
        ----------
        amazon_order_reference_id : string : required
            The order reference identifier.

        merchant_id : string, required
            Your merchant ID. If you are a marketplace enter the seller's merchant
            ID.

        mws_auth_token: string, optional
            Your marketplace web service auth token. Default: None
        """
        parameters = {
            'Action': 'ConfirmOrderReference',
            'AmazonOrderReferenceId': amazon_order_reference_id}
        optionals = {
            'SellerId': merchant_id,
            'MWSAuthToken': mws_auth_token}
        return self._operation(params=parameters, options=optionals)

    def cancel_order_reference(
            self,
            amazon_order_reference_id,
            cancelation_reason=None,
            merchant_id=None,
            mws_auth_token=None):
        """Cancels a previously confirmed order reference.

        Parameters
        ----------
        amazon_order_reference_id : string, required
            The order reference identifier.

        cancelation_reason : string, optional
            Describes the reason for the cancelation. Default: None

        merchant_id : string, required
            Your merchant ID. If you are a marketplace enter the seller's merchant
            ID.

        mws_auth_token: string, optional
            Your marketplace web service auth token. Default: None
        """
        parameters = {
            'Action': 'CancelOrderReference',
            'AmazonOrderReferenceId': amazon_order_reference_id}
        optionals = {
            'CancelationReason': cancelation_reason,
            'SellerId': merchant_id,
            'MWSAuthToken': mws_auth_token}
        return self._operation(params=parameters, options=optionals)

    def close_order_reference(
            self,
            amazon_order_reference_id,
            closure_reason=None,
            merchant_id=None,
            mws_auth_token=None):
        """Confirms that an order reference has been fulfilled
        (fully or partially) and that you do not expect to create any new
        authorizations on this order reference.

        Parameters
        ----------
        amazon_order_reference_id : string, required
            The ID of the order reference for which the details are being
            requested.

        closure_reason : string, optional
            Describes the reason for closing the order reference. Default: None

        merchant_id : string, required
            Your merchant ID. If you are a marketplace enter the seller's merchant
            ID.

        mws_auth_token: string, optional
            Your marketplace web service auth token. Default: None
        """
        parameters = {
            'Action': 'CloseOrderReference',
            'AmazonOrderReferenceId': amazon_order_reference_id}
        optionals = {
            'ClosureReason': closure_reason,
            'SellerId': merchant_id,
            'MWSAuthToken': mws_auth_token}
        return self._operation(params=parameters, options=optionals)

    def list_order_reference(
            self,
            query_id,
            query_id_type,
            created_time_range_start=None,
            created_time_range_end=None,
            sort_order=None,
            payment_domain=None,
            page_size=None,
            order_reference_status_list_filter=None,
            merchant_id=None,
            mws_auth_token=None):

        """
        Allows the search of any Amazon Pay order made using secondary
        seller order IDs generated manually, a solution provider, or a custom
        order fulfillment service.

        Parameters
        ==========================================
        query_id: string, required
            The identifier that the merchant wishes to use in relation to the
            query id type.

        query_id_type: string, required
            The type of query the id is referencing.
            Note: At this time, you can only use the query type (SellerOrderId).
            More options will be available in the future. Default: SellerOrderId
        
        payment_domain: string, optional
            The region and currency that will be set to authorize and collect
            payments from your customers. You can leave this blank for the 
            system to automatically assign the default payment domain for 
            your region.

        created_time_range_start: string, optional
            This filter will allow a merchant to search for a particular item
            within a date range of their choice.
            Note: If you wish to use this filter, you MUST fill in an end date,
            otherwise you will get an error returned when searching. You must
            also use the ISO 8601 time format to return a valid response when
            searching in a date range. Either of the two examples will work
            when using this filter. Default: None
            Example: YYYY-MM-DD or YYYY-MM-DDTHH:MM.

        created_time_range_end: string, optional
            The end-date for the date range the merchant wishes to search for
            any of their orders they're looking for.
            Note: You need to only use this option if you are using the 
            created_time_range_start parameter. Default: None

        sort_order: string, optional
            Filter can be set for "Ascending", or "Descending" order, and must
            be written out as shown above. This will sort the orders via 
            the respective option. Default: None

        page_size: integer, optional
            This filter limits how many results will be displayed per 
            request. Default: None

        merchant_id : string, optional
            Your merchant ID. If you are a marketplace enter the seller's merchant
            ID.

        mws_auth_token: string, optional
            Your marketplace web service auth token. Default: None

        order_reference_status_list_filter: list (string), optional
            When searching for an order, this filter is related to the status
            of the orders on file. You can search for any valid status for orders
            on file. Filters MUST be written out in English.
            Example: "Open", "Closed", "Suspended", "Canceled"
            Default: None       
        """
        
        if self.region is not None:
            region_code = self.region.lower()
            if region_code == 'na':
                payment_domain = 'NA_USD'
            elif region_code in ('uk', 'gb'):
                payment_domain = 'EU_GBP'
            elif region_code in ('jp', 'fe'):
                payment_domain = 'FE_JPY' 
            elif region_code in ('eu', 'de', 'fr', 'it', 'es', 'cy'):
                payment_domain = 'EU_EUR'
            else:
                raise ValueError("Error. The current region code does not match our records")

        parameters = {
            'Action': 'ListOrderReference',
            'QueryId': query_id,
            'QueryIdType': query_id_type,
            'PaymentDomain': payment_domain
        }            
        optionals = {
            'CreatedTimeRange.StartTime': created_time_range_start,
            'CreatedTimeRange.EndTime': created_time_range_end,
            'SortOrder': sort_order,
            'SellerId': merchant_id,
            'MWSAuthToken': mws_auth_token,
            'PageSize': page_size
        }

        if order_reference_status_list_filter is not None:
            self._enumerate(
                'OrderReferenceStatusListFilter.OrderReferenceStatus.',
                order_reference_status_list_filter, optionals)

        return self._operation(params=parameters, options=optionals)

    def list_order_reference_by_next_token(
            self,
            next_page_token,
            merchant_id=None,
            mws_auth_token=None):
        """
        next_page_token : string, required
            Uses the key from a list_order_reference call that provides a 
            NextPageToken for a merchant to call to review the next page 
            of items, and if applicable, another NextPageToken for the next
            set of items to read through.

        merchant_id : string, optional
            Your merchant ID. If you are a marketplace enter the seller's merchant
            ID.

        mws_auth_token: string, optional
            Your marketplace web service auth token. Default: None

        """

        parameters = {
            'Action': 'ListOrderReferenceByNextToken',
            'NextPageToken': next_page_token}
        optionals = {
            'SellerId': merchant_id,
            'MWSAuthToken': mws_auth_token}
        return self._operation(params=parameters, options=optionals)

    def get_payment_details(
            self,
            amazon_order_reference_id,
            merchant_id=None,
            mws_auth_token=None):

        '''
        This is a convenience function that will return every authorization, 
        charge, and refund call of an Amazon Pay order ID.

        Parameters
        ----------
        amazon_order_reference_id: string, required
            The ID of the order reference for which the details are being
            requested.

        merchant_id : string, optional
            Your merchant ID. If you are a marketplace enter the seller's merchant
            ID.

        mws_auth_token: string, optional
            Your marketplace web service auth token. Default: None
        '''

        parameters = {
            'Action': 'GetOrderReferenceDetails',
            'AmazonOrderReferenceId': amazon_order_reference_id
        }

        optionals = {
            'SellerId': merchant_id,
            'MWSAuthToken': mws_auth_token
        }

        query = self._operation(params=parameters, options=optionals)
        answer = []
        answer.append(query)
        queryID = json.loads(query.to_json())
        memberID = queryID['GetOrderReferenceDetailsResponse']\
            ['GetOrderReferenceDetailsResult']['OrderReferenceDetails']['IdList']

        if memberID is not None:
            '''
                This check will see if the variable is in a list form or not
                if it is not it will covert it into a single item list.
                Otherwise, it will process the variable normally as a list.
            '''
            if type(memberID['member']) is not list:
                memberID = [memberID['member']]
            else:
                memberID = memberID['member']

            for id in memberID:
                parameters = {
                    'Action': 'GetAuthorizationDetails',
                    'AmazonAuthorizationId': id
                }
                response = self._operation(params=parameters)
                answer.append(response)
                queryID = json.loads(response.to_json())
                chargeID = queryID['GetAuthorizationDetailsResponse']\
                    ['GetAuthorizationDetailsResult']['AuthorizationDetails']['IdList']

                if chargeID is not None:
                    chargeID = chargeID['member']
                    parameters = {
                        'Action': 'GetCaptureDetails',
                        'AmazonCaptureId': chargeID
                    }
                    response = self._operation(params=parameters)
                    queryID = json.loads(response.to_json())
                    refundID = queryID['GetCaptureDetailsResponse']\
                        ['GetCaptureDetailsResult']['CaptureDetails']['IdList']
                    answer.append(response)

                    if refundID is not None:
                        if type(refundID['member']) is not list:
                            refundID = [refundID['member']]
                        else:
                            refundID = refundID['member'] 

                        for id in refundID:
                            parameters = {
                                'Action': 'GetRefundDetails',
                                'AmazonRefundId': id
                            }
                        response = self._operation(params=parameters)
                        answer.append(response)

        return answer

    def authorize(
            self,
            amazon_order_reference_id,
            authorization_reference_id,
            authorization_amount,
            seller_authorization_note=None,
            transaction_timeout=1440,
            capture_now=False,
            soft_descriptor=None,
            merchant_id=None,
            mws_auth_token=None):
        # pylint: disable=too-many-arguments
        """Reserves a specified amount against the payment method(s) stored in
        the order reference.

        Parameters
        ----------
        amazon_order_reference_id : string, required
            The order reference identifier.

        authorization_reference_id : string, required
            The identifier for this authorization transaction that you specify.
            This identifier must be unique for all your transactions
            (authorization, capture, refund, etc.).

        authorization_amount : string, required
            Represents the amount to be authorized.

        seller_authorization_note : string, optional
            A description for the transaction that is displayed in emails to
            the buyer. Maximum: 225 characters.

        transaction_timeout : unsigned integer, optional
            The number of minutes after which the authorization will
            automatically be closed and you will not be able to capture funds
            against the authorization.

            Note: In asynchronous mode, the Authorize operation always returns
            the State as Pending. The authorization remains in this state until
            it is processed by Amazon. The processing time varies and can be a
            minute or more. After processing is complete, Amazon will notify
            you of the final processing status. For more information, see
            Synchronizing your systems with Amazon Pay in the Amazon Pay 
            Integration Guide. Default: 1440

        capture_now : boolean, optional
            Indicates whether to directly capture a specified amount against an
            order reference (without needing to call Capture and without waiting
            until the order ships). The captured amount is disbursed to your
            account in the next disbursement cycle.

            Note: The Amazon Pay policy states that you charge your buyer
            when you fulfill the items in the order. You should not collect
            funds prior to fulfilling the order. Default: False

        soft_descriptor : string, optional
            The description to be shown on the buyer’s payment instrument
            statement if CaptureNow is set to true. The soft descriptor sent to
            the payment processor is: “AMZ* <soft descriptor specified here>”.

        merchant_id : string, required
            Your merchant ID. If you are a marketplace enter the seller's merchant
            ID.

        mws_auth_token: string, optional
            Your marketplace web service auth token. Default: None
        """
        parameters = {
            'Action': 'Authorize',
            'AmazonOrderReferenceId': amazon_order_reference_id,
            'TransactionTimeout': transaction_timeout,
            'AuthorizationReferenceId': authorization_reference_id,
            'AuthorizationAmount.Amount': authorization_amount,
            'AuthorizationAmount.CurrencyCode': self.currency_code}
        optionals = {
            'SellerAuthorizationNote': seller_authorization_note,
            'CaptureNow': str(capture_now).lower(),
            'SoftDescriptor': soft_descriptor,
            'SellerId': merchant_id,
            'MWSAuthToken': mws_auth_token}
        return self._operation(params=parameters, options=optionals)

    def get_authorization_details(
            self,
            amazon_authorization_id,
            merchant_id=None,
            mws_auth_token=None):
        """Returns the status of a particular authorization and the total amount
        captured on the authorization.

        Parameters
        ----------
        amazon_authorization_id : string, required
            The authorization identifier that was generated by Amazon in the
            earlier call to Authorize.

        merchant_id : string, required
            Your merchant ID. If you are a marketplace enter the seller's merchant
            ID.

        mws_auth_token: string, optional
            Your marketplace web service auth token. Default: None
        """
        parameters = {
            'Action': 'GetAuthorizationDetails',
            'AmazonAuthorizationId': amazon_authorization_id}
        optionals = {
            'SellerId': merchant_id,
            'MWSAuthToken': mws_auth_token}
        return self._operation(params=parameters, options=optionals)

    def capture(
            self,
            amazon_authorization_id,
            capture_reference_id,
            capture_amount,
            seller_capture_note=None,
            soft_descriptor=None,
            merchant_id=None,
            mws_auth_token=None):
        # pylint: disable=too-many-arguments
        """Captures funds from an authorized payment instrument.

        Parameters
        ----------
        amazon_authorization_id : string, required
            The authorization identifier that was generated by Amazon in the
            earlier call to Authorize or AuthorizeOnBillingAgreement.

        capture_reference_id : string, required
            The identifier for this capture transaction that you specify. This
            identifier must be unique for all your transactions
            (authorization, capture, refund, etc.).

        capture_amount : string, required
            The amount to capture in this transaction. This amount cannot exceed
            the original amount that was authorized less any previously captured
            amount on this authorization.

        seller_capture_note : string, optional
            A description for the capture transaction that is displayed in
            emails to the buyer. Maximum: 255 characters, Default: None

        soft_descriptor : string, optional
            The description to be shown on the buyer’s payment instrument
            statement. The soft descriptor sent to the payment processor is:
            “AMZ* <soft descriptor specified here>”.

        merchant_id : string, required
            Your merchant ID. If you are a marketplace enter the seller's merchant
            ID.

        mws_auth_token: string, optional
            Your marketplace web service auth token. Default: None
        """
        parameters = {
            'Action': 'Capture',
            'AmazonAuthorizationId': amazon_authorization_id,
            'CaptureReferenceId': capture_reference_id,
            'CaptureAmount.Amount': capture_amount,
            'CaptureAmount.CurrencyCode': self.currency_code}
        optionals = {
            'SellerCaptureNote': seller_capture_note,
            'SoftDescriptor': soft_descriptor,
            'SellerId': merchant_id,
            'MWSAuthToken': mws_auth_token}
        return self._operation(params=parameters, options=optionals)

    def get_capture_details(
            self,
            amazon_capture_id,
            merchant_id=None,
            mws_auth_token=None):
        """Returns the status of a particular capture and the total amount
        refunded on the capture.

        Parameters
        ----------
        amazon_capture_id : string, required
            The capture identifier that was generated by Amazon on the earlier
            call to Capture.

        merchant_id : string, required
            Your merchant ID. If you are a marketplace enter the seller's merchant
            ID.

        mws_auth_token: string, optional
            Your marketplace web service auth token. Default: None
        """
        parameters = {
            'Action': 'GetCaptureDetails',
            'AmazonCaptureId': amazon_capture_id}
        optionals = {
            'SellerId': merchant_id,
            'MWSAuthToken': mws_auth_token}
        return self._operation(params=parameters, options=optionals)

    def close_authorization(
            self,
            amazon_authorization_id,
            closure_reason=None,
            merchant_id=None,
            mws_auth_token=None):
        """Closes an authorization.

        Parameters
        ----------
        amazon_authorization_id : string, required
            The authorization identifier that was generated by Amazon in the
            earlier call to Authorize.

        closure_reason : string, optional
            A description for the closure that is displayed in emails to the
            buyer.

        merchant_id : string, required
            Your merchant ID. If you are a marketplace enter the seller's merchant
            ID.

        mws_auth_token: string, optional
            Your marketplace web service auth token. Default: None
        """
        parameters = {
            'Action': 'CloseAuthorization',
            'AmazonAuthorizationId': amazon_authorization_id}
        optionals = {
            'ClosureReason': closure_reason,
            'SellerId': merchant_id,
            'MWSAuthToken': mws_auth_token}
        return self._operation(params=parameters, options=optionals)

    def refund(
            self,
            amazon_capture_id,
            refund_reference_id,
            refund_amount,
            seller_refund_note=None,
            soft_descriptor=None,
            merchant_id=None,
            mws_auth_token=None):
        # pylint: disable=too-many-arguments
        """Refunds a previously captured amount.

        Parameters
        ----------
        amazon_capture_id : string, required
            The capture identifier that was generated by Amazon in the earlier
            call to Capture.

        refund_reference_id : string, required
            The identifier for this refund transaction that you specify. This
            identifier must be unique for all your transactions
            (authorization, capture, refund, etc.).

        refund_amount : string, required
            The amount to refund. This amount cannot exceed:
                In the US: the lesser of 15% or $75 above the captured amount
                    less the amount already refunded on the capture.
                In the UK: the lesser of 15% or £75 above the captured amount
                    for the Capture object.
                In Germany: the lesser of 15% or €75 above the captured amount
                    for the Capture object.

        seller_refund_note : string, optional
            A description for the refund that is displayed in emails to the
            buyer. Maximum: 255 characters, Default: None

        soft_descriptor : string, optional
            The description to be shown on the buyer’s payment instrument
            statement. The soft descriptor sent to the payment processor is:
            “AMZ* <soft descriptor specified here>”.

        merchant_id : string, required
            Your merchant ID. If you are a marketplace enter the seller's merchant
            ID.

        mws_auth_token: string, optional
            Your marketplace web service auth token. Default: None
        """
        parameters = {
            'Action': 'Refund',
            'AmazonCaptureId': amazon_capture_id,
            'RefundReferenceId': refund_reference_id,
            'RefundAmount.Amount': refund_amount,
            'RefundAmount.CurrencyCode': self.currency_code}
        optionals = {
            'SellerRefundNote': seller_refund_note,
            'SoftDescriptor': soft_descriptor,
            'SellerId': merchant_id,
            'MWSAuthToken': mws_auth_token}
        return self._operation(params=parameters, options=optionals)

    def get_refund_details(
            self,
            amazon_refund_id,
            merchant_id=None,
            mws_auth_token=None):
        """Returns the status of a particular refund.

        Parameters
        ----------
        amazon_refund_id : string, required
            The Amazon-generated identifier for this refund transaction.

        merchant_id : string, required
            Your merchant ID. If you are a marketplace enter the seller's merchant
            ID.

        mws_auth_token: string, optional
            Your marketplace web service auth token. Default: None
        """
        parameters = {
            'Action': 'GetRefundDetails',
            'AmazonRefundId': amazon_refund_id}
        optionals = {
            'SellerId': merchant_id,
            'MWSAuthToken': mws_auth_token}
        return self._operation(params=parameters, options=optionals)

    def get_service_status(self):
        """Returns the operational status of the Off-Amazon Payments API section.
        """
        parameters = {
            'Action': 'GetServiceStatus'}

        return self._operation(params=parameters)

    def charge(
            self,
            amazon_reference_id,
            charge_amount,
            authorize_reference_id,
            charge_note,
            charge_order_id=None,
            store_name=None,
            custom_information=None,
            platform_id=None,
            merchant_id=None,
            mws_auth_token=None,
            soft_descriptor=None):
        """Combine the set, confirm, authorize, and capture calls into one.

        Parameters
        ----------
        amazon_reference_id : string, required
            The order reference or billing agreement identifier.

        charge_amount : string, required
            The amount to capture in this transaction.

        authorize_reference_id : string, required
            The seller-specified identifier of this charge. This parameter sets
            both authorization_reference_id and capture_reference_id.

        charge_order_id : string, optional
            The seller-specified identifier of this order. This is displayed to
            the buyer in the emails they receive from Amazon and also in their
            transaction history on the Amazon Pay website.

        store_name : string, optional
            The identifier of the store from which the order was placed. This
            overrides the default value in Seller Central under Settings >
            Account Settings. It is displayed to the buyer in the email they
            receive from Amazon and also in their transaction history on the
            Amazon Pay website.

        custom_information : string, optional
            Any additional information you wish to include with this billing
            agreement.

        charge_note : string, optional
            A description for the capture transaction that is displayed in
            emails to the buyer.

        platform_id
            Represents the SellerId of the Solution Provider that developed the
            platform. This value should only be provided by Solution Providers.
            It should not be provided by sellers creating their own custom
            integration.

        merchant_id : string, required
            Your merchant ID. If you are a marketplace enter the seller's merchant
            ID.

        mws_auth_token: string, optional
            Your marketplace web service auth token. Default: None

        soft_descriptor : string, optional
            The description to be shown on the buyer’s payment instrument
            statement if CaptureNow is set to true. The soft descriptor sent to
            the payment processor is: “AMZ* <soft descriptor specified here>”.
        """

        if self.is_order_reference_id(amazon_reference_id):
            # set
            ret = self.set_order_reference_details(
                amazon_order_reference_id=amazon_reference_id,
                order_total=charge_amount,
                platform_id=platform_id,
                seller_note=charge_note,
                seller_order_id=charge_order_id,
                store_name=store_name,
                custom_information=custom_information,
                merchant_id=merchant_id,
                mws_auth_token=mws_auth_token)
            if ret.success:
                # confirm
                ret = self.confirm_order_reference(
                    amazon_order_reference_id=amazon_reference_id,
                    merchant_id=merchant_id,
                    mws_auth_token=mws_auth_token)
                if ret.success:
                    # auth
                    ret = self.authorize(
                        amazon_order_reference_id=amazon_reference_id,
                        authorization_reference_id=authorize_reference_id,
                        authorization_amount=charge_amount,
                        seller_authorization_note=charge_note,
                        transaction_timeout=0,
                        capture_now=True,
                        soft_descriptor=soft_descriptor,
                        merchant_id=merchant_id,
                        mws_auth_token=mws_auth_token)
                    return ret
                else:
                    return ret
            else:
                return ret

        if self.is_billing_agreement_id(amazon_reference_id):
            """Since this is a billing agreement we need to see if details have
            already been set. If so, we just need to authorize.
            """
            ret = self.get_billing_agreement_details(
                amazon_billing_agreement_id=amazon_reference_id,
                address_consent_token=None,
                merchant_id=merchant_id,
                mws_auth_token=mws_auth_token)
            if ret.to_dict().get('GetBillingAgreementDetailsResponse').get(
                'GetBillingAgreementDetailsResult').get(
                    'BillingAgreementDetails').get(
                        'BillingAgreementStatus').get('State') == 'Draft':
                # set
                ret = self.set_billing_agreement_details(
                    amazon_billing_agreement_id=amazon_reference_id,
                    platform_id=platform_id,
                    seller_note=charge_note,
                    seller_billing_agreement_id=charge_order_id,
                    store_name=store_name,
                    custom_information=custom_information,
                    merchant_id=merchant_id,
                    mws_auth_token=mws_auth_token)
                if ret.success:
                    # confirm
                    ret = self.confirm_billing_agreement(
                        amazon_billing_agreement_id=amazon_reference_id,
                        merchant_id=merchant_id,
                        mws_auth_token=mws_auth_token)
                    if not ret.success:
                        return ret
                else:
                    return ret
            # auth
            ret = self.authorize_on_billing_agreement(
                amazon_billing_agreement_id=amazon_reference_id,
                authorization_reference_id=authorize_reference_id,
                authorization_amount=charge_amount,
                seller_authorization_note=charge_note,
                transaction_timeout=0,
                capture_now=True,
                soft_descriptor=soft_descriptor,
                seller_note=charge_note,
                platform_id=platform_id,
                seller_order_id=charge_order_id,
                store_name=store_name,
                custom_information=custom_information,
                inherit_shipping_address=True,
                merchant_id=merchant_id,
                mws_auth_token=mws_auth_token)
            return ret

    def is_order_reference_id(self, amazon_reference_id):
        """Checks if Id is order reference. P or S at the beginning indicate a
        order reference ID.
        """
        return re.search('^(P|S)', amazon_reference_id)

    def is_billing_agreement_id(self, amazon_reference_id):
        """Checks if Id is billing agreement. B or C at the beginning indicate a
        billing agreement ID
        """
        return re.search('^(B|C)', amazon_reference_id)

    def _operation(self, params, options=None):
        """Parses required and optional parameters and passes to the Request
        object.
        """
        if options is not None:
            for opt in options.keys():
                if options[opt] is not None:
                    params[opt] = options[opt]

        request = PaymentRequest(
            params=params,
            config={'mws_access_key': self.mws_access_key,
                    'mws_secret_key': self.mws_secret_key,
                    'api_version': self._api_version,
                    'merchant_id': self.merchant_id,
                    'mws_endpoint': self._mws_endpoint,
                    'headers': self._headers,
                    'handle_throttle': self.handle_throttle})

        request.send_post()
        return request.response
 
    def _enumerate(
        self,
        category,
        filter_types,
        optionals):

        def enumerate_param(param, values):
            """
                Builds a dictionary of an enumerated parameter from the filter list.
                This is currently used for two API calls in the client. Specifically,
                set_order_attributes & list_order_reference
                Example: (For set_order_attributes)
                enumerate_param(
                'OrderAttributes.SellerOrderAttributes.OrderItemCategories.OrderItemCategory.',
                (["Antiques", "Outdoor"])
                returns
                {
                OrderAttributes.SellerOrderAttributes.OrderItemCategories.OrderItemCategory.1:
                    Antiques,
                OrderAttributes.SellerOrderAttributes.OrderItemCategories.OrderItemCategory.2:
                    Outdoor
                }
            """
            params = {}
            if values is not None:
                if not param.endswith('.'):
                    param = "%s." % param
                for num, value in enumerate(values):
                    params['%s%d' % (param, (num + 1))] = value
            return params

        """This will apply your filters from the list filter parameter"""
        if isinstance(filter_types, list):
            optionals.update(enumerate_param(category, filter_types))
        else:
            if ',' in filter_types:
                filter_types = filter_types.replace(' ','')
                filter_types = filter_types.split(',')
                optionals.update(enumerate_param(category, filter_types))
            else:
                raise Exception("Invalid format for this request.")
