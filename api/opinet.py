import requests
from config import OPINET_KEY, BASE_URL

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


# 특정 시도 지역의 최저가 주유소 TOP10 조회
def get_low_top10(sido_name: str, prodcd: str = "B027") -> list[dict]:
    """
    특정 시도 지역의 최저가 주유소 TOP10 조회

    Args:
        sido_name (str): 조회할 시도명
        prodcd (str): 유종 코드 (기본값: B027 = 휘발유)

    Returns:
        list[dict]: 오피넷 API 원본 데이터
    """

    sido_cd = SIDO_CODES.get(sido_name)

    if not sido_cd:
        raise ValueError(f"'{sido_name}'은 올바른 지역명이 아닙니다.")

    parameters = {
        "code": OPINET_KEY,
        "out": "json",
        "area": sido_cd,
        "prodcd": prodcd,
        "cnt": "10"
    }

    try:
        response = requests.get(
            f"{BASE_URL}/lowTop10.do",
            params=parameters,
            timeout=5
        )

        response.raise_for_status()

        data_result = response.json()
        oil_list = data_result.get("RESULT", {}).get("OIL", [])

        return oil_list

    except Exception as e:
        print(f"[opinet] 조회 중 오류 발생: {e}")
        return []


# API 원본 데이터를 프로젝트용 딕셔너리 형태로 가공
def format_oil_data(oil_list: list[dict], sido_name: str) -> list[dict]:
    """
    오피넷 API 원본 데이터를 CSV/JSON 저장용 딕셔너리 형태로 가공

    Args:
        oil_list (list[dict]): API 원본 데이터
        sido_name (str): 조회 지역명

    Returns:
        list[dict]: 가공된 데이터 리스트
    """

    formatted_list = []

    for i, oil in enumerate(oil_list, 1):
        clean_data = {
            "rank": i,
            "region": sido_name,
            "station_name": oil.get("OS_NM"),
            "price": oil.get("PRICE"),
            "address": oil.get("VAN_ADR"),
            "brand": oil.get("POLL_DIV_CD")
        }

        formatted_list.append(clean_data)

    return formatted_list