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
import math # 거리 계산을 위해 추가

from api.config import FLASK_SECRET_KEY
from api.opinet import get_low_top10, format_oil_data
from api.geocoder import get_geocode # 지오코더 API 추가
from utils.validator import validate_address, validate_coordinates, validate_oil_list
from utils.report import save_report

# =========================
# 1. Flask 앱 생성
# =========================

app = Flask(__name__)

if not FLASK_SECRET_KEY:
    raise ValueError(".env 파일에 FLASK_SECRET_KEY가 없습니다.")

app.secret_key = FLASK_SECRET_KEY


# =========================
# 2. 임시 주소 저장소
# =========================

address_book = []


# =========================
# 3. 기본 데이터
# =========================

PRODUCT_CODES = {
    "B027": "보통휘발유",
    "D047": "자동차경유",
    "B034": "고급휘발유",
    "C004": "실내등유",
    "K015": "자동차부탄",
}

BRAND_NAMES = {
    "SKE": "SK에너지",
    "GSC": "GS칼텍스",
    "HDO": "HD현대오일뱅크",
    "SOL": "S-OIL",
    "RTO": "자영알뜰",
    "RTX": "고속알뜰",
    "NHO": "NH오일",
    "EX": "이엑스오일",
    "PB": "PB",
}

# =========================
# 4. 보조 함수
# =========================

def extract_sido_gu(address):
    words = address.strip().split()
    if len(words) < 2:
        return None, None
    sido = words[0]
    gu = words[1]
    return sido, gu

def find_address_by_alias(alias):
    for item in address_book:
        if item["alias"] == alias:
            return item
    return None

def parse_count(raw_count):
    try:
        count = int(raw_count)
    except (ValueError, TypeError):
        return 10

    if count < 1:
        return 1
    if count > 20:
        return 20
    return count

def get_distance(x1, y1, x2, y2):
    """두 좌표 사이의 거리를 계산하는 함수"""
    return math.sqrt((x1 - x2)**2 + (y1 - y2)**2)


# =========================
# 5. 주소 등록 / 삭제 함수
# =========================

def add_address(alias, address):
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
    target = find_address_by_alias(alias)
    if not target:
        return False, "해당 별칭의 주소를 찾지 못했습니다."

    address_book.remove(target)
    return True, "주소가 삭제되었습니다."


# =========================
# 6. 저가 주유소 조회 함수
# =========================

def make_target_address_by_direct_input(direct_address):
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
    # 조회 기준 주소 결정
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

    sido = target_address["sido"]
    gu = target_address["gu"]

    # 사용자 주소의 좌표 구하기
    user_coords = get_geocode(target_address["address"])
    if user_coords is None:
        # 상세 주소 검색 실패 시 시도+구 이름으로 재검색
        user_coords = get_geocode(sido + " " + gu)

    coordinate_error = validate_coordinates(user_coords)
    if coordinate_error:
        return False, coordinate_error, target_address, []

    user_x = user_coords["x"]
    user_y = user_coords["y"]

    oil_list = get_low_top10(sido_name=sido, prodcd=product_code)

    oil_error = validate_oil_list(oil_list)
    if oil_error:
        return False, oil_error, target_address, []

    formatted_data = format_oil_data(oil_list, sido)


    for station in formatted_data:
        station_addr = station.get("address")
        

        if not station_addr:
            station["distance"] = None
            continue

        station_coords = get_geocode(station_addr)
        if station_coords is not None:
            dist = get_distance(user_x, user_y, station_coords["x"], station_coords["y"])
            station["distance"] = round(dist)
        else:
            station["distance"] = None

    def sort_by_distance(station):
        if station.get("distance") is None:
            return 999999
        return station.get("distance")

    formatted_data.sort(key=sort_by_distance)

    top_stations = formatted_data[:count]


    def sort_by_price(station):
        if station.get("price") is None:
            return 999999
        return int(station.get("price"))

    top_stations.sort(key=sort_by_price)

    for station in top_stations:

        brand_code = station.get("brand", "-")
        station["brand_name"] = BRAND_NAMES.get(brand_code, brand_code)
        
        price_val = int(station.get('price', 0))
        station['price_str'] = f"{price_val:,}원"
        
        dist_val = station.get('distance')
        if dist_val is not None:
            dist_km = round(dist_val / 1000, 1)
            station['dist_str'] = f"{dist_km}km"
        else:
            station['dist_str'] = "-"

    save_report(top_stations)

    return True, f"{sido} {gu} 기준 저가 주유소 조회가 완료되었습니다.", target_address, top_stations


# =========================
# 7. Flask Route
# =========================

@app.route("/")
def index():
    return render_template(
        "index.html",
        addresses=address_book,
        product_codes=PRODUCT_CODES,
    )

@app.route("/address/create", methods=["POST"])
def create_address_route():
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
    alias = request.form.get("delete_alias", "").strip()

    if not alias:
        flash("삭제할 별칭을 입력해주세요.")
        return redirect(url_for("index"))

    success, message = delete_address(alias)
    flash(message)

    return redirect(url_for("index"))

@app.route("/fuel/search", methods=["POST"])
def fuel_search_route():
    search_type = request.form.get("search_type", "alias").strip()
    alias = request.form.get("search_alias", "").strip()
    direct_address = request.form.get("direct_address", "").strip()
    product_code = request.form.get("product_code", "B027").strip()
    count = parse_count(request.form.get("count", "10"))

    if product_code not in PRODUCT_CODES:
        product_code = "B027"

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

    return render_template(
        "result.html",
        search_result=search_result
    )

# =========================
# 8. 실행
# =========================

if __name__ == "__main__":
    app.run(debug=True, port=5000)