import requests
import pay_with_amazon.lwa_region as lwa_region


class LoginWithAmazon:

    """Login with Amazon class to wrap the get login profile method"""

    def __init__(self, client_id, region, sandbox=False):
        """
        Parameters
        ----------
        client_id: string, required
            The client Id of your Login with Amazon application.

        region : string, required
            The region in which you are conducting business.

        sandbox : string, optional
            Toggle sandbox mode. Default: False
        """
        self._client_id = client_id

        try:
            self.region = lwa_region.regions[region]
        except KeyError:
            raise KeyError('Invalid region code ({}).'.format(region))

        self._sandbox_str = 'api.sandbox' if sandbox else 'api'
        self._endpoint = 'https://{}.{}'.format(
            self._sandbox_str,
            self.region)

    def get_login_profile(self, access_token):
        """Get profile associated with LWA user."""
        token_info = requests.get(
            url='{}/auth/o2/tokeninfo'.format(self._endpoint),
            headers=None,
            params={'access_token': access_token},
            verify=True)

        token_decoded = token_info.json()

        if 'error' in token_decoded:
            raise ValueError(token_decoded['error'])

        if 'aud' not in token_decoded:
            raise ValueError('Client Id not present.')

        if token_decoded['aud'] != self._client_id:
            raise ValueError('Invalid client Id.')

        profile = requests.get(
            url='{}/user/profile'.format(self._endpoint),
            headers={'Authorization': 'bearer {}'.format(access_token)},
            params=None,
            verify=True)

        return profile.json()
