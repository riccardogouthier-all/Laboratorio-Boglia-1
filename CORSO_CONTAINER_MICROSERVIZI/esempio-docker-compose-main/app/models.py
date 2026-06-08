from sqlalchemy import Column, Integer, String
from database import Base

class Student(Base):
    __tablename__ = "studenti"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    corso = Column(String, nullable=False)
    matricola = Column(String, unique=True, nullable=False)

