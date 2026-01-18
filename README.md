# Etkinlik Bilet Satış Sistemi

## Mikroservis Mimarisi ile Geliştirilmiş Bilet Satış Platformu



---

##  Proje Hakkında

Bu proje, **BLM5126 İleri Yazılım Mimarisi** dersi kapsamında geliştirilmiş bir mikroservis mimarisi örneğidir. Sistem, konser, tiyatro, spor müsabakaları ve benzeri etkinlikler için çevrimiçi bilet satışı yapılmasını sağlar.

### Özellikler

- ✅ 6 bağımsız mikroservis
- ✅ Her servis için ayrı PostgreSQL veritabanı
- ✅ RabbitMQ ile asenkron mesajlaşma
- ✅ Redis ile rate limiting
- ✅ JWT tabanlı authentication
- ✅ Role-Based Access Control (RBAC)
- ✅ Docker Compose ile containerization
- ✅ Modern Bootstrap 5 frontend

---

##  Mimari Yapı

### Sistem Diyagramı

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend  │────▶│ API Gateway │────▶│   Services  │
│  (HTML/JS)  │     │  (Port 8000)│     │             │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│    User     │    │    Event    │    │   Ticket    │
│   Service   │    │   Service   │    │   Service   │
│ (Port 8001) │    │ (Port 8002) │    │ (Port 8003) │
└─────────────┘    └─────────────┘    └─────────────┘
        │                  │                  │
        ▼                  ▼                  ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Payment   │    │ Notification│    │   RabbitMQ  │
│   Service   │    │   Service   │◀───│   (MQ)      │
│ (Port 8004) │    │ (Port 8005) │    └─────────────┘
└─────────────┘    └─────────────┘
        │                  │
        └────────┬─────────┘
                 ▼
         ┌─────────────┐
         │    Redis    │
         │   (Cache)   │
         └─────────────┘
```

### Mikroservisler

| Servis | Port | Açıklama | Veritabanı |
|--------|------|----------|------------|
| **API Gateway** | 8000 | Merkezi giriş noktası, routing, auth | - |
| **User Service** | 8001 | Kullanıcı yönetimi, authentication | userdb |
| **Event Service** | 8002 | Etkinlik yönetimi | eventdb |
| **Ticket Service** | 8003 | Bilet rezervasyonu ve satış | ticketdb |
| **Payment Service** | 8004 | Ödeme işlemleri | paymentdb |
| **Notification Service** | 8005 | Bildirim yönetimi | notificationdb |

### Teknoloji Stack

| Kategori | Teknoloji | Versiyon |
|----------|-----------|----------|
| Backend Framework | FastAPI | 0.104.1 |
| Programlama Dili | Python | 3.11 |
| Veritabanı | PostgreSQL | 15 |
| Message Queue | RabbitMQ | 3.x |
| Cache | Redis | 7.x |
| Containerization | Docker & Compose | Latest |
| Authentication | JWT (python-jose) | 3.3.0 |
| ORM | SQLAlchemy | 2.0.23 |
| Frontend | Bootstrap | 5.3.0 |

---

##  Kurulum ve Çalıştırma

### Gereksinimler

- Docker ve Docker Compose
- En az 4GB RAM
- Boş portlar: 8000-8005, 5432-5436, 6379, 5672, 15672

### Hızlı Başlangıç

```bash
# 1. Projeyi klonlayın
git clone https://github.com/Yusufycelik/-YM-2025-Final_Project.git
cd -YM-2025-Final_Project

# 2. Tüm servisleri başlatın
docker-compose up -d --build

# 3. Servislerin durumunu kontrol edin
docker-compose ps

