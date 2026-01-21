# InBody OCR & LLM 서비스 성능 테스트 가이드

## 📊 성능 평가 KPI

### 1. 응답 시간 (Response Time)
| 항목--- | 목표값 | 측정 방법 |
|-------------------|----------------|---------------------------------------|
| OCR 처리 시간 | **10초 이내** | 이미지 업로드 → OCR 결과 반환 |
| LLM 응답 시간 | **8초 이내**-- | 질문 입력 → AI 답변 생성 완료-- |
| 히스토리 조회  | 1초 이내------ | DB 쿼리 응답 시간 ---------------|

**실측 기준:** OCR 단독 테스트 시 8초 소요 → 여유있게 10초 설정

### 2. 처리량 (Throughput)
| -------지표------------------------- |------------ 목표값 --------------|
|---------------------------------------|-----------------------------------|
| 동시 사용자 처리-------------------| 2명 동시 처리------------------ |
| RPS (Requests Per Second) -------| 0.1 RPS 이상 유지 -------------|
| 실패율 ------------------------------| 10% 이하 -----------------------|

---

## 🚀 부하 테스트 실행 방법

### 사전 준비
```bash
# 1. Locust 설치
pip install locust

# 2. FastAPI 서버 실행 (다른 터미널에서)
cd /path/to/your/project
python main.py
# 또는
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 테스트 시나리오
- **동시 사용자:** 2명
- **대기 시간:** 20초 (각 요청 후)
- **테스트 비율:**
  - OCR 처리: 50% (가중치 3)
  - LLM 챗봇: 33% (가중치 2)
  - 이력 조회: 17% (가중치 1)

### 실행 옵션

#### Option 1: 웹 UI 모드 (추천 - 교육용)
```bash
locust -f locustfile.py --host=http://localhost:8000
```
- 브라우저에서 `http://localhost:8089` 접속
- Number of users: **2**
- Spawn rate: **1** (1명씩 점진적 증가)
- Host: `http://localhost:8000`
- Start 버튼 클릭

**실시간으로 다음 정보 확인 가능:**
- RPS (초당 요청 수)
- 응답 시간 분포
- 실패율
- 각 API별 성능

#### Option 2: Headless 모드 (자동 실행)
```bash
# 5분간 자동 테스트 + HTML 리포트 생성
locust -f locustfile.py --host=http://localhost:8000 \
       --users 2 \
       --spawn-rate 1 \
       --run-time 5m \
       --headless \
       --html report.html
```

#### Option 3: CSV 리포트 포함
```bash
locust -f locustfile.py --host=http://localhost:8000 \
       --users 2 \
       --spawn-rate 1 \
       --run-time 3m \
       --headless \
       --html report.html \
       --csv results
```

생성 파일:
- `results_stats.csv`: 전체 통계
- `results_stats_history.csv`: 시간별 추이
- `results_failures.csv`: 실패 내역

---

## 📈 결과 분석

### 성공 기준
✅ **통과 조건:**
- OCR 처리: 평균 10초 이내, 95% 요청 10초 이내
- LLM 응답: 평균 8초 이내, 95% 요청 8초 이내
- 전체 실패율: 5% 이하

❌ **실패 조건:**
- OCR 또는 LLM 타임아웃 초과
- HTTP 500 에러 발생
- 처리량 급격히 감소

### Locust 리포트 해석

**주요 지표:**
1. **Response Time (ms)**
   - Average: 평균 응답 시간
   - Min/Max: 최소/최대 응답 시간
   - 95%ile: 95%의 요청이 이 시간 이내 완료

2. **RPS (Requests/s)**
   - 초당 처리 요청 수
   - 2 users × (1/20초) = 약 0.1 RPS 예상

3. **Failures**
   - 실패한 요청 비율
   - 타임아웃, HTTP 에러 포함

### 개선 방안
- OCR 처리 > 10초: PaddleOCR 최적화, GPU 활용
- LLM 응답 > 8초: 프롬프트 간소화, 스트리밍 응답
- 메모리 부족: 배치 크기 조정, 모델 경량화

---

## 🔧 고급 설정

### GPU 활용 확인
```python
# locustfile.py에 추가
import torch
print(f"CUDA Available: {torch.cuda.is_available()}")
print(f"GPU Count: {torch.cuda.device_count()}")
```

### 실시간 모니터링
```bash
# 별도 터미널에서 시스템 리소스 모니터링
# CPU, Memory, GPU 사용률 확인
watch -n 1 nvidia-smi  # GPU 모니터링
htop                    # CPU/Memory 모니터링
```

### 로그 레벨 조정
```bash
locust -f locustfile.py --host=http://localhost:8000 --loglevel DEBUG
```

---

## 📝 체크리스트

테스트 전:
- [ ] FastAPI 서버 정상 구동 확인
- [ ] GPU 드라이버 및 CUDA 설치 확인
- [ ] 가상환경 활성화
- [ ] Locust 설치 확인 (`locust --version`)

테스트 중:
- [ ] 2명의 사용자가 정상 생성되었는지 확인
- [ ] 20초 대기 간격 준수 확인
- [ ] 실시간 응답 시간 모니터링
- [ ] 에러 로그 확인

테스트 후:
- [ ] HTML 리포트 생성 확인
- [ ] KPI 달성 여부 판단
- [ ] 병목 구간 식별
- [ ] 개선 사항 문서화

---

## 🎓 교육 목적 추가 시나리오

### 부하 증가 테스트
```bash
# 2명 → 5명 → 10명으로 점진 증가
locust -f locustfile.py --host=http://localhost:8000 \
       --users 10 --spawn-rate 1 --run-time 3m
```

### 스트레스 테스트 (한계 테스트)
```bash
# 대기 시간 없이 연속 요청
# wait_time = between(0, 1) 로 수정 후
locust -f locustfile.py --host=http://localhost:8000 \
       --users 5 --spawn-rate 2 --run-time 2m
```

### API별 개별 테스트
locustfile.py에서 `@task` 데코레이터 조정:
- OCR만: `@task(1)` 주석 처리하고 OCR만 활성화
- LLM만: OCR 주석 처리하고 LLM만 활성화
