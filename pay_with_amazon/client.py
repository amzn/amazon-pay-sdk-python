import re
import os
import sys
import pay_with_amazon.pwa_region as pwa_region
import pay_with_amazon.version as pwa_version
from pay_with_amazon.payment_request import PaymentRequest


class PayWithAmazonClient(object):

    """This client allows you to make all the necessary API calls to
        integrate with Login and Pay with Amazon.
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
            application_version=None):
        """
        Parameters
        ----------
        mws_access_key : string, optional
            Your MWS access key. If no value is passed, check environment.
            Environment variable: PWA_MWS_ACCESS_KEY

        mws_secret_key : string, optional
            Your MWS secret key. If no value is passed, check environment.
            Environment variable: PWA_MWS_SECRET_KEY

        merchant_id : string, optional
            Your merchant ID. If you are a marketplace enter the seller's merchant
            ID. If no value is passed, check environment.
            Environment variable: PWA_MERCHANT_ID

        region : string, optional
            The region in which you are conducting business. If no value is
            passed, check environment.
            Environment variable: PWA_REGION

        sandbox : string, optional
            Toggle sandbox mode. Default: False.

        currency_code: string, optional
            Currency code for your region.
            Environment variable: PWA_CURRENCY_CODE

        handle_throttle: boolean, optional
            If requests are throttled, do you want this client to pause and
            retry? Default: True

        application_name: string, optional
            The name of your application. This will get set in the UserAgent.
            Default: None

        application_version: string, optional
            Your application version. This will get set in the UserAgent.
            Default: None
        """
        env_param_map = {'mws_access_key': 'PWA_MWS_ACCESS_KEY',
                         'mws_secret_key': 'PWA_MWS_SECRET_KEY',
                         'merchant_id': 'PWA_MERCHANT_ID',
                         'region': 'PWA_REGION',
                         'currency_code': 'PWA_CURRENCY_CODE'}
        for param in env_param_map:
            if eval(param) is None:
                try:
                    setattr(self, param, os.environ[env_param_map[param]])
                except:
                    raise ValueError('Invalid {0}.'.format(param))
            else:
                setattr(self, param, eval(param))

        try:
            self._region = pwa_region.regions[self.region]
            # used for Login with Amazon helper
            self._region_code = self.region
        except KeyError:
            raise KeyError('Invalid region code ({0})'.format(self.region))

        self.mws_access_key = self.mws_access_key
        self.mws_secret_key = self.mws_secret_key
        self.merchant_id = self.merchant_id
        self.currency_code = self.currency_code
        self.handle_throttle = handle_throttle
        self.application_name = application_name
        self.application_version = application_version

        self._sandbox = sandbox
        self._api_version = pwa_version.versions['api_version']
        self._application_library_version = pwa_version.versions[
            'application_version']
        self._mws_endpoint = None
        self._set_endpoint()

        application = {'Language': 'Python',
                       'Platform': sys.platform,
                       'MWSClientVersion': self._api_version}
        if application_name is not None:
            application['ApplicationName'] = application_name

        if application_version is not None:
            application['ApplicationVersion'] = application_version

        self._user_agent = '; '.join(
            '{0}={1}'.format(k, v) for (k, v) in sorted(application.items())
        )

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
                'https://{0}/OffAmazonPayments_Sandbox/{1}'.format(
                    self._region, self._api_version)
        else:
            self._mws_endpoint = \
                'https://{0}/OffAmazonPayments/{1}'.format(
                    self._region, self._api_version)

    def get_login_profile(self, access_token, client_id):
        """Get profile associated with LWA user. This is a helper method for
        Login with Amazon (separate service). Added here for convenience.
        """
        from pay_with_amazon.login_with_amazon import LoginWithAmazon
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
            Amazon Payments website.

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
            history on the Amazon Payments website. Default: None

        store_name : string, optional
            The identifier of the store from which the order was placed. This
            overrides the default value in Seller Central under Settings >
            Account Settings. It is displayed to the buyer in the email they
            receive from Amazon and also in their transaction history on the
            Amazon Payments website. Default: None

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
        # pylint: disable=too-many-arguments
        """Sets order reference details such as the order total and a
        description for the order.

        Parameters
        ----------
        amazon_order_reference_id : string, required
            The order reference identifier retrieved from the Amazon Button
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
            transaction history on the Amazon Payments website. Default: None

        store_name : string, optional
            The identifier of the store from which the order was placed. This
            overrides the default value in Seller Central under Settings >
            Account Settings. It is displayed to the buyer in the email they
            receive from Amazon and also in their transaction history on the
            Amazon Payments website. Default: None

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

    def get_order_reference_details(
            self,
            amazon_order_reference_id,
            address_consent_token=None,
            merchant_id=None,
            mws_auth_token=None):
        """Returns details about the order reference object and its current
        state.

        Parameters
        ----------
        amazon_order_reference_id : string, optional
            The order reference identifier. This value is retrieved from the
            Amazon Button widget after the buyer has successfully authenticated
            with Amazon.

        address_consent_token : string, optional
            The buyer address consent token. This value is retrieved from the
            Amazon Button widget after the buyer has successfully authenticated
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
            Synchronizing your systems with Amazon Payments in the Login and
            Pay with Amazon Integration Guide. Default: 1440

        capture_now : boolean, optional
            Indicates whether to directly capture a specified amount against an
            order reference (without needing to call Capture and without waiting
            until the order ships). The captured amount is disbursed to your
            account in the next disbursement cycle.

            Note: The Amazon Payments policy states that you charge your buyer
            when you fulfill the items in the order. You should not collect
            funds prior to fulfilling the order. Default: False

        soft_descriptor : string, optional
            The description to be shown on the buyer's payment instrument
            statement if CaptureNow is set to true. The soft descriptor sent to
            the payment processor is: "AMZ* <soft descriptor specified here>".

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
            The description to be shown on the buyer's payment instrument
            statement. The soft descriptor sent to the payment processor is:
            "AMZ* <soft descriptor specified here>".

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
            The description to be shown on the buyer's payment instrument
            statement. The soft descriptor sent to the payment processor is:
            "AMZ* <soft descriptor specified here>".

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
            transaction history on the Amazon Payments website.

        store_name : string, optional
            The identifier of the store from which the order was placed. This
            overrides the default value in Seller Central under Settings >
            Account Settings. It is displayed to the buyer in the email they
            receive from Amazon and also in their transaction history on the
            Amazon Payments website.

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
            The description to be shown on the buyer's payment instrument
            statement if CaptureNow is set to true. The soft descriptor sent to
            the payment processor is: "AMZ* <soft descriptor specified here>".
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
