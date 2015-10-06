## Synopsis

The official Login and Pay with Amazon Python SDK.

## Requirements

Python >= 3.2<br/>
pyOpenSSL >= 0.11<br/>
Requests >= 2.6.0<br/>

## Documentation

* The Integration steps can be found [here](https://payments.amazon.com/documentation)

## Sample

* View the sample integration demo [here](https://amzn.github.io/login-and-pay-with-amazon-sdk-samples/)

## Installation

```
$ git clone https://github.com/amzn/login-and-pay-with-amazon-sdk-python.git
$ cd login-and-pay-with-amazon-sdk-python
$ sudo python3 setup.py install
```

PyPI
```
$ sudo pip3 install pay_with_amazon
```

Test it.
```
$ python3
Python 3.4.0 (default, Apr 11 2014, 13:05:11) 
[GCC 4.8.2] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> from pay_with_amazon.client import PayWithAmazonClient
>>> 
```

If you run into problems related to 'IncompleteRead' try the following.
```
$ sudo easy_install3 -U pip
```

## Client Code Examples
*This is only a subset of calls. All MWS Pay with Amazon API calls are supported.*

Instantiate the client. The only required parameter is *sandbox*. If you do not pass in the other parameters you must set the corresponding environment variable. 
See the [client](https://github.com/amzn/login-and-pay-with-amazon-sdk-python/blob/master/pay_with_amazon/client.py#L31-L67) documentation for more information.
```python
from pay_with_amazon.client import PayWithAmazonClient

client = PayWithAmazonClient(
        mws_access_key='YOUR_ACCESS_KEY',
        mws_secret_key='YOUR_SECRET_KEY',
        merchant_id='YOUR_MERCHANT_ID',
        region='na',
        currency_code='USD',
        sandbox=True)
```

GetOrderReferenceDetails
```python
ret = client.get_order_reference_details(
    amazon_order_reference_id='AMAZON_ORDER_REFERENCE_ID',
    address_consent_token='ADDRESS_CONSENT_TOKEN')
print(ret.to_json()) # to_xml and to_dict are also valid
```

SetOrderReferenceDetails
```python
ret = client.set_order_reference_details(
    amazon_order_reference_id='AMAZON_ORDER_REFERENCE_ID',
    order_total='1.00',
    seller_note='My seller note.',
    seller_order_id='MY_UNIQUE_ORDER_ID',
    store_name='My store name.',
    custom_information='My custom information.')
print(ret.to_json()) # to_xml and to_dict are also valid
```

ConfirmOrderReference
```python
ret = client.confirm_order_reference(
    amazon_order_reference_id='AMAZON_ORDER_REFERENCE_ID')
print(ret.to_json()) # to_xml and to_dict are also valid
```

Authorize
```python
ret = client.authorize(
    amazon_order_reference_id='AMAZON_ORDER_REFERENCE_ID',
    authorization_reference_id='MY_UNIQUE_AUTHORIZATION_ID',
    amount='1.00',
    seller_authorization_note='Authorization note.',
    transaction_timeout=10,
    capture_now=False)    
json_response = ret.to_json()
```

GetAuthorizationDetails
```python
# authorization ID returned from 'Authorize' call.
authorization_id = json.loads(json_response)['AuthorizeResponse'][
    'AuthorizeResult']['AuthorizationDetails']['AmazonAuthorizationId']

ret = client.get_authorization_details(
    amazon_authorization_id=authorization_id)
print(ret.to_json()) # to_xml and to_dict are also valid
```

Capture
```python
# authorization ID returned from 'Authorize' call.
ret = client.capture(
    amazon_authorization_id='MY_ATHORIZATION_ID',
    capture_reference_id='MY_UNIQUE_CAPTURE_ID',
    capture_amount='1.00',
    seller_capture_note='Capture note.')
print(ret.to_json()) # to_xml and to_dict are also valid
```

GetCaptureDetails
```python
# capture ID returned from 'Capture' call.
ret = client.get_capture_details(
    amazon_capture_id='MY_CAPTURE_ID')
print(ret.to_json()) # to_xml and to_dict are also valid
 ```

Charge - This method combines all the above calls into one which allows you to set, confirm, authorize, and capture in a single call.
 If this is a billing agreement it will first check to see what state it's in to see if it needs to be set. If already set, it will authorize on the billing agreement.
```python
ret = client.charge(
    amazon_order_reference_id='ORDER_REFERENCE_ID or BILLING_AGREEMENT_ID',
    charge_amount='10.00',
    charge_note='MY_CHARGE_NOTE',
    authorize_reference_id='MY_UNIQUE_AUTHORIZATION_ID')
    print(ret.to_json())
```

## Example Responses

GetOrderReferenceDetails (JSON)
```json
{
  "GetOrderReferenceDetailsResponse": {
    "ResponseMetadata": {
      "RequestId": "2bf1f693-0f8f-4c11-990a-db59e3ec571d"
    },
    "GetOrderReferenceDetailsResult": {
      "OrderReferenceDetails": {
        "CreationTimestamp": "2015-03-05T17:56:11.317Z",
        "AmazonOrderReferenceId": "S01-5835994-2647190",
        "OrderTotal": {
          "CurrencyCode": "USD",
          "Amount": "100.00"
        },
        "SellerNote": "My seller note.",
        "SellerOrderAttributes": {
          "CustomInformation": "My custom information.",
          "SellerOrderId": "14553",
          "StoreName": "My store name."
        },
        "ReleaseEnvironment": "Sandbox",
        "Buyer": {
          "Email": "bob@example.com",
          "Name": "Bob"
        },
        "Destination": {
          "DestinationType": "Physical",
          "PhysicalDestination": {
            "PostalCode": "60602",
            "Phone": "800-000-0000",
            "Name": "Susie Smith",
            "StateOrRegion": "IL",
            "AddressLine2": "Suite 2500",
            "AddressLine1": "10 Ditka Ave",
            "CountryCode": "US",
            "City": "Chicago"
          }
        },
        "OrderReferenceStatus": {
          "LastUpdateTimestamp": "2015-03-05T17:57:16.233Z",
          "State": "Open"
        },
        "ExpirationTimestamp": "2015-09-01T17:56:11.317Z",
        "IdList": {
          "member": [
            "S01-5835994-2647190-A082288",
            "S01-5835994-2647190-A044104",
            "S01-5835994-2647190-A097659",
            "S01-5835994-2647190-A061272",
            "S01-5835994-2647190-A037220",
            "S01-5835994-2647190-A092983",
            "S01-5835994-2647190-A077012",
            "S01-5835994-2647190-A065424",
            "S01-5835994-2647190-A041441",
            "S01-5835994-2647190-A058669"
          ]
        }
      }
    }
  }
}
```

GetOrderReferenceDetails (XML)
```xml
<GetOrderReferenceDetailsResponse xmlns="http://mws.amazonservices.com/schema/OffAmazonPayments/2013-01-01">
  <GetOrderReferenceDetailsResult>
    <OrderReferenceDetails>
      <AmazonOrderReferenceId>S01-5835994-2647190</AmazonOrderReferenceId>
      <ExpirationTimestamp>2015-09-01T17:56:11.317Z</ExpirationTimestamp>
      <SellerNote>My seller note.</SellerNote>
      <OrderTotal>
        <Amount>100.00</Amount>
        <CurrencyCode>USD</CurrencyCode>
      </OrderTotal>
      <IdList>
        <member>S01-5835994-2647190-A082288</member>
        <member>S01-5835994-2647190-A044104</member>
        <member>S01-5835994-2647190-A097659</member>
        <member>S01-5835994-2647190-A061272</member>
        <member>S01-5835994-2647190-A037220</member>
        <member>S01-5835994-2647190-A092983</member>
        <member>S01-5835994-2647190-A077012</member>
        <member>S01-5835994-2647190-A065424</member>
        <member>S01-5835994-2647190-A041441</member>
        <member>S01-5835994-2647190-A058669</member>
      </IdList>
      <OrderReferenceStatus>
        <LastUpdateTimestamp>2015-03-05T17:57:16.233Z</LastUpdateTimestamp>
        <State>Open</State>
      </OrderReferenceStatus>
      <Destination>
        <DestinationType>Physical</DestinationType>
        <PhysicalDestination>
          <Phone>800-000-0000</Phone>
          <PostalCode>60602</PostalCode>
          <Name>Susie Smith</Name>
          <CountryCode>US</CountryCode>
          <StateOrRegion>IL</StateOrRegion>
          <AddressLine2>Suite 2500</AddressLine2>
          <AddressLine1>10 Ditka Ave</AddressLine1>
          <City>Chicago</City>
        </PhysicalDestination>
      </Destination>
      <ReleaseEnvironment>Sandbox</ReleaseEnvironment>
      <Buyer>
        <Email>bob@example.com</Email>
        <Name>Bob</Name>
      </Buyer>
      <SellerOrderAttributes>
        <CustomInformation>My custom information.</CustomInformation>
        <StoreName>My store name.</StoreName>
        <SellerOrderId>14553</SellerOrderId>
      </SellerOrderAttributes>
      <CreationTimestamp>2015-03-05T17:56:11.317Z</CreationTimestamp>
    </OrderReferenceDetails>
  </GetOrderReferenceDetailsResult>
  <ResponseMetadata>
    <RequestId>6c2a39ce-afb3-492e-8e67-4945a9a63f0e</RequestId>
  </ResponseMetadata>
</GetOrderReferenceDetailsResponse>
```

## IPN Handler Code Example
Flask
```python
from flask import request

@app.route('/ipn_handler', methods=['GET', 'POST'])
def ipn_handler():
    from pay_with_amazon.ipn_handler import IpnHandler
    
    ret = IpnHandler(request.data, request.headers)
    if ret.authenticate():
        return(ret.to_json())
    else:
        return(ret.error)
```
Response
```json
{
  "OrderReferenceNotification": {
    "OrderReference": {
      "OrderTotal": {
        "CurrencyCode": "USD",
        "Amount": "0.0"
      },
      "CreationTimestamp": "2013-01-01T01:01:01.001Z",
      "OrderReferenceStatus": {
        "State": "Closed",
        "ReasonCode": "AmazonClosed",
        "LastUpdateTimestamp": "2013-01-01T01:01:01.001Z"
      },
      "SellerOrderAttributes": null,
      "AmazonOrderReferenceId": "P01-0000000-0000000-000000",
      "ExpirationTimestamp": "2013-01-01T01:01:01.001Z"
    }
  }
}
```


## API Reference

[Official Login and Pay with Amazon API Reference](https://payments.amazon.com/documentation) 


