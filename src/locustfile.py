"""
InBody OCR & LLM 서비스 부하 테스트
- 2명의 동시 사용자 시뮬레이션
- 20초 대기 간격
- OCR 처리: 10초 이내 목표
- LLM 응답: 8초 이내 목표
"""

from locust import HttpUser, task, between
import time
import random
import json

class InBodyUser(HttpUser):
    wait_time = between(20, 20)  # 20초 고정 대기
    
    def on_start(self):
        """각 사용자 시작 시 로그인 (옵션)"""
        # 매번 다른 사용자로 로그인
        username = f"user_{random.randint(1, 100)}"
        self.client.post("/api/login", json={
            "username": username,
            "password": "test123"
        }, name="Login")
        print(f"[{time.strftime('%H:%M:%S')}] {username} 로그인")
    
    @task(3)
    def upload_and_ocr_process(self):
        """OCR 업로드 및 처리 테스트 (가중치 3)"""
        # 임의의 InBody 결과 데이터 (OCR이 추출했다고 가정)
        mock_inbody_data = {
            "user_id": f"user_{random.randint(1, 100)}",
            "weight": round(random.uniform(50.0, 90.0), 1),
            "skeletal_muscle_mass": round(random.uniform(20.0, 40.0), 1),
            "body_fat_mass": round(random.uniform(10.0, 30.0), 1),
            "body_fat_percentage": round(random.uniform(15.0, 35.0), 1),
            "bmi": round(random.uniform(18.5, 30.0), 1),
            "basal_metabolic_rate": random.randint(1200, 2000)
        }
        
        start_time = time.time()
        
        with self.client.post("/api/ocr/process", 
                             json=mock_inbody_data,
                             catch_response=True,
                             timeout=15) as response:
            
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                if elapsed > 10.0:
                    response.failure(f"OCR 처리 시간 초과: {elapsed:.2f}초 (목표: 10초 이내)")
                    print(f"❌ OCR 처리 실패: {elapsed:.2f}초")
                else:
                    response.success()
                    print(f"✅ OCR 처리 성공: {elapsed:.2f}초")
            else:
                response.failure(f"HTTP {response.status_code}")
    
    @task(2)
    def chat_query(self):
        """LLM 챗봇 질의 테스트 (가중치 2)"""
        questions = [
            "내 체지방률은 정상인가요?",
            "근육량을 늘리려면 어떻게 해야 하나요?",
            "추천 운동 루틴을 알려주세요",
            "BMI 수치가 의미하는 것은 무엇인가요?",
            "기초대사량을 높이는 방법은?",
            "체성분 검사 결과를 어떻게 해석하나요?"
        ]
        
        payload = {
            "user_id": f"user_{random.randint(1, 100)}",
            "message": random.choice(questions)
        }
        
        start_time = time.time()
        
        with self.client.post("/api/chat", 
                             json=payload,
                             catch_response=True,
                             timeout=12) as response:
            
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                if elapsed > 8.0:
                    response.failure(f"LLM 응답 시간 초과: {elapsed:.2f}초 (목표: 8초 이내)")
                    print(f"❌ LLM 응답 실패: {elapsed:.2f}초")
                else:
                    response.success()
                    print(f"✅ LLM 응답 성공: {elapsed:.2f}초")
            else:
                response.failure(f"HTTP {response.status_code}")
    
    @task(1)
    def get_analysis_history(self):
        """분석 이력 조회 (가중치 1)"""
        user_id = f"user_{random.randint(1, 100)}"
        
        with self.client.get(f"/api/history/{user_id}", 
                            name="Get History",
                            catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}")


# 실행 방법:
# 1. 웹 UI 모드: locust -f locustfile.py --host=http://localhost:8000
#    -> http://localhost:8089 접속하여 Users: 2, Spawn rate: 1 설정
#
# 2. Headless 모드 (5분간 자동 실행):
#    locust -f locustfile.py --host=http://localhost:8000 \
#           --users 2 --spawn-rate 1 --run-time 5m \
#           --headless --html report.html
#
# 3. CSV 리포트 포함:
#    locust -f locustfile.py --host=http://localhost:8000 \
#           --users 2 --spawn-rate 1 --run-time 5m \
#           --headless --html report.html --csv results
