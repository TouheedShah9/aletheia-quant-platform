"""
Schema Validation — Pydantic models for data integrity
"""
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field, validator

class TranscriptRecord(BaseModel):
    id: str
    ticker: str = Field(..., min_length=1, max_length=10)
    company_name: Optional[str] = None
    market: str
    event_date: date
    ingestion_timestamp: datetime
    source: str
    word_count: int = Field(..., ge=0)
    has_qa_section: bool = False
    checksum: Optional[str] = None
    full_text: Optional[str] = None

    @validator('ticker')
    def ticker_uppercase(cls, v):
        return v.upper().strip()

class PriceRecord(BaseModel):
    id: str
    ticker: str
    trade_date: date
    adj_close: float = Field(..., gt=0)
    volume: int = Field(..., ge=0)
    ingestion_timestamp: datetime

class ENSScore(BaseModel):
    id: str
    transcript_id: str
    ticker: str
    ens_final: float = Field(..., ge=-1.0, le=1.0)
    tcs_score: Optional[float] = Field(None, ge=-1.0, le=1.0)

def validate_transcript(data: dict) -> bool:
    try:
        TranscriptRecord(**data)
        return True
    except Exception as e:
        print(f"Validation failed: {e}")
        return False