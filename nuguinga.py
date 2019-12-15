# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, render_template
import requests
import json
import math
from werkzeug.datastructures import ImmutableMultiDict
from datetime import datetime
app = Flask(__name__)
apiKey = 'xNH2WKytP%2Bu7hIVRja1PcTCJ%2FVOcBBMiyAQ0bq9ocLE'
odsay = 'https://api.odsay.com/v1/api/searchPubTransPath?'
Kapikey = 'e58fafda50cba0f7624743d075d8b515'

@app.route('/', methods = ['POST', 'GET'])
@app.route('/', methods =['POST', 'GET'])
def index(name=None):
    location = ''
    if request.method == 'POST':
        sdata = request.data
        sdata = sdata.decode('utf-8')
        jsdata = json.loads(sdata)
        if jsdata['action']['actionName'] != 'response.time' \
                and jsdata['action']['actionName'] != 'time' \
                and jsdata['action']['actionName'] != 'location' \
                and jsdata['action']['actionName'] != 'walk' \
                and jsdata['action']['actionName'] != 'response' \
                and jsdata['action']['actionName'] != 'response_default':
            return json.dumps(jsdata)

        para = jsdata['action']['parameters']
        try:
            hour = 0
            minute = 0
            location = para['location']['value']
            m = para['M']['value']
            hour = int(para['hour']['value'])
            try:
                minute = int(para['min']['value'])
            except:
                minute = 0
        except:
            print('No location/hour')
            return json.dumps(jsdata)
    else:
        print('Not POST')

    kurl = 'https://dapi.kakao.com/v2/local/search/keyword.json'
    header={'authorization':'KakaoAK e58fafda50cba0f7624743d075d8b515'}
    queryString={'query':location}
    r = requests.get(kurl, headers=header, params=queryString)
    data = json.loads(r.text)
    ex = data['documents'][0]['x']
    ey = data['documents'][0]['y']
    total = 0
    # 광운대학교 sx = 127.059696 sy = 37.619620
    url = odsay + 'SX=' + str(sx) + '&SY=' + str(sy) + '&EX=' + str(ex) + '&EY=' + str(ey) + '&apiKey=' + apiKey
    FSstation = location
    # request for finding paths
    r = requests.get(url)
    data = json.loads(r.text)
    if not 'error' in data:
        ways = []
        for d in data['result']['path']:
            ways.append(d)
            destination = ways[0]
            try:
                FSstation = destination['info']['firstStartStation']
            except:
                FSstation = ''
            ptime = destination['info']['totalTime']

    # 보행자 길 찾기 시작
    # 첫번째 정류장 X,Y 좌표 추출
    firstStationX = data['result']['path'][0]['subPath'][1]['startX']
    firstStationY = data['result']['path'][0]['subPath'][1]['startY']

    # SK Tmap 길찾기
    TmapURL = 'https://apis.openapi.sk.com/tmap/routes/pedestrian?version=1&startX=' + str(sx) + '&startY=' + str(sy) + '&endX=' + str(firstStationX) + '&endY=' + str(firstStationY) + '&startName=시작&endName=끝'
    TmapHeaders = {'Accept': 'application/json','Content-Type': 'application/json; charset=UTF-8','AppKey': 'c5058c89-36e2-48ed-8d96-96b712e9a33e'}

    # 보행자 길 찾기 request
    TmapR = requests.get(TmapURL,headers=TmapHeaders)

    # json화
    TmapData = json.loads(TmapR.text)
    startPedTime = TmapData['features'][0]['properties']['totalTime']
    # 집->첫 정류장 이동시간 출력
    lastStationX = data['result']['path'][0]['subPath'][1]['endX']
    lastStationY = data['result']['path'][0]['subPath'][1]['endY']
    TmapURL = 'https://apis.openapi.sk.com/tmap/routes/pedestrian?version=1&startX=' + str(lastStationX) + '&startY=' + str(lastStationY) + '&endX=' + str(ex) + '&endY=' + str(ey) + '&startName=시작&endName=끝'

    # 보행자 길 찾기 request
    TmapR = requests.get(TmapURL,headers=TmapHeaders)

    # json화
    TmapData = json.loads(TmapR.text)
    endPedTime = TmapData['features'][0]['properties']['totalTime']

    # 집->첫 정류장 이동시간 출력
    totalPedTime = startPedTime + endPedTime

    # 보행자 길 찾기 종료
    fStation = destination['info']['firstStartStation']
    eStation = destination['info']['lastEndStation']
    total = ptime + totalPedTime/60
    tothour = 0
    totmin = 0
    walk = '0'

    # SK Tmap 길찾기
    TmapURL = 'https://apis.openapi.sk.com/tmap/routes/pedestrian?version=1&startX=' + str(sx) + '&startY=' + str(sy) + '&endX=' + str(ex) + '&endY=' + str(ey) + '&startName=시작&endName=끝'
    TmapHeaders = {'Accept': 'application/json','Content-Type': 'application/json; charset=UTF-8','AppKey': 'c5058c89-36e2-48ed-8d96-96b712e9a33e'}

    # 보행자 길 찾기 request
    TmapR = requests.get(TmapURL,headers=TmapHeaders)

    # json화
    TmapData = json.loads(TmapR.text)
    walkingTime = math.ceil(TmapData['features'][0]['properties']['totalTime']/60)

    if walkingTime < total or total == 0:
        walk = str(walkingTime)

    # 이미 늦은 경우 확인
    stime = int(hour)
    wtime = int(walk)
    if m == '오후':
        stime = stime + 12
    prom_total = stime * 60 + minute
    if wtime != 0:
        take_total = wtime
    else:
        take_total = total
        walk = '0'
    now = datetime.now()
    cur_total = int(now.hour) * 60 + int(now.minute)
    if cur_total + take_total > prom_total:
        walk = '0'
        late = True
    else:
        late = False

    # 출발 시간 계산
    inputtime = int(hour) * 60 + minute
    if inputtime > total:
        tothour = hour - int(total/60)
        if minute > int(total%60):
            totmin = minute - int(total%60)
        else:
            tothour -= 1
            totmin = minute + 60 - int(total%60)
    elif inputtime == total:
        if m == '오전':
            m = '오후'
        else:
            m = '오전'
        tothour = 12
        totmin = 0
    else:
        if m == '오전':
            m = '오후'
        else:
            m = '오전'
        tothour = 12 - int(total/60)
        if minute > int(total%60):
            totmin = minute - int(total%60)
        else:
            tothour -= 1
            totmin = minute + 60 - int(total%60)

    if tothour == 0:
        tothour = 12

    total_hour = ''
    if late == True:
        total_hour = '-1'
    else:
        total_hour = str(tothour)

    rdata = {"version": "2.0"}
    rdata["resultCode"] = "OK"
    rdata["output"] = {'arrival': {'value':'도착', 'type':'ARRIVAL'},
                       'hour': {'value' : hour, 'type': 'BID_TI_HOUR'},
                       'location': {'value': location, 'type': 'LOCATION'},
                       'total_Time': total_hour, 'total_min': str(totmin), 'N': m, 'FS': FSstation, 'WALK': walk}
    return json.dumps(rdata)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)