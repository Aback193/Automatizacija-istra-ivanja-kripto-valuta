import time
import scrapy
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

DEPTH_LIMIT = 5
RESULTS_LIST = []

# Create chrome driver, headless by default
def create_webdriver():
    chrome_options = Options()
    prefs = {"credentials_enable_service": False, "profile.password_manager_enabled": False}
    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ['enable-automation'])
    chrome_options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.74 Safari/537.36")
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    #chrome_options.add_argument("window-size=1400,850")
    driver = webdriver.Chrome(options=chrome_options)
    return driver

# Crawler Class
class CointelegraphSpider(scrapy.Spider):
    name = 'CointelegraphSpider'
    custom_settings = {
        'LOG_ENABLED': False,
        'DEPTH_LIMIT': DEPTH_LIMIT,
        'DOWNLOADER_MIDDLEWARES':{
            'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
            'scrapy.downloadermiddlewares.retry.RetryMiddleware': None,
            'scrapy_fake_useragent.middleware.RandomUserAgentMiddleware': 400,
            'scrapy_fake_useragent.middleware.RetryUserAgentMiddleware': 401,
            #'rotating_proxies.middlewares.RotatingProxyMiddleware': 610,
            #'rotating_proxies.middlewares.BanDetectionMiddleware': 620,
        },
        'FAKEUSERAGENT_PROVIDERS':[
            'scrapy_fake_useragent.providers.FakeUserAgentProvider',  # this is the first provider we'll try
            'scrapy_fake_useragent.providers.FakerProvider',  # if FakeUserAgentProvider fails, we'll use faker to generate a user-agent
            'scrapy_fake_useragent.providers.FixedUserAgentProvider',  # fall back to USER_AGENT value
        ],
        'USER_AGENT':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.74 Safari/537.36'
        #'ROTATING_PROXY_LIST_PATH':'../Lists/proxy_list'
    }

    # Create search requests.
    def start_requests(self):
        for ticker in self.TICKERS:
            try:
                driver = create_webdriver()
                driver.get('https://cointelegraph.com/search?query={}'.format(ticker))
                time.sleep(5)
                for i in range(0, DEPTH_LIMIT):                    
                    driver.execute_script("document.querySelectorAll('div.search-nav__load-more a')[0].click()")
                    time.sleep(5)
                # Extract Links
                links = []
                link_elements = driver.find_elements_by_xpath("//h2[@class='header']/a")    # Cointelegraph extract links
                for el in link_elements:
                    links.append(el.get_attribute("href"))
                for i, url in enumerate(links):
                    if url is not None:
                        #print("{}.{}".format(i+1, url))
                        yield scrapy.Request(url, callback = self.parse, meta={'message':str(ticker)})
                driver.close()
                driver.quit()
            except Exception as e:
                print(print("Exception {}".format(e)))

    def parse(self, response):
        global RESULTS_LIST
        try:
            text = [' '.join(line.strip() for line in p.xpath('.//text()').extract() if line.strip()) for p in response.xpath('//p')]
            text_str = ' '.join([str(item) for item in text])
            #print("\nTicker {}  Link {}".format(str(response.meta['message']), response.url))
            RESULTS_LIST.append({"Ticker":str(response.meta['message']), "Link":response.url, "Text":text_str})
        except Exception as e:
            print(print("Exception {}".format(e)))
            

# Return crawler results.
def get_CointelegraphSpider():
    return RESULTS_LIST
