from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from google.cloud import firestore
import vertexai
from vertexai.generative_models import GenerativeModel
import os
from datetime import datetime
import logging
import re
import requests

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

        # 대괄호 안의 특수문자 처리 - 예: [Cloud Storage (Static Files)]
        # Mermaid에서 대괄호 안에 특수문자가 있으면 문제가 될 수 있으므로 안전하게 제거
        # 대괄호 안에 특수문자가 있는 패턴을 찾아서 특수문자를 제거
        def clean_special_chars_in_label(match):
            label_content = match.group(1)
            # 특수문자를 공백으로 변환 후 여러 공백을 하나로 정리
            # 영문자, 숫자, 공백, 언더스코어만 남기고 나머지 제거
            cleaned_content = re.sub(r"[^\w\s]", " ", label_content)
            # 여러 공백을 하나로 정리하고 앞뒤 공백 제거
            cleaned_content = re.sub(r"\s+", " ", cleaned_content).strip()
            return f"[{cleaned_content}]"

        # 패턴: [내용] 형태에서 특수문자가 포함된 경우 정리
        line = re.sub(
            r"\[([^\[\]]*[^\w\s][^\[\]]*)\]", clean_special_chars_in_label, line
        )

        # architecture-beta 구문에서는 기본적으로 안전한 구문 사용
        # 특수문자 처리는 최소화 (architecture-beta는 구조가 더 엄격함)
        cleaned_lines.append(line)

    cleaned_code = "\n".join(cleaned_lines)

    # 기본 구조 검증 - architecture-beta 지원 추가
    if not cleaned_code.strip().startswith(
        ("graph", "flowchart", "sequenceDiagram", "architecture-beta")
    ):
        logger.warning("Mermaid 코드가 올바른 다이어그램 타입으로 시작하지 않습니다")
        # 기본 architecture-beta 추가
        cleaned_code = f"architecture-beta\n{cleaned_code}"

    return cleaned_code


app = FastAPI(title="Cloud Architecture Diagram Generator")

# 환경변수에서 허용된 오리진 가져오기 (쉼표로 구분)
# 예: ALLOWED_ORIGINS="https://example.com,https://storage.googleapis.com"
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "*")
ALLOWED_ORIGINS = [origin.strip() for origin in allowed_origins_env.split(",")]

# CORS 와일드카드 검증
if "*" in ALLOWED_ORIGINS:
    if len(ALLOWED_ORIGINS) > 1:
        logger.error("⚠️  CORS 설정 오류: 와일드카드(*)는 단독으로만 사용 가능합니다. 다른 오리진과 함께 사용할 수 없습니다.")
        # 보안을 위해 와일드카드가 포함된 경우 와일드카드만 사용
        ALLOWED_ORIGINS = ["*"]
    logger.warning("⚠️  CORS가 모든 오리진을 허용하도록 설정되어 있습니다. 프로덕션 환경에서는 ALLOWED_ORIGINS 환경변수를 설정하세요.")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
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
            response = requests.get(
                "http://metadata.google.internal/computeMetadata/v1/project/project-id",
                headers={"Metadata-Flavor": "Google"},
                timeout=5,
            )
            response.raise_for_status()
            project_id = response.text
        except requests.RequestException as e:
            logger.warning(f"메타데이터에서 프로젝트 ID 가져오기 실패: {e}")

    if not project_id:
        # 프로젝트 ID를 찾을 수 없는 경우 에러 로그
        logger.error("⚠️  프로젝트 ID를 찾을 수 없습니다. 다음 환경변수 중 하나를 설정하세요: GOOGLE_CLOUD_PROJECT, GCP_PROJECT, GCLOUD_PROJECT")
        # 개발 환경에서만 기본값 사용 (환경변수로 명시적으로 설정된 경우)
        project_id = os.getenv("DEFAULT_PROJECT_ID")
        if project_id:
            logger.warning(f"개발 환경 기본 프로젝트 ID 사용: {project_id}")
        else:
            raise ValueError("프로젝트 ID를 설정할 수 없습니다. 환경변수를 확인하세요.")

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
except ValueError as e:
    logger.error(f"Vertex AI 초기화 실패 - 프로젝트 ID 오류: {e}")
    model = None
