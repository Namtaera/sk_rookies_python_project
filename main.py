from flask import Flask, render_template, request, redirect, url_for, flash

from api.config import FLASK_SECRET_KEY
from api.opinet import get_around_stations, format_around_oil_data
from api.geocoder import get_geocode
from utils.validator import validate_address, validate_coordinates, validate_oil_list
from utils.report import save_report


app = Flask(__name__)

if not FLASK_SECRET_KEY:
    raise ValueError(".env 파일에 FLASK_SECRET_KEY가 없습니다.")

app.secret_key = FLASK_SECRET_KEY

address_book = []

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

SIDO_NAME_MAP = {
    "서울특별시": "서울",
    "서울시": "서울",
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
    return SIDO_NAME_MAP.get(sido, sido)


def extract_sido_gu(address):
    words = address.strip().split()
    if len(words) < 2:
        return None, None

    sido = normalize_sido_name(words[0])
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


def add_address(alias, address):
    error_message = validate_address(address)
    if error_message:
        return False, error_message

    if find_address_by_alias(alias):
        return False, "이미 등록된 별칭입니다."

    sido, gu = extract_sido_gu(address)
    if not sido or not gu:
        return False, "주소는 '경기도 고양시 ...'처럼 시도와 시/구를 포함해서 입력해주세요."

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


def make_target_address_by_direct_input(direct_address):
    error_message = validate_address(direct_address)
    if error_message:
        return None, error_message

    sido, gu = extract_sido_gu(direct_address)
    if not sido or not gu:
        return None, "주소는 '경기도 고양시 ...'처럼 시도와 시/구를 포함해서 입력해주세요."

    return {
        "alias": "직접 입력 주소",
        "address": direct_address,
        "sido": sido,
        "gu": gu,
    }, None


def search_low_price_stations(search_type, alias, direct_address, product_code, count):
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

    user_coords = get_geocode(target_address["address"])

    if user_coords is None:
        user_coords = get_geocode(f"{sido} {gu}")

    coordinate_error = validate_coordinates(user_coords)
    if coordinate_error:
        return False, coordinate_error, target_address, []

    user_x = user_coords["x"]
    user_y = user_coords["y"]

    oil_list = get_around_stations(
        x=user_x,
        y=user_y,
        radius=5000,
        prodcd=product_code
    )

    oil_error = validate_oil_list(oil_list)
    if oil_error:
        return False, oil_error, target_address, []

    formatted_data = format_around_oil_data(oil_list)

    def sort_by_price(station):
        try:
            return int(station.get("price"))
        except (TypeError, ValueError):
            return 999999

    formatted_data.sort(key=sort_by_price)
    top_stations = formatted_data[:count]

    for station in top_stations:
        brand_code = station.get("brand", "-")
        station["brand_name"] = BRAND_NAMES.get(brand_code, brand_code)

        try:
            price_val = int(station.get("price", 0))
            station["price_str"] = f"{price_val:,}원"
        except (TypeError, ValueError):
            station["price_str"] = "-"

        dist_val = station.get("distance")
        if dist_val is not None:
            try:
                station["dist_str"] = f"{round(float(dist_val) / 1000, 1)}km"
            except (TypeError, ValueError):
                station["dist_str"] = "-"
        else:
            station["dist_str"] = "-"

    save_report(top_stations)

    return True, f"{sido} {gu} 기준 주변 저가 주유소 조회가 완료되었습니다.", target_address, top_stations


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

    if not success:
        flash(message)
        return redirect(url_for("index"))

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


if __name__ == "__main__":
    app.run(debug=True, port=5000)