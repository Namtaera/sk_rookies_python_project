from api.opinet import SIDO_CODES


SIDO_NAME_MAP = {
    "서울특별시": "서울",
    "서울시": "서울",
    "부산광역시": "부산",
    "부산시": "부산",
    "대구광역시": "대구",
    "대구시": "대구",
    "인천광역시": "인천",
    "인천시": "인천",
    "광주광역시": "광주",
    "광주시": "광주",
    "대전광역시": "대전",
    "대전시": "대전",
    "울산광역시": "울산",
    "울산시": "울산",
    "세종특별자치시": "세종",
    "세종시": "세종",
    "제주특별자치도": "제주",
    "제주시": "제주",
    "경기도": "경기",
    "강원도": "강원",
    "충청북도": "충북",
    "충청남도": "충남",
    "전라북도": "전북",
    "전북특별자치도": "전북",
    "전라남도": "전남",
    "경상북도": "경북",
    "경상남도": "경남",
}


def normalize_sido_name(sido):
    return SIDO_NAME_MAP.get(sido, sido)


def validate_region(region):
    region = normalize_sido_name(region.strip()) if region else region

    if not region or not region.strip():
        return "지역명을 입력해주세요."

    if region.strip() not in SIDO_CODES:
        return "올바른 지역명을 입력해주세요. (예: 서울, 경기, 인천)"

    return None


def validate_address(address):
    """
    주소 입력 검증
    허용 예:
    - 서울 강서구 화곡동
    - 서울시 강서구 화곡동
    - 서울특별시 강서구 화곡동
    - 경기도 고양시 일산동구
    """

    if not address or not address.strip():
        return "주소를 입력해주세요."

    words = address.strip().split()

    # 최소 2단어 이상: 시도 + 시/구/군
    if len(words) < 2:
        return "주소는 '서울시 강서구 ...' 또는 '경기도 고양시 ...'처럼 입력해주세요."

    raw_sido = words[0]
    normalized_sido = normalize_sido_name(raw_sido)

    # 첫 단어가 지원 가능한 시도명이 아니면 실패
    if normalized_sido not in SIDO_CODES:
        return "주소 형식이 올바르지 않습니다. 예: 서울시 강서구 ..., 경기도 고양시 ..."

    second = words[1]

    # 두 번째 단어가 시/구/군이 아니면 실패
    if not (
        second.endswith("시")
        or second.endswith("구")
        or second.endswith("군")
    ):
        return "주소 형식이 올바르지 않습니다. 시도 뒤에 시/구/군 정보를 포함해주세요."

    return None


def validate_coordinates(coords):
    if coords is None:
        return "주소를 좌표로 변환하지 못했습니다. 주소 형식을 다시 확인해주세요."

    if not isinstance(coords, dict):
        return "좌표 데이터 형식이 올바르지 않습니다."

    if "x" not in coords or "y" not in coords:
        return "좌표 정보가 올바르지 않습니다."

    return None


def validate_oil_list(oil_list):
    if oil_list is None:
        return "유가 데이터를 불러오지 못했습니다."

    if not isinstance(oil_list, list):
        return "유가 데이터 형식이 올바르지 않습니다."

    if len(oil_list) == 0:
        return "조회 결과가 없습니다. 검색 반경 안에 주유소가 없을 수 있습니다."

    return None