except Exception as e:
    logger.error(f"Vertex AI 초기화 실패: {e}")
    model = None


# 데이터 모델
class DiagramRequest(BaseModel):
    description: str = Field(..., min_length=10, max_length=5000, description="Architecture description")
    cloud_provider: str = Field(default="gcp", description="Cloud provider")
    diagram_type: str = Field(default="architecture-beta", description="Diagram type")
    
    @classmethod
    def model_validate(cls, obj):
        # cloud_provider 정규화: 소문자로 변환하고 공백 제거
        if isinstance(obj, dict) and "cloud_provider" in obj:
            obj["cloud_provider"] = obj["cloud_provider"].strip().lower()
            # 유효한 값인지 확인
            if obj["cloud_provider"] not in ["gcp", "aws", "azure"]:
                raise ValueError("Invalid cloud_provider. Must be one of: gcp, aws, azure")
        return super().model_validate(obj)


class DiagramResponse(BaseModel):
    id: str
    mermaid_code: str
    description: str
    cloud_provider: str
    created_at: str


@app.post("/generate-diagram", response_model=DiagramResponse)
async def generate_diagram(request: DiagramRequest):
    """
    AI로 Mermaid 다이어그램 코드 생성
    
    Args:
        request: 다이어그램 생성 요청 (description, cloud_provider, diagram_type)
        
    Returns:
        DiagramResponse: 생성된 다이어그램 정보
        
    Raises:
        HTTPException: Vertex AI 또는 Firestore 서비스 오류, 다이어그램 생성 실패
    """
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
        다음 설명을 바탕으로 {request.cloud_provider.upper()} 클라우드 아키텍처 다이어그램을 Mermaid architecture-beta 코드로 생성해주세요.

        사용자 설명: {request.description}
        클라우드 제공자: {request.cloud_provider.upper()}
        다이어그램 타입: architecture-beta

        **중요한 Mermaid architecture-beta 구문 규칙을 반드시 준수하세요:**

        1. **기본 구조**:
           - architecture-beta로 시작
           - 4칸 들여쓰기 사용
           - ( ), [ ] 괄호안에 빈값은 허용하지 않음
           - 주석은 %% 로 시작하지만, 이번에는 사용하지 않음
           - Edge 선언 시 그룹은 절대 사용하지 않음 (serviceId{{group}} 형태 금지)
           - 주석 절대 쓰지마

           
        2. **아이콘 참고**:
           - <provider>:아이콘명 형식 사용
           - 서비스 / 리소스명은 소문자 _(언더스코어)로 연결 (예: cloud_run, sql_database)
           - GCP: logos:google-cloud, gcp:virtual_private_cloud
           - AWS: logos:aws, aws:amazon_virtual_private_cloud
           - Azure: logos:microsoft-azure, azr:virtual_networks
           - logos: logos:python, logos:react, logos:fastapi-icon
           - mdi: mdi:account, mdi:server, mdi:earth, mdi:heart

        주요 서비스 및 아이콘:
        - GCP: Compute Engine(gcp:compute_engine), Cloud Run(gcp:cloud_run), Cloud Storage(gcp:cloud_storage), Cloud SQL(gcp:cloud_sql), Firestore(gcp:firestore), Vertex AI(gcp:vertexai)
        - AWS: EC2(aws:amazon_ec2_db_instance), VPC(aws:amazon_virtual_private_cloud), Lambda(aws:aws_lambda_lambda_function), S3(aws:amazon_simple_storage_service_s3_standard), RDS(aws:amazon_rds_multi_az), ALB(aws:elastic_load_balancing_application_load_balancer), CloudFront(aws:amazon_cloudfront)
        - Azure: VM(azr:virtual_machine), App Service(azr:app_services), Functions(azr:functions), Blob Storage(azr:blob_block), SQL Database(azr:sql_database)

        ---

        """

        prompt += r"""
        # Architecture Diagrams Documentation (v11.1.0+)

        > In the context of mermaid-js, the architecture diagram is used to show the relationship between services and resources commonly found within the Cloud or CI/CD deployments. In an architecture diagram, services (nodes) are connected by edges. Related services can be placed within groups to better illustrate how they are organized.

        ## Example

        ```mermaid-example
        architecture-beta
            group api(cloud)[API]

            service db(database)[Database] in api
            service disk1(disk)[Storage] in api
            service disk2(disk)[Storage] in api
            service server(server)[Server] in api

            db:L -- R:server
            disk1:T -- B:server
            disk2:T -- B:db
        ```

        ## Syntax

        The building blocks of an architecture are `groups`, `services`, `edges`, and `junctions`.

        For supporting components, icons are declared by surrounding the icon name with `()`, while labels are declared by surrounding the text with `[]`.

        To begin an architecture diagram, use the keyword `architecture-beta`, followed by your groups, services, edges, and junctions. While each of the 3 building blocks can be declared in any order, care must be taken to ensure the identifier was previously declared by another component.

        ### Groups

        The syntax for declaring a group is:

        ```
        group {group id}({icon name})[{title}] (in {parent id})?
        ```

        Put together:

        ```
        group public_api(cloud)[Public API]
        ```

        creates a group identified as `public_api`, uses the icon `cloud`, and has the label `Public API`.

        Additionally, groups can be placed within a group using the optional `in` keyword

        ```
        group private_api(cloud)[Private API] in public_api
        ```

        ### Services

        The syntax for declaring a service is:

        ```
        service {service id}({icon name})[{title}] (in {parent id})?
        ```

        Put together:

        ```
        service database1(database)[My Database]
        ```

        creates the service identified as `database1`, using the icon `database`, with the label `My Database`.

        If the service belongs to a group, it can be placed inside it through the optional `in` keyword

        ```
        service database1(database)[My Database] in private_api
        ```

        ### Edges

        The syntax for declaring an edge is:

        ```
        {serviceId}?:{T|B|L|R} {<}?--{>}? {T|B|L|R}:{serviceId}?
        ```

        #### Edge Direction

        The side of the service the edge comes out of is specified by adding a colon (`:`) to the side of the service connecting to the arrow and adding `L|R|T|B`

        For example:

        ```
        db:R -- L:server
        ```

        creates an edge between the services `db` and `server`, with the edge coming out of the right of `db` and the left of `server`.

        ```
        db:T -- L:server
        ```

        creates a 90 degree edge between the services `db` and `server`, with the edge coming out of the top of `db` and the left of `server`.

        #### Arrows

        Arrows can be added to each side of an edge by adding `<` before the direction on the left, and/or `>` after the direction on the right.

        For example:

        ```
        subnet:R --> L:gateway
        ```

        creates an edge with the arrow going into the `gateway` service

        #### Edges out of Groups

        To have an edge go from a group to another group or service within another group, the `{group}` modifier can be added after the `serviceId`.

        For example:

        ```
        service server[Server] in groupOne
        service subnet[Subnet] in groupTwo

        server{group}:B --> T:subnet{group}
        ```

        creates an edge going out of `groupOne`, adjacent to `server`, and into `groupTwo`, adjacent to `subnet`.

        It's important to note that `groupId`s cannot be used for specifying edges and the `{group}` modifier can only be used for services within a group.

        ### Junctions

        Junctions are a special type of node which acts as a potential 4-way split between edges.

        The syntax for declaring a junction is:

        ```
        junction {junction id} (in {parent id})?
        ```

        ```mermaid-example
        architecture-beta
            service left_disk(disk)[Disk]
            service top_disk(disk)[Disk]
            service bottom_disk(disk)[Disk]
            service top_gateway(internet)[Gateway]
            service bottom_gateway(internet)[Gateway]
            junction junctionCenter
            junction junctionRight

            left_disk:R -- L:junctionCenter
            top_disk:B -- T:junctionCenter
            bottom_disk:T -- B:junctionCenter
            junctionCenter:R -- L:junctionRight
            top_gateway:B -- T:junctionRight
            bottom_gateway:T -- B:junctionRight
        ```

        ---

        이제 위 규칙을 엄격히 따라 architecture-beta Mermaid 코드만 생성해주세요:
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
