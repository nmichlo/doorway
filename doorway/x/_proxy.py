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

__all__ = [
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
]

import io
import os
from collections import defaultdict
from logging import getLogger
from multiprocessing.pool import ThreadPool
from pathlib import Path
from random import Random
from typing import Callable, Iterable, Literal, TYPE_CHECKING, TypedDict, TypeVar, Union
from typing import Dict
from typing import List
from typing import Optional
from typing import Sequence
from typing import Tuple
import urllib.request

from doorway import EnvVar

_LOGGER = getLogger(__name__)


if TYPE_CHECKING:
    import requests


# ============================================================================ #
# Proxy Scraping                                                               #
# ============================================================================ #


class HTTPProxyHint(TypedDict):
    HTTP: str


class HTTPSProxyHint(TypedDict):
    HTTPS: str


ProxyRegisteredScraperHint = str
ProxyTypeHint = Literal["http", "https", "all"]
ProxyDictHint = Union[HTTPProxyHint, HTTPSProxyHint]
ProxyScrapeFnHint = Callable[[ProxyTypeHint], List[ProxyDictHint]]

_GenericScrapeFn = TypeVar("_GenericScrapeFn", bound=ProxyScrapeFnHint)


# ============================================================================ #
# Proxy Scraping                                                               #
# ============================================================================ #


_PROXY_SOURCES = {}
_DEFAULT_SOURCE = None


def proxies_set_default_scraper(name: ProxyRegisteredScraperHint) -> None:
    if name not in _PROXY_SOURCES:
        raise KeyError(
            f"Cannot set as default! Scrape function with name: {repr(name)} does not exist."
        )
    global _DEFAULT_SOURCE
    if _DEFAULT_SOURCE != name:
        _LOGGER.info(
            f"overridden default proxy scrape_fn: {repr(_DEFAULT_SOURCE)} -> {repr(name)}"
        )
        _DEFAULT_SOURCE = name


def proxies_register_scraper(
    name: ProxyRegisteredScraperHint,
    *,
    is_default: bool = False,
    scrape_fn: Optional[_GenericScrapeFn] = None,
) -> Union[_GenericScrapeFn, Callable[[_GenericScrapeFn], _GenericScrapeFn]]:
    if name in _PROXY_SOURCES:
        raise KeyError("scrape function with name: {repr(name)} already exists")

    # decorator
    def wrapper(scrape_fn: _GenericScrapeFn) -> _GenericScrapeFn:
        # just in case the decorator call was delayed
        assert name not in _PROXY_SOURCES
        _PROXY_SOURCES.setdefault(name, scrape_fn)
        _LOGGER.debug(f"registered proxy scrape_fn: {repr(name)}")
        # set the default
        if is_default:
            proxies_set_default_scraper(name=name)
        return scrape_fn

    # decorator or function
    if scrape_fn is None:
        return wrapper
    else:
        return wrapper(scrape_fn)


def proxies_scrape(
    source: Optional[str] = ProxyRegisteredScraperHint,
    proxy_type: ProxyTypeHint = "all",
    cache_dir: str = "data/proxies/cachier",
    cached: bool = True,
) -> List[ProxyDictHint]:
    if source is None:
        if _DEFAULT_SOURCE is None:
            raise RuntimeError("no default proxy scrape function has been set.")
        source = _DEFAULT_SOURCE
        _LOGGER.info(f"using default proxy scrape function: {repr(source)}")
    # get source
    try:
        proxy_scrape_fn = _PROXY_SOURCES[source]
    except KeyError:
        raise KeyError(
            f"proxy scrape function with name: {repr(source)} does not exist. Valid scrape sources are: {sorted(_PROXY_SOURCES.keys())}"
        )
    # wrap the function
    if cached:
        try:
            from cachier import cachier
        except ImportError as e:
            raise ImportError(
                "To use the 'cached' feature, you must install cachier."
                "You can install it via: `pip install cachier`"
            ) from e

        from datetime import timedelta

        proxy_scrape_fn = cachier(
            stale_after=timedelta(days=1), backend="pickle", cache_dir=cache_dir
        )(proxy_scrape_fn)
    # obtain the proxies
    _LOGGER.info(f"scraping proxies from source: {repr(source)}")
    proxy_list = proxy_scrape_fn(proxy_type=proxy_type)
    _LOGGER.info(f"scrapped: {len(proxy_list)} proxies from source: {repr(source)}")
    # done!
    return proxy_list