# 4. Frontend'i başlatın (ayrı bir terminal)
cd frontend
python -m http.server 5500
```

### Erişim Adresleri

| Servis | URL | Açıklama |
|--------|-----|----------|
| Frontend | http://localhost:8080 | Web arayüzü |
| API Gateway | http://localhost:8000 | API endpoint |
| API Docs | http://localhost:8000/docs | Swagger UI |
| RabbitMQ | http://localhost:15672 | Management UI (guest/guest) |

---

## 👤 Admin Kullanıcı Oluşturma

Sistem ilk kurulumda admin kullanıcısı içermez. Admin kullanıcısı oluşturmak için aşağıdaki adımları izleyin:

### Yöntem 1: Script ile (Önerilen)

```bash
# User service container'ı içinde admin oluşturma scripti çalıştır
docker exec -it user-service python scripts/create_admin.py
```

Bu komut varsayılan olarak aşağıdaki admin kullanıcısını oluşturur:
- **E-posta**: admin@example.com
- **Kullanıcı Adı**: admin
- **Şifre**: admin123

### Yöntem 2: Özel Bilgilerle Admin Oluşturma

```bash
# Ortam değişkenleri ile özel admin bilgileri belirle
docker exec -it -e ADMIN_EMAIL="benim@email.com" \
  -e ADMIN_USERNAME="adminuser" \
  -e ADMIN_PASSWORD="guclu_sifre_123" \
  -e ADMIN_FULL_NAME="Admin Adı Soyadı" \
  user-service python scripts/create_admin.py
```

### Yöntem 3: Mevcut Kullanıcıyı Admin Yapma

Önce normal kayıt ile bir kullanıcı oluşturun, ardından veritabanından rolünü güncelleyin:

```bash
# User veritabanına bağlan
docker exec -it user-db psql -U postgres -d userdb

# Kullanıcının rolünü admin yap
UPDATE users SET role = 'admin' WHERE username = 'kullanici_adi';

# Çıkış
\q
```

### Admin Yetkileri

Admin kullanıcısı oluşturulduktan sonra:
-  Tüm kullanıcıları görüntüleme ve rol değiştirme
-  Etkinlik oluşturma, düzenleme ve silme
-  Kullanıcılara bilet atama ve bilet silme
-  Admin ve organizer'lar bilet **satın alamaz** (sadece atayabilir)

---

##  API Endpoints

### Authentication

```http
POST /api/v1/auth/register    # Kullanıcı kaydı
POST /api/v1/auth/login       # Kullanıcı girişi
```

### Users (Admin)

```http
GET  /api/v1/users/           # Tüm kullanıcıları listele
GET  /api/v1/users/{id}       # Kullanıcı detayı
PUT  /api/v1/users/{id}       # Kullanıcı güncelle (rol dahil)
```

### Events

```http
GET    /api/v1/events/        # Etkinlikleri listele
GET    /api/v1/events/{id}    # Etkinlik detayı
POST   /api/v1/events/        # Etkinlik oluştur (Admin/Organizer)
PUT    /api/v1/events/{id}    # Etkinlik güncelle
DELETE /api/v1/events/{id}    # Etkinlik sil
```

### Tickets

```http
GET    /api/v1/tickets/              # Kullanıcının biletleri
POST   /api/v1/tickets/              # Bilet satın al (User)
DELETE /api/v1/tickets/{id}          # Bilet iptal
POST   /api/v1/tickets/admin/assign  # Bilet ata (Admin)
DELETE /api/v1/tickets/admin/{id}    # Bilet sil (Admin)
```

### Payments

```http
POST /api/v1/payments/        # Ödeme yap
GET  /api/v1/payments/{id}    # Ödeme detayı
```

---

##  Kullanıcı Rolleri

| Rol | Yetkiler |
|-----|----------|
| **User** | Etkinlik görüntüleme, bilet satın alma, kendi biletlerini görme |
| **Organizer** | User yetkileri + kendi etkinliklerini oluşturma/düzenleme |
| **Admin** | Tüm yetkiler + kullanıcı yönetimi + bilet atama/silme |

### Rol Kısıtlamaları

- Admin ve Organizer **bilet satın alamaz**
- Organizer sadece **kendi etkinliklerini** düzenleyebilir
- Sadece Admin **kullanıcı rollerini** değiştirebilir

---

##  Proje Yapısı

```
YM-2025-Final_Project/
├── api-gateway/                 # API Gateway servisi
│   ├── app/
│   │   ├── routes/
│   │   ├── utils/
│   │   ├── config.py
│   │   └── main.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── services/
│   ├── user-service/           # Kullanıcı servisi
│   ├── event-service/          # Etkinlik servisi
│   ├── ticket-service/         # Bilet servisi
│   ├── payment-service/        # Ödeme servisi
│   └── notification-service/   # Bildirim servisi
│
├── frontend/
│   └── index.html              # Web arayüzü
│
├── docs/
│   └── ARCHITECTURE.md         # Mimari dokümantasyon
│
├── docker-compose.yml          # Container orchestration
├── requirements.txt            # Python bağımlılıkları
└── README.md                   # Bu dosya
```

---

##  Geliştirme

### Servisleri Yeniden Başlatma

```bash
# Tek bir servisi yeniden başlat
docker-compose restart user-service

