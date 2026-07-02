import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID

from app.core.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    doc_type = Column(String, nullable=False, index=True)  # document_type enum stored as string
    file_path = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    file_size_kb = Column(Integer, nullable=True)
    mime_type = Column(String, nullable=True)
    extracted_text = Column(Text, nullable=True)
    auto_tags = Column(JSONB, nullable=True)
    manual_tags = Column(ARRAY(String), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"), onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<Document(id={self.id}, title={self.title}, doc_type={self.doc_type})>"
