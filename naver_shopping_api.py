import pandas as pd
import json
import urllib.request


class NaverDataLabOpenAPI():
    """
    네이버 데이터랩 오픈 API 컨트롤러 클래스
    """
    def __init__(self, client_id, client_secret):
        """
        인증키 설정 및 검색어 그룹 초기화
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.url = "https://openapi.naver.com/v1/datalab/shopping/category/age"


    def get_age_data(self, startDate, endDate, timeUnit, category):
        """
        요청 결과 반환
        """
        # Request body
        body = json.dumps({
            "startDate": startDate,
            "endDate": endDate,
            "timeUnit": timeUnit,
            "category": category,
        }, ensure_ascii=False)
        # Results
        request = urllib.request.Request(self.url)
        request.add_header("X-Naver-Client-Id",self.client_id)
        request.add_header("X-Naver-Client-Secret",self.client_secret)
        request.add_header("Content-Type","application/json")
        response = urllib.request.urlopen(request, data=body.encode("utf-8"))
        rescode = response.getcode()
        
        if(rescode==200):
            result = json.loads(response.read())  
            df = pd.DataFrame()
            date = sorted(list(set(data['period'] for data in result['results'][0]['data'])))
            g10, g20, g30, g40, g50, g60 = [], [], [], [], [], []
            for i in range(len(date)):
                for data in result['results'][0]['data']:
                    if data['period'] == date[i]:
                        if data['group'] == '10':
                            g10.append(data['ratio'])
                        if data['group'] == '20':
                            g20.append(data['ratio'])
                        if data['group'] == '30':
                            g30.append(data['ratio'])
                        if data['group'] == '40':
                            g40.append(data['ratio'])
                        if data['group'] == '50':
                            g50.append(data['ratio'])
                        if data['group'] == '60':
                            g60.append(data['ratio'])
                for group in [g10,g20,g30,g40,g50,g60]:
                    if len(group) != i+1:
                        group.append('')
            df['날짜'] = date
            df['10대'] = g10
            df['20대'] = g20
            df['30대'] = g30
            df['40대'] = g40
            df['50대'] = g50
            df['60대+'] = g60
            df['날짜'] = pd.to_datetime(df['날짜'])
        else:
            print("Error Code:" + rescode)
            
        return df