# ============================================================================ #
# Proxy Scrapers                                                               #
# ============================================================================ #


def _requests_get(
    url: str,
    fake_user_agent: bool = True,
    params: Optional[dict] = None,
) -> "requests.Response":
    try:
        import requests
    except ImportError as e:
        raise ImportError(
            "To use the 'requests' library, you must install it."
            "You can install it via: `pip install requests`"
        ) from e

    # fake a request from a browser
    return requests.get(
        url,
        headers={}
        if not fake_user_agent
        else {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
        },
        params=params,
    )


@proxies_register_scraper("proxylist.geonode.com", is_default=True)
def _scrape_proxylist_geonode_com(proxy_type: ProxyTypeHint) -> List[ProxyDictHint]:
    def _get_page(page):
        r = _requests_get(
            f"https://proxylist.geonode.com/api/proxy-list?limit=500&page={page}&sort_by=lastChecked&sort_type=desc",
            fake_user_agent=True,
        )
        r.raise_for_status()
        return r.json()

    proxies: "List[ProxyDictHint]" = []
    page_num = 1
    while True:
        print(f"page_num={page_num}")
        data = _get_page(page_num)
        for row in data["data"]:
            proto = row["protocols"][0].upper()
            url = f"{proto}://{row['ip']}:{row['port']}"
            proxies.append({proto: url})
        if page_num >= data["total"]:
            break
        page_num += 1
        if page_num > 3:
            break

    # filter by type
    if proxy_type == "http":
        proxies = [p for p in proxies if "HTTP" in p]
    elif proxy_type == "https":
        proxies = [p for p in proxies if "HTTPS" in p]
    else:
        pass

    return proxies


@proxies_register_scraper("morph.io")
def _scrape_proxies_morph(proxy_type: ProxyTypeHint) -> List[ProxyDictHint]:
    morph_api_key = EnvVar.env_str("MORPH_API_KEY").get()
    morph_api_url = "https://api.morph.io/CookieMichal/us-proxy/data.json"

    query = (
        "select * from 'data' where (anonymity='elite proxy' or anonymity='anonymous')"
    )

    if "https" == proxy_type:
        query += " and https='yes'"
    elif "http" == proxy_type:
        query += " and https='no'"
    elif "all" == proxy_type:
        pass
    else:
        raise KeyError(f"invalid proxy_type: {proxy_type}")

    r = _requests_get(morph_api_url, params={"key": morph_api_key, "query": query})

    proxies: "List[ProxyDictHint]" = []
    for row in r.json():
        proto = "HTTPS" if row["https"] == "yes" else "HTTP"
        url = "{}://{}:{}".format(proto, row["ip"], row["port"])
        proxies.append({proto: url})

    return proxies


@proxies_register_scraper("free-proxy-list.net")
def _scrape_proxies_freeproxieslist(proxy_type: ProxyTypeHint) -> List[Dict[str, str]]:
    def can_add(https):
        if proxy_type == "all":
            return True
        elif proxy_type == "https":
            return https == "yes"
        elif proxy_type == "http":
            return https == "no"
        else:
            raise KeyError(f"invalid proxy_type: {proxy_type}")

    try:
        from bs4 import BeautifulSoup
    except ImportError as e:
        raise ImportError(
            "To use the 'free-proxy-list.net' scraper, you must install bs4."
            "You can install it via: `pip install beautifulsoup4`"
        ) from e

    page = _requests_get("https://free-proxy-list.net/", fake_user_agent=True)
    soup = BeautifulSoup(page.content, "html.parser")
    rows = soup.find_all("tr", recursive=True)

    proxies: "List[ProxyDictHint]" = []
    for row in rows:
        try:
            ip, port, country, country_long, anonymity, google, https, last_checked = (
                elem.text for elem in row.find_all("td", recursive=True)
            )
            # check this entry is an ip entry
            if len(ip.split(".")) != 4:
                raise ValueError("not an ip entry")
            # filter entries
            if not can_add(https):
                continue
            # make entry
            proto = "HTTPS" if (https == "yes") else "HTTP"
            url = "{}://{}:{}".format(proto, ip, int(port))
            proxies.append({proto: url})
        except Exception:
            pass

    return proxies


