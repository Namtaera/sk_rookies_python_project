import requests
from api.config import OPINET_KEY, BASE_URL

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
def get_low_top10(sido_name: str, prodcd: str = "B027", cnt: int = 10) -> list[dict]:
    """
    특정 시도 지역의 최저가 주유소 TOP10 조회

    Args:
        sido_name (str): 조회할 시도명
        prodcd (str): 유종 코드 (기본값: B027 = 휘발유)
        cnt (int): 조회 개수(오피넷 lowTop10는 최대 10 권장)

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
        "cnt": str(cnt)
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

    # 요청 시간 초과
    except requests.exceptions.Timeout:
        print("[opinet] 요청 시간이 초과되었습니다.")
        return []

    # 네트워크/API 요청 오류
    except requests.exceptions.RequestException as e:
        print(f"[opinet] API 요청 오류: {e}")
        return []

    # JSON 파싱 오류
    except ValueError:
        print("[opinet] JSON 데이터 변환 실패")
        return []

    # 기타 예외
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


def get_around_all(x: float, y: float, radius: int = 5000, prodcd: str = "B027", sort: int = 1) -> list[dict]:
    """
    특정 위치(KATEC) 기준 반경 내 주유소 목록 조회.

    오피넷 aroundAll.do는 시도/구가 아니라 '좌표+반경' 기준으로 조회하므로
    상세 주소를 입력해도 실제 위치 중심으로 결과가 나온다.
    """
    parameters = {
        "certkey": OPINET_KEY,
        "out": "json",
        "x": str(x),
        "y": str(y),
        "radius": str(radius),
        "prodcd": prodcd,
        "sort": str(sort),  # 1: 가격순, 2: 거리순
    }

    try:
        response = requests.get(
            f"{BASE_URL}/aroundAll.do",
            params=parameters,
            timeout=5,
        )
        response.raise_for_status()

        data_result = response.json()
        oil_list = data_result.get("RESULT", {}).get("OIL", [])
        return oil_list
    except requests.exceptions.Timeout:
        print("[opinet] 요청 시간이 초과되었습니다.")
        return []
    except requests.exceptions.RequestException as e:
        print(f"[opinet] API 요청 오류: {e}")
        return []
    except ValueError:
        print("[opinet] JSON 데이터 변환 실패")
        return []
    except Exception as e:
        print(f"[opinet] 조회 중 오류 발생: {e}")
        return []


def get_detail_by_id(station_id: str) -> dict | None:
    """주유소 ID(UNI_ID)로 상세정보(주소 포함) 조회."""
    if not station_id:
        return None

    parameters = {
        "certkey": OPINET_KEY,
        "out": "json",
        "id": station_id,
    }

    try:
        response = requests.get(
            f"{BASE_URL}/detailById.do",
            params=parameters,
            timeout=5,
        )
        response.raise_for_status()

        data_result = response.json()
        oil_list = data_result.get("RESULT", {}).get("OIL", [])
        if not oil_list:
            return None
        return oil_list[0]
    except requests.exceptions.Timeout:
        print("[opinet] 요청 시간이 초과되었습니다.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"[opinet] API 요청 오류: {e}")
        return None
    except ValueError:
        print("[opinet] JSON 데이터 변환 실패")
        return None
    except Exception as e:
        print(f"[opinet] 조회 중 오류 발생: {e}")
        return None


def format_around_data(around_list: list[dict], address_by_id: dict[str, dict] | None = None) -> list[dict]:
    """
    aroundAll.do 결과를 템플릿에서 쓰는 형태로 정규화.

    aroundAll.do는 주소(VAN_ADR/NEW_ADR)를 주지 않으므로,
    필요하면 detailById.do 응답을 address_by_id로 주입한다.
    """
    address_by_id = address_by_id or {}
    formatted_list: list[dict] = []

    for i, oil in enumerate(around_list, 1):
        station_id = oil.get("UNI_ID")
        detail = address_by_id.get(station_id, {})

        van_addr = detail.get("VAN_ADR")
        new_addr = detail.get("NEW_ADR")
        address = new_addr or van_addr

        clean_data = {
            "rank": i,
            "station_id": station_id,
            "station_name": oil.get("OS_NM"),
            "price": oil.get("PRICE"),
            "distance": oil.get("DISTANCE"),
            "address": address,
            "brand": oil.get("POLL_DIV_CD"),
        }
        formatted_list.append(clean_data)

    return formatted_list