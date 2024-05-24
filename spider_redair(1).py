# encoding: utf-8
'''
@Time : 2019/12/2 22:18 
@File : spider_redair.py
@Software: PyCharm
'''
import math
import random
import time, requests
import uuid
from fake_useragent import UserAgent
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
location = 'fake_useragent.json'
ua = UserAgent(cache_path=location)

import json


def Redair_search(start_data):
    #print('ok')
    if start_data.get('proxy')==None:
        pro_ip = 'null'
    else:
        pro_ip=str(start_data['proxy'])
    try:
    # if True:

        payload = "{\"t\":{\"tripType\":\"OW\",\"depAirportCode\":\"%s\",\"arrAirportCode\":\"%s\",\"depDate\":\"%s\"}}"%(start_data['from'],start_data['to'],start_data['daytime'])
        headers = {
            'sec-ch-ua': '"Google Chrome";v="87", " Not;A Brand";v="99", "Chromium";v="87"',
            'Accept': 'application/json, text/plain, */*',
            'User-Agent': str(ua.random),#'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
            'Content-Type': 'application/json',
            'origin': 'https://www.redair.cn',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            # 'referer': 'https://www.redair.cn/ticket?deptAirportCode=CSX&arrAirportCode=WUX&deptDate=2021-06-10&retDate=2021-06-17&switch=OW&normalBooking=true',
        }

        if pro_ip != 'null':
            response = requests.post(url = "https://sf.redair.cn/route/searchflight", data=payload, headers=headers, proxies={'https':'https://'+str(pro_ip)},timeout=18)
        else:
            response = requests.post(url = "https://sf.redair.cn/route/searchflight", data=payload, headers=headers,timeout=18)

        # print(response.text[:20])
        # print(data)
        # exit()
        if response.status_code==200:
            data = response.json()
            #print(data)
            if data['success']==True:
                list_l=[]
                for datas in data['data']:
                    depAirportCode=datas['depAirportCode']
                    arrAirportCode=datas['arrAirportCode']
                    deptime=datas['depDatetime'].split('-')+datas['depTime'].split(':')
                    arrtime=datas['arrDatetime'].split('-')+datas['arrTime'].split(':')
                    flightNoGroup=datas['flightNoGroup']#航班号
                    newlist=[]
                    for base in datas['flightUnitVOList']:
                        #if base['productSpace']['name']!='会员专享'and base['productSpace']['name']!='会员秒杀价' and base['productSpace']['name']!='实名会员价':
                        #if base['productSpace'].get('product')==None or base['productSpace']['product']['productCode']!='SMHY':
                        if 'SM' not in base['productCodeGroup'] and  base['productSpace'].get('product')==None:

                        # if '会员' not in base['productSpace']['name']:
                        #     newlist.append(base)
                        # else:
                        #     continue
                            newlist.append(base)
                    newlist.sort(key=lambda k:k['adultTotalPrice']['amount'])
                    # baseAmount=datas['flightUnitVOList'][0]
                    # print(baseAmount)
                    # print(newlist)
                    adultPrice=newlist[0]['adultTotalPrice']['amount']
                    tax=newlist[0]['adultTotalTax']['amount']
                    cabinCode=newlist[0]['cabinCodeGroup']
                    # print(json.dumps(newlist))
                    # if len(cabinCode)==1:
                    if newlist[0]['segmentList'][0]['stopList']!=[]:
                        stopAirportName = newlist[0]['segmentList'][0]['stopList'][0]['stopAirportCode']
                    else:
                        stopAirportName=''
                    seat=newlist[0]['segmentList'][0]['cabin']['inventory']
                    sj = parse(depAirportCode, arrAirportCode, deptime, arrtime, flightNoGroup, stopAirportName,adultPrice,tax,cabinCode,seat)
                    if sj != {}:
                        list_l.append(sj)
                    # else:
                    #     with open('zzh.txt','a')as f:
                    #         f.write(start_data['from']+'-'+start_data['to']+'-'+start_data['daytime']+'-'+cabinCode+'\n')
                return {'results': list_l}
            else:
                # print(len(data))
                if data['data']==None or data['errorMessage']=='无航班信息' or data['errorMessage']=='查询航线不销售':
                    return {'results': []}#
                else:
                    return {'error': '出错'}
        else:
            return {'error': '状态码等于{}'.format(response.status_code)}

    except Exception as e:

        return {'error': 'Redair_Search Error:%s' % str(e)}