# ============================================================================ #
# Proxy Errors                                                                 #
# ============================================================================ #


class ProxyMalformedError(Exception):
    """
    raised if a proxy does not follow the correct format.
    eg. `proxy = {'<protocol>': '<protocol>://<url>'}`
    """


class ProxiesRunOutError(Exception):
    """
    raise if the ProxyDownloader has run out of proxies!
    """


class ProxyDownloadFailedError(Exception):
    """
    raise if the ProxyDownloader download has failed
    """


# ============================================================================ #
# Proxy Download Helper                                                        #
# ============================================================================ #


def _make_proxy_opener(proxy: ProxyDictHint):
    if len(proxy) != 1:
        raise ProxyMalformedError(
            f"proxy dictionaries should only have one entry, the key is the protocol, and the value is the url... invalid: {proxy}"
        )
    # build connection
    return urllib.request.build_opener(
        urllib.request.ProxyHandler(proxy), urllib.request.ProxyBasicAuthHandler()
    )


def proxy_download(
    url: str,
    file: Union[str, Path],
    proxy: ProxyDictHint,
    timeout: Optional[float] = 8,
):
    # TODO: should use AtomicOpen
    data = _make_proxy_opener(proxy=proxy).open(url, timeout=timeout).read()
    # download to temp file in case there is an error
    file = str(file)
    temp_file = file + ".dl"
    with io.FileIO(temp_file, "w") as f:
        f.write(data)
    # make this atomic
    os.rename(temp_file, file)


def _skip_or_prepare_file(
    file: Union[str, Path],
    exists_mode: Literal["error", "skip", "overwrite"],
    make_dirs: bool,
):
    """
    returns True if the file should be skipped, False otherwise.
    - also prepare the directories or deletion of the file!
    """
    file = str(file)

    if os.path.exists(file):
        # the file exists
        # make sure it is actually a file, not a directory or link
        if not os.path.isfile(file):
            raise IOError(f"the specified file is not a file: {file}")
        # handle the different modes
        if exists_mode == "error":
            raise FileExistsError(f"the file already exists: {file}")
        elif exists_mode == "skip":
            return True
        elif exists_mode == "overwrite":
            os.unlink(file)
            _LOGGER.warning("overwriting file: {url}")
        else:
            raise KeyError(f"invalid exists_mode={repr(exists_mode)}")
    else:
        # the file does not exist
        # check the parent path
        parent_dir = os.path.dirname(file)
        if not os.path.exists(parent_dir):
            # the parent path does not exist
            if make_dirs:
                os.makedirs(parent_dir, exist_ok=True)
                _LOGGER.debug(f"[MADE] directory: {parent_dir}")
            else:
                raise FileNotFoundError(
                    f"Parent directory does not exist: {parent_dir} Otherwise set make_dirs=True"
                )
        else:
            # the parent path exists
            if not os.path.isdir(parent_dir):
                raise NotADirectoryError(
                    f"Parent directory is not a directory: {parent_dir}"
                )
    return False


# ============================================================================ #
# Proxy Downloader                                                             #
# ============================================================================ #


