"""
Flask + HTML 입력 페이지 구성 파일

이 파일의 역할:
- 사용자가 웹 화면에서 입력한 값을 Flask route에서 받는다.
- 주소를 임시 리스트(address_book)에 등록/삭제한다.
- 저장된 주소의 시도/구 정보를 기준으로 오피넷 API를 호출한다.
- 조회 결과를 다시 HTML 화면에 전달한다.

담당 기능:
1. 주소 등록 form에서 별칭/주소 입력값 받기
2. 등록된 주소 목록 조회
3. 별칭 기준 주소 삭제
4. 저장된 주소 기준 저가 주유소 조회 버튼 처리

"""

# Flask에서 필요한 기능들을 가져온다.
# Flask: 웹 애플리케이션 객체를 만들 때 사용
# render_template: templates 폴더의 HTML 파일을 화면에 보여줄 때 사용
# request: 사용자가 form에 입력한 값을 받을 때 사용
# redirect: 특정 route로 다시 이동시킬 때 사용
# url_for: route 함수 이름으로 URL을 만들어줄 때 사용
# flash: 사용자에게 안내 메시지를 보여줄 때 사용
from flask import Flask, render_template, request, redirect, url_for, flash

# api/opinet.py에서 만든 오피넷 관련 함수를 가져온다.
# get_low_top10: 특정 시도 기준 저가 주유소 TOP10 조회
# format_oil_data: 오피넷 API 원본 데이터를 우리 프로젝트에서 쓰기 좋게 가공
from api.opinet import get_low_top10, format_oil_data

# utils/validator.py에서 만든 주소 입력 검증 함수를 가져온다.
from utils.validator import validate_address

# utils/report.py에서 만든 CSV/JSON 저장 함수를 가져온다.
from utils.report import save_report

#
from api.config import FLASK_SECRET_KEY

# =========================
# 1. Flask 앱 생성
# =========================

# Flask 애플리케이션 객체를 생성한다.
# __name__은 현재 실행 중인 파일 이름을 의미한다.
# Flask가 이 값을 기준으로 templates, static 폴더 위치를 찾는다.
app = Flask(__name__)

# flash 메시지를 사용하려면 secret_key가 필요하다.
# flash는 "주소가 등록되었습니다." 같은 안내 문구를 HTML에 띄울 때 사용한다.
app.secret_key = FLASK_SECRET_KEY

# =========================
# 2. 임시 주소 저장소
# =========================

# 주소 정보를 저장하는 임시 리스트
# DB나 파일 저장을 쓰지 않고, 서버가 켜져 있는 동안만 메모리에 저장된다.
# 주소 정보를 저장하는 임시 리스트
# 처음 실행 시에는 아무 주소도 등록되어 있지 않도록 빈 리스트로 시작한다.
address_book = []


# =========================
# 3. 기본 데이터
# =========================

