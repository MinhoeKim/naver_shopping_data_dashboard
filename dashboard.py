import streamlit as st
import pandas as pd
from naver_shopping_api import *
from data_to_fig import *
from streamlit_gsheets import GSheetsConnection
import gspread
from streamlit_option_menu import option_menu
from datetime import date, timedelta
import base64

st.set_page_config(page_title=None, page_icon=None, layout="wide")

conn = st.connection("gsheets", type=GSheetsConnection)

client_id = st.secrets["naver"]["naver_client_id"]
client_secret = st.secrets["naver"]["naver_client_secret"]

gc = gspread.service_account_from_dict(st.secrets["gspread_credentials"])
sh = gc.open_by_url(st.secrets["gspread_credentials"]["spreadsheet"])
worksheet_list = sh.worksheets()
worksheet_names = [ws.title for ws in worksheet_list]

if 'data' not in st.session_state: 
    st.session_state.data = pd.DataFrame()
    st.session_state.worksheet_name = None

# 버튼 스타일 설정
button_style = """
<style>
div.stButton > button:first-child {
    background-color: #02ab21;
    color:#ffffff;
}
</style>
"""
st.markdown(button_style, unsafe_allow_html=True)

# HTML 다운로드 버튼 생성 함수
def html_download_button(fig, file_name):
    html_content = fig.to_html(full_html=True, include_plotlyjs='cdn')
    b64 = base64.b64encode(html_content.encode()).decode()
    href2 = f"data:text/html;base64,{b64}"
    
    st.markdown(f"""
        <a href="{href2}" download="{file_name}" target="_blank">
            <button style="background-color: #02ab21; color: white; border: none; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 8px;">
                html로 저장
            </button>
        </a>
        """, unsafe_allow_html=True)

#사이드바
with st.sidebar:
    #페이지 선택창
    selected = option_menu("Index", ["Home", "구매 분석", "구매 예측"],
                        icons=['house', 'bar-chart-steps', 'kanban'],
                        menu_icon="app-indicator", default_index=0,
                        styles={
        "container": {"padding": "5!important", "background-color": "#black"},
        "icon": {"color": "orange", "font-size": "25px"}, 
        "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#eee"},
        "nav-link-selected": {"background-color": "#02ab21"},
    }
    )
    
    # 구글시트 데이터 불러오기
    @st.cache_data
    def load_from_gsheet(selected_worksheet):
        data = conn.read(worksheet=selected_worksheet)
        return data
    
    selected_worksheet = st.selectbox("**구글시트 데이터**", worksheet_names)

    if st.button("불러오기"):
        st.session_state.worksheet_name = selected_worksheet
        st.session_state.data = load_from_gsheet(selected_worksheet)
        if '날짜' in st.session_state.data.columns:
            st.session_state.data['날짜'] = pd.to_datetime(st.session_state.data['날짜'])

    # 네이버 쇼핑 API 호출기
    st.markdown('**네이버 쇼핑 API 호출기**')

    @st.cache_data
    def load_category_df():
        category_df = pd.read_excel("category_20240610_152534.xls")
        return category_df

    category_df = load_category_df()
    category_columns = ["대분류", "중분류", "소분류", "세분류"]

    main_category = st.selectbox("대분류", category_df["대분류"].unique())
    filtered_df = category_df if not (category_df["대분류"] == main_category).any() else  category_df[category_df["대분류"] == main_category]
    sub_category1 = st.selectbox("중분류", filtered_df["중분류"].unique())
    filtered_df = filtered_df if not (filtered_df["중분류"] == sub_category1).any() else  filtered_df[filtered_df["중분류"] == sub_category1]
    sub_category2 = st.selectbox("소분류", filtered_df["소분류"].unique())
    filtered_df = filtered_df if not (filtered_df["소분류"] == sub_category2).any() else  filtered_df[filtered_df["소분류"] == sub_category2]    
    sub_category3 = st.selectbox("세분류", filtered_df["세분류"].unique())
    filtered_df = filtered_df if not (filtered_df["세분류"] == sub_category3).any() else  filtered_df[filtered_df["세분류"] == sub_category3]

    start_date_input = str(st.date_input('시작일', date.today()-timedelta(days=365), min_value=date(2018, 1, 1), max_value=date.today()))
    end_date_input = str(st.date_input('종료일', date.today(), min_value=date(2018, 1, 1), max_value=date.today()))
    time_unit = st.radio("날짜단위", ['date', 'month'])

    if st.sidebar.button(label="호출하기"):
        category = f"{main_category}_{sub_category1}_{sub_category2}_{sub_category3}"
        catid = str(filtered_df["카테고리번호"].iloc[0])
        start_date = start_date_input
        end_date = end_date_input
        st.session_state.worksheet_name = category + '_' + start_date + '~' + end_date
        ShoppingInsight = NaverDataLabOpenAPI(client_id=client_id, client_secret=client_secret)
        df = ShoppingInsight.get_age_data(start_date, end_date, time_unit, catid)
        st.session_state.data = df