class ProxyDownloader:
    def __init__(
        self,
        proxies: Optional[
            Union[Sequence[ProxyDictHint], ProxyRegisteredScraperHint]
        ] = None,
        req_min_remove_count: int = 5,
        req_max_fail_ratio: float = 0.5,
    ):
        # default proxy scraping
        if proxies is None:
            proxies = proxies_scrape()
        elif isinstance(proxies, str):
            proxies = proxies_scrape(source=proxies)
        # convert
        self._proxies = list(proxies)  # TODO: add support for raw proxy strings?
        # proxy statistics
        self._req_counts = defaultdict(int)
        self._req_fails = defaultdict(int)
        self._req_max_fail_ratio = req_max_fail_ratio
        self._req_min_remove_count = req_min_remove_count
        # random instance
        self._rand = Random()  # TODO: add round robbin mode?

    def random_proxy(self) -> ProxyDictHint:
        if len(self._proxies) <= 0:
            raise ProxiesRunOutError(
                "The proxy downloader has run out of valid proxies."
            )
        # return a random proxy!
        index = self._rand.randint(0, len(self._proxies) - 1)
        return self._proxies[index]

    def _update_proxy(self, proxy: ProxyDictHint, success: bool) -> None:
        (purl,) = proxy.values()
        # update uses and failures
        self._req_counts[purl] += 1
        self._req_fails[purl] += int(bool(not success))
        # make remove if there was an error
        counts, fails = self._req_counts[purl], self._req_fails[purl]
        if (counts > self._req_min_remove_count) and (
            fails / counts > self._req_max_fail_ratio
        ):
            try:
                self._proxies.remove(proxy)
                del self._req_counts[purl]
                del self._req_fails[purl]
            except (ValueError, KeyError):
                pass  # removed in another thread

    def download_threaded(
        self,
        url_file_tuples: Iterable[Tuple[str, Union[str, Path]]],
        exists_mode: Literal["error", "skip", "overwrite"] = "error",
        verbose: bool = False,
        make_dirs: bool = False,
        ignore_failures=False,
        threads=64,
        attempts: int = 128,
        timeout: int = 8,
    ):
        try:
            from tqdm import tqdm
        except ImportError:
            raise ImportError(
                "To use the download_threaded function, you must install tqdm."
                "You can install it via: `pip install tqdm`"
            )

        # check inputs
        try:
            total = len(url_file_tuples)
            if total <= 0:
                return []
        except TypeError:
            total = None

        def download(url_file):
            url, file = url_file
            try:
                self.download(
                    url=url,
                    file=file,
                    exists_mode=exists_mode,
                    verbose=verbose,
                    make_dirs=make_dirs,
                    attempts=attempts,
                    timeout=timeout,
                )
            except ProxyDownloadFailedError:
                if ignore_failures:
                    return url, file
                else:
                    raise
            return None

        def get_desc():
            if ignore_failures:
                return (
                    f"Downloading [p={len(self._proxies)},t={threads},f={len(failed)}]"
                )
            else:
                return f"Downloading [p={len(self._proxies)},t={threads}]"

        # download all files, keeping track of failed items!
        failed = []
        with ThreadPool(processes=threads) as pool:
            with tqdm(desc=get_desc(), total=total) as pbar:
                for pair in pool.imap_unordered(download, url_file_tuples):
                    if pair:
                        failed.append(pair)
                    pbar.desc = get_desc()
                    pbar.update()

        # return all tuples for failed attempts
        return failed

    def download(
        self,
        url: str,
        file: Union[str, Path],
        exists_mode: Literal["error", "skip", "overwrite"] = "error",
        verbose: bool = False,
        make_dirs: bool = False,
        attempts: int = 128,
        timeout: int = 8,
    ):
        """
        Download a file using random proxies.
        """
        if _skip_or_prepare_file(
            file=file, exists_mode=exists_mode, make_dirs=make_dirs
        ):
            if verbose:
                _LOGGER.debug(f"[SKIPPED]: {file} | {url}")
            return
        # attempt download
        for i in range(attempts):
            proxy = self.random_proxy()
            try:
                proxy_download(url, file, proxy=proxy, timeout=timeout)
                if verbose:
                    _LOGGER.info(f"[DOWNLOADED]: {file} | {url}")
                self._update_proxy(proxy, success=True)
                return
            except Exception as e:
                if verbose:
                    _LOGGER.debug(f"[FAILED ATTEMPT {i + 1}]: {file} | {url} -- {e}")
                self._update_proxy(proxy, success=False)
        # download failed
        raise ProxyDownloadFailedError(f"[FAILED] tries={attempts}: {file} | {url}")


# ============================================================================ #
# Entrypoint                                                                   #
# ============================================================================ #


if __name__ == "__main__":

    def _command_line_app():
        import argparse
        import logging

        # parse arguments
        parser = argparse.ArgumentParser()
        parser.add_argument("-d", "--cache-dir", type=str, default="data/cache/proxies")
        parser.add_argument("-t", "--proxy-type", type=str, default="all")
        parser.add_argument("-s", "--proxy-source", type=str, default=None)
        parser.add_argument("-f", "--force-download", action="store_true")
        args = parser.parse_args()

        # download the proxies
        logging.basicConfig(level=logging.DEBUG)
        ProxyDownloader(
            proxies=proxies_scrape(
                source=args.proxy_source,
                proxy_type=args.proxy_type,
                cache_dir=args.cache_dir,
                cached=not args.force_download,
            )
        )

    _command_line_app()


# ============================================================================ #
# END                                                                          #
# ============================================================================ #
