import sqlite3
import uuid
from datetime import datetime
from  main import main
# 데이터베이스 연결
conn = sqlite3.connect('example.db')
cursor = conn.cursor()


# 데이터 삽입 함수
def insert_data(datetime_value, uuid_value, is_defective, defect_reason=None):
    insert_query = '''
    INSERT INTO 제품 (datetime, uuid, is_defective, defect_reason)
    VALUES (?,?,?,?)
    '''
    cursor.execute(insert_query, (datetime_value, uuid_value, is_defective, defect_reason))
    conn.commit()


# 데이터 예제
datetime_value = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # 현재 날짜와 시간
uuid_value = str(uuid.uuid4())  # UUID 생성
is_defective =  # 불량품인 경우 (1: 불량, 0: 양품)
defect_reason = "스크래치 있음"  # 불량 사유 (양품인 경우 None 또는 생략 가능)   


# 데이터 삽입 호출
insert_data(datetime_value, uuid_value, is_defective, defect_reason)

# 연결 종료
conn.close()