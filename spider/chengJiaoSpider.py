# -*- coding: utf-8 -*-
import random
import re
import requests
import sys
import lxml
import datetime
from bs4 import BeautifulSoup
from generate_excle import generate_excle
from AgentAndProxies import hds
from AgentAndProxies import GetIpProxy
from model.ElementConstant import ElementConstant

cityMap = {'北京':'bj','上海':'sh', '深圳':'sz', '杭州':'hz'}
class chengJiaoInfo:
    # 初始化构造函数
    def __init__(self, city):
        self.city = city
        self.elementConstant = ElementConstant()
        self.getIpProxy = GetIpProxy()
#        self.url = "https://bj.lianjia.com/ershoufang/pg{}/"
        self.url = "https://%s.lianjia.com/chengjiao/pg{}/"%cityMap[self.city]
        self.infos = {}
        self.proxyServer = ()
        # 传参使用进行excle生成
        self.generate_excle = generate_excle()
        self.elementConstant = ElementConstant()

    # 生成需要生成页数的链接
    def generate_allurl(self, user_in_nub):
        for url_next in range(1, int(user_in_nub) + 1):
            self.page = url_next
            yield self.url.format(url_next)

    # 开始函数
    def start(self):
        self.generate_excle.addSheetExcle(u'在售列表')
        user_in_nub = 100#input('输入生成页数：')

        for i in self.generate_allurl(user_in_nub):
            self.get_allurl(i)
            print(i)
        date = str(datetime.datetime.now().date())
        self.generate_excle.saveExcle('chengjiao-%s/%s-%s.xls'%(self.city, date, self.city))

    def get_allurl(self, generate_allurl):
        geturl = self.requestUrlForRe(generate_allurl)
        if geturl.status_code == 200:
            # 提取title跳转地址　对应每个商品
            re_set = re.compile('<li.*?<a.*?class="img.*?".*?href="(.*?)"')
            re_get = re.findall(re_set, geturl.text)
            for index in range(len(re_get)):
                self.open_url(re_get[index], index)
                print(re_get[index])

    def open_url(self, re_get, index):
        print(re_get, index)
        res = self.requestUrlForRe(re_get)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'lxml')
            self.infos['网址'] = re_get
            self.infos['标题'] = soup.title.text.split('_')[0]
            self.infos['总价'] = soup.find(class_='dealTotalPrice').text
            self.infos['每平方售价'] = soup.find(class_='record_detail').text.split('元')[0][2:]
            partent = re.compile('<li><span class="label">(.*?)</span>(.*?)</li>')
            result = re.findall(partent, res.text)
            for item in result:
                if item[0] == '建成年代':
                    self.infos['建成时间：年'] = item[1].strip()
                else:
                    self.infos[item[0]] = item[1].strip()
                  
            partent = re.compile('<i>></i>(.*?)</a>')
            result = re.findall(partent, res.text)
            self.infos['所属下辖区']=result[1].split('>')[1].split('二手房')[0]
            self.infos['所属商圈']=result[2].split('>')[1].split('二手房')[0]
            self.infos['所属小区']=result[3].split('>')[1].split('二手房')[0]
            msg = soup.find(class_='msg').contents
            result = [(a.contents[1], a.contents[0].text, ) for a in msg]
            for item in result:
                if item[0] == '建成年代':
                    self.infos['建成时间：年'] = item[1].strip()
                else:
                    self.infos[item[0]] = item[1].strip()
            row = index + (self.page - 1) * 30
            #self.infos['序号'] = row + 1
            self.infos['城市'] = self.city
            print('row:' + str(row))
            if row == 0:
                for index_item in self.elementConstant.data_constant.keys():
                    self.generate_excle.writeExclePositon(0, self.elementConstant.data_constant.get(index_item),
                                                          index_item)

                self.wirte_source_data(1)

            else:
                row = row + 1
                self.wirte_source_data(row)
        return self.infos

    # 封装统一request请求,采取动态代理和动态修改User-Agent方式进行访问设置,减少服务端手动暂停的问题
    def requestUrlForRe(self, url):

        try:
            if len(self.proxyServer) == 0:
                tempProxyServer = self.getIpProxy.get_random_ip()
            else:
                tempProxyServer = self.proxyServer

            proxy_dict = {
                tempProxyServer[0]: tempProxyServer[1]
            }
            tempUrl = requests.get(url, headers=hds[random.randint(0, len(hds) - 1)], proxies=proxy_dict)

            code = tempUrl.status_code
            if code >= 200 or code < 300:
                self.proxyServer = tempProxyServer
                return tempUrl
            else:
                self.proxyServer = self.getIpProxy.get_random_ip()
                return self.requestUrlForRe(url)
        except Exception as e:
            self.proxyServer = self.getIpProxy.get_random_ip()
            s = requests.session()
            s.keep_alive = False
            return self.requestUrlForRe(url)

    # 源数据生成,写入excle中,从infos字典中读取数据,放置到list列表中进行写入操作,其中可修改规定写入格式
    def wirte_source_data(self, row):
        for itemKey in self.infos.keys():
            print(itemKey + ':' + str(self.infos.get(itemKey)))

            item_valus = self.infos.get(itemKey)
            tempItemKey = self.elementConstant.unit_check_name(itemKey.encode('utf-8'))
            count = self.elementConstant.data_constant.get(tempItemKey)
            print(tempItemKey, self.elementConstant.data_constant.get(tempItemKey), item_valus)
            if tempItemKey != None and count != None:

                self.generate_excle.writeExclePositon(row,
                                                      self.elementConstant.data_constant.get(tempItemKey),
                                                      item_valus)

for city in ['北京', '上海', '深圳', '杭州']:
    spider = chengJiaoInfo('深圳')
    spider.start()
