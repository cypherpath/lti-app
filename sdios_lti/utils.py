#!/usr/bin/env python3
# encoding: utf-8

import base64
import urllib
from xml.sax.saxutils import escape as htmlescape

from Crypto.Hash import HMAC, SHA

from sdios_lti.models import Consumer


class BadRequest(Exception):
    pass


class UnauthorizedRequest(Exception):
    pass


def validate_signature(post, meta, post_body, uri_path):
    """
    Validate an LTI signature.

    If the signature fails to validate, an exception is raised.

    :class:`BadRequest` is raised if an expected key is missing or has a
    bad value.

    :class:`UnauthorizedRequest` is raised if the consumer key is
    unknown or the signature fails to validate.

    Other exceptions may also be raised.

    :param post: A dict representing HTTP POST values as stored in
        ``request.POST``.
    :type post: dict
    :param meta: A dict representing HTTP header information, as stored
        in ``request.META``.
    :type meta: dict
    :param post_body The body of an HTTP POST.
    :type post_body: string
    :param uri_path: The path to the view handling LTI requests, e.g.
        ``"/lti/"``.  This is typically obtained via
        :func:`django.core.urlresolvers.reverse`.
    :type uri_path: string
    """
    __validate_keys(post)

    normalized_request_parameters = __normalize_request_parameters(post_body, meta["QUERY_STRING"])
    signature_base_string = __create_signature_base_string(normalized_request_parameters, meta, uri_path)

    try:
        consumer_secret = Consumer.get_secret(post["oauth_consumer_key"])
    except Consumer.DoesNotExist:
        raise UnauthorizedRequest("invalid consumer key")

    # Consumer secret must be concatenated with "&" and the token
    # secret, even if that is empty (OAuth 1.0 §9.2).
    secret = urllib.parse.quote(consumer_secret, "") + "&"

    # OAuth 1.0 §9.2.2.
    hmac = HMAC.new(secret.encode(), msg=signature_base_string.encode(), digestmod=SHA)
    oauth_signature = base64.b64decode(urllib.parse.unquote(post["oauth_signature"]))

    if oauth_signature != hmac.digest():
        raise UnauthorizedRequest("Signature validation failed")


def __validate_keys(post):
    """
    Given POST data as a dictionary, validate that required keys exist
    in the POST.

    :class:`BadRequest` is raised if an expected key is missing or has a
    bad value.

    :params post: HTTP POST data.
    :type post: dict
    """

    static_keys = {
        "oauth_signature_method": ("HMAC-SHA1", "only HMAC-SHA1 is supported"),
        "lti_message_type": ("basic-lti-launch-request", "only supported message type is basic launch request"),
        "lti_version": ("LTI-1p0", "only LTI version 1.0/1.1 supported"),
    }

    required_keys = ("oauth_consumer_key", "oauth_signature") + tuple(static_keys.keys())
    missing_keys = [key for key in required_keys if key not in post]
    if missing_keys:
        raise BadRequest("Missing keys: {}".format(",".join(sorted(missing_keys))))

    for key, (value, msg) in static_keys.items():
        if post[key] != value:
            raise BadRequest("{} (\"{}\" provided)".format(msg, htmlescape(post[key])))


def __normalize_request_parameters(post_body, query):
    """
    Return a normalized string representing request parameters.  This
    includes POST parameters as well as query string parameters.

    "oauth_signature" is not included.

    :param post_body: The body of an HTTP POST request.
    :type post_body: string
    :param query: The query string of the request.
    :type query: string
    :returns: The post body and query string merged into a single query
        string with the "oauth_signature" key removed.
    :rtype: string
    """

    # Spaces can be encoded as + in HTTP POSTs, so normalize them.
    post_body = post_body.replace(b"+", b"%20")

    parts = post_body.split(b"&")
    if query:
        parts += query.split(b"&")

    # OAuth 1.0 §9.1.1.
    return b"&".join(entry for entry in sorted(parts) if entry.split(b"=")[0] != b"oauth_signature")


def __create_signature_base_string(normalized_request_parameters, meta, path):
    """
    Create a string to be signed as required by OAuth.  The protocol is
    inferred to be HTTPS if the port is 443, HTTP otherwise.

    :param normalized_request_parameters: A query string representing
        all request parameters apart from "oauth_signature".
    :type normalized_request_parameters: string
    :param meta: A dictionary representing HTTP meta-data, specifically
        including `SERVER_PORT` and `HTTP_HOST`.
    :type meta: dict
    :param path: The URI path to this LTI request.
    :type path: string
    :returns: A string representing this request, to be signed as
        required by OAuth.
    :rtype: string
    """
    protocol = "https" if int(meta["SERVER_PORT"]) == 443 else "http"

    parts = [
        b"POST",
        "{}://{}{}".format(protocol, meta["HTTP_HOST"], path).encode(),
        normalized_request_parameters
    ]

    # OAuth 1.0 §9.1.3.
    return '&'.join(urllib.parse.quote_from_bytes(part, b"") for part in parts)
