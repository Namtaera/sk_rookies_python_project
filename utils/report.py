import csv
import json
from pathlib import Path

def save_csv(data, path="output/report.csv"):
    """데이터를 CSV 파일로 저장"""

    # output 폴더가 없으면 새로 생성
    Path("output").mkdir(exist_ok=True)

    # 저장할 데이터가 없으면 메시지를 출력하고 함수 종료
    if not data:
        print("저장할 데이터가 없습니다.")
        return

    try:
        # newline=""은 CSV 저장 시 줄 사이에 빈 줄이 생기는 것을 방지
        with open(path, "w", newline="", encoding="utf-8-sig") as file:

            # 첫 번째 데이터의 key 값을 CSV 컬럼명으로 사용
            # 예: {"sido": "서울", "price": 1756} → sido, price가 컬럼명이 됨
            fieldnames = data[0].keys()

            # 딕셔너리 데이터를 CSV 형식으로 저장할 writer 객체 생성
            # fieldnames 기준으로 각 딕셔너리 값을 컬럼에 맞춰 저장
            writer = csv.DictWriter(file, fieldnames=fieldnames)

            # CSV 첫 번째 줄에 컬럼명 작성
            writer.writeheader()

            # data 리스트 안의 딕셔너리들을 CSV 파일에 한 줄씩 저장
            writer.writerows(data)
        
        print(f"CSV 저장 완료: {path}")

    except PermissionError:
        print(f"CSV 저장 권한이 없습니다: {path}")

    except OSError as e:
        print(f"CSV 저장 중 파일 오류 발생: {e}")

    except Exception as e:
        print(f"CSV 저장 중 오류 발생: {e}")



def save_json(data, path="output/report.json"):
    """데이터를 JSON 파일로 저장"""
    
    # output 폴더가 없으면 새로 생성
    Path("output").mkdir(exist_ok=True)

    # 저장할 데이터가 없으면 메시지를 출력하고 함수 종료
    if not data:
        print("저장할 데이터가 없습니다.")
        return
    
    try:
        with open(path, "w", encoding="utf-8") as file:

            # data를 JSON 형식으로 파일에 저장
            # ensure_ascii=False는 한글이 유니코드로 깨져 보이지 않게 함
            json.dump(data, file, ensure_ascii=False, indent=4)

        print(f"JSON 저장 완료: {path}")

    except PermissionError:
        print(f"JSON 저장 권한이 없습니다: {path}")

    except TypeError as e:
        print(f"JSON 저장 불가능한 데이터 형식입니다: {e}")

    except OSError as e:
        print(f"JSON 저장 중 파일 오류 발생: {e}")

    except Exception as e:
        print(f"JSON 저장 중 오류 발생: {e}")  


def save_report(data):
    """데이터를 CSV와 JSON 파일로 모두 저장"""
    save_csv(data)
    save_json(data)