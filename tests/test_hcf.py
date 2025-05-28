import pytest
from scrapy import Request, Spider, signals
from scrapy.crawler import CrawlerRunner
from scrapy.utils.request import request_from_dict
from scrapy.utils.test import get_crawler
from twisted.internet.defer import inlineCallbacks

from scrapy_frontera.manager import ScrapyFrontierManager

hcf_backend = pytest.importorskip("hcf_backend")


@inlineCallbacks
@pytest.mark.parametrize(
    "request_",
    [
        Request("https://toscrape.com", dont_filter=True),
        {
            "url": "https://videos.toscrape.com/watch?v=57e2bf6",
            "callback": "parse",
            "errback": None,
            "headers": {
                b"Referer": [b"https://toscrape.com/foo.txt"],
                b"Accept": [
                    b"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
                ],
                b"Accept-Language": [b"en"],
                b"User-Agent": [
                    b"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3294.5 Safari/537.36"
                ],
                b"Accept-Encoding": [b"gzip, deflate, br"],
            },
            "method": "GET",
            "body": b"",
            "cookies": {},
            "meta": {
                "zyte_api": {"httpResponseBody": True, "geolocation": "US"},
                "depth": 1,
                "_hsparent": 0,
                "autothrottle_dont_adjust_delay": True,
                "download_slot": "zyte-api@videos.toscrape.com",
                "download_timeout": 180.0,
            },
            "encoding": "utf-8",
            "priority": 0,
            "dont_filter": True,
            "flags": [],
            "cb_kwargs": {"source_url": "https://videos.toscrape.com/watch?v=57e2bf6"},
        },
    ],
)
def test_add_seeds(request_):
    class TestSpider(Spider):
        name = "test_spider"

    seeds = [request_]
    manager = ScrapyFrontierManager()

    def spider_open():
        manager.set_spider(crawler.spider)
        for i in range(len(seeds)):
            if isinstance(seeds[i], dict):
                seeds[i] = request_from_dict(seeds[i], spider=crawler.spider)
        manager.add_seeds(seeds)

    crawler = get_crawler(
        TestSpider, settings_dict={"BACKEND": "hcf_backend.HCFBackend"}
    )
    crawler.signals.connect(spider_open, signal=signals.spider_opened)
    runner = CrawlerRunner()
    yield runner.crawl(crawler)

    runner.stop()

    processed_requests = manager.get_next_requests()

    def serialize_request(request):
        return request.to_dict(spider=crawler.spider)

    expected = [serialize_request(request) for request in seeds]
    actual = [serialize_request(request) for request in processed_requests]
    assert expected == actual