#데이터 미선택 안내 함수
def non_data_error():
    st.title("🍀네이버 쇼핑 연령대별 구매예측 대시보드")
    st.divider()
    st.error("데이터가 비어있습니다. 사이드바를 통해서 데이터를 선택해주세요.")
    st.markdown("""
    ## 사이드바

    **Index**

    - Home, 구매 분석, 구매 예측 페이지 중 선택합니다.

    **구글시트 데이터**

    - 구글시트에 저장된 연령별 시계열 데이터를 불러옵니다.

    **네이버 쇼핑 API 호출기**

    - 네이버 쇼핑 데이터랩 API 를 이용하여 데이터를 전처리 후 불러옵니다.
    """)

# 홈 페이지 함수
def home_page():
    if st.session_state.data.empty:
        non_data_error()
        return
    data_visualization()


def data_visualization():
    st.title("🍀네이버 쇼핑 연령대별 구매예측 대시보드")
    st.header("🏡Home")
    st.success("선택된 데이터의 연령대별 구매 횟수의 시계열 그래프, 파이 차트를 제공하여 데이터를 시각화합니다.")
    st.divider()
    st.write(f"**{st.session_state.worksheet_name}**")
    st.write(st.session_state.data)
    # save_to_google_sheets_button()
    fig = time_series_and_pie(st.session_state.data, st.session_state.worksheet_name)
    st.plotly_chart(fig, use_container_width=True)
    html_download_button(fig, st.session_state.worksheet_name+"time_series_and_pie")

# #구글시트에 저장버튼 함수
# def save_to_google_sheets_button():
#     if st.button('구글시트에 저장'):
#         if st.session_state.worksheet_name in worksheet_names:
#             conn.clear(worksheet=st.session_state.worksheet_name)
#             conn.update(worksheet=st.session_state.worksheet_name, data=st.session_state.data)
#             st.success(f'데이터가 구글 스프레드시트에 업데이트 되었습니다.\n{st.session_state.worksheet_name}')
#         else:
#             conn.create(worksheet=st.session_state.worksheet_name, data=st.session_state.data)
#             st.success(f'데이터가 구글 스프레드시트에 저장되었습니다.\n{st.session_state.worksheet_name}')

# 분석 페이지 함수
def analytics_page():
    if st.session_state.data.empty:
        non_data_error()
        return
    st.header("📊구매 분석")
    st.success("연령대별 ACF, PACF 를 제공합니다.")
    st.divider()
    analytics_visualization()

def analytics_visualization():
    if len(st.session_state.data) < 8:
        st.error("분석에 필요한 데이터의 수가 부족합니다. 최소 8개 이상의 데이터를 선택해주세요")
        return
    date_time = st.selectbox("날짜 컬럼 선택", st.session_state.data.columns)
    col_name = st.selectbox("시계열 컬럼 선택", st.session_state.data.columns, index=1)
    max_lags = 50 if not len(st.session_state.data)//2-1 < 50 else len(st.session_state.data)//2-2
    lags = st.slider("ACF, PACF 랙 수 선택", min_value=1, max_value=max_lags, value=max_lags//2)
    fig = age_analytics(st.session_state.data, date_time, col_name, lags)
    st.plotly_chart(fig, use_container_width=True)
    html_download_button(fig, st.session_state.worksheet_name + "ACF, PACF 테스트")
    st.write("")
    diff = st.slider("차분 계수 선택", min_value=1, max_value=2, value=1)
    fig = diff_age_analytics(st.session_state.data, date_time, col_name, lags, diff)
    st.plotly_chart(fig, use_container_width=True)
    html_download_button(fig, st.session_state.worksheet_name + "차분 ACF, PACF 테스트")

# 예측 페이지 함수
def forecast_page():
    if st.session_state.data.empty:
        non_data_error()
        return
    st.header("📑구매 예측")
    st.success("autoARIMA 모델을 이용하여 연령대별 구매횟수를 예측합니다")
    st.divider()
    forecast_visualization()

def forecast_visualization():
    if len(st.session_state.data) < 8:
        st.error("분석에 필요한 데이터의 수가 부족합니다. 최소 8개 이상의 데이터를 선택해주세요")
        return
    date_time = st.selectbox("날짜 컬럼 선택", st.session_state.data.columns)
    col_name = st.selectbox("시계열 컬럼 선택", st.session_state.data.columns, index=1)
    if st.button('예측') :
        fig = age_purchase_predict(st.session_state.data, date_time, col_name)
        st.plotly_chart(fig, use_container_width=True)
        html_download_button(fig, st.session_state.worksheet_name+"예측")

# 페이지 실행
if selected == "Home":
    home_page()
elif selected == "구매 분석":
    analytics_page()
elif selected == "구매 예측":
    forecast_page()
