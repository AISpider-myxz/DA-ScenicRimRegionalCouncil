import scrapy
import requests
import json
from pathlib import Path
from collections import OrderedDict
from urllib.parse import urlencode, urlparse
from scrapy import Request, Selector
from scrapy.http import HtmlResponse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from common._string import except_blank
from AISpider.items.scenic_rim_items import ScenicRimItem
import time
from datetime import date, datetime, timedelta
from common._date import get_all_month_
from common.set_date import get_this_month

class ScenicRimSpider(scrapy.Spider):
    """
    Scenic Rim 数据爬虫：
    源网站仍是动态网站 .net实现，接口直接返回
    这个网站目前的接口指定时间范围不生效， 过滤出的结果比较奇怪，因此只能按照网页上给出的时间范围进行过滤
    """
    name = "scenic_rim"
    base_url = 'https://srr-prod-icon.saas.t1cloud.com/'
    allowed_domains = ["srr-prod-icon.saas.t1cloud.com"]
    start_urls = ["https://srr-prod-icon.saas.t1cloud.com/Pages/XC.Track/SearchApplication.aspx"]
    term_url = 'https://srr-prod-icon.saas.t1cloud.com/Common/Common/terms.aspx'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'menu_Sub': 'hide'
    }
    all_search = 'COM.Bd,COM.Bn,COM.Ip,DevEnf,MC.Bd1,MC.Bd2,MC.Bn,MC.Ip,RL.Bd1,RL.Bd2,RL.Bn,RL.IP,OW.Bd1,OW.Bd2,OW.Bn,OW.Ip,Subdiv,QMCU,QRAL,QPOS,QDBW,QOPW,QEXC,QSPS,QCAR,BuildEnvAm,QCOM'
    tssm = ';Telerik.Web.UI, Version=2021.1.224.40, Culture=neutral, PublicKeyToken=121fae78165ba3d4:en:1e85b3b0-6b8d-4515-b62f-0dac55e921df:aac1aeb7:c86a4a06;Telerik.Web.UI.Skins, Version=2021.1.224.40, Culture=neutral, PublicKeyToken=121fae78165ba3d4:en:64cfe723-6d1f-45f7-a1ef-61e25fea9ae5:a07539a3:648927c0'
    tsm = ';;System.Web.Extensions, Version=4.0.0.0, Culture=neutral, PublicKeyToken=31bf3856ad364e35:en:9ddf364d-d65d-4f01-a69e-8b015049e026:ea597d4b:b25378d2;Telerik.Web.UI, Version=2021.1.224.40, Culture=neutral, PublicKeyToken=121fae78165ba3d4:en:1e85b3b0-6b8d-4515-b62f-0dac55e921df:16e4e7cd:f7645509:33715776:88144a7a:8674cba1:7c926187:b7778d6c:c08e9f8a:a51ee93e:59462f1;Artem.Google, Version=6.1.0.0, Culture=neutral, PublicKeyToken=fc8d6190a3aeb01c:en:48d6dde7-c728-4b51-b8fe-a8d1514595bc:93793f06:c2eaa3fd'
    date_client_state = json.dumps({"enabled": True, "emptyMessage": "", "validationText": "", "valueAsString": "",
                                    "minDateStr": "1980-01-01-00-00-00", "maxDateStr": "2099-12-31-00-00-00",
                                    "lastSetTextBoxValue": ""})

    custom_settings = {
        # 'ITEM_PIPELINES': {
        #     "AISpider.pipelines.AispiderPipeline": None,
        # }
        'DOWNLOAD_DELAY': 3,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'LOG_STDOUT': True,
        #'LOG_FILE': 'scrapy_scenic_rim.log',
        'DOWNLOAD_TIMEOUT': 1200
    }

    def __init__(self, run_type='all', category=None,days=None, *args, **kwargs):
        super(ScenicRimSpider, self).__init__(*args, **kwargs)
        self.run_type = run_type
        # category 
        #['today','lastfinancialyear', 'lastcalendaryear', 'thiscalendaryear', 'nextcalendaryear']
        self.category = category
        self.cookie = None
        if days == None:
        # 如果没有传days默认为这个月的数据
            self.days = get_this_month()
            date_obj = datetime.strptime(self.days, "%d/%m/%Y")
            self.days_ = date_obj.strftime("%Y-%m-%d")
        else:
            now = datetime.now()
            days = int(days)
            date_from = (now - timedelta(days)).date().strftime('%d/%m/%Y')
            # 这里计算出开始时间 设置到self.days
            self.days = date_from
            self.days_ = (now - timedelta(days)).date().strftime('%Y-%m-%d')

    def start_requests(self):
        """
        第一次请求，获取下一次请求的相关参数
        """
        for url in self.start_urls:
            # url = self.get_url(url)
            self.update_cookie()
            # self.update_search_option(url)
            yield Request(url, dont_filter=True, headers=self.headers, cookies=self.cookie)

    def update_cookie(self):
        """需要调用semuluar同意用户条款"""
        #driver_path = str(Path(__file__).parent.parent.parent / 'chrome/chromedriver.exe')
        opt = webdriver.ChromeOptions()
        opt.add_argument('--headless')
        opt.add_argument('--no-sandbox')
        opt.add_argument('--disable-dev-shm-usage')
        browser = webdriver.Chrome(opt)
        browser.get(self.term_url)
        wait = WebDriverWait(browser, 1)
        agree_box = wait.until(EC.presence_of_element_located((By.ID, 'ctl00_ctMain_chkAgree_chk1')))
        if not agree_box.is_selected():
            agree_box.click()
        agree_button = wait.until(EC.element_to_be_clickable((By.ID, 'ctl00_ctMain_BtnAgree')))
        agree_button.click()
        # 获取cookie
        cookie = browser.get_cookie('ASP.NET_SessionId')
        self.cookie = {'ASP.NET_SessionId': cookie['value']}
        # 关闭浏览器
        browser.close()
        # r = requests.get(self.term_url)
        # self.cookie = {'ASP.NET_SessionId': r.cookies.get('ASP.NET_SessionId')}
        print(f'cookies:{self.cookie}')

    def parse(self, response):

        # 进行请求
        if self.run_type == 'all':
            # 为获取比较多的数据，daterange需要指定
            temp_list =[]
            temp_list.append(self.category)
            for daterange in temp_list: #['today','lastfinancialyear', 'lastcalendaryear', 'thiscalendaryear', 'nextcalendaryear'][:1]:
                for filter_type in ['LodgementDate', 'DeterminationDate'][1:]:
                    payload = self.get_paload(response, daterange, filter_type)  # filter_type)
                    yield Request(self.get_query_url(response.url, daterange.lower(), filter_type.lower()),
                                  dont_filter=True, method='POST', body=payload, callback=self.parse_list,
                                  headers=self.headers, cookies=self.cookie,meta={'type':daterange})

    def parse_list(self, respond: HtmlResponse):
        """
        查找到所有的application， 并请求详情
        """
        print(respond.meta['type'])
        all_app_hrefs = respond.css('div.result a::attr(href)').extract()
        if all_app_hrefs == []:return
        for href in all_app_hrefs:
            try:
                # _, query = href.split('?')
                query = href.split('?')
            except:
                self.logger.error(f'Detail link invalid: href:{href}.')
                continue
            url = '?'.join([respond.url.split('?')[0], query[1]])
            print(url)
            yield Request(url, dont_filter=True, headers=self.headers, cookies=self.cookie, callback=self.parse_detail)

    def parse_detail(self, respond: HtmlResponse):
        item = ScenicRimItem()
        app_id = respond.css('div h2::text').extract_first()
        if app_id:
            app_id = except_blank([app_id])
        if app_id:
            app_id = app_id[0].split(':')
        if len(app_id) == 2:
            item['application_id'] = app_id[1].strip()
        else:
            return
        # Application Details
        details = respond.css('div#s_ctl00_ctMain_info_app div.detail')
        for detail in details:
            key = except_blank([detail.css('div.detailleft::text').extract_first()])[0]
            val = detail.css('div.detailright::text').extract_first() or ''
            val.strip()
            if key.lower() == 'description:':
                item['description'] = val.strip()
            elif key.lower() == 'status:':
                item['status'] = val.strip()
            elif key.lower() == 'submitted:':
                #item['lodgement_date'] = val.strip()
                try:
                    lodged_date = val.strip()
                    time_array = time.strptime(lodged_date, '%d/%m/%Y')
                    temp_data = int(time.mktime(time_array))
                    item['lodgement_date'] = temp_data if lodged_date else 0  
                except:
                    item['lodgement_date'] = 0
            elif key.lower() == 'determined:':
                #item['finalised_date'] = val.strip()
                try:
                    lodged_date = val.strip()
                    time_array = time.strptime(lodged_date, '%d/%m/%Y')
                    temp_data = int(time.mktime(time_array))
                    item['finalised_date'] = temp_data if lodged_date else 0  
                except:
                    item['finalised_date'] = 0

        details = respond.css('div#s_ctl00_ctMain_info_app2 div.detail')
        for detail in details:
            key = except_blank([detail.css('div.detailleft::text').extract_first()])[0]
            if key.lower() == 'officer:':
                item['officer'] = except_blank([detail.css('div.detailright::text').extract_first()])[0]
            if key.lower() == 'categories:':
                item['category'] = ';'.join(detail.css('div.detailright::text').extract())
        addr = respond.css('div#addr div.detail a::text').extract_first()
        if addr:
            addr = addr.strip()
        item['address'] = addr
        people = respond.css('div#ppl div#b_ctl00_ctMain_info_party div.detail')
        item['names'] = ';'.join([
            f"{person.css('div.detailleft::text').extract_first()}:{person.css('div.detailright::text').extract_first()}"
            for person in people])

        cid = urlparse(respond.url).query.split('=')[1]
        item['documents'] = self.get_documents(cid)
        del item['metadata']
        yield item

    def get_documents(self, c_id):
        url = 'https://srr-prod-icon.saas.t1cloud.com/pages/xc.track/Services/ECMConnectService.aspx/GetDocuments'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Content-Type': 'application/json; charset=UTF-8',
        }
        # 调用document接口，查询document.....这个破接口返回很慢，得4秒左右
        try:
            r = requests.post(url, data=json.dumps({'PageIndex': '1', 'PageSize': '100', 'cId': c_id}), headers=headers)
            selector = Selector(text=r.json().get('d', ''))
            all_documents = selector.css('tr')
            documents = ['@@'.join(
                [document.css('td')[1].css('a::attr(href)').extract_first().replace('../../', self.base_url),
                document.css('td')[2].css('a::text').extract_first()]) for document in all_documents]
            documents_string = ';'.join(documents)
            return documents_string
        except:
            return ''


    def get_query_url(self, url, d, k):
        parames = {}
        parames['d'] = d
        parames['k'] = k
        parames['t'] = self.all_search.lower()
        parames['sb'] = ''
        parames['ds'] = ''
        parames['de'] = ''
        parames['sa'] = 1
        return '?'.join([url, urlencode(parames)])

    def get_paload(self, response, daterange, filter_type):
        now = datetime.now()
        self.now = now.date().strftime('%d/%m/%Y')
        self.now_ = now.date().strftime('%Y-%m-%d')
        calendar_ad = json.dumps([[1980, 1, 1], [2099, 12, 30], [now.year, now.month, now.day]])
        params = OrderedDict()
        selector = Selector(text=response.text)
        params['ctl00_rcss_TSSM'] = self.tssm
        params['ctl00_script_TSM'] = self.tsm
        params['__EVENTTARGET'] = ''
        params['__EVENTARGUMENT'] = ''
        params['__VIEWSTATE'] = selector.css('#__VIEWSTATE::attr(value)').get()
        params['__VIEWSTATEGENERATOR'] = selector.css('#__VIEWSTATEGENERATOR::attr(value)').get()
        params['__EVENTVALIDATION'] = selector.css('#__EVENTVALIDATION::attr(value)').get()
        params['ctl00$ctMain$search$txtSearch'] = ''
        params['ctl00$ctMain$search$advancedSearch$ddlType$ddl1'] = self.all_search
        params['ctl00$ctMain$search$advancedSearch$ddlRange$ddl1'] = daterange
        params['ctl00$ctMain$search$advancedSearch$dteDates$dteDates_txt1'] = self.days_
        params['ctl00$ctMain$search$advancedSearch$dteDates$dteDates_txt1$dateInput'] = self.days
        params[
            'ctl00_ctMain_search_advancedSearch_dteDates_dteDates_txt1_dateInput_ClientState'] = self.date_client_state
        params['ctl00_ctMain_search_advancedSearch_dteDates_dteDates_txt1_calendar_SD'] = json.dumps([])
        params[
            'ctl00_ctMain_search_advancedSearch_dteDates_dteDates_txt1_calendar_AD'] = calendar_ad
        params['ctl00_ctMain_search_advancedSearch_dteDates_dteDates_txt1_ClientState'] = ''
        params['ctl00$ctMain$search$advancedSearch$dteDates$dteDates_txt2'] = self.now_
        params['ctl00$ctMain$search$advancedSearch$dteDates$dteDates_txt2$dateInput'] = self.now
        params[
            'ctl00_ctMain_search_advancedSearch_dteDates_dteDates_txt2_dateInput_ClientState'] = self.date_client_state
        params['ctl00_ctMain_search_advancedSearch_dteDates_dteDates_txt2_calendar_SD'] = json.dumps([])
        params[
            'ctl00_ctMain_search_advancedSearch_dteDates_dteDates_txt2_calendar_AD'] = calendar_ad
        params['ctl00_ctMain_search_advancedSearch_dteDates_dteDates_txt2_ClientState'] = ''
        params['ctl00$ctMain$search$advancedSearch$ddlTowns$ddl1'] = 0
        params['ctl00$ctMain$search$advancedSearch$ddlSubDet$ddl1'] = filter_type
        params['ctl00$ctMain$search$advancedSearch$BtnSelect'] = 'Advanced Search'
        return urlencode(params)