# Servisi rebuild et
docker-compose up -d --build user-service
```

### Logları Görüntüleme

```bash
# Tüm loglar
docker-compose logs -f

# Belirli servis
docker-compose logs -f user-service
```

### Veritabanına Bağlanma

```bash
# User veritabanı
docker exec -it user-db psql -U postgres -d userdb
```

### Redis CLI

```bash
docker exec -it redis redis-cli
KEYS rate_limit:*
```

---

##  Güvenlik Özellikleri

- **JWT Authentication**: Access token (30dk) ve Refresh token (7 gün)
- **Password Hashing**: bcrypt (12 rounds)
- **Rate Limiting**: Redis tabanlı (5 istek/dakika/IP)
- **CORS**: Yapılandırılmış origin listesi
- **Input Validation**: Pydantic schema validation

---

## Servisler Arası İletişim

### Senkron (HTTP/REST)
- Frontend → API Gateway → Servisler
- Ticket Service → Event Service (stok kontrolü)

### Asenkron (RabbitMQ)
| Event | Publisher | Consumer |
|-------|-----------|----------|
| ticket.reserved | Ticket Service | Event Service, Notification Service |
| ticket.cancelled | Ticket Service | Event Service, Notification Service |
| payment.completed | Payment Service | Ticket Service, Notification Service |

---

##  Sorun Giderme

### Servis başlamıyor
```bash
docker-compose logs [service-name]
```

### Rate limit hatası
```bash
# Redis'te rate limit key'lerini temizle
docker exec -it redis redis-cli FLUSHALL
```

### Veritabanı bağlantı hatası
```bash
# Veritabanlarının hazır olmasını bekleyin
docker-compose up -d user-db event-db ticket-db payment-db notification-db
sleep 15
docker-compose up -d
```

### Port çakışması
```bash
# Kullanılan portları kontrol et
netstat -ano | findstr :8000
```

---

##  Lisans

Bu proje **BLM5126 İleri Yazılım Mimarisi** dersi kapsamında eğitim amaçlı geliştirilmiştir.

---

##  Geliştirici

**Yusuf Yemliha Çelik**  
Yıldız Teknik Üniversitesi  
BLM5126 İleri Yazılım Mimarisi - 2025-2026 Güz Dönem Projesi

---

##  Bağlantılar

- **GitHub**: https://github.com/Yusufycelik/-YM-2025-Final_Project
- **API Docs**: http://localhost:8000/docs
- **RabbitMQ Management**: http://localhost:15672
- **Mimari Dokümantasyon**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

>  **Not**: Bu sistem demo amaçlıdır. Production ortamında ek güvenlik önlemleri, HTTPS, ve ölçeklenebilirlik iyileştirmeleri yapılmalıdır.

video linki:https://youtu.be/yiy8VsPmtyY