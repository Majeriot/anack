# -*- coding: utf-8 -*-
"""
Created on Mon Mar 26 21:29:43 2018

@author: lh
@version: 1.0
@time:20180403
@detail:实现模块化功能，计算股息率、分红率
"""
import tushare as ts
import pandas as pd
import requests
from requests.exceptions import RequestException
from bs4 import BeautifulSoup
headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.79 Safari/537.36'}

class dividend_rate:
    
    def __init__(self,id):
        self.id =id
    
    def get_one_page(url):
        try:
            response = requests.get(url,headers = headers)
            response.encoding = 'GB2312'
            if response.status_code == 200:
                return response.text
            return None
        except RequestException:
            return None
    
    def parse(html):
        raw_data = []
        try:
            year_raw = []
            year = []
            bonus_share = []
            bonus_convert = []
            profit_send = []
            ex_rights = []
            register_day = []
            
            soup = BeautifulSoup(html,'html5lib')
            l = soup.select('table#sharebonus_1')
            ls = l[0].tbody
            lls = ls.select('td')
            for l in lls:
                if (l.get_text().strip()) != '预案' and \
                (l.get_text().strip()) != '实施' and \
                (l.get_text().strip()) != '不分配' and \
                (l.get_text().strip()) != '查看':
                    raw_data.append(l.get_text().strip())
            
            year_raw = raw_data[::7]
    #        print(raw_data)        #出错的话请检查此处的输出
    #        print(year_raw)        #出错的话请检查此处的输出
            for item in year_raw:
                a = pd.to_datetime(item).year - 1
                year.append(a)
            bonus_share = raw_data[1::7]
            bonus_convert = raw_data[2::7]
            profit_send = raw_data[3::7]
            ex_rights = raw_data[4::7]
            register_day = raw_data[5::7]
    #        print(register_day)
            data = {'年度':year,
                    '送股':bonus_share,
                    '转股':bonus_convert,
                    '派息':profit_send,
                    '除权日':ex_rights,
                    '登记日':register_day
                    }
            frame = pd.DataFrame(data)
            return frame
        except:
            print('cannot parse this page')
    
    
    # 提供给用户的函数，输入ID，解析出历史分红列表   

    def get_bonus_table(self):
        url = 'http://vip.stock.finance.sina.com.cn/corp/go.php/vISSUE_ShareBonus/stockid/'
        url += str(self.id)
        url += '.phtml'
        html = dividend_rate.get_one_page(url)
        return dividend_rate.parse(html)     



    @property
    def divident_rate(self):
        stock = ts.get_hist_data(self.id)
        df = dividend_rate.get_bonus_table(self)
        df_dividend = df[['年度','派息','登记日']]
#        print(df_dividend)
        stock_close_price = stock["close"]
        sIndex = stock_close_price.index.tolist()
        # 获取登记日
        regis = df_dividend['登记日'].tolist()
#        print(sIndex)
#        print(regis)
        close_price = []
        diVi = []
        aIn = []
        aPe = []
        bonus = []
        div_year = []
        for i in regis:
            if i != "--" and i in sIndex:
#                print(i)
                cprice = stock_close_price.loc[i]
                close_price.append(cprice)
                aDiv = df_dividend[df_dividend['登记日'] == i]['派息'].tolist()[0]

                year = df_dividend[df_dividend['登记日'] == i]['年度'].values #获得年份
                div_year.append(year)
                
                profit_table = ts.get_report_data(year[0],4) #获取年度eps
                target_eps = profit_table[profit_table['code'] == self.id]['eps']
                bonus.append(float(aDiv) / 10 / float(target_eps) * 100)
#                print(target_eps)

                diVi.append(aDiv)
                aIn.append(i)
#        print(diVi)        
#        print(close_price)
        div_ratio = []
        for i,j in zip(diVi,close_price):
            adivr = float(i) / float(j) / 10 * 100
            div_ratio.append(adivr)
            aPe.append(round(100/adivr,2))
        
        reDf = pd.DataFrame({"dividend":diVi,
                             "dividend_ratio(%)":div_ratio,
                             'ape':aPe,
                             'bonus(%)':bonus},index = aIn)
        return reDf

a = dividend_rate('000651')
s = a.divident_rate
print(s)
#获取的股息率完全正确，已确定。接下来需要获取分红率
#分红率1 = 每股派息 / 每股利润
#分红率2 = 每股派息 * 股本 / 总利润
#ts.get_report_data(2016,4)
#ts.get_profit_data(2014,4)
##############################################