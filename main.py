"""
Flask + HTML 입력 페이지 구성 파일

이 파일의 역할:
- 사용자가 웹 화면에서 입력한 값을 Flask route에서 받는다.
- 주소를 임시 리스트(address_book)에 등록/삭제한다.
- 저가 주유소 조회 시,
  1) 저장된 별칭으로 조회하거나
  2) 주소를 직접 입력해서 조회할 수 있게 한다.
- 조회 버튼을 누르면 결과를 index.html 하단에 붙이지 않고 result.html 페이지로 넘긴다.

담당 기능:
1. 주소 등록 form에서 별칭/주소 입력값 받기
2. 등록된 주소 목록 조회
3. 별칭 기준 주소 삭제
4. 별칭 또는 직접 주소 기준 저가 주유소 조회 route 처리
"""

from flask import Flask, render_template, request, redirect, url_for, flash

from api.config import FLASK_SECRET_KEY
from api.opinet import get_low_top10, format_oil_data
from utils.validator import validate_address
from utils.report import save_report


# =========================
# 1. Flask 앱 생성
# =========================

app = Flask(__name__)

# flash 메시지를 사용하려면 secret_key가 필요하다.
# 이 값은 .env → api/config.py를 통해 불러온다.
if not FLASK_SECRET_KEY:
    raise ValueError(".env 파일에 FLASK_SECRET_KEY가 없습니다.")

app.secret_key = FLASK_SECRET_KEY


# =========================
# 2. 임시 주소 저장소
# =========================

# 주소 정보를 저장하는 임시 리스트.
# 서버를 끄면 데이터는 사라진다.
address_book = []


# =========================
# 3. 기본 데이터
# =========================

# 오피넷 API에서 사용하는 유종 코드와 화면에 보여줄 이름을 매칭한 딕셔너리.
# HTML select 박스에서 사용하고, 실제 API 요청에는 코드값이 전달된다.
PRODUCT_CODES = {
    "B027": "보통휘발유",
    "D047": "자동차경유",
    "B034": "고급휘발유",
    "C004": "실내등유",
    "K015": "자동차부탄",
}


# =========================
# 4. 보조 함수
# =========================

def extract_sido_gu(address):
    """
    주소 문자열에서 시도와 구를 추출하는 함수.

    예:
    address = "서울 강서구 화곡동 123-45"

    결과:
    sido = "서울"
    gu = "강서구"

    현재는 공백 기준으로 단순 추출한다.
    """
    words = address.strip().split()

    if len(words) < 2:
        return None, None

    sido = words[0]
    gu = words[1]

    return sido, gu


def find_address_by_alias(alias):
    """
    별칭으로 저장된 주소를 찾는 함수.

    찾으면 주소 딕셔너리 반환,
    못 찾으면 None 반환.
    """
    for item in address_book:
        if item["alias"] == alias:
            return item

    return None


def parse_count(raw_count):
    """
    조회 개수 입력값을 숫자로 변환하는 함수.

    잘못된 값이 들어와도 프로그램이 멈추지 않게 처리한다.
    """
    try:
        count = int(raw_count)

    except (ValueError, TypeError):
        return 10

    if count < 1:
        return 1

    if count > 20:
        return 20

    return count


# =========================
# 5. 주소 등록 / 삭제 함수
# =========================

def add_address(alias, address):
    """
    주소 등록 처리 함수.

    처리 흐름:
    1. 주소 입력값 검증
    2. 별칭 중복 확인
    3. 주소에서 시도/구 추출
    4. address_book 리스트에 저장
    """
    error_message = validate_address(address)

    if error_message:
        return False, error_message

    if find_address_by_alias(alias):
        return False, "이미 등록된 별칭입니다."

    sido, gu = extract_sido_gu(address)

    if not sido or not gu:
        return False, "주소는 '서울 강서구 ...'처럼 시도와 구를 포함해서 입력해주세요."

    address_book.append({
        "alias": alias,
        "address": address,
        "sido": sido,
        "gu": gu,
    })

    return True, "주소가 등록되었습니다."


def delete_address(alias):
    """
    주소 삭제 처리 함수.

    별칭으로 주소를 찾아 address_book에서 제거한다.
    """
    target = find_address_by_alias(alias)

    if not target:
        return False, "해당 별칭의 주소를 찾지 못했습니다."

    address_book.remove(target)

    return True, "주소가 삭제되었습니다."


# =========================
# 6. 저가 주유소 조회 함수
# =========================

def make_target_address_by_direct_input(direct_address):
    """
    직접 입력한 주소를 조회 기준 주소 딕셔너리로 바꾸는 함수.

    별칭으로 저장된 주소가 아니더라도,
    조회에 필요한 address, sido, gu 형태를 맞추기 위해 사용한다.
    """
    error_message = validate_address(direct_address)

    if error_message:
        return None, error_message

    sido, gu = extract_sido_gu(direct_address)

    if not sido or not gu:
        return None, "주소는 '서울 강서구 ...'처럼 시도와 구를 포함해서 입력해주세요."

    target_address = {
        "alias": "직접 입력 주소",
        "address": direct_address,
        "sido": sido,
        "gu": gu,
    }

    return target_address, None


