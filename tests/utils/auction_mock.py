import os
from bs4 import BeautifulSoup

TEST_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

default_html = """
                <html><head><title>The Dormouse's story</title></head>
                <body>
                <p class="title"><b>The Dormouse's story</b></p>

                <p class="story">Once upon a time there were three little sisters; and their names were
                <a href="http://example.com/elsie" class="sister" id="link1">Elsie</a>,
                <a href="http://example.com/lacie" class="sister" id="link2">Lacie</a> and
                <a href="http://example.com/tillie" class="sister" id="link3">Tillie</a>;
                and they lived at the bottom of a well.</p>

                <p class="story">...</p>
                </body>
                </html>
            """


def auction_query_multiplexer(url):
    """
    """
    if "passees" in url:
        if "page=0" in url:
            path = os.path.join(TEST_DIR, "mock_data", "auction", "sale_listing.html")
            with open(path, "r") as f:
                html_doc = "\n".join(f.readlines())
        else:
            html_doc = default_html
    elif "vente" in url:
        if "/_fr/vente/vente-classique-a-10h-et-14h-70883" in url:
            path = os.path.join(TEST_DIR, "mock_data", "auction", "sale_page_lot_listing.html")
            with open(path, "r") as f:
                html_doc = "\n".join(f.readlines())
        else:
            html_doc = default_html
    elif "lot" in url:
        path = os.path.join(TEST_DIR, "mock_data", "auction", "lot_page.html")
        with open(path, "r") as f:
            html_doc = "\n".join(f.readlines())
    else:
        raise Exception("Unknown kind of url")

    return BeautifulSoup(html_doc, 'html.parser')
