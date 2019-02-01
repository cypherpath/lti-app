#!/usr/bin/env python2

import functools

from django.http import Http404


def ajax_required(fn):
    """
    Placed on a view, this decorator will raise
    :class:`django.http.Http404` if the incoming request is not an HTTP
    POST or if the header `HTTP_X_REQUESTED_WITH` is not set.
    """

    @functools.wraps(fn)
    def wrapper(request, *args, **kwargs):
        if request.method != "POST" or not request.is_ajax():
            raise Http404

        return fn(request, *args, **kwargs)

    return wrapper