# 오피넷 API에서 사용하는 유종 코드와 화면에 보여줄 이름을 매칭한 딕셔너리
# # 실제 API 요청에는 "B027", "D047" 같은 코드값이 전달
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
    address = '서울 강서구 화곡동 123-45'

    address.strip().split() 결과:
    ['서울', '강서구', '화곡동', '123-45']

    여기서는 첫 번째 단어를 시도,
    두 번째 단어를 구로 사용한다.

    반환값:
    - 성공하면 ("서울", "강서구")
    - 실패하면 (None, None)
    """

    # strip()은 문자열 앞뒤 공백을 제거한다.
    # split()은 공백 기준으로 문자열을 나누어 리스트로 만든다.
    words = address.strip().split()

    # 주소가 너무 짧아서 시도/구를 추출할 수 없는 경우
    # 예: "서울"만 입력한 경우
    if len(words) < 2:
        return None, None

    # 첫 번째 단어를 시도명으로 사용한다.
    sido = words[0]

    # 두 번째 단어를 구/시/군 단위로 사용한다.
    gu = words[1]

    return sido, gu


def find_address_by_alias(alias):
    """
    별칭으로 저장된 주소를 찾는 함수.

    예:
    alias = "집"

    address_book 안에서 item["alias"]가 "집"인 데이터를 찾는다.

    반환값:
    - 찾으면 해당 주소 딕셔너리 반환
    - 없으면 None 반환
    """

    # address_book 리스트 안의 주소 데이터를 하나씩 확인한다.
    for item in address_book:
        # 저장된 별칭과 사용자가 입력한 별칭이 같으면 해당 item 반환
        if item["alias"] == alias:
            return item

    # 반복문이 끝날 때까지 못 찾으면 None 반환
    return None


def parse_count(raw_count):
    """
    조회 개수 입력값을 숫자로 변환하는 함수.

    HTML input에서 넘어오는 값은 기본적으로 문자열이다.
    예:
    raw_count = "10"

    이 값을 int로 바꿔야 리스트 슬라이싱 등에 사용할 수 있다.

    예외처리 목적:
    - 사용자가 문자를 입력한 경우
    - 값이 비어 있는 경우
    - 1보다 작은 값을 입력한 경우
    - 20보다 큰 값을 입력한 경우

    반환값:
    - 정상 숫자면 해당 숫자
    - 잘못된 값이면 기본값 10
    - 1보다 작으면 1
    - 20보다 크면 20
    """

    try:
        # 문자열을 정수로 변환한다.
        count = int(raw_count)

    except (ValueError, TypeError):
        # ValueError: "abc"처럼 숫자로 바꿀 수 없는 값
        # TypeError: None처럼 int 변환이 어려운 값
        return 10

    # 1개 미만 조회는 의미가 없으므로 최소값을 1로 제한한다.
    if count < 1:
        return 1

    # 오피넷 TOP 조회는 보통 10~20개 정도로 제한해서 쓰기 때문에
    # 화면 입력값도 최대 20으로 제한한다.
    if count > 20:
        return 20

    return count


# =========================
# 5. 주소 등록 / 삭제 함수
# =========================

def add_address(alias, address):
    """
    주소 등록 처리 함수.

    사용자가 입력한 별칭과 주소를 address_book에 저장한다.

    처리 흐름:
    1. 주소 입력값이 올바른지 검증한다.
    2. 같은 별칭이 이미 등록되어 있는지 확인한다.
    3. 주소에서 시도/구를 추출한다.
    4. address_book 리스트에 새 주소 데이터를 추가한다.

    반환값:
    - 성공: (True, "주소가 등록되었습니다.")
    - 실패: (False, "실패 사유 메시지")
    """

    # utils/validator.py의 validate_address()를 사용해 주소 입력값을 검증한다.
    # 문제가 있으면 에러 메시지 문자열을 반환하고,
    # 문제가 없으면 None을 반환한다.
    error_message = validate_address(address)

    # 에러 메시지가 있으면 주소 등록을 진행하지 않는다.
    if error_message:
        return False, error_message

    # 이미 같은 별칭이 등록되어 있는지 확인한다.
    # 예: "집"이 이미 있는데 또 "집"을 등록하는 경우 방지
    if find_address_by_alias(alias):
        return False, "이미 등록된 별칭입니다."

    # 주소에서 시도와 구를 추출한다.
    sido, gu = extract_sido_gu(address)

    # 주소에서 시도/구를 추출하지 못하면 등록 실패 처리한다.
    if not sido or not gu:
        return False, "주소는 '서울 강서구 ...'처럼 시도와 구를 포함해서 입력해주세요."

    # 주소 데이터를 딕셔너리 형태로 만들어 address_book에 추가한다.
    address_book.append({
        "alias": alias,
        "address": address,
        "sido": sido,
        "gu": gu,
    })

    # 성공 여부와 메시지를 반환한다.
    return True, "주소가 등록되었습니다."


def delete_address(alias):
    """
    주소 삭제 처리 함수.

    사용자가 입력한 별칭에 해당하는 주소를 address_book에서 삭제한다.

    처리 흐름:
    1. 별칭으로 주소를 찾는다.
    2. 없으면 실패 메시지를 반환한다.
    3. 있으면 address_book에서 제거한다.

    반환값:
    - 성공: (True, "주소가 삭제되었습니다.")
    - 실패: (False, "해당 별칭의 주소를 찾지 못했습니다.")
    """

    # 별칭으로 주소 데이터를 찾는다.
    target = find_address_by_alias(alias)

    # 해당 별칭의 주소가 없으면 삭제할 수 없다.
    if not target:
        return False, "해당 별칭의 주소를 찾지 못했습니다."

    # 리스트에서 해당 주소 데이터를 제거한다.
    address_book.remove(target)

    return True, "주소가 삭제되었습니다."


# =========================
# 6. 저가 주유소 조회 함수
# =========================

def search_low_price_stations(alias, product_code, count):
    """
    저장된 주소 기준 저가 주유소 조회 함수.

    사용자가 별칭을 입력하면,
    그 별칭에 해당하는 주소의 시도/구 정보를 가져와서
    오피넷 API로 저가 주유소를 조회한다.

    처리 흐름:
    1. 별칭으로 저장된 주소를 찾는다.
    2. 저장된 주소에서 시도/구를 가져온다.
    3. 오피넷 API로 해당 시도 TOP10 저가 주유소를 조회한다.
    4. 조회 결과 중 주소에 해당 구가 포함된 데이터만 필터링한다.
    5. 가격 기준으로 정렬한다.
    6. 사용자가 입력한 개수만큼 자른다.
    7. CSV/JSON 리포트로 저장한다.

    반환값:
    - 성공: (True, "조회 완료 메시지", 주유소 리스트)
    - 실패: (False, "실패 사유 메시지", [])
    """

    # 별칭으로 저장된 주소를 찾는다.
    saved_address = find_address_by_alias(alias)

    # 해당 별칭이 없으면 조회할 기준 주소가 없으므로 실패 처리한다.
    if not saved_address:
        return False, "해당 별칭의 주소를 찾지 못했습니다.", []

    # 저장된 주소에서 시도와 구 정보를 가져온다.
    # 예: sido = "서울", gu = "강서구"
    sido = saved_address["sido"]
    gu = saved_address["gu"]

    # 오피넷 API를 호출한다.
    # get_low_top10()은 api/opinet.py에 정의된 함수이다.
    # sido_name에는 "서울" 같은 시도명이 들어간다.
    # prodcd에는 "B027" 같은 유종 코드가 들어간다.
    oil_list = get_low_top10(sido_name=sido, prodcd=product_code)

    # 오피넷 결과가 비어 있으면 실패 처리한다.
    if not oil_list:
        return False, "오피넷 조회 결과가 없습니다.", []

    # 오피넷 API 원본 데이터를 프로젝트에서 쓰기 편한 딕셔너리 형태로 바꾼다.
    # format_oil_data()도 api/opinet.py에 정의된 함수이다.
    formatted_data = format_oil_data(oil_list, sido)

    # 구 단위 필터링 결과를 담을 리스트이다.
    filtered_data = []

    # 가공된 주유소 데이터를 하나씩 확인한다.
    for station in formatted_data:
        # 주유소 주소를 가져온다.
        # 주소가 None일 경우를 대비해서 빈 문자열로 처리한다.
        station_address = station.get("address") or ""

        # 저장된 주소의 구 이름이 주유소 주소에 포함되어 있으면 결과에 추가한다.
        # 예: gu = "강서구"
        # station_address = "서울 강서구 화곡동 ..."
        if gu in station_address:
            filtered_data.append(station)

    # 가격 기준으로 오름차순 정렬한다.
    # 가격이 숫자 문자열이면 int로 바꿔 비교한다.
    # 가격이 없거나 숫자가 아니면 999999로 처리해서 뒤로 보낸다.
    filtered_data.sort(
        key=lambda item: int(item["price"]) if str(item.get("price", "")).isdigit() else 999999
    )

    # 사용자가 입력한 count만큼만 결과를 남긴다.
    filtered_data = filtered_data[:count]

    # 필터링 후 데이터가 없으면 실패 메시지를 반환한다.
    if not filtered_data:
        return False, f"{sido} TOP 조회 결과 중 '{gu}'가 포함된 주유소가 없습니다.", []

    # 조회 결과를 CSV와 JSON 파일로 저장한다.
    # save_report()는 utils/report.py에 정의된 함수이다.
    save_report(filtered_data)

    # 성공 여부, 메시지, 조회 결과 리스트를 반환한다.
    return True, f"{sido} {gu} 기준 저가 주유소 조회가 완료되었습니다.", filtered_data


# =========================
# 7. Flask Route
# =========================

@app.route("/")
def index():
    """
    메인 입력 페이지 route.

    사용자가 http://127.0.0.1:5000 에 접속하면 실행된다.

    render_template() 역할:
    - templates/index.html 파일을 화면에 보여준다.
    - 동시에 HTML에서 사용할 데이터를 전달한다.

    index.html에 전달하는 값:
    - addresses: 등록된 주소 목록
    - product_codes: 유종 코드 목록
    - search_result: 검색 결과
    """

    return render_template(
        "index.html",

        # HTML에서 addresses라는 이름으로 address_book을 사용할 수 있게 전달한다.
        addresses=address_book,

        # HTML에서 product_codes라는 이름으로 PRODUCT_CODES를 사용할 수 있게 전달한다.
        product_codes=PRODUCT_CODES,

        # 처음 메인 화면에 들어왔을 때는 검색 결과가 없으므로 None을 전달한다.
        search_result=None
    )


@app.route("/address/create", methods=["POST"])
def create_address_route():
    """
    주소 등록 route.

    HTML의 주소 등록 form에서 submit 버튼을 누르면 이 함수가 실행된다.

    HTML form에서 전달받는 값:
    - alias: 별칭
    - address: 주소

    처리 흐름:
    1. request.form.get()으로 사용자가 입력한 값을 가져온다.
    2. 별칭이 비어 있으면 안내 메시지를 띄우고 메인으로 이동한다.
    3. add_address()를 호출해 주소 등록을 처리한다.
    4. flash()로 처리 결과 메시지를 저장한다.
    5. redirect()로 메인 페이지로 돌아간다.
    """

    # HTML input name="alias"에 입력된 값을 가져온다.
    # 값이 없으면 ""를 기본값으로 사용한다.
    # strip()으로 앞뒤 공백을 제거한다.
    alias = request.form.get("alias", "").strip()

    # HTML input name="address"에 입력된 값을 가져온다.
    address = request.form.get("address", "").strip()

    # 별칭이 비어 있으면 등록하지 않고 안내 메시지를 띄운다.
    if not alias:
        flash("별칭을 입력해주세요.")
        return redirect(url_for("index"))

    # 실제 주소 등록 로직을 실행한다.
    success, message = add_address(alias, address)

    # 성공/실패 메시지를 HTML에 보여주기 위해 flash에 저장한다.
    flash(message)

    # 등록 후 메인 페이지로 다시 이동한다.
    return redirect(url_for("index"))


@app.route("/address/delete", methods=["POST"])
def delete_address_route():
    """
    주소 삭제 route.

    HTML의 주소 삭제 form에서 submit 버튼을 누르면 실행된다.

    HTML form에서 전달받는 값:
    - delete_alias: 삭제할 별칭

    처리 흐름:
    1. 삭제할 별칭을 form에서 가져온다.
    2. 값이 없으면 안내 메시지를 띄운다.
    3. delete_address()를 호출해 삭제 처리한다.
    4. 처리 결과를 flash 메시지로 보여준다.
    5. 메인 페이지로 돌아간다.
    """

    # HTML input name="delete_alias"에 입력된 값을 가져온다.
    alias = request.form.get("delete_alias", "").strip()

    # 삭제할 별칭이 비어 있으면 삭제하지 않는다.
    if not alias:
        flash("삭제할 별칭을 입력해주세요.")
        return redirect(url_for("index"))

    # 실제 삭제 함수 실행
    success, message = delete_address(alias)

    # 삭제 성공/실패 메시지 저장
    flash(message)

    # 삭제 후 메인 페이지로 이동
    return redirect(url_for("index"))


@app.route("/fuel/search", methods=["POST"])
def fuel_search_route():
    """
    저가 주유소 조회 route.

    HTML의 저가 주유소 조회 form에서 submit 버튼을 누르면 실행된다.

    HTML form에서 전달받는 값:
    - search_alias: 조회할 별칭
    - product_code: 유종 코드
    - count: 조회 개수

    처리 흐름:
    1. form에서 별칭, 유종 코드, 조회 개수를 가져온다.
    2. 별칭이 비어 있으면 메인으로 돌려보낸다.
    3. 유종 코드가 잘못되었으면 기본값 B027로 바꾼다.
    4. search_low_price_stations()를 호출한다.
    5. 조회 결과를 search_result 딕셔너리로 만든다.
    6. index.html을 다시 렌더링하면서 조회 결과를 전달한다.
    """

    # HTML input name="search_alias" 값 가져오기
    alias = request.form.get("search_alias", "").strip()

    # HTML select name="product_code" 값 가져오기
    # 값이 없으면 기본값 B027 사용
    product_code = request.form.get("product_code", "B027").strip()

    # HTML input name="count" 값 가져오기
    # parse_count()로 숫자 검증 및 변환
    count = parse_count(request.form.get("count", "10"))

    # 조회할 별칭이 비어 있으면 조회 불가
    if not alias:
        flash("조회할 별칭을 입력해주세요.")
        return redirect(url_for("index"))

    # 사용자가 이상한 유종 코드를 보냈을 경우 기본값으로 바꾼다.
    if product_code not in PRODUCT_CODES:
        product_code = "B027"

    # 실제 저가 주유소 조회 함수 실행
    success, message, stations = search_low_price_stations(
        alias=alias,
        product_code=product_code,
        count=count
    )

    # HTML에서 검색 결과를 쉽게 출력할 수 있도록 딕셔너리로 묶는다.
    search_result = {
        "success": success,
        "message": message,
        "alias": alias,
        "product_name": PRODUCT_CODES.get(product_code, ""),
        "count": count,
        "stations": stations,
    }

    # 검색 결과를 포함해서 index.html을 다시 렌더링한다.
    # redirect를 쓰면 search_result가 사라지기 때문에 여기서는 render_template을 사용한다.
    return render_template(
        "index.html",
        addresses=address_book,
        product_codes=PRODUCT_CODES,
        search_result=search_result
    )


# =========================
# 8. 실행
# =========================

# 이 파일을 직접 실행했을 때만 Flask 서버를 실행한다.
# 다른 파일에서 import될 때는 서버가 자동 실행되지 않는다.
if __name__ == "__main__":

    # debug=True:
    # 코드 수정 후 서버가 자동 재시작되고,
    # 오류가 발생했을 때 디버깅 정보를 자세히 보여준다.
    #
    # port=5000:
    # 브라우저에서 http://127.0.0.1:5000 으로 접속한다.
    app.run(debug=True, port=5000)