from api.opinet import SIDO_CODES


# 전체 시도명을 오피넷용 짧은 이름으로 바꾸기 위한 매핑
SIDO_NAME_MAP = {
    "서울특별시": "서울",
    "부산광역시": "부산",
    "대구광역시": "대구",
    "인천광역시": "인천",
    "광주광역시": "광주",
    "대전광역시": "대전",
    "울산광역시": "울산",
    "세종특별자치시": "세종",
    "제주특별자치도": "제주",
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
    """시도명을 오피넷 코드 기준에 맞게 정규화"""
    return SIDO_NAME_MAP.get(sido, sido)


# 사용자가 입력한 지역명이 올바른지 검사하는 함수
def validate_region(region):
    region = normalize_sido_name(region.strip()) if region else region

    if not region or not region.strip():
        return "지역명을 입력해주세요."

    if region.strip() not in SIDO_CODES:
        return "올바른 지역명을 입력해주세요. (예: 서울, 경기, 인천)"

    return None


# 사용자가 입력한 주소가 올바른지 검사하는 함수
def validate_address(address):
    if not address or not address.strip():
        return "주소를 입력해주세요."

    if len(address.strip()) < 2:
        return "주소를 두 글자 이상 입력해주세요."

    return None


# 지오코더 API로 변환된 좌표 데이터가 정상인지 검사하는 함수
def validate_coordinates(coords):
    if coords is None:
        return "주소를 좌표로 변환하지 못했습니다."

    if not isinstance(coords, dict):
        return "좌표 데이터 형식이 올바르지 않습니다."

    if "x" not in coords or "y" not in coords:
        return "좌표 정보가 올바르지 않습니다."

    return None


# 오피넷 API에서 받아온 유가 데이터가 정상인지 검사하는 함수
def validate_oil_list(oil_list):
    if oil_list is None:
        return "유가 데이터를 불러오지 못했습니다."

    if not isinstance(oil_list, list):
        return "유가 데이터 형식이 올바르지 않습니다."

    if len(oil_list) == 0:
        return "조회 결과가 없습니다."

    return None