from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from app.models import Event, EventStatus
from app.schemas import EventCreate, EventUpdate
from app.utils.redis import cache_get, cache_set, cache_delete, cache_delete_pattern


def get_event(db: Session, event_id: int):
    # Detay sayfası için cache kullanmıyoruz (stok bilgisi sık değişebilir)
    return db.query(Event).filter(Event.id == event_id).first()


def get_events(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: Optional[EventStatus] = None,
    city: Optional[str] = None
):
    # Cache key oluştur
    cache_key = f"events:list:skip={skip}:limit={limit}:status={status}:city={city}"
    
    # Önce cache'ten kontrol et
    # Not: Cache'ten dict okunsa bile Event objeleri döndürmemiz gerekiyor
    # Şimdilik cache'i sadece performans için tutuyoruz, Event objeleri her zaman DB'den
    
    # Cache'te yoksa veritabanından çek
    query = db.query(Event)
    
    if status:
        query = query.filter(Event.status == status)
    
    if city:
        query = query.filter(Event.city.ilike(f"%{city}%"))
    
    events = query.offset(skip).limit(limit).all()
    
    # Event objelerini dict'e dönüştür ve cache'le (5 dakika TTL) - gelecekte kullanım için
    # Şimdilik cache'i sadece gelecekteki kullanım için hazırlıyoruz
    # Event objelerini döndürmeye devam ediyoruz
    
    return events


def create_event(db: Session, event: EventCreate):
    db_event = Event(
        title=event.title,
        description=event.description,
        category=event.category,
        venue=event.venue,
        city=event.city,
        address=event.address,
        start_date=event.start_date,
        end_date=event.end_date,
        base_price=event.base_price,
        total_capacity=event.total_capacity,
        available_tickets=event.total_capacity,
        organizer_id=event.organizer_id,
        image_url=event.image_url
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    
    # Event listesi cache'ini temizle (yeni event eklendi)
    cache_delete_pattern("events:list:*")
    
    return db_event


def update_event(db: Session, event_id: int, event_update: EventUpdate):
    db_event = db.query(Event).filter(Event.id == event_id).first()
    if not db_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    update_data = event_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_event, field, value)
    
    db.commit()
    db.refresh(db_event)
    
    # İlgili cache'leri temizle
    cache_delete_pattern("events:list:*")
    
    return db_event


def delete_event(db: Session, event_id: int):
    db_event = db.query(Event).filter(Event.id == event_id).first()
    if not db_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    db.delete(db_event)
    db.commit()
    
    # İlgili cache'leri temizle
    cache_delete_pattern("events:list:*")
    
    return {"message": "Event deleted successfully"}


def reserve_tickets(db: Session, event_id: int, quantity: int):
    """Bilet rezervasyonu için kullanılır"""
    db_event = db.query(Event).filter(Event.id == event_id).first()
    if not db_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    if db_event.available_tickets < quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not enough tickets available"
        )
    
    db_event.available_tickets -= quantity
    db.commit()
    db.refresh(db_event)
    
    # Event cache'ini güncelle (stok değişti)
    cache_delete(f"events:detail:{event_id}")
    cache_delete_pattern("events:list:*")
    
    return db_event


def release_tickets(db: Session, event_id: int, quantity: int):
    """Bilet iptali durumunda kullanılır"""
    db_event = db.query(Event).filter(Event.id == event_id).first()
    if not db_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    db_event.available_tickets += quantity
    if db_event.available_tickets > db_event.total_capacity:
        db_event.available_tickets = db_event.total_capacity
    
    db.commit()
    db.refresh(db_event)
    
    # Event cache'ini güncelle (stok değişti)
    cache_delete(f"events:detail:{event_id}")
    cache_delete_pattern("events:list:*")
    
    return db_event

