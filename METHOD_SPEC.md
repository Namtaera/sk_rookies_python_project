## 1. geocoder.py

### `get_geocode(address)`

주소 문자열을 입력받아 KATEC 좌표로 변환하는 메서드입니다.

- 입력값

  - `address: str`
  - 예: `"서울특별시 은평구"`
- 반환값

  - 성공 시: `{"x": katec_x, "y": katec_y}`
  - 실패 시: `None`
- 사용 예시

```python
coords = get_geocode(address)

if coords is None:
    error = "주소를 좌표로 변환하지 못했습니다."
else:
    x = coords["x"]
    y = coords["y"]
```

- 참고
  - 주소 검색 실패, 요청 시간 초과, API 요청 오류 발생 시 `None` 반환

---

## 2. opinet.py

### `get_low_top10(sido_name, prodcd="B027")`

입력한 시도 지역의 최저가 주유소 TOP10 원본 데이터를 조회하는 메서드입니다.

- 입력값

  - `sido_name: str`
  - `prodcd: str = "B027"`
  - 예: `"서울"`
- 반환값

  - 성공 시: `list[dict]`
  - 실패 시: `[]`
- 사용 예시

```python
oil_list = get_low_top10("서울")

if not oil_list:
    error = "조회 결과가 없습니다."
```

- 참고
  - 현재는 시도 단위 조회만 가능
  - 기본 유종 코드는 휘발유(`B027`)입니다.

### `format_oil_data(oil_list, sido_name)`

오피넷 원본 데이터를 화면 출력 및 CSV/JSON 저장용 형태로 가공하는 메서드입니다.

- 입력값

  - `oil_list: list[dict]`
  - `sido_name: str`
- 반환값

  - `list[dict]`
- 반환 데이터 형태

```python
[
    {
        "rank": 1,
        "region": "서울",
        "station_name": "주유소명",
        "price": "가격",
        "address": "주소",
        "brand": "브랜드코드"
    }
]
```

- 사용 예시

```python
oil_list = get_low_top10("서울")
formatted_data = format_oil_data(oil_list, "서울")
```

---

## 3. validator.py

### `validate_region(region)`

지역명 입력값을 검증하는 메서드입니다.

- 입력값

  - `region: str`
- 반환값

  - 정상: `None`
  - 오류: 오류 메시지 문자열
- 반환 예시

```python
None
"지역명을 입력해주세요."
"올바른 지역명을 입력해주세요. (예: 서울, 경기, 인천)"
```

- 사용 예시

```python
error = validate_region(region)

if error:
    return render_template("index.html", error=error)
```

### `validate_address(address)`

주소 입력값을 검증하는 메서드입니다.

- 입력값

  - `address: str`
- 반환값

  - 정상: `None`
  - 오류: 오류 메시지 문자열
- 반환 예시

```python
None
"주소를 입력해주세요."
"주소를 두 글자 이상 입력해주세요."
```

- 사용 예시

```python
error = validate_address(address)

if error:
    return render_template("index.html", error=error)
```

### `validate_coordinates(coords)`

지오코더 결과값을 검증하는 메서드입니다.

- 입력값

  - `coords: dict | None`
- 반환값

  - 정상: `None`
  - 오류: 오류 메시지 문자열
- 반환 예시

```python
None
"주소를 좌표로 변환하지 못했습니다."
"좌표 데이터 형식이 올바르지 않습니다."
"좌표 정보가 올바르지 않습니다."
```

- 사용 예시

```python
coords = get_geocode(address)
error = validate_coordinates(coords)

if error:
    return render_template("index.html", error=error)
```

### `validate_oil_list(oil_list)`

오피넷 조회 결과를 검증하는 메서드입니다.

- 입력값

  - `oil_list: list | None`
- 반환값

  - 정상: `None`
  - 오류: 오류 메시지 문자열
- 반환 예시

```python
None
"유가 데이터를 불러오지 못했습니다."
"유가 데이터 형식이 올바르지 않습니다."
"조회 결과가 없습니다."
```

- 사용 예시

```python
oil_list = get_low_top10(region)
error = validate_oil_list(oil_list)

if error:
    return render_template("index.html", error=error)
```

---

## 4. report.py

### `save_csv(data, path="output/report.csv")`

데이터를 CSV 파일로 저장하는 메서드입니다.

- 입력값

  - `data: list[dict]`
  - `path: str`
- 반환값

  - 별도 반환값 없음
- 사용 예시

```python
save_csv(formatted_data)
```

### `save_json(data, path="output/report.json")`

데이터를 JSON 파일로 저장하는 메서드입니다.

- 입력값

  - `data: list[dict]`
  - `path: str`
- 반환값

  - 별도 반환값 없음
- 사용 예시

```python
save_json(formatted_data)
```

### `save_report(data)`

데이터를 CSV와 JSON 파일로 모두 저장하는 메서드입니다.

- 입력값

  - `data: list[dict]`
- 반환값

  - 별도 반환값 없음
- 사용 예시

```python
save_report(formatted_data)
```

---

## 5. HTML에서 사용할 값

### `result.html`에서 주유소 조회 결과 출력 시

```python
results
```

### 각 원소에서 사용 가능한 키

```python
oil["rank"]
oil["region"]
oil["station_name"]
oil["price"]
oil["address"]
oil["brand"]
```

### `result.html`에서 좌표 출력 시

```python
coords["x"]
coords["y"]
```
