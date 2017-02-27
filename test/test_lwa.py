import unittest
from unittest.mock import Mock, patch
from amazon_pay.login_with_amazon import LoginWithAmazon


class LoginWithAmazonClientTest(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None

        self.lwa_client = LoginWithAmazon(
            client_id='client_id',
            region='na',
            sandbox=True)

    def mock_get_error(self, url, headers, params, verify):
        mock_response = Mock()
        mock_response.json.return_value = {
            "error": "test error",
            "error_description": "This is a test error"}
        mock_response.status_code = 200
        return mock_response

    def mock_get_error_aud(self, url, headers, params, verify):
        mock_response = Mock()
        mock_response.json.return_value = {"test": "aud not present"}
        mock_response.status_code = 200
        return mock_response

    def mock_get_success(self, url, headers, params, verify):
        mock_response = Mock()
        mock_response.json.return_value = {"aud": "client_id"}
        mock_response.status_code = 200
        return mock_response

    @patch('requests.get')
    def test_get_login_profile_error(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_get_error
        with self.assertRaises(ValueError):
            self.lwa_client.get_login_profile(access_token='access_token')

    @patch('requests.get')
    def test_get_login_profile_error_aud(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_get_error_aud
        with self.assertRaises(ValueError):
            self.lwa_client.get_login_profile(access_token='access_token')

    @patch('requests.get')
    def test_get_login_profile_success(self, mock_urlopen):
        mock_urlopen.side_effect = self.mock_get_success
        res = self.lwa_client.get_login_profile(
            access_token='access_token')
        print(res)

    def test_invalid_region(self):
        with self.assertRaises(KeyError):
            LoginWithAmazon(client_id='test', region='xx', sandbox=True)
