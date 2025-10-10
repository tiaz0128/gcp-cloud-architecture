from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google.cloud import firestore
import vertexai
from vertexai.generative_models import GenerativeModel
import os
from datetime import datetime
import logging
import re

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def clean_mermaid_code(code: str) -> str:
    """Mermaid 코드를 안전하게 정리하고 검증"""
    lines = code.split("\n")
    cleaned_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 주석 제거
        if line.startswith("%%"):
            continue

        # 괄호 () 사용을 대괄호 [] 로 변경
        # 예: A(Load Balancer) -> A["Load Balancer"]
        line = re.sub(r"(\w+)\(([^)]+)\)", r'\1["\2"]', line)

        # 레이블에 특수문자가 있으면 따옴표로 감싸기
        # 예: A[Cloud Run - Web App] -> A["Cloud Run - Web App"]
        line = re.sub(r'(\w+)\[([^"\]]+[^a-zA-Z0-9_\s][^"\]]*)\]', r'\1["\2"]', line)

        # 노드 ID에서 특수문자 제거 (영문자, 숫자, 언더스코어만 허용)
        line = re.sub(r'([^\w\s\[\]":\-\.><=|]+)', "", line)

        cleaned_lines.append(line)

    cleaned_code = "\n".join(cleaned_lines)

    # 기본 구조 검증
    if not cleaned_code.strip().startswith(("graph", "flowchart", "sequenceDiagram")):
        logger.warning("Mermaid 코드가 올바른 다이어그램 타입으로 시작하지 않습니다")
        # 기본 graph TB 추가
        cleaned_code = f"graph TB\n{cleaned_code}"

    return cleaned_code


app = FastAPI(title="Cloud Architecture Diagram Generator")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 프로젝트 ID 가져오기 (Cloud Run에서 자동으로 설정됨)
def get_project_id():
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        project_id = os.getenv("GCP_PROJECT")
    if not project_id:
        project_id = os.getenv("GCLOUD_PROJECT")
    if not project_id:
        # metadata 서버에서 프로젝트 ID 가져오기 시도
        try:
            import requests

            response = requests.get(
                "http://metadata.google.internal/computeMetadata/v1/project/project-id",
                headers={"Metadata-Flavor": "Google"},
                timeout=5,
            )
            if response.status_code == 200:
                project_id = response.text
        except Exception as e:
            logger.warning(f"메타데이터에서 프로젝트 ID 가져오기 실패: {e}")

    if not project_id:
        # 기본값 설정 (환경에 따라 수정 필요)
        project_id = "gleaming-modem-474701-f3"
        logger.warning(f"프로젝트 ID를 찾을 수 없어 기본값 사용: {project_id}")

    logger.info(f"사용중인 프로젝트 ID: {project_id}")
    return project_id


# Firestore 및 Vertex AI 초기화
try:
    db = firestore.Client()
    # Firestore 연결 테스트
    test_collection = db.collection("test")
    logger.info("Firestore 클라이언트 초기화 성공")
except Exception as e:
    logger.error(f"Firestore 클라이언트 초기화 실패: {e}")
    if "does not exist" in str(e):
        logger.error(
            "Firestore 데이터베이스가 설정되지 않았습니다. GCP 콘솔에서 Firestore를 활성화해주세요."
        )
        logger.error(
            f"URL: https://console.cloud.google.com/firestore/databases?project={get_project_id()}"
        )
    db = None

# Vertex AI 초기화
try:
    project_id = get_project_id()
    vertexai.init(project=project_id, location="asia-northeast3")
    model = GenerativeModel("gemini-2.5-flash")
    logger.info("Vertex AI 초기화 성공")
except Exception as e:
    logger.error(f"Vertex AI 초기화 실패: {e}")
    model = None


# 데이터 모델
class DiagramRequest(BaseModel):
    description: str
    cloud_provider: str = "gcp"  # gcp, aws, azure
    diagram_type: str = "flowchart"  # flowchart, sequence, etc.


class DiagramResponse(BaseModel):
    id: str
    mermaid_code: str
    description: str
    cloud_provider: str
    created_at: str


