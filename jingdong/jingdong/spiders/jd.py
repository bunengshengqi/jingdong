# -*- coding: utf-8 -*-
import scrapy
from copy import deepcopy
import json


class JdSpider(scrapy.Spider):
    name = 'jd'
    allowed_domains = ['jd.com','p.3.cn']
    start_urls = ['https://book.jd.com/booksort.html']

    def parse(self, response): # 提取所有的大分类和对应的小分类
        # 获取大分类的分组
        dt_list = response.xpath('//div[@class="mc"]/dl/dt')
        for dt in dt_list:
            item = {}
            # 获取大分类的名字
            item["b_cate"] = dt.xpath('./a/text()').extract_first()
            # 获取小分类的分组
            em_list = dt.xpath('./following-sibling::*[1]/em')
            for em in em_list:
                # 获取小分类的地址
                item["s_href"] = "https:" + em.xpath('./a/@href').extract_first()
                # 小分类的名字
                item["s_cate"] = em.xpath('./a/text()').extract_first()
                print(item)
                # 构造小分类的url地址的请求,能够进入列表页
                yield scrapy.Request(
                    item["s_href"],
                    callback=self.parse_book_list,
                    meta={"item":deepcopy(item)}
                )

    def parse_book_list(self,response):
        item = response.meta["item"]
        # 图书列表页的书的分组
        li_list = response.xpath("//div[@id='plist']/ul/li")
        for li in li_list:
            item["book_name"] = li.xpath(".//div[@class='p-name']/a/em/text()").extract_first().strip()
            item["book_author"] = li.xpath(".//span[@class='p-bi-name']/span/a/text()").extract()
            item["book_press"] = li.xpath(".//span[@class='p-bi-store']/a/text()").extract_first()
            item["book_publisth_date"] = li.xpath(".//span[@class='p-bi-date']/text()").extract_first().strip()
            item["book_sku"] = li.xpath("./div/@data-sku").extract_first()
            # 发送价格的请求，获取价格
            price_url_temp = "https://p.3.cn/prices/mgets?ext=11000000&pin=&type=1&area=1_72_4137_0&skuIds=J_{}"
            price_url = price_url_temp.format(item["book_sku"])
            yield scrapy.Request(
                price_url,
                callback=self.parse_book_price,
                meta={"item": deepcopy(item)}
            )

            # 实现翻页
        next_url = response.xpath("//a[@class='pn-next']/@href").extract_first()
        if next_url is not None:
            yield response.follow(
                next_url,
                callback=self.parse_book_list,
                meta={"item": item}
            )

    def parse_book_price(self, resposne):  # 提取价格
        item = resposne.meta["item"]
        item["book_price"] = json.loads(resposne.body.decode())[0]["op"]
        print(item)
