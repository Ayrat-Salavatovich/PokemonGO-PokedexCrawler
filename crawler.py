import scrapy
import json
import os

from scrapy.crawler import CrawlerProcess


class FevSpider(scrapy.Spider):
    name = 'pokedex'

    def __init__(self, file=None, *pargs, **kargs):
        super(FevSpider, self).__init__(*pargs, **kargs)
        self.start_urls = ['https://fevgames.net/pokedex/', ]
        self.count_urls = 0
        self.result_file = file
        self.results_list = []

    def parse(self, response):
        # extract all urls and send them to 'parse_pokemon' function
        for item in response.xpath('//a[@class="pokedex-item"]'):
            self.count_urls += 1
            url = 'https://fevgames.net' + item.xpath('@href').extract()[0]
            yield scrapy.Request(url, callback=self.parse_pokemon)

    def parse_pokemon(self, response):
        result_dict = {}
        article = response.xpath('//article[@id="omc-full-article"]')

        result_dict['img'] = 'https://fevgames.net' + article.xpath('img/@src').extract()[0]
        for item in article.xpath('//table/tr'):
            name = item.xpath('td')[0]
            name = name.xpath('strong/text()').extract()[0].lower()
            value = item.xpath('td')[1]
            # remove spaces from 'next evolution requirements'
            if name == 'next evolution requirements':
                value = value.xpath('descendant-or-self::text()').extract()[0].split()
            else:
                value = list(filter(None, (item.strip() for item in value.xpath('descendant-or-self::text()').extract())))

            # convert lists with only one item to strings and add them to 'result_dict'
            if type(value) == list and len(value) == 1:
                result_dict[name] = value[0]
            else:
                result_dict[name] = value

        # safe results as json
        self.results_list.append(result_dict)
        if self.count_urls == len(self.results_list):
            self.result_file.write(json.dumps(self.results_list))


# load results from file and return generator object
def load_results():
    results_list = json.loads(open('results.json').read())
    for item in results_list:
        yield item


def start():
    print('All data belongs to https://fevgames.net (https://fevgames.net/pokedex/)!')

    # clear logfile
    with open('log/fev_spider.log', 'w'):
        pass

    process = CrawlerProcess({
        'LOG_FILE': 'log/fev_spider.log',
        'LOG_ENABLED': False,
        })

    process.crawl(FevSpider(), file=open('results.json', 'w'))
    process.start()

start()
