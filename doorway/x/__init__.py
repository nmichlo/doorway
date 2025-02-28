#  ~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~
#  MIT License
#
#  Copyright (c) 2025 Nathan Juraj Michlo
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.
#  ~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~

from doorway.x._uri import (
    UriMalformedException,
    UriIsIncorrectTypeError,
    UriValMode,
    UriTypeEnum,
    UriFieldValidator,
    UriValidator,
    UriValidatorUrl,
    UriValidatorFile,
    uri_parse,
    uri_validate,
    uri_extract,
    Uri,
)
from doorway.x._proxy import (
    proxies_set_default_scraper,
    proxies_register_scraper,
    proxies_scrape,
    ProxiesRunOutError,
    ProxyMalformedError,
    ProxyDownloadFailedError,
    ProxyRegisteredScraperHint,
    ProxyTypeHint,
    ProxyDictHint,
    ProxyScrapeFnHint,
    proxy_download,
    ProxyDownloader,
)

__all__ = [
    # ===== proxy ===== #
    # proxy scraper registration
    "proxies_set_default_scraper",
    "proxies_register_scraper",
    "proxies_scrape",
    # errors
    "ProxiesRunOutError",
    "ProxyMalformedError",
    "ProxyDownloadFailedError",
    # hints
    "ProxyRegisteredScraperHint",
    "ProxyTypeHint",
    "ProxyDictHint",
    "ProxyScrapeFnHint",
    # helpers
    "proxy_download",
    # main api
    "ProxyDownloader",
    # ===== uri ===== #
    # errors
    "UriMalformedException",
    "UriIsIncorrectTypeError",
    # enums
    "UriValMode",
    "UriTypeEnum",
    # validation
    "UriFieldValidator",
    "UriValidator",
    "UriValidatorUrl",
    "UriValidatorFile",
    # functional
    "uri_parse",
    "uri_validate",
    "uri_extract",
    # oop
    "Uri",
]