@app.post("/generate-diagram", response_model=DiagramResponse)
async def generate_diagram(request: DiagramRequest):
    """AI로 Mermaid 다이어그램 코드 생성"""
    try:
        if model is None:
            raise HTTPException(
                status_code=503, detail="Vertex AI 서비스를 사용할 수 없습니다"
            )

        if db is None:
            raise HTTPException(
                status_code=503, detail="Firestore 서비스를 사용할 수 없습니다"
            )

        # Vertex AI (Gemini) 프롬프트 생성
        prompt = f"""
        다음 설명을 바탕으로 {request.cloud_provider.upper()} 클라우드 아키텍처 다이어그램을 Mermaid 코드로 생성해주세요.

        사용자 설명: {request.description}
        클라우드 제공자: {request.cloud_provider.upper()}
        다이어그램 타입: {request.diagram_type}

        **중요한 Mermaid 구문 규칙을 반드시 준수하세요:**

        1. **노드 ID 규칙**:
           - 노드 ID는 영문자로 시작하고 영문자, 숫자, 언더스코어만 사용
           - 예: A, B1, User_Input, CloudRun, LoadBalancer
           
        2. **노드 레이블 규칙**:
           - 레이블에 특수문자가 있으면 반드시 큰따옴표로 감싸기
           - 괄호 () 사용 금지 - 대신 하이픈이나 언더스코어 사용
           - 예: A["Cloud Run - Web App"], B["Cloud SQL - Database"]
           
        3. **화살표와 연결**:
           - --> (기본 화살표), -.-> (점선), ==> (굵은 화살표) 사용
           - 연결선에 레이블 추가시: A -->|"HTTP"| B
           
        4. **전체 구조**:
           - graph TB (위에서 아래), graph LR (왼쪽에서 오른쪽) 사용
           - 들여쓰기 4칸으로 일관성 유지
           
        5. **금지사항**:
           - 노드 레이블에 괄호 () 사용 금지
           - 특수문자는 반드시 따옴표 안에
           - 공백이 있는 레이블은 반드시 따옴표로 감싸기

        {request.cloud_provider.upper()} 주요 서비스 참고:
        - GCP: Cloud Run, App Engine, Compute Engine, Cloud Storage, Firestore, Cloud SQL, Load Balancer, Cloud CDN
        - AWS: EC2, Lambda, S3, RDS, ALB, CloudFront, API Gateway
        - Azure: App Service, Functions, Blob Storage, SQL Database, Application Gateway

        **올바른 예시:**
        ```
        graph TB
            User["User"] --> LoadBalancer["Load Balancer"]
            LoadBalancer --> CloudRun["Cloud Run - Web App"]
            CloudRun --> CloudSQL["Cloud SQL - Database"]
            CloudRun --> CloudStorage["Cloud Storage - Static Files"]
            CloudRun -.-> Firestore["Firestore - NoSQL DB"]
        ```

        **잘못된 예시 (사용하지 마세요):**
        ```
        graph TB
            User --> LoadBalancer(Load Balancer)
            LoadBalancer --> CloudRun[Cloud Run (Web App)]
        ```

        이제 위 규칙을 엄격히 따라 Mermaid 코드만 생성해주세요:
        """

        # Vertex AI (Gemini) 호출
        response = model.generate_content(prompt)
        mermaid_code = response.text.strip()

        # 코드 블록 제거 (```로 감싸진 부분)
        if "```" in mermaid_code:
            lines = mermaid_code.split("\n")
            start_idx = -1
            end_idx = -1

            for i, line in enumerate(lines):
                if line.strip().startswith("```"):
                    if start_idx == -1:
                        start_idx = i
                    else:
                        end_idx = i
                        break

            if start_idx != -1 and end_idx != -1:
                mermaid_code = "\n".join(lines[start_idx + 1 : end_idx])
            elif start_idx != -1:
                mermaid_code = "\n".join(lines[start_idx + 1 :])

        mermaid_code = mermaid_code.strip()

        # Mermaid 코드 안전성 검증 및 정리
        mermaid_code = clean_mermaid_code(mermaid_code)

        logger.info(f"생성된 Mermaid 코드: {mermaid_code}")

        # Firestore에 저장
        diagram_ref = db.collection("diagrams").document()
        diagram_data = {
            "mermaid_code": mermaid_code,
            "description": request.description,
            "cloud_provider": request.cloud_provider,
            "diagram_type": request.diagram_type,
            "created_at": datetime.now().isoformat(),
        }
        diagram_ref.set(diagram_data)

        return DiagramResponse(
            id=diagram_ref.id,
            mermaid_code=mermaid_code,
            description=request.description,
            cloud_provider=request.cloud_provider,
            created_at=diagram_data["created_at"],
        )

    except Exception as e:
        logger.error(f"다이어그램 생성 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"다이어그램 생성 실패: {str(e)}")


@app.get("/diagrams/{diagram_id}", response_model=DiagramResponse)
async def get_diagram(diagram_id: str):
    """저장된 다이어그램 조회"""
    try:
        diagram_ref = db.collection("diagrams").document(diagram_id)
        diagram = diagram_ref.get()

        if not diagram.exists:
            raise HTTPException(status_code=404, detail="다이어그램을 찾을 수 없습니다")

        data = diagram.to_dict()
        return DiagramResponse(
            id=diagram_id,
            mermaid_code=data["mermaid_code"],
            description=data["description"],
            cloud_provider=data["cloud_provider"],
            created_at=data["created_at"],
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/diagrams")
async def list_diagrams(limit: int = 10):
    """다이어그램 목록 조회"""
    try:
        diagrams_ref = (
            db.collection("diagrams")
            .order_by("created_at", direction=firestore.Query.DESCENDING)
            .limit(limit)
        )
        diagrams = diagrams_ref.stream()

        diagram_list = []
        for diagram in diagrams:
            data = diagram.to_dict()
            diagram_list.append(
                {
                    "id": diagram.id,
                    "description": data["description"],
                    "cloud_provider": data["cloud_provider"],
                    "created_at": data["created_at"],
                }
            )

        return {"diagrams": diagram_list}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/diagrams/{diagram_id}")
async def update_diagram(diagram_id: str, request: DiagramRequest):
    """다이어그램 수정 (재생성)"""
    try:
        # 기존 다이어그램 확인
        diagram_ref = db.collection("diagrams").document(diagram_id)
        if not diagram_ref.get().exists:
            raise HTTPException(status_code=404, detail="다이어그램을 찾을 수 없습니다")

        # 새로 생성 (기존 generate_diagram 로직 재사용)
        new_diagram = await generate_diagram(request)

        # 기존 문서 업데이트
        diagram_ref.update(
            {
                "mermaid_code": new_diagram.mermaid_code,
                "description": request.description,
                "cloud_provider": request.cloud_provider,
                "diagram_type": request.diagram_type,
                "updated_at": datetime.now().isoformat(),
            }
        )

        return {
            "message": "다이어그램이 업데이트되었습니다",
            "mermaid_code": new_diagram.mermaid_code,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/diagrams/{diagram_id}")
async def delete_diagram(diagram_id: str):
    """다이어그램 삭제"""
    try:
        diagram_ref = db.collection("diagrams").document(diagram_id)
        if not diagram_ref.get().exists:
            raise HTTPException(status_code=404, detail="다이어그램을 찾을 수 없습니다")

        diagram_ref.delete()
        return {"message": "다이어그램이 삭제되었습니다"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    return {
        "message": "Cloud Architecture Diagram Generator API",
        "version": "1.0.0",
        "endpoints": {
            "POST /generate-diagram": "다이어그램 생성",
            "GET /diagrams/{id}": "다이어그램 조회",
            "GET /diagrams": "다이어그램 목록",
            "PUT /diagrams/{id}": "다이어그램 수정",
            "DELETE /diagrams/{id}": "다이어그램 삭제",
        },
    }


@app.get("/health")
async def health_check():
    """서비스 상태 확인"""
    status = "healthy"
    issues = []

    # Firestore 연결 확인
    firestore_status = "healthy"
    if db is None:
        status = "unhealthy"
        firestore_status = "unhealthy"
        issues.append("Firestore 연결 실패")
    else:
        # Firestore 실제 연결 테스트
        try:
            # 간단한 읽기 테스트
            test_ref = db.collection("health_check").document("test")
            test_ref.get()
            firestore_status = "healthy"
        except Exception as e:
            status = "unhealthy"
            firestore_status = "unhealthy"
            issues.append(f"Firestore 연결 테스트 실패: {str(e)}")

    # Vertex AI 모델 확인
    vertex_ai_status = "healthy"
    if model is None:
        status = "unhealthy"
        vertex_ai_status = "unhealthy"
        issues.append("Vertex AI 모델 초기화 실패")

    return {
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "project_id": get_project_id(),
        "services": {
            "firestore": firestore_status,
            "vertex_ai": vertex_ai_status,
        },
        "issues": issues if issues else None,
    }