def search_low_price_stations(search_type, alias, direct_address, product_code, count):
    """
    저가 주유소 조회 함수.

    search_type에 따라 조회 기준이 달라진다.

    1. search_type == "alias"
       - 저장된 별칭으로 주소를 찾아 조회한다.

    2. search_type == "direct"
       - 사용자가 직접 입력한 주소를 기준으로 조회한다.

    반환값:
    - 성공: True, 메시지, 조회 기준 주소, 주유소 리스트
    - 실패: False, 메시지, 조회 기준 주소 또는 None, 빈 리스트
    """

    # =========================
    # 1. 조회 기준 주소 결정
    # =========================

    if search_type == "alias":
        target_address = find_address_by_alias(alias)

        if not target_address:
            return False, "해당 별칭의 주소를 찾지 못했습니다.", None, []

    elif search_type == "direct":
        target_address, error_message = make_target_address_by_direct_input(direct_address)

        if error_message:
            return False, error_message, None, []

    else:
        return False, "조회 방식을 올바르게 선택해주세요.", None, []

    # =========================
    # 2. 시도/구 정보 추출
    # =========================

    sido = target_address["sido"]
    gu = target_address["gu"]

    # =========================
    # 3. 오피넷 API 호출
    # =========================

    oil_list = get_low_top10(sido_name=sido, prodcd=product_code)

    if not oil_list:
        return False, "오피넷 조회 결과가 없습니다.", target_address, []

    # 오피넷 API 원본 데이터를 프로젝트에서 쓰기 좋은 형태로 가공한다.
    formatted_data = format_oil_data(oil_list, sido)

    # =========================
    # 4. 구 기준 필터링
    # =========================

    filtered_data = []

    for station in formatted_data:
        station_address = station.get("address") or ""

        if gu in station_address:
            filtered_data.append(station)

    # =========================
    # 5. 가격 기준 정렬
    # =========================

    filtered_data.sort(
        key=lambda item: int(item["price"]) if str(item.get("price", "")).isdigit() else 999999
    )

    # 사용자가 입력한 개수만큼만 자른다.
    filtered_data = filtered_data[:count]

    if not filtered_data:
        return False, f"{sido} TOP 조회 결과 중 '{gu}'가 포함된 주유소가 없습니다.", target_address, []

    # =========================
    # 6. CSV/JSON 저장
    # =========================

    save_report(filtered_data)

    return True, f"{sido} {gu} 기준 저가 주유소 조회가 완료되었습니다.", target_address, filtered_data


# =========================
# 7. Flask Route
# =========================

@app.route("/")
def index():
    """
    메인 입력 페이지 route.

    index.html에 전달하는 값:
    - addresses: 등록된 주소 목록
    - product_codes: 유종 코드 목록
    """
    return render_template(
        "index.html",
        addresses=address_book,
        product_codes=PRODUCT_CODES,
    )


@app.route("/address/create", methods=["POST"])
def create_address_route():
    """
    주소 등록 route.

    HTML form에서 전달받는 값:
    - alias
    - address
    """
    alias = request.form.get("alias", "").strip()
    address = request.form.get("address", "").strip()

    if not alias:
        flash("별칭을 입력해주세요.")
        return redirect(url_for("index"))

    success, message = add_address(alias, address)
    flash(message)

    return redirect(url_for("index"))


@app.route("/address/delete", methods=["POST"])
def delete_address_route():
    """
    주소 삭제 route.

    HTML form에서 전달받는 값:
    - delete_alias
    """
    alias = request.form.get("delete_alias", "").strip()

    if not alias:
        flash("삭제할 별칭을 입력해주세요.")
        return redirect(url_for("index"))

    success, message = delete_address(alias)
    flash(message)

    return redirect(url_for("index"))


@app.route("/fuel/search", methods=["POST"])
def fuel_search_route():
    """
    저가 주유소 조회 route.

    HTML form에서 전달받는 값:
    - search_type: alias 또는 direct
    - search_alias: 별칭 조회일 때 사용하는 값
    - direct_address: 주소 직접 입력 조회일 때 사용하는 값
    - product_code: 유종 코드
    - count: 조회 개수

    중요:
    - 조회 결과는 index.html 하단에 출력하지 않는다.
    - result.html 페이지로 넘긴다.
    """

    search_type = request.form.get("search_type", "alias").strip()
    alias = request.form.get("search_alias", "").strip()
    direct_address = request.form.get("direct_address", "").strip()
    product_code = request.form.get("product_code", "B027").strip()
    count = parse_count(request.form.get("count", "10"))

    # 잘못된 유종 코드가 들어오면 기본값으로 변경
    if product_code not in PRODUCT_CODES:
        product_code = "B027"

    # 조회 방식별 필수 입력값 검증
    if search_type == "alias" and not alias:
        flash("저장된 별칭으로 조회하려면 별칭을 입력해주세요.")
        return redirect(url_for("index"))

    if search_type == "direct" and not direct_address:
        flash("주소 직접 입력으로 조회하려면 주소를 입력해주세요.")
        return redirect(url_for("index"))

    success, message, target_address, stations = search_low_price_stations(
        search_type=search_type,
        alias=alias,
        direct_address=direct_address,
        product_code=product_code,
        count=count,
    )

    # result.html로 넘길 데이터
    search_result = {
        "success": success,
        "message": message,
        "search_type": search_type,
        "alias": alias,
        "direct_address": direct_address,
        "target_address": target_address,
        "product_name": PRODUCT_CODES.get(product_code, ""),
        "product_code": product_code,
        "count": count,
        "stations": stations,
    }

    # 결과 페이지 담당자가 result.html을 만들면 이 데이터로 화면을 구성하면 된다.
    return render_template(
        "result.html",
        search_result=search_result
    )


# =========================
# 8. 실행
# =========================

if __name__ == "__main__":
    app.run(debug=True, port=5000)