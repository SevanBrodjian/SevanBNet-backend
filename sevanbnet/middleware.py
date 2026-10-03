def noindex(get_response):
    """Keep every backend host (API, admin, QR redirects) out of search results.

    The backend is never a page a visitor should land on from a search engine;
    only the frontend at www.sevanb.net should be indexed. A header (rather than
    a robots.txt Disallow) lets crawlers fetch the URL and see the instruction,
    which is what gets already-indexed pages dropped.
    """

    def middleware(request):
        response = get_response(request)
        response["X-Robots-Tag"] = "noindex, nofollow"
        return response

    return middleware
