import requests
from config import GEO_API_KEY
from pyproj import Transformer

#WGS84 -> KATEC 변환 정의
KATEC_PROJ = (
    "+proj=tmerc +lat_0=38 +lon_0=128 +k=0.9999 "
    "+x_0=400000 +y_0=600000 +ellps=bessel +units=m +no_defs "
    "+towgs84=-115.80,474.99,674.11,1.16,-2.31,-1.63,6.43"
)

def get_geocode(address):
    """주소를 입력받아 KATEC 좌표로 변환하여 반환하는 함수"""


    url = "http://api.vworld.kr/req/address"
    params ={
        "service" : "address",
        "request" : "getcoord",
        "version" : "2.0",
        "crs"     : "epsg:4326",
        "format"  : "json",
        "type"    : "road",
        "address" : address,
        "key"     : GEO_API_KEY
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if data["response"]['status']!="OK":
            print(f"[geocoder] 주소 검색 실패: {data['response']['status']}")
            return None
        
        point = data["response"]["result"]["point"]
        wgs84_x = float(point["x"]) #경도
        wgs84_y = float(point["y"]) #위도

        return _convert_to_katec(wgs84_x, wgs84_y)
    
    except Exception as e:
        print(f"[geocoder] 주소 검색 중 오류 발생: {e}")
        return None

def _convert_to_katec(wgs84_x, wgs84_y):
    """WGS84 좌표를 KATEC 좌표로 변환하는 함수"""
    transformer = Transformer.from_crs("epsg:4326", KATEC_PROJ, always_xy=True)
    katec_x, katec_y = transformer.transform(wgs84_x, wgs84_y)
    return {"x": katec_x, "y": katec_y}


if __name__ == "__main__":
    test_address = "서울특별시 중구 세종대로 110"
    result = get_geocode(test_address)

    if result:
        print(f"주소: {test_address}")
        print(f"KATEC X 좌표: {result['x']}")
        print(f"KATEC Y 좌표: {result['y']}")
    else:
        print("주소 검색 실패")