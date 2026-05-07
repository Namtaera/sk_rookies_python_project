"""
Flask + HTML 입력 페이지 구성 파일
"""

from flask import Flask, render_template, request, redirect, url_for, flash
import math
import re

from api.config import FLASK_SECRET_KEY
from api.opinet import get_low_top10, format_oil_data
from api.geocoder import get_geocode
from utils.validator import validate_address
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


# =========================
# 4. 보조 함수
# =========================

def extract_sido_gu(address):
    words = address.strip().split()
    if len(words) < 2:
        return None, None
    return words[0], words[1]


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
    return max(1, min(20, count))


def calc_distance(x1, y1, x2, y2):
    """KATEC 좌표 기반 유클리드 거리 계산"""
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def clean_address_for_geocode(address):
    """
    vworld API가 인식 못하는 주소 형식을 정리하는 함수.

    문제: '신월4동', '신정3동' 처럼 동 이름에 숫자가 붙으면 API가 못 찾음
    해결: 숫자 제거 후 재시도

    예: '서울 양천구 신월4동 525-1' → '서울 양천구 신월동 525-1'
    """
    return re.sub(r'([가-힣]+)\d+(동)', r'\1\2', address)


def geocode_with_fallback(address):
    """
    주소 지오코딩. 실패하면 주소 정제 후 재시도.

    1차: 원본 주소로 시도
    2차: 동 이름 숫자 제거 후 재시도
    3차: 시도+구 만으로 재시도 (최후 수단)
    """
    # 1차 시도
    coord = get_geocode(address)
    if coord:
        return coord

    # 2차: 동 숫자 제거
    cleaned = clean_address_for_geocode(address)
    if cleaned != address:
        coord = get_geocode(cleaned)
        if coord:
            return coord

    # 3차: 시도+구만 사용
    words = address.strip().split()
    if len(words) >= 2:
        short_address = " ".join(words[:2])
        coord = get_geocode(short_address)
        if coord:
            return coord

    return None


# =========================
# 5. 주소 등록 / 삭제
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
    address_book.append({"alias": alias, "address": address, "sido": sido, "gu": gu})
    return True, "주소가 등록되었습니다."


def delete_address(alias):
    target = find_address_by_alias(alias)
    if not target:
        return False, "해당 별칭의 주소를 찾지 못했습니다."
    address_book.remove(target)
    return True, "주소가 삭제되었습니다."


# =========================
# 6. 조회 기준 주소 결정
# =========================

def resolve_target_address(alias, direct_address):
    if alias:
        target = find_address_by_alias(alias)
        if not target:
            return None, f"'{alias}' 별칭의 주소를 찾지 못했습니다."
        return target, None

    if direct_address:
        error_message = validate_address(direct_address)
        if error_message:
            return None, error_message
        sido, gu = extract_sido_gu(direct_address)
        if not sido or not gu:
            return None, "주소는 '서울 강서구 ...'처럼 시도와 구를 포함해서 입력해주세요."
        return {"alias": "직접 입력", "address": direct_address, "sido": sido, "gu": gu}, None

    return None, "별칭 또는 주소를 입력해주세요."


# =========================
# 7. 저가 주유소 조회
# =========================

def search_low_price_stations(alias, direct_address, product_code, count):
    """
    처리 흐름:
    1. 조회 기준 주소 결정
    2. 입력 주소 지오코딩 (fallback 포함)
    3. 오피넷 TOP10 조회
    4. 각 주유소 지오코딩 (fallback 포함) → 거리 계산
    5. 거리/유가 가중치 점수 합산 → 정렬
    6. count만큼 반환
    """

    # 1. 조회 기준 주소 결정
    target_address, error = resolve_target_address(alias, direct_address)
    if error:
        return False, error, None, []

    sido = target_address["sido"]

    # 2. 입력 주소 → KATEC 좌표 (fallback 포함)
    user_coord = geocode_with_fallback(target_address["address"])
    if not user_coord:
        return False, "입력 주소의 좌표를 가져올 수 없습니다. 주소를 다시 확인해주세요.", target_address, []

    user_x = user_coord["x"]
    user_y = user_coord["y"]

    # 3. 오피넷 TOP10 조회
    oil_list = get_low_top10(sido_name=sido, prodcd=product_code)
    if not oil_list:
        return False, "오피넷 조회 결과가 없습니다.", target_address, []

    formatted_data = format_oil_data(oil_list, sido)

    # 4. 각 주유소 지오코딩 (fallback 포함) → 거리 계산
    for station in formatted_data:
        addr = station.get("address")
        if not addr:
            station["distance"] = None
            continue
        coord = geocode_with_fallback(addr)
        if coord:
            station["distance"] = round(calc_distance(user_x, user_y, coord["x"], coord["y"]))
        else:
            station["distance"] = None

    # 5. 거리/유가 가중치 점수 합산 정렬
    valid   = [s for s in formatted_data if s["distance"] is not None]
    invalid = [s for s in formatted_data if s["distance"] is None]

    if valid:
        max_dist  = max(s["distance"] for s in valid) or 1
        max_price = max(int(s["price"]) for s in valid if str(s.get("price","")).isdigit()) or 1

        for s in valid:
            price       = int(s["price"]) if str(s.get("price","")).isdigit() else max_price
            dist_score  = s["distance"] / max_dist
            price_score = price / max_price
            s["score"]  = round(dist_score * 0.5 + price_score * 0.5, 4)

        valid.sort(key=lambda s: s["score"])

    result = (valid + invalid)[:count]

    save_report(result)
    return True, f"{sido} 기준 저가 주유소 조회가 완료되었습니다.", target_address, result


# =========================
# 8. Flask Route
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
    alias   = request.form.get("alias", "").strip()
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
    alias          = request.form.get("search_alias", "").strip()
    direct_address = request.form.get("direct_address", "").strip()
    product_code   = request.form.get("product_code", "B027").strip()
    count          = parse_count(request.form.get("count", "10"))

    if product_code not in PRODUCT_CODES:
        product_code = "B027"

    if not alias and not direct_address:
        flash("별칭 또는 주소를 입력해주세요.")
        return redirect(url_for("index"))

    success, message, target_address, stations = search_low_price_stations(
        alias=alias,
        direct_address=direct_address,
        product_code=product_code,
        count=count,
    )

    if not success:
        flash(message)
        return redirect(url_for("index"))

    search_result = {
        "success":        success,
        "message":        message,
        "alias":          alias,
        "direct_address": direct_address,
        "target_address": target_address,
        "product_name":   PRODUCT_CODES.get(product_code, ""),
        "product_code":   product_code,
        "count":          count,
        "stations":       stations,
    }

    return render_template("result.html", search_result=search_result)


# =========================
# 9. 실행
# =========================

if __name__ == "__main__":
    app.run(debug=True, port=5000)