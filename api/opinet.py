import requests
from api.config import OPINET_KEY, BASE_URL


SIDO_CODES = {
    "서울": "01", "서울특별시": "01", "서울시": "01",
    "경기": "02", "경기도": "02",
    "강원": "03", "강원도": "03",
    "충북": "04", "충청북도": "04",
    "충남": "05", "충청남도": "05",
    "전북": "06", "전라북도": "06",
    "전남": "07", "전라남도": "07",
    "경북": "08", "경상북도": "08",
    "경남": "09", "경상남도": "09",
    "제주": "10", "제주특별자치도": "10",
    "부산": "11", "부산광역시": "11",
    "대구": "12", "대구광역시": "12",
    "인천": "13", "인천광역시": "13",
    "광주": "14", "광주광역시": "14",
    "대전": "15", "대전광역시": "15",
    "울산": "16", "울산광역시": "16",
    "세종": "17", "세종특별자치시": "17",
}


def get_around_stations(
    x: float,
    y: float,
    radius: int = 5000,
    prodcd: str = "B027"
) -> list[dict]:
    """
    KATEC 좌표 기준 주변 주유소 조회
    """

    parameters = {
        "code": OPINET_KEY,
        "out": "json",
        "x": x,
        "y": y,
        "radius": radius,
        "prodcd": prodcd,
        "sort": "1",
    }

    try:
        response = requests.get(
            f"{BASE_URL}/aroundAll.do",
            params=parameters,
            timeout=5
        )
        response.raise_for_status()

        data_result = response.json()
        oil_list = data_result.get("RESULT", {}).get("OIL", [])

        return oil_list

    except requests.exceptions.Timeout:
        print("[opinet] 주변 주유소 조회 요청 시간이 초과되었습니다.")
        return []

    except requests.exceptions.RequestException as e:
        print(f"[opinet] 주변 주유소 API 요청 오류: {e}")
        return []

    except ValueError:
        print("[opinet] 주변 주유소 JSON 데이터 변환 실패")
        return []

    except Exception as e:
        print(f"[opinet] 주변 주유소 조회 중 오류 발생: {e}")
        return []


def get_station_detail(uni_id: str) -> dict:
    """
    주유소 고유 ID(UNI_ID) 기준 상세정보 조회
    aroundAll.do 응답에는 주소가 없어서 detailById.do로 주소를 보완함
    """

    if not uni_id:
        return {}

    parameters = {
        "code": OPINET_KEY,
        "out": "json",
        "id": uni_id,
    }

    try:
        response = requests.get(
            f"{BASE_URL}/detailById.do",
            params=parameters,
            timeout=5
        )
        response.raise_for_status()

        data_result = response.json()
        oil_list = data_result.get("RESULT", {}).get("OIL", [])

        if oil_list:
            return oil_list[0]

        return {}

    except requests.exceptions.Timeout:
        print("[opinet] 주유소 상세 조회 요청 시간이 초과되었습니다.")
        return {}

    except requests.exceptions.RequestException as e:
        print(f"[opinet] 주유소 상세 API 요청 오류: {e}")
        return {}

    except ValueError:
        print("[opinet] 주유소 상세 JSON 데이터 변환 실패")
        return {}

    except Exception as e:
        print(f"[opinet] 주유소 상세 조회 중 오류 발생: {e}")
        return {}


def format_around_oil_data(oil_list: list[dict]) -> list[dict]:
    """
    주변 주유소 API 데이터를 화면 표시용으로 가공
    주소는 UNI_ID로 상세 조회해서 보완
    """

    formatted_list = []

    for i, oil in enumerate(oil_list, 1):
        detail = get_station_detail(oil.get("UNI_ID"))

        address = (
            detail.get("NEW_ADR")
            or detail.get("VAN_ADR")
            or detail.get("ADR")
            or detail.get("ADDR")
            or detail.get("OS_ADR")
            or "-"
        )

        clean_data = {
            "rank": i,
            "station_name": oil.get("OS_NM"),
            "price": oil.get("PRICE"),
            "address": address,
            "brand": oil.get("POLL_DIV_CD"),
            "distance": oil.get("DISTANCE"),
            "tel": detail.get("TEL") or oil.get("TEL"),
            "x": oil.get("GIS_X_COOR"),
            "y": oil.get("GIS_Y_COOR"),
        }

        formatted_list.append(clean_data)

    return formatted_list