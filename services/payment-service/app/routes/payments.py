from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas import PaymentCreate, PaymentResponse, PaymentUpdate
from app.services import payment_service

router = APIRouter()


@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(payment: PaymentCreate, db: Session = Depends(get_db)):
    """Ödeme işlemi oluştur"""
    return await payment_service.create_payment(db, payment)


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(payment_id: int, db: Session = Depends(get_db)):
    """Ödeme bilgilerini getir"""
    payment = payment_service.get_payment(db, payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    return payment


@router.get("/number/{payment_number}", response_model=PaymentResponse)
async def get_payment_by_number(payment_number: str, db: Session = Depends(get_db)):
    """Ödeme numarası ile ödeme bilgilerini getir"""
    payment = payment_service.get_payment_by_number(db, payment_number)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    return payment


@router.get("/user/{user_id}", response_model=List[PaymentResponse])
async def get_user_payments(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Kullanıcının ödemelerini listele"""
    return payment_service.get_user_payments(db, user_id, skip=skip, limit=limit)


@router.put("/{payment_id}", response_model=PaymentResponse)
async def update_payment(
    payment_id: int,
    payment_update: PaymentUpdate,
    db: Session = Depends(get_db)
):
    """Ödeme bilgilerini güncelle"""
    return payment_service.update_payment(db, payment_id, payment_update)

