from api.opinet import SIDO_CODES


def validate_region(region):
    """지역명 입력 검증"""
    if not region or not region.strip():
        return "지역명을 입력해주세요."

    if region.strip() not in SIDO_CODES:
        return "올바른 지역명을 입력해주세요. (예: 서울, 경기, 인천)"

    return None


def validate_address(address):
    """주소 입력 검증"""
    if not address or not address.strip():
        return "주소를 입력해주세요."

    if len(address.strip()) < 2:
        return "주소를 두 글자 이상 입력해주세요."

    return None


def validate_coordinates(coords):
    """지오코더 결과 검증"""
    if coords is None:
        return "주소를 좌표로 변환하지 못했습니다."

    if not isinstance(coords, dict):
        return "좌표 데이터 형식이 올바르지 않습니다."

    if "x" not in coords or "y" not in coords:
        return "좌표 정보가 올바르지 않습니다."

    return None


def validate_oil_list(oil_list):
    """오피넷 결과 검증"""
    if oil_list is None:
        return "유가 데이터를 불러오지 못했습니다."

    if not isinstance(oil_list, list):
        return "유가 데이터 형식이 올바르지 않습니다."

    if len(oil_list) == 0:
        return "조회 결과가 없습니다."

    return None