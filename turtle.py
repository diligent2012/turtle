#!/usr/bin/python
# -*- coding: utf-8 -*-
# encoding: utf-8
#客户端调用，用于查看API返回结果

import time
import csv
from OkcoinFutureAPI import OKCoinFuture
import pandas as pd
import logging


class Turtle:
    # TODO 初始化apikey，secretkey,url
    def __init__(self):
        with open("key","r",encoding="utf-8") as csvfile:
            key = [ item for item in csv.reader(csvfile) ][0]
        apikey = key[0]
        secretkey = key[1]

        # 请求注意：国内账号需要 修改为 www.okcoin.cn
        api = 'www.okcoin.com'
        okcoin = self.okcoin = OKCoinFuture(api, apikey, secretkey)

        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                            datefmt='%b %d %H:%M:%S', filename='turtle.out', filemode='a')

        self.step = 0.01    # 0.01 即 1%
        logging.info('设置初始步进: %.1f%%' % (self.step*100))
        self.record_info()


    # TODO 资金\头寸\头寸数\加仓价\平仓价\加仓时间戳\休市深度
    def record_info(self):
        logging.info('-' * 80)
        self.funds = self.okcoin.future_userinfo().get('info').get('btc').get('account_rights')
        logging.info('持有资金: %.4f BTC' % self.funds)
        holding = self.okcoin.future_position('btc_usd', 'quarter').get('holding')[0]
        logging.info('持有多仓 %d 张  可平多仓 %d 张' % (holding.get('buy_amount'), holding.get('buy_available')))
        logging.info('持有空仓 %d 张  可平空仓 %d 张' % (holding.get('sell_amount'), holding.get('sell_available')))
        last = self.last = self.okcoin.future_ticker('btc_usd', 'quarter').get('ticker').get('last')
        self.bull_ov_price = last * (1+self.step)
        self.bull_li_price = last * (1-self.step/2)
        self.bear_ov_price = last * (1-self.step)
        self.bear_li_price = last * (1+self.step/2)
        logging.info('最新价:%.2f' % last)
        logging.info('多仓加仓价 %4.2f  多仓止损价 %4.2f  空仓加仓价 %4.2f  空仓止损价 %4.2f' %
                (self.bull_ov_price, self.bull_li_price, self.bear_ov_price, self.bear_li_price))
        logging.info('-' * 80)

    # TODO 计算平均振幅
    def count_atr_mean(self):
        data = self.okcoin.future_kline('btc_usd', '1day', 'quarter', '100', str(time.time()-100*24*3600))
        count = 0
        sum = 0.0
        atr_mean = []
        for item in data:
            count += 1
            jitter = (item[2]-item[3])/(item[2]+item[3])*2
            sum += jitter
            if count == 1:
                if jitter<0.01: sum += self.step-jitter
                atr_mean.append(sum)
            if count == 2: atr_mean.append(sum/count)
            if count == 3: atr_mean.append(sum/count)
            if count == 5: atr_mean.append(sum/count)
            if count == 8: atr_mean.append(sum/count)
            if count == 13: atr_mean.append(sum/count)
            if count == 21: atr_mean.append(sum/count)
            if count == 34: atr_mean.append(sum/count)
            if count == 55: atr_mean.append(sum/count)
            if count == 89: atr_mean.append(sum/count)
        return atr_mean

    # TODO 计算头寸, 返回头寸(单位:张)
    def count_pos(self):
        self.funds = self.okcoin.future_userinfo().get('info').get('btc').get('account_rights')
        self.last = self.okcoin.future_ticker('btc_usd', 'quarter').get('ticker').get('last')
        # 1张合约100美元, 20倍杠杆, 以资金5%作为头寸
        self.position = int(self.funds * self.last / 100)
        return self.position


    # TODO 价格监测, 执行 继续监测 / 加仓 / 平仓 命令
    def price_monitor(self):
        last = self.last = self.okcoin.future_ticker('btc_usd', 'quarter').get('ticker').get('last')
        if last < self.bull_li_price:
            # TODO 平多仓
            self.order('cover_bull')
        elif last > self.bull_ov_price:
            self.order('bull')

        if last > self.bear_li_price:
            # TODO 平空仓
            self.order('cover_bear')
        elif last < self.bear_ov_price:
            self.order('bear')


    # TODO 下单函数, 返回订单号等
    def order(self, ktype):
        type = {'bull':1, 'bear':2, 'cover_bull':3, 'cover_bear':4}[ktype]
        # 根据海龟交易法则设置加仓点和止损点
        if self.last < self.bull_li_price or self.last > self.bull_ov_price:
            self.bull_ov_price = self.last * (1+self.step)
            self.bull_li_price = self.last * (1-self.step/2)

        if self.last > self.bear_li_price or self.last < self.bear_ov_price:
            self.bear_ov_price = self.last * (1-self.step)
            self.bear_li_price = self.last * (1+self.step/2)

        # https://www.okcoin.com/about/rest_api.do#ftapi
        # btc/ltc, 合约类型, 价格, 数量, 1:开多 2:开空 3:平多 4:平空, 是否市价交易, 杠杆倍数
        # 多仓 
        order_id = {}
        if ktype == 'bull':
            pos = self.count_pos()
            logging.info('加多仓 - 加仓价:%.2f' % self.last)
            order_id = self.okcoin.future_trade('btc_usd', 'quarter', str(self.last+0.01), str(pos), str(type), '0', '20')
            self.record_info()
        elif ktype == 'cover_bull':
            buy_available = self.okcoin.future_position('btc_usd', 'quarter').get('holding')[0].get('buy_available')
            if buy_available:
                logging.info('平多仓 - 平仓价:%.2f' % self.last)
                order_id = self.okcoin.future_trade('btc_usd', 'quarter', str(self.last), str(buy_available), str(type), '1', '20')
                self.record_info()
        # 空仓  
        elif ktype == 'bear':
            pos = self.count_pos()
            logging.info('加空仓 - 加仓价:%.2f' % self.last)
            order_id = self.okcoin.future_trade('btc_usd', 'quarter', str(self.last-0.01), str(pos), str(type), '0', '20')
            self.record_info()
        elif ktype == 'cover_bear':
            sell_available = self.okcoin.future_position('btc_usd', 'quarter').get('holding')[0].get('sell_available')
            if sell_available:
                logging.info('平空仓 - 平仓价:%.2f' % self.last)
                order_id = self.okcoin.future_trade('btc_usd', 'quarter', str(self.last), str(sell_available), str(type), '1', '20')
                self.record_info()

        return order_id


    def cancle(self):
        return self.okcoin.future_cancel('btc_usd', 'quarter', '47231499')



if __name__ == '__main__':
    # TODO
    turtle = Turtle()
    last = time.time()
    while True:
        now = time.time()
        if now - last > 3600:
            last = now
            turtle.step = turtle.count_atr_mean()[2]
            logging.info('设置步进: %.2f%%' % (turtle.step*100))
        turtle.price_monitor()
        time.sleep(2)

