"""환경 설정 (pydantic-settings 기반).

`.env` 파일을 자동으로 로드. 키 이름은 대소문자 무관.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # 서버
    app_name: str = "beggar-ai"
    app_env: str = "local"
    host: str = "0.0.0.0"
    port: int = 8000

    # 백엔드 연동
    backend_base_url: str = "http://localhost:8080"
    backend_api_key: str = ""

    # 외부 API
    kakao_rest_api_key: str = ""
    naver_client_id: str = ""
    naver_client_secret: str = ""

    # AWS S3
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "ap-northeast-2"
    s3_bucket: str = ""

    # 로깅
    log_level: str = "DEBUG"


settings = Settings()
