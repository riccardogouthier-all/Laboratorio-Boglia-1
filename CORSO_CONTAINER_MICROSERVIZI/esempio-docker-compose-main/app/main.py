from fastapi import FastAPI
from pydantic import BaseModel
from database import get_db
from models import Student
from sqlalchemy.orm import Session

app = FastAPI(
    title="Studenti API",
    description="API GET/POST per gestire studenti con PostgreSQL",
    version="1.0.0"
)

class StudentCreate(BaseModel):
    nome: str
    corso: str
    matricola: str

@app.get("/studenti")
def get_studenti():
    db: Session = get_db()
    studenti = db.query(Student).all()
    return studenti

@app.post("/studenti")
def create_studente(studente: StudentCreate):
    db: Session = get_db()
    nuovo = Student(
        nome=studente.nome,
        corso=studente.corso,
        matricola=studente.matricola
    )
    db.add(nuovo)
    db.commit()
    db.refresh(nuovo)
    return nuovo

