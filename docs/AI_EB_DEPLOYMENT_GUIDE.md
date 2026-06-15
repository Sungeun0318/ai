# beggar-ai Elastic Beanstalk 배포 가이드

## 목표

`deploy-ai` 브랜치에 push되면 GitHub Actions가 FastAPI AI 서버를 Elastic Beanstalk로 자동 배포한다.

```text
sungeun 또는 main 브랜치에서 개발
→ deploy-ai 브랜치로 merge
→ GitHub Actions 실행
→ Elastic Beanstalk beggar-ai 환경 배포
```

## 서버 구조

운영 서버는 총 3개다.

```text
beggar-admin   관리자 JSP 웹
beggar-backend Spring Boot API 서버
beggar-ai      FastAPI AI 서버
```

관리자 AI 기능 호출 흐름:

```text
관리자 브라우저
→ beggar-admin
→ beggar-backend
→ beggar-ai
```

## 배포 브랜치

```text
deploy-ai
```

이 브랜치에 push되면 `.github/workflows/deploy-ai-eb.yml`이 실행된다.

## GitHub Secrets

AI repository의 GitHub Secrets에 아래 값을 넣는다.

```text
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_REGION
EB_APPLICATION_NAME
EB_ENVIRONMENT_NAME
EB_S3_BUCKET
```

예시:

```text
AWS_REGION=ap-northeast-2
EB_APPLICATION_NAME=beggar-ai
EB_ENVIRONMENT_NAME=Beggar-ai-env
EB_S3_BUCKET=elasticbeanstalk-ap-northeast-2-계정ID
```

주의:

- AWS access key는 코드에 넣지 않는다.
- `.env`, `application.properties`, README에 평문 키를 쓰지 않는다.
- 계정을 바꾸면 GitHub Secrets의 `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`만 새 계정 키로 교체한다.

## 로컬 AWS CLI 계정 변경

새 AWS 계정 키로 로컬 CLI를 바꾸려면 아래 명령을 실행한다.

```bash
aws configure
```

입력값:

```text
AWS Access Key ID: 새 access key id
AWS Secret Access Key: 새 secret access key
Default region name: ap-northeast-2
Default output format: json
```

현재 설정 확인:

```bash
aws sts get-caller-identity
```

여기서 나오는 `Account`가 새 AWS 계정 ID면 정상이다.

## IAM 권한

자동 배포용 IAM 사용자는 최소한 아래 권한이 필요하다.

```text
Elastic Beanstalk 애플리케이션 버전 생성
Elastic Beanstalk 환경 업데이트
S3 배포 zip 업로드
CloudFormation/EC2/AutoScaling 관련 EB 환경 관리
```

처음에는 빠르게 검증하려면 AWS 관리형 권한을 붙일 수 있다.

```text
AWSElasticBeanstalkFullAccess
AmazonS3FullAccess
```

운영 안정화 후에는 S3 버킷과 EB 애플리케이션 단위로 권한을 줄인다.

## Elastic Beanstalk 환경 변수

AI 서버 자체는 현재 필수 비밀값이 없다.
필요하면 EB 환경 변수에 아래 값을 추가한다.

```text
APP_ENV=prod
MODEL_DIR=data/models
```

## FastAPI 실행 명령

Elastic Beanstalk는 `Procfile`을 보고 서버를 실행한다.

```text
web: uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

## 백엔드 연결

백엔드 Elastic Beanstalk 환경 변수에 AI 서버 주소를 넣는다.

```text
AI_SERVER_BASE_URL=http://beggar-ai-env.eba-xxxxx.ap-northeast-2.elasticbeanstalk.com
```

백엔드 설정 파일에서는 아래 값으로 사용한다.

```properties
ai-server.base-url=${AI_SERVER_BASE_URL:http://localhost:8000}
```

## 배포 검증

배포 후 확인:

```bash
curl http://AI_EB_URL/api/v1/health
```

정상 응답:

```json
{
  "status": "ok"
}
```

관리자 1차 기능까지 확인:

```text
관리자 로그인
→ 대시보드
→ 통계 보기
→ 소비 인사이트 화면 표시
```
