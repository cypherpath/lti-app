import json

import requests

from sdios_lti.models import Setting


class APIRequest:
    """
    This class allows API calls to be made to SDI OS.
    Credentials are pulled from the Setting table in the database, so
    nothing needs to be passed to the constructor.

    When making API calls, paths are represented without the leading
    "api" and without a trailing slash.  For example, to call the API
    function `http://sdios/api/accounts/users/`, the path should be passed
    as `accounts/users`.

    :param verify_ssl: If true, verify_ssl SSL certificates, raising an
        exception for invalid certificates.
    :type verify_ssl: bool
    """

    def __init__(self, verify_ssl=False):
        setting = Setting.get()

        self.__url = "https://{}".format(setting.sdios_url)
        self.__verify = verify_ssl

        params = {
            "grant_type": "password",
            "username": setting.sdios_username,
            "password": setting.sdios_password,
        }

        response = requests.post(self.__api("o/token"), data=params, auth=(setting.client_id, setting.client_secret), verify=self.__verify)
        response.raise_for_status()

        if "error" in response.json():
            raise Exception(response.json()["error"])

        self.__headers = {
            "Authorization": "{} {}".format(response.json()["token_type"], response.json()["access_token"]),
            "Content-Type": "application/json",
            "Accept": "application/json; version=2.1.0",
        }

    def post(self, path, params={}):
        """
        Make a POST request.

        An exception is raised if there is a problem communicating with
        the API, or if the specified API function returns an error.

        :param path: The API function to call.
        :type path: string
        :param params: Parameters to pass to the API function.
        :type params: dict
        :returns: A dict representing the JSON return value from the API
            call, or `None` if nothing is returned.
        :rtype: dict or `None`
        """
        response = requests.post(self.__api(path), data=json.dumps(params), headers=self.__headers, verify=self.__verify)
        if 400 <= response.status_code < 500:
            print(response.text)

        response.raise_for_status()

        return self.__json(response)

    def get(self, path):
        """
        Make a GET request.

        An exception is raised if there is a problem communicating with
        the API, or if the specified API function returns an error.

        :param path: The API function to call.
        :type path: string
        :returns: A dict representing the JSON return value from the API
            call, or `None` if nothing is returned.
        :rtype: dict or `None`
        """

        response = requests.get(self.__api(path), headers=self.__headers, verify=self.__verify)
        response.raise_for_status()

        return self.__json(response)

    def put(self, path, params={}):
        """
        Make a PUT request.

        An exception is raised if there is a problem communicating with
        the API, or if the specified API function returns an error.

        :param path: The API function to call.
        :type path: string
        :param params: Parameters to pass to the API function.
        :type params: dict
        :returns: A dict representing the JSON return value from the API
            call, or `None` if nothing is returned.
        :rtype: dict or `None`
        """

        response = requests.put(self.__api(path), data=json.dumps(params), headers=self.__headers, verify=self.__verify)
        if 400 <= response.status_code < 500:
            print(response.text)

        response.raise_for_status()

        return self.__json(response)

    def delete(self, path):
        """
        Make a DELETE request.

        An exception is raised if there is a problem communicating with
        the API, or if the specified API function returns an error.

        :param path: The API function to call.
        :type path: string
        :returns: A dict representing the JSON return value from the API
            call, or `None` if nothing is returned.
        :rtype: dict or `None`
        """

        response = requests.delete(self.__api(path), headers=self.__headers, verify=self.__verify)
        response.raise_for_status()

        return self.__json(response)

    def __json(self, response):
        """
        An API request can return either a JSON string or nothing.  Wrap
        the response to return a suitable Python object.

        :param response: A :class:`requests.models.Response'` object.
        :type response: :class:`requests.models.Response`
        :returns: Either a dict representing the returned JSON object,
            or `None` if there is no response body.
        :rtype: dict or `None`
        """

        try:
            return response.json()
        except ValueError:
            return None

    def __api(self, path):
        return "{}/api/{}/".format(self.__url, path)
