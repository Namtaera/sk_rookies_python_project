import os
import requests
from dotenv import load_dotenv

load_dotenv()

OPINET_KEY = os.getenv("OPINET_KEY")
BASE_URL = os.getenv("BASE_URL")

if not OPINET_KEY or not BASE_URL:
    raise ValueError(".env 값 없음 (┬┬﹏┬┬)")

# 사용자가 입력하는 지역명과 오피넷 시도 코드 매칭
SIDO_CODES = {
    "서울": "01",
    "경기": "02",
    "강원": "03",
    "충북": "04",
    "충남": "05",
    "전북": "06",
    "전남": "07",
    "경북": "08",
    "경남": "09",
    "제주": "10",
    "부산": "11",
    "대구": "12",
    "인천": "13",
    "광주": "14",
    "대전": "15",
    "울산": "16",
    "세종": "17",
}


# 오피넷 API에서 특정 시도의 휘발유 최저가 주유소 TOP10 조회
def get_low_top10(sido_name):
    # 입력한 지역명을 오피넷 지역 코드로 변환
    sido_cd = SIDO_CODES.get(sido_name)

    # 지역명이 딕셔너리에 없으면 에러 발생
    if not sido_cd:
        raise ValueError(f"'{sido_name}'은 올바른 지역명이 아닙니다. 다시 확인해주세요.")

    # API 요청에 필요한 파라미터 설정
    # prodcd: B027 = 휘발유
    parameters = {
        "code": OPINET_KEY,
        "out": "json",
        "area": sido_cd,
        "prodcd": "B027",
        "cnt": "10"
    }

    # 오피넷 최저가 TOP10 API 요청
    response = requests.get(
        f"{BASE_URL}/lowTop10.do",
        params=parameters,
        timeout=5
    )
    response.raise_for_status()
    data_result = response.json()

    # 응답 데이터에서 주유소 목록만 추출
    oil_list = data_result.get("RESULT", {}).get("OIL", [])

    # API 원본 주유소 목록 반환
    return oil_list


# API 원본 데이터를 프로젝트에서 쓰기 좋은 딕셔너리 형태로 정리
def format_oil_data(oil_list, sido_name):
    formatted_list = []

    for i, oil in enumerate(oil_list, 1):
        clean_data = {
            "rank": i,                         # 순위
            "region": sido_name,               # 조회 지역
            "station_name": oil.get("OS_NM"),  # 주유소명
            "price": oil.get("PRICE"),         # 가격
            "address": oil.get("VAN_ADR"),     # 주소
            "brand": oil.get("POLL_DIV_CD")    # 브랜드 코드
        }

        formatted_list.append(clean_data)

    return formatted_list


try:
    # 사용자에게 조회할 지역 입력받기
    sido_input = input("조회할 지역을 입력하세요 (예: 서울, 경기): ")

    # 오피넷 API에서 원본 데이터 조회
    oil_list = get_low_top10(sido_input)

    # 원본 데이터를 깔끔한 딕셔너리 형태로 가공
    formatted_oil_list = format_oil_data(oil_list, sido_input)

    print("=" * 60)
    print(f"{sido_input} 지역 휘발유 최저가 주유소 TOP10")
    print("=" * 60)

    # 조회 결과가 없을 때
    if not formatted_oil_list:
        print("조회 결과가 없습니다.")

    # 조회 결과 출력
    else:
        for oil in formatted_oil_list:
            print(f"{oil['rank']}위: {oil['station_name']} --- (가격: {oil['price']}원)")
            print(f"주소: {oil['address']}")
            print("-" * 60)

except requests.exceptions.HTTPError as e:
    print(f"HTTP 에러 (상태코드 확인): {e}")

except requests.exceptions.RequestException as e:
    print(f"네트워크 통신 에러: {e}")

except Exception as e:
    print(f"알 수 없는 에러 : {e}")