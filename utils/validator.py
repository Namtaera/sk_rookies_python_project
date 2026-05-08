from api.opinet import SIDO_CODES


# 사용자가 입력한 지역명이 올바른지 검사하는 함수
def validate_region(region):

    # 입력값이 비어 있거나 공백만 있는 경우
    if not region or not region.strip():
        return "지역명을 입력해주세요."

    # 입력한 지역명이 오피넷 시도 코드 목록에 없는 경우
    # 예: 서울, 경기, 인천 등 미리 정의된 지역만 허용
    if region.strip() not in SIDO_CODES:
        return "올바른 지역명을 입력해주세요. (예: 서울, 경기, 인천)"

    # 문제가 없으면 None 반환
    return None


# 사용자가 입력한 주소가 올바른지 검사하는 함수
def validate_address(address):
    
    # 주소 입력값이 비어 있거나 공백만 있는 경우
    if not address or not address.strip():
        return "주소를 입력해주세요."

    # 주소가 너무 짧으면 정상적인 주소로 보기 어렵기 때문에 예외 처리
    if len(address.strip()) < 2:
        return "주소를 두 글자 이상 입력해주세요."

    return None


# 지오코더 API로 변환된 좌표 데이터가 정상인지 검사하는 함수
def validate_coordinates(coords):
    
    # 좌표 변환 결과가 없는 경우
    if coords is None:
        return "주소를 좌표로 변환하지 못했습니다."

    # 좌표 데이터가 딕셔너리 형태가 아닌 경우
    if not isinstance(coords, dict):
        return "좌표 데이터 형식이 올바르지 않습니다."

    # 딕셔너리 안에 x, y 좌표 값이 없는 경우
    if "x" not in coords or "y" not in coords:
        return "좌표 정보가 올바르지 않습니다."

    return None


# 오피넷 API에서 받아온 유가 데이터가 정상인지 검사하는 함수
def validate_oil_list(oil_list):

    # API 호출 결과 자체가 없는 경우
    if oil_list is None:
        return "유가 데이터를 불러오지 못했습니다."

    # 데이터 형식이 리스트가 아닌 경우
    if not isinstance(oil_list, list):
        return "유가 데이터 형식이 올바르지 않습니다."

    # 리스트는 맞지만 조회 결과가 비어 있는 경우
    if len(oil_list) == 0:
        return "조회 결과가 없습니다."

    return None