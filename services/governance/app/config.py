from pydantic import BaseModel
import os

class Settings(BaseModel):
    gov_port: int = int(os.getenv("GOV_PORT", "8003"))
    db_user: str = os.getenv("POSTGRES_USER", "govai")
    db_password: str = os.getenv("POSTGRES_PASSWORD", "govai")
    db_name: str = os.getenv("POSTGRES_DB", "govai")
    db_host: str = os.getenv("POSTGRES_HOST", "localhost")
    db_port: str = os.getenv("POSTGRES_PORT", "5432")
    default_confidence: float = float(os.getenv("POLICY_DEFAULT_CONFIDENCE", "0.25"))
    require_citations: bool = os.getenv("POLICY_REQUIRE_CITATIONS", "true").lower() == "true"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

settings = Settings()