def redair(start_data):
    #print(start_data)
    redata = Redair_search(start_data)
    #print(redata)
    if redata.get('error') == None:
        # for ii in redata['results']:
        #     with open('data.txt','a')as f:
        #         f.write(ii['_id']+'--'+str(ii['flights'][0]['adultPrice'])+'--'+str(ii['flights'][0]['segmentsList'][0][0]['seats'])+'--'+ii['flights'][0]['segmentsList'][0][0]['cabin']+'--'+str(time.ctime())+'\n')
        redata['need'] = 0
        return redata
    else:
        redata['need'] = 1
        return redata


def parse(depAir, arrAir, deptime, arrtime, flightN, stopCities,adultPrice,tax,cabinCode,seats):
    # print(depAir, arrAir, deptime, arrtime, flightN, stopCities,adultPrice,tax,cabinCode)

    list_mongo=[]
    list_flight = []
    # if stopnum==None:
    #     stopCities=''
    # else:
    #     stopCities=stopnum
    if seats=='A':
        seat=9
    else:
        seat=int(seats)
    # print(departure.split('T')[1].split(':'))
    flight_dict = {
        "flightNumber": flightN,
        "depAirport":depAir,
        "depTime": ''.join(deptime),
        "depTerminal": '',
        "arrAirport": arrAir,
        "arrTime": ''.join(arrtime),
        "arrTerminal": '',
        "stopCities": stopCities,
        "operatingFlightNumber": "",
        "cabin": cabinCode,
        "cabinClass": "",
        "seats": seat,
        "aircraftCode": "",
        "operating": 0#不是共享1是共享
    }
    if flight_dict['cabin']!='C':
        list_flight.append(flight_dict)
        # print(list_flight)
        if list_flight != []:
            adultPrice = math.ceil(float(adultPrice))
            adultTax=math.ceil(float(tax))
            adultTotalPrice = adultPrice + adultTax
            mongo_dict={
                '_id':'Redair'+'-'+str(list_flight[0]['depAirport'])+'-'+str(list_flight[-1]['arrAirport'])+'-'+str(list_flight[0]['depTime'])[:8]+'-'+'@'.join([str(fly_i['flightNumber']) for fly_i in list_flight]),
                'flights':[{
                    'segmentsList':[list_flight],
                    'currency': 'CNY',
                    'adultPrice': adultPrice,
                    'adultTax': adultTax,
                    'adultTotalPrice': adultTotalPrice,
                            }],
                'status': 0,
                'msg': '',
                'siteCode': 'Redair',
                'datetime': int(str(list_flight[0]['depTime'])[:8]),
                'updatetime': int(time.time()),
            }
            # print('>>>>>>>>>>>>>>>',mongo_dict)
            list_mongo.append(mongo_dict)
    if list_mongo==[]:
        return {}
    else:
        return list_mongo[0]


if __name__ == '__main__':
    start_data = {
        'from': 'CSX',#CDG
        'to': 'WUX',#FOC
        'daytime': '2023-08-3',
        'adt_num': '1',
        'chd_num': '0',
        'inf_num': '0',
        'fly_num': '1',
        'limit_seat': '1',
        'proxy': 'null'
    }
    s = time.time()
    a = redair(start_data)
    print(a)
    # for i in a['results']:
    #     print(i)
    # print(time.time() - s)

































