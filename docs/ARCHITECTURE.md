# Etkinlik Bilet Satış Sistemi
## Mikroservis Mimarisi Proje Raporu

**Ders:** BLM5126 İleri Yazılım Mimarisi  
**Dönem:** 2025-2026 Güz Yarıyılı  
**Tarih:** Ocak 2026

---

## İçindekiler

1. [Giriş ve Konu Tanımı](#1-giriş-ve-konu-tanımı)
2. [İşlevsel Gereksinimler (Senaryolar)](#2-işlevsel-gereksinimler-senaryolar)
3. [İşlevsel Olmayan Gereksinimler](#3-işlevsel-olmayan-gereksinimler)
4. [Analiz Modeli](#4-analiz-modeli)
5. [Tasarım Modeli](#5-tasarım-modeli)
6. [Mimari Tasarım](#6-mimari-tasarım)
7. [Mikroservisler](#7-mikroservisler)
8. [Veri Modeli](#8-veri-modeli)
9. [Servisler Arası İletişim](#9-servisler-arası-iletişim)
10. [Güvenlik Mimarisi](#10-güvenlik-mimarisi)
11. [Deployment ve Altyapı](#11-deployment-ve-altyapı)
12. [Çözümün Değerlendirilmesi ve Tartışması](#12-çözümün-değerlendirilmesi-ve-tartışması)
13. [İyileştirme Önerileri](#13-iyileştirme-önerileri)
14. [Sonuç](#14-sonuç)

---

## 1. Giriş ve Konu Tanımı

### 1.1. Projenin Amacı

Bu proje, mikroservis mimarisine dayalı bir **Etkinlik Bilet Satış Sistemi** geliştirmeyi amaçlamaktadır. Sistem, konser, tiyatro, spor müsabakaları ve benzeri etkinlikler için çevrimiçi bilet satışı yapılmasını sağlar. Proje, modern yazılım mimarisi prensiplerini uygulayarak ölçeklenebilir, dayanıklı ve yüksek performanslı bir sistem ortaya koymayı hedeflemektedir.

### 1.2. Problem Tanımı

Geleneksel monolitik bilet satış sistemleri aşağıdaki problemlerle karşı karşıyadır:

- **Ölçeklenebilirlik sorunları**: Yoğun dönemlerde (popüler etkinlik satışları) sistem tıkanabilir
- **Tek hata noktası**: Bir modüldeki hata tüm sistemi çökertebilir
- **Bakım zorluğu**: Büyük kod tabanlarında değişiklik yapmak risklidir
- **Teknoloji bağımlılığı**: Tüm sistem tek bir teknoloji stack'ine bağımlıdır
- **Bağımsız deployment imkansızlığı**: Her değişiklik için tüm sistemin yeniden deploy edilmesi gerekir

### 1.3. Önerilen Çözüm

Mikroservis mimarisi kullanılarak geliştirilen bu sistem, yukarıdaki problemleri çözmek için tasarlanmıştır:

- **6 bağımsız mikroservis** ile modüler yapı
- **Asenkron mesajlaşma** ile gevşek bağlı (loosely coupled) servisler
- **Her servis için ayrı veritabanı** ile veri izolasyonu
- **Container tabanlı deployment** ile taşınabilirlik
- **API Gateway** ile merkezi giriş noktası

### 1.4. Kapsam

Sistem aşağıdaki temel işlevleri kapsamaktadır:

- Kullanıcı kaydı, girişi ve profil yönetimi
- Etkinlik oluşturma, listeleme ve yönetimi
- Bilet rezervasyonu ve satın alma
- Ödeme işlemleri (simüle edilmiş)
- E-posta/SMS bildirimleri (simüle edilmiş)
- Admin ve organizatör panelleri

---

## 2. İşlevsel Gereksinimler (Senaryolar)

### 2.1. Aktörler

| Aktör | Açıklama |
|-------|----------|
| **Ziyaretçi** | Sisteme kayıt olmamış kullanıcı |
| **Kullanıcı (User)** | Sisteme kayıtlı, bilet satın alabilen kullanıcı |
| **Organizatör (Organizer)** | Etkinlik oluşturabilen ve yönetebilen kullanıcı |
| **Yönetici (Admin)** | Tüm sistemi yönetebilen, kullanıcı rollerini değiştirebilen kullanıcı |

### 2.2. Kullanım Senaryoları

#### Senaryo 1: Kullanıcı Kaydı
**Aktör:** Ziyaretçi  
**Ön koşul:** Kullanıcı sisteme kayıtlı değil  
**Ana Akış:**
1. Ziyaretçi kayıt formunu doldurur (e-posta, kullanıcı adı, şifre, ad-soyad)
2. Sistem e-posta ve kullanıcı adının benzersiz olduğunu kontrol eder
3. Sistem şifreyi hash'leyerek veritabanına kaydeder
4. Sistem kullanıcıya başarılı kayıt mesajı gösterir

**Alternatif Akış:**
- 2a. E-posta veya kullanıcı adı zaten kayıtlıysa hata mesajı gösterilir
- 2b. Aynı IP'den 5 dakikada 5'ten fazla kayıt denemesi yapılırsa rate limit hatası döner

#### Senaryo 2: Kullanıcı Girişi
**Aktör:** Kayıtlı Kullanıcı  
**Ön koşul:** Kullanıcı sisteme kayıtlı  
**Ana Akış:**
1. Kullanıcı kullanıcı adı ve şifresini girer
2. Sistem kimlik bilgilerini doğrular
3. Sistem JWT access token ve refresh token üretir
4. Kullanıcı ana sayfaya yönlendirilir

**Alternatif Akış:**
- 2a. Kimlik bilgileri yanlışsa hata mesajı gösterilir
- 2b. Aynı IP'den 1 dakikada 5'ten fazla giriş denemesi yapılırsa rate limit hatası döner (Redis)

#### Senaryo 3: Etkinlik Oluşturma
**Aktör:** Organizatör veya Admin  
**Ön koşul:** Kullanıcı giriş yapmış ve yetkili role sahip  
**Ana Akış:**
1. Organizatör etkinlik formunu doldurur (başlık, açıklama, kategori, mekan, tarih, fiyat, kapasite)
2. Sistem form verilerini doğrular
3. Sistem etkinliği veritabanına kaydeder
4. Sistem başarılı mesajı gösterir ve etkinlik listesini günceller

**Alternatif Akış:**
- 2a. Gerekli alanlar eksikse hata mesajı gösterilir
- 3a. Organizatör sadece kendi etkinliklerini düzenleyebilir, Admin tüm etkinlikleri düzenleyebilir

#### Senaryo 4: Bilet Satın Alma
**Aktör:** Kullanıcı (User rolü)  
**Ön koşul:** Kullanıcı giriş yapmış ve User rolüne sahip  
**Ana Akış:**
1. Kullanıcı etkinlik listesinden bir etkinlik seçer
2. Kullanıcı almak istediği bilet adedini belirler
3. Sistem stok kontrolü yapar (Event Service ile senkron iletişim)
4. Sistem bilet rezervasyonu oluşturur (Ticket Service)
5. Kullanıcı ödeme bilgilerini girer
6. Sistem ödemeyi işler (Payment Service)
7. Sistem bilet durumunu "confirmed" olarak günceller
8. Sistem RabbitMQ üzerinden Event Service'e stok güncelleme mesajı gönderir
9. Sistem RabbitMQ üzerinden Notification Service'e bildirim mesajı gönderir
10. Kullanıcıya e-posta bildirimi gönderilir

**Alternatif Akış:**
- 3a. Yeterli stok yoksa hata mesajı gösterilir
- 6a. Ödeme başarısız olursa bilet rezervasyonu iptal edilir
- 4a. Admin veya Organizer rolündeki kullanıcılar bilet satın alamaz

#### Senaryo 5: Bilet İptali
**Aktör:** Kullanıcı veya Admin  
**Ön koşul:** Kullanıcının aktif bileti var  
**Ana Akış:**
1. Kullanıcı biletlerim sayfasından iptal edilecek bileti seçer
2. Sistem onay ister
3. Kullanıcı onaylar
4. Sistem bilet durumunu "cancelled" olarak günceller
5. Sistem RabbitMQ üzerinden Event Service'e stok geri verme mesajı gönderir
6. Kullanıcıya iptal bildirimi gönderilir

#### Senaryo 6: Kullanıcı Yönetimi (Admin)
**Aktör:** Admin  
**Ön koşul:** Kullanıcı Admin rolüne sahip  
**Ana Akış:**
1. Admin kullanıcı yönetimi panelini açar
2. Sistem tüm kullanıcıları listeler
3. Admin bir kullanıcının rolünü değiştirir (user, organizer, admin)
4. Sistem değişikliği kaydeder

#### Senaryo 7: Bilet Atama (Admin)
**Aktör:** Admin  
**Ön koşul:** Kullanıcı Admin rolüne sahip  
**Ana Akış:**
1. Admin bilet yönetimi panelini açar
2. Admin etkinlik ve kullanıcı seçer (sadece User rolündeki kullanıcılara)
3. Admin bilet adedini belirler
4. Sistem bileti kullanıcıya atar
5. Sistem stok günceller

---

## 3. İşlevsel Olmayan Gereksinimler

### 3.1. Performans Gereksinimleri

| Gereksinim | Hedef Değer | Açıklama |
|------------|-------------|----------|
| API Yanıt Süresi | < 500ms | Normal yük altında ortalama yanıt süresi |
| Veritabanı Sorgusu | < 100ms | Optimize edilmiş sorgular için |
| Eşzamanlı Kullanıcı | 1000+ | Sistem aynı anda 1000 kullanıcıyı desteklemeli |
| Sayfa Yüklenme | < 3 saniye | Frontend yüklenme süresi |
| Throughput | 100 req/sec | Saniyede işlenebilecek istek sayısı |

### 3.2. Güvenlik Gereksinimleri

| Gereksinim | Uygulama |
|------------|----------|
| Kimlik Doğrulama | JWT (JSON Web Tokens) tabanlı authentication |
| Yetkilendirme | Role-Based Access Control (RBAC) - user, admin, organizer |
| Şifre Güvenliği | bcrypt ile hash'leme (12 rounds) |
| Token Süresi | Access token: 30 dakika, Refresh token: 7 gün |
| Rate Limiting | Login: 5 deneme/dakika/IP, Register: 5 deneme/dakika/IP |
| CORS | Sadece izin verilen origin'lerden istek kabul edilir |
| SQL Injection | SQLAlchemy ORM ile parametreli sorgular |
| XSS Koruması | FastAPI otomatik input validation |

### 3.3. Ölçeklenebilirlik Gereksinimleri

| Gereksinim | Açıklama |
|------------|----------|
| Yatay Ölçekleme | Her servis bağımsız olarak ölçeklendirilebilir |
| Database per Service | Her mikroservis kendi veritabanına sahip |
| Stateless Servisler | Servisler durum bilgisi tutmaz (session Redis'te) |
| Container Orchestration | Docker Compose ile orkestrasyon |
| Load Balancing | API Gateway üzerinden yük dağıtımı |

### 3.4. Kullanılabilirlik Gereksinimleri

| Gereksinim | Hedef Değer |
|------------|-------------|
| Uptime | %99.9 (yıllık maksimum 8.76 saat kesinti) |
| MTTR | < 30 dakika (Mean Time To Recovery) |
| Health Checks | Her servis için `/health` endpoint |
| Graceful Degradation | Bir servis çökerse diğerleri çalışmaya devam eder |

### 3.5. Bakım Kolaylığı Gereksinimleri

| Gereksinim | Uygulama |
|------------|----------|
| Kod Standartları | PEP 8 (Python), Type hints |
| Dokümantasyon | Swagger/OpenAPI otomatik API dokümantasyonu |
| Modülerlik | Her servis bağımsız geliştirilebilir |
| Versiyon Kontrolü | Git ile kaynak kod yönetimi |
| Environment Variables | Konfigürasyon environment variable'larla yönetilir |

### 3.6. Taşınabilirlik Gereksinimleri

| Gereksinim | Uygulama |
|------------|----------|
| Container | Docker ile containerization |
| Platform Bağımsızlığı | Linux, Windows, macOS üzerinde çalışır |
| Cloud Ready | AWS, GCP, Azure'a deploy edilebilir |
| Portable Configuration | Docker Compose ile tek komutla kurulum |

---

## 4. Analiz Modeli

### 4.1. Use Case Diyagramı 

```
                    +------------------------------------------+
                    |     Etkinlik Bilet Satış Sistemi         |
                    +------------------------------------------+
                    |                                          |
    Ziyaretçi ----->|  [ Kayıt Ol ]                           |
                    |  [ Etkinlikleri Görüntüle ]             |
                    |                                          |
    Kullanıcı ----->|  [ Giriş Yap ]                          |
      (User)        |  [ Profil Görüntüle ]                   |
                    |  [ Bilet Satın Al ]                     |
                    |  [ Biletlerimi Görüntüle ]              |
                    |  [ Bilet İptal Et ]                     |
                    |                                          |
   Organizatör ---->|  [ Etkinlik Oluştur ]                   |
   (Organizer)      |  [ Etkinlik Düzenle ]                   |
                    |  [ Etkinlik Sil ]                       |
                    |  [ Kendi Etkinliklerini Yönet ]         |
                    |                                          |
    Yönetici ------>|  [ Tüm Etkinlikleri Yönet ]             |
     (Admin)        |  [ Kullanıcı Rollerini Değiştir ]       |
                    |  [ Kullanıcılara Bilet Ata ]            |
                    |  [ Bilet Sil ]                          |
                    |  [ Tüm Kullanıcıları Görüntüle ]        |
                    |                                          |
                    +------------------------------------------+
```

### 4.2. Aktör-Use Case İlişkileri

| Aktör | Use Case'ler |
|-------|--------------|
| Ziyaretçi | Kayıt Ol, Etkinlikleri Görüntüle |
| Kullanıcı | Giriş Yap, Profil Görüntüle, Bilet Satın Al, Biletlerimi Görüntüle, Bilet İptal Et |
| Organizatör | Kullanıcı use case'leri + Etkinlik CRUD (kendi etkinlikleri) |
| Admin | Tüm use case'ler + Kullanıcı Yönetimi + Bilet Yönetimi |

### 4.3. Domain Model (Kavramsal Sınıf Diyagramı)

```
+----------------+       +----------------+       +----------------+
|     User       |       |     Event      |       |    Ticket      |
+----------------+       +----------------+       +----------------+
| - id           |       | - id           |       | - id           |
| - email        |       | - title        |       | - ticket_number|
| - username     |       | - description  |       | - quantity     |
| - password     |       | - category     |       | - unit_price   |
| - full_name    |       | - venue        |       | - total_price  |
| - phone        |       | - city         |       | - status       |
| - role         |       | - start_date   |       | - reserved_at  |
| - is_active    |       | - end_date     |       | - confirmed_at |
+----------------+       | - base_price   |       +----------------+
        |                | - capacity     |              |
        |                | - available    |              |
        |                | - organizer_id |              |
        |                +----------------+              |
        |                       |                        |
        |     organizes         |         belongs to     |
        +------------>----------+----------<-------------+
        |                       |                        |
        |     purchases         |                        |
        +--------------------------------------------->--+
        |                                                |
        |                +----------------+              |
        |                |    Payment     |              |
        |                +----------------+              |
        |                | - id           |              |
        |                | - amount       |              |
        +--------------->| - status       |<-------------+
           pays          | - method       |    for
                         | - ticket_id    |
                         +----------------+
                                |
                                | triggers
                                v
                         +----------------+
                         | Notification   |
                         +----------------+
                         | - id           |
                         | - user_id      |
                         | - type         |
                         | - message      |
                         | - status       |
                         +----------------+
```

### 4.4. Aktivite Diyagramı: Bilet Satın Alma Akışı

```
                    [Başlangıç]
                         |
                         v
                +------------------+
                | Etkinlik Seç     |
                +------------------+
                         |
                         v
                +------------------+
                | Bilet Adedi Gir  |
                +------------------+
                         |
                         v
                +------------------+
                | Stok Kontrolü    |
                +------------------+
                         |
            +------------+------------+
            |                         |
            v                         v
    [Stok Yeterli]            [Stok Yetersiz]
            |                         |
            v                         v
    +------------------+      +------------------+
    | Bilet Rezerve Et |      | Hata Mesajı      |
    +------------------+      +------------------+
            |                         |
            v                         v
    +------------------+           [Son]
    | Ödeme Bilgisi Al |
    +------------------+
            |
            v
    +------------------+
    | Ödeme İşle       |
    +------------------+
            |
    +-------+-------+
    |               |
    v               v
[Başarılı]     [Başarısız]
    |               |
    v               v
+----------+  +-------------+
|Bilet Onayla| |Rezervasyon  |
|Stok Düş   | |İptal Et     |
+----------+  +-------------+
    |               |
    v               v
+----------+  +-------------+
|Bildirim  |  |Hata Mesajı  |
|Gönder    |  |Göster       |
+----------+  +-------------+
    |               |
    v               v
  [Son]           [Son]
```

---

## 5. Tasarım Modeli

### 5.1. Component Diyagramı

```
+------------------------------------------------------------------+
|                        <<subsystem>>                              |
|                      Etkinlik Bilet Sistemi                       |
+------------------------------------------------------------------+
|                                                                   |
|  +---------------+     +-----------------+     +---------------+  |
|  |  <<component>>|     |  <<component>>  |     | <<component>> |  |
|  |   Frontend    |---->|   API Gateway   |---->|  User Service |  |
|  |   (HTML/JS)   |     |   (Port 8000)   |     |  (Port 8001)  |  |
|  +---------------+     +-----------------+     +---------------+  |
|                               |                       |           |
|                               |              +--------+--------+  |
|                               |              |                 |  |
|                               v              v                 v  |
|                        +-------------+ +-------------+ +----------+
|                        |<<component>>| |<<component>>| |<<infra>> |
|                        |Event Service| |Ticket Svc   | |PostgreSQL|
|                        |(Port 8002)  | |(Port 8003)  | |(userdb)  |
|                        +-------------+ +-------------+ +----------+
|                               |              |                    |
|                               v              v                    |
|                        +-------------+ +-------------+            |
|                        |<<component>>| |<<component>>|            |
|                        |Payment Svc  | |Notif. Svc   |            |
|                        |(Port 8004)  | |(Port 8005)  |            |
|                        +-------------+ +-------------+            |
|                               |              |                    |
|                               v              v                    |
|  +---------------+     +-----------------+     +---------------+  |
|  |  <<infra>>    |     |   <<infra>>     |     |  <<infra>>    |  |
|  |    Redis      |<----|   RabbitMQ      |     |  PostgreSQL   |  |
|  | (Port 6379)   |     | (Port 5672)     |     | (5432-5436)   |  |
|  +---------------+     +-----------------+     +---------------+  |
|                                                                   |
+------------------------------------------------------------------+
```

### 5.2. Sequence Diyagramı: Bilet Satın Alma

```
Frontend    API Gateway    User Svc    Event Svc    Ticket Svc    Payment Svc    RabbitMQ    Notif Svc
    |            |            |            |             |              |            |           |
    |---(1) POST /tickets---->|            |             |              |            |           |
    |            |---(2) Verify JWT-------->|             |              |            |           |
    |            |<---(3) User Info---------|             |              |            |           |
    |            |---(4) POST /tickets----->|             |              |            |           |
    |            |            |             |<--(5) GET event stock-----|              |            |
    |            |            |             |---(6) Stock info-------->|              |            |
    |            |            |             |<--(7) Create ticket------|              |            |
    |            |            |             |             |              |            |           |
    |            |            |             |---(8) Publish ticket.reserved---------->|           |
    |            |            |             |             |              |            |           |
    |            |            |             |             |<--(9) Update stock--------|           |
    |            |            |             |             |              |            |           |
    |<---(10) Ticket Created--|             |             |              |            |           |
    |            |            |             |             |              |            |           |
    |---(11) POST /payments-->|             |             |              |            |           |
    |            |---(12) Process payment---------------->|              |            |           |
    |            |            |             |             |<--(13) Update ticket status            |
    |            |            |             |             |              |            |           |
    |            |            |             |             |---(14) Publish payment.completed------>|
    |            |            |             |             |              |            |           |
    |            |            |             |             |              |            |<-(15) Consume
    |            |            |             |             |              |            |   Send Email
    |<---(16) Payment Success-|             |             |              |            |           |
    |            |            |             |             |              |            |           |
```

### 5.3. Deployment Diyagramı

```
+------------------------------------------------------------------+
|                      <<execution environment>>                     |
|                         Docker Host                                |
+------------------------------------------------------------------+
|                                                                    |
|  +------------------------+    +------------------------+          |
|  | <<container>>          |    | <<container>>          |          |
|  | api-gateway            |    | user-service           |          |
|  | Port: 8000             |    | Port: 8001             |          |
|  | Image: python:3.11-slim|    | Image: python:3.11-slim|          |
|  +------------------------+    +------------------------+          |
|                                         |                          |
|  +------------------------+    +------------------------+          |
|  | <<container>>          |    | <<container>>          |          |
|  | event-service          |    | ticket-service         |          |
|  | Port: 8002             |    | Port: 8003             |          |
|  | Image: python:3.11-slim|    | Image: python:3.11-slim|          |
|  +------------------------+    +------------------------+          |
|                                                                    |
|  +------------------------+    +------------------------+          |
|  | <<container>>          |    | <<container>>          |          |
|  | payment-service        |    | notification-service   |          |
|  | Port: 8004             |    | Port: 8005             |          |
|  | Image: python:3.11-slim|    | Image: python:3.11-slim|          |
|  +------------------------+    +------------------------+          |
|                                                                    |
|  +------------------------+    +------------------------+          |
|  | <<container>>          |    | <<container>>          |          |
|  | postgres (x5)          |    | redis                  |          |
|  | Ports: 5432-5436       |    | Port: 6379             |          |
|  | Image: postgres:15     |    | Image: redis:7-alpine  |          |
|  +------------------------+    +------------------------+          |
|                                                                    |
|  +------------------------+                                        |
|  | <<container>>          |                                        |
|  | rabbitmq               |                                        |
|  | Ports: 5672, 15672     |                                        |
|  | Image: rabbitmq:3-mgmt |                                        |
|  +------------------------+                                        |
|                                                                    |
+------------------------------------------------------------------+
|                    <<network>>                                     |
|              microservices-network (bridge)                        |
+------------------------------------------------------------------+
```

### 5.4. Class Diyagramı: User Service

```
+----------------------------------+
|           <<entity>>             |
|             User                 |
+----------------------------------+
| - id: Integer (PK)               |
| - email: String (unique)         |
| - username: String (unique)      |
| - hashed_password: String        |
| - full_name: String              |
| - phone: String (nullable)       |
| - is_active: Boolean             |
| - is_verified: Boolean           |
| - role: UserRole (Enum)          |
| - created_at: DateTime           |
| - updated_at: DateTime           |
+----------------------------------+
| + verify_password(): Boolean     |
| + set_password(): void           |
+----------------------------------+

+----------------------------------+
|           <<enum>>               |
|           UserRole               |
+----------------------------------+
| USER                             |
| ADMIN                            |
| ORGANIZER                        |
+----------------------------------+

+----------------------------------+
|         <<service>>              |
|         UserService              |
+----------------------------------+
| + create_user()                  |
| + get_user_by_email()            |
| + get_user_by_username()         |
| + authenticate_user()            |
| + update_user()                  |
+----------------------------------+

+----------------------------------+
|          <<utility>>             |
|           AuthUtils              |
+----------------------------------+
| + create_access_token()          |
| + create_refresh_token()         |
| + verify_password()              |
| + get_password_hash()            |
+----------------------------------+
```

---

## 6. Mimari Tasarım

### 6.1. Mimari Stil: Mikroservis Mimarisi

Projede **Mikroservis Mimarisi** tercih edilmiştir. Bu mimari stilin seçilme nedenleri:

1. **Bağımsız Deployment**: Her servis ayrı ayrı deploy edilebilir
2. **Teknoloji Çeşitliliği**: Her servis farklı teknoloji kullanabilir
3. **Ölçeklenebilirlik**: Yoğun kullanılan servisler bağımsız ölçeklenir
4. **Hata İzolasyonu**: Bir servisin çökmesi diğerlerini etkilemez
5. **Takım Organizasyonu**: Farklı takımlar farklı servisleri geliştirebilir

### 6.2. Mimari Desenler (Patterns)

| Desen | Uygulama Yeri | Açıklama |
|-------|---------------|----------|
| **API Gateway** | api-gateway | Tüm isteklerin tek giriş noktası |
| **Database per Service** | Her servis | Her servis kendi DB'sine sahip |
| **Event-Driven** | RabbitMQ | Asenkron mesajlaşma ile gevşek bağlılık |
| **CQRS (kısmi)** | Event Service | Okuma ve yazma işlemleri ayrı |
| **Repository Pattern** | Tüm servisler | Veri erişim katmanı soyutlaması |
| **Saga Pattern (basit)** | Ticket-Payment | Dağıtık transaction yönetimi |

### 6.3. Katmanlı Mimari (Her Servis İçin)

```
+------------------------------------------+
|            Presentation Layer            |
|         (Routes / Controllers)           |
+------------------------------------------+
|            Business Layer                |
|             (Services)                   |
+------------------------------------------+
|            Data Access Layer             |
|        (Models / Repositories)           |
+------------------------------------------+
|            Infrastructure Layer          |
|    (Database, RabbitMQ, Redis, Utils)    |
+------------------------------------------+
```

### 6.4. Servis Bağımlılık Haritası

```
                    +----------------+
                    |   Frontend     |
                    +----------------+
                           |
                           v
                    +----------------+
                    |  API Gateway   |
                    +----------------+
                    /      |        \
                   /       |         \
                  v        v          v
         +--------+  +--------+  +--------+
         |  User  |  | Event  |  | Ticket |
         | Service|  |Service |  |Service |
         +--------+  +--------+  +--------+
              \          |           /
               \         |          /
                \        v         /
                 \  +--------+    /
                  ->| Payment|<--
                    |Service |
                    +--------+
                         |
                         v
                    +--------+
                    | Notif. |
                    |Service |
                    +--------+
```

---

## 7. Mikroservisler

### 7.1. User Service (Port: 8001)

**Sorumluluk:** Kullanıcı yönetimi, kimlik doğrulama ve yetkilendirme

**Teknolojiler:**
- FastAPI (Python 3.11)
- PostgreSQL (userdb)
- Redis (rate limiting)
- JWT (python-jose)
- bcrypt (password hashing)

**API Endpoints:**

| Method | Endpoint | Açıklama | Yetki |
|--------|----------|----------|-------|
| POST | /api/v1/auth/register | Kullanıcı kaydı | Public |
| POST | /api/v1/auth/login | Kullanıcı girişi | Public |
| GET | /api/v1/users/{id} | Kullanıcı bilgisi | Auth |
| PUT | /api/v1/users/{id} | Kullanıcı güncelle | Auth |
| GET | /api/v1/users/ | Tüm kullanıcılar | Admin |

**Özellikler:**
- Rate limiting (Redis): 5 deneme/dakika/IP
- JWT token üretimi ve doğrulama
- Rol tabanlı erişim kontrolü (RBAC)
- Şifre güvenliği (bcrypt, 12 rounds)

### 7.2. Event Service (Port: 8002)

**Sorumluluk:** Etkinlik yönetimi ve stok takibi

**Teknolojiler:**
- FastAPI (Python 3.11)
- PostgreSQL (eventdb)
- RabbitMQ (stok güncellemeleri)
- Redis (cache - hazır)

**API Endpoints:**

| Method | Endpoint | Açıklama | Yetki |
|--------|----------|----------|-------|
| GET | /api/v1/events/ | Etkinlik listesi | Public |
| GET | /api/v1/events/{id} | Etkinlik detayı | Public |
| POST | /api/v1/events/ | Etkinlik oluştur | Admin/Organizer |
| PUT | /api/v1/events/{id} | Etkinlik güncelle | Admin/Organizer* |
| DELETE | /api/v1/events/{id} | Etkinlik sil | Admin/Organizer* |

*Organizer sadece kendi etkinliklerini düzenleyebilir

**Özellikler:**
- Etkinlik kategorileri (concert, theatre, sports, conference, exhibition, other)
- Stok yönetimi (available_tickets)
- RabbitMQ consumer (stok güncelleme mesajları)

### 7.3. Ticket Service (Port: 8003)

**Sorumluluk:** Bilet rezervasyonu ve satış yönetimi

**Teknolojiler:**
- FastAPI (Python 3.11)
- PostgreSQL (ticketdb)
- RabbitMQ (mesaj yayınlama)
- HTTPX (servisler arası HTTP)

**API Endpoints:**

| Method | Endpoint | Açıklama | Yetki |
|--------|----------|----------|-------|
| GET | /api/v1/tickets/ | Kullanıcının biletleri | Auth (User) |
| POST | /api/v1/tickets/ | Bilet satın al | Auth (User) |
| GET | /api/v1/tickets/{id} | Bilet detayı | Auth |
| DELETE | /api/v1/tickets/{id} | Bilet iptal | Auth |
| POST | /api/v1/tickets/admin/assign | Admin bilet ata | Admin |
| DELETE | /api/v1/tickets/admin/{id} | Admin bilet sil | Admin |

**Özellikler:**
- Bilet durumları: reserved, confirmed, cancelled, used
- Admin/Organizer bilet satın alamaz
- Event Service ile stok kontrolü (senkron)
- RabbitMQ ile mesaj yayınlama (asenkron)

### 7.4. Payment Service (Port: 8004)

**Sorumluluk:** Ödeme işlemleri (simüle edilmiş)

**Teknolojiler:**
- FastAPI (Python 3.11)
- PostgreSQL (paymentdb)
- RabbitMQ (bildirim mesajları)

**API Endpoints:**

| Method | Endpoint | Açıklama | Yetki |
|--------|----------|----------|-------|
| POST | /api/v1/payments/ | Ödeme yap | Auth |
| GET | /api/v1/payments/{id} | Ödeme detayı | Auth |
| GET | /api/v1/payments/user/{user_id} | Kullanıcı ödemeleri | Auth |

**Özellikler:**
- Ödeme simülasyonu (gerçek ödeme entegrasyonu yok)
- Ödeme durumları: pending, completed, failed, refunded
- RabbitMQ ile bildirim tetikleme

### 7.5. Notification Service (Port: 8005)

**Sorumluluk:** Bildirim yönetimi (simüle edilmiş)

**Teknolojiler:**
- FastAPI (Python 3.11)
- PostgreSQL (notificationdb)
- RabbitMQ (mesaj tüketimi)

**API Endpoints:**

| Method | Endpoint | Açıklama | Yetki |
|--------|----------|----------|-------|
| GET | /api/v1/notifications/ | Kullanıcı bildirimleri | Auth |
| GET | /api/v1/notifications/{id} | Bildirim detayı | Auth |

**Özellikler:**
- RabbitMQ consumer (ticket.reserved, payment.completed, vb.)
- E-posta/SMS simülasyonu
- Bildirim türleri: ticket_reserved, payment_completed, ticket_cancelled

### 7.6. API Gateway (Port: 8000)

**Sorumluluk:** Merkezi giriş noktası, yönlendirme, authentication

**Teknolojiler:**
- FastAPI (Python 3.11)
- HTTPX (proxy)
- JWT doğrulama

**Özellikler:**
- Tüm servislere tek giriş noktası
- JWT token doğrulama
- Request routing
- CORS yönetimi
- X-Forwarded-For header ekleme

---

## 8. Veri Modeli

### 8.1. User Service - User Tablosu

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    phone VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    role userrole DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TYPE userrole AS ENUM ('user', 'admin', 'organizer');
```

### 8.2. Event Service - Event Tablosu

```sql
CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    category eventcategory NOT NULL,
    venue VARCHAR(255) NOT NULL,
    city VARCHAR(100) NOT NULL,
    address TEXT,
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    base_price DECIMAL(10,2) NOT NULL,
    total_capacity INTEGER NOT NULL,
    available_tickets INTEGER NOT NULL,
    status eventstatus DEFAULT 'active',
    organizer_id INTEGER NOT NULL,
    image_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TYPE eventcategory AS ENUM ('concert', 'theatre', 'sports', 'conference', 'exhibition', 'other');
CREATE TYPE eventstatus AS ENUM ('draft', 'active', 'cancelled', 'completed', 'sold_out');
```

### 8.3. Ticket Service - Ticket Tablosu

```sql
CREATE TABLE tickets (
    id SERIAL PRIMARY KEY,
    ticket_number VARCHAR(50) UNIQUE NOT NULL,
    event_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    status ticketstatus DEFAULT 'reserved',
    payment_id INTEGER,
    reserved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confirmed_at TIMESTAMP,
    cancelled_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TYPE ticketstatus AS ENUM ('reserved', 'confirmed', 'cancelled', 'used');
```

### 8.4. Payment Service - Payment Tablosu

```sql
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    payment_number VARCHAR(50) UNIQUE NOT NULL,
    ticket_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'TRY',
    payment_method VARCHAR(50),
    status paymentstatus DEFAULT 'pending',
    transaction_id VARCHAR(100),
    failure_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TYPE paymentstatus AS ENUM ('pending', 'completed', 'failed', 'refunded');
```

### 8.5. Notification Service - Notification Tablosu

```sql
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    notification_type notificationtype NOT NULL,
    subject VARCHAR(255),
    message TEXT NOT NULL,
    status notificationstatus DEFAULT 'pending',
    sent_at TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TYPE notificationtype AS ENUM ('ticket_reserved', 'payment_completed', 'payment_failed', 'ticket_cancelled');
CREATE TYPE notificationstatus AS ENUM ('pending', 'sent', 'failed');
```

### 8.6. Entity-Relationship Diyagramı

```
+----------+       +----------+       +----------+
|   User   |       |  Event   |       |  Ticket  |
+----------+       +----------+       +----------+
| id (PK)  |       | id (PK)  |       | id (PK)  |
| email    |       | title    |       | ticket_# |
| username |       | venue    |       | event_id |----> Event.id
| password |       | city     |       | user_id  |----> User.id
| role     |       | price    |       | quantity |
+----------+       | capacity |       | price    |
     |             |organizer |---+   | status   |
     |             +----------+   |   +----------+
     |                  |         |        |
     +------------------+---------+        |
     |                                     |
     v                                     v
+----------+                         +----------+
| Payment  |                         |Notification|
+----------+                         +----------+
| id (PK)  |                         | id (PK)  |
| ticket_id|------------------------>| user_id  |----> User.id
| user_id  |----> User.id            | type     |
| amount   |                         | message  |
| status   |                         | status   |
+----------+                         +----------+
```

---

## 9. Servisler Arası İletişim

### 9.1. Senkron İletişim (REST API)

**Kullanım Durumları:**
- Client → API Gateway → Servis
- Ticket Service → Event Service (stok kontrolü)
- Ticket Service → User Service (kullanıcı rol kontrolü)

**İletişim Akışı:**
```
[Frontend] --HTTP--> [API Gateway] --HTTP--> [Microservice]
                           |
                     JWT Validation
```

### 9.2. Asenkron İletişim (RabbitMQ)

**Exchange Yapısı:**
- `events` exchange (topic type)
- `tickets` exchange (topic type)
- `notifications` exchange (topic type)

**Routing Keys ve Mesaj Akışı:**

| Routing Key | Publisher | Consumer | Açıklama |
|-------------|-----------|----------|----------|
| ticket.reserved | Ticket Service | Event Service | Stok düşürme |
| ticket.reserved | Ticket Service | Notification Service | Bildirim gönderme |
| ticket.cancelled | Ticket Service | Event Service | Stok artırma |
| ticket.cancelled | Ticket Service | Notification Service | Bildirim gönderme |
| payment.completed | Payment Service | Ticket Service | Bilet onaylama |
| payment.completed | Payment Service | Notification Service | Bildirim gönderme |
| payment.failed | Payment Service | Ticket Service | Bilet iptal |
| payment.failed | Payment Service | Notification Service | Bildirim gönderme |

**Mesaj Formatı (JSON):**
```json
{
  "event_id": 1,
  "ticket_id": 123,
  "user_id": 456,
  "quantity": 2,
  "timestamp": "2026-01-15T10:30:00Z"
}
```

### 9.3. Redis Kullanımı

**Rate Limiting:**
- Key pattern: `rate_limit:{endpoint}:{ip}`
- TTL: 60 saniye
- Limit: 5 istek/dakika

**Örnek:**
```
rate_limit:login:192.168.1.1 = 3  (TTL: 45s)
rate_limit:register:192.168.1.1 = 1  (TTL: 58s)
```

---

## 10. Güvenlik Mimarisi

### 10.1. Authentication (Kimlik Doğrulama)

**JWT Token Yapısı:**
```json
{
  "sub": "username",
  "user_id": 1,
  "email": "user@example.com",
  "role": "user",
  "exp": 1705312200,
  "iat": 1705310400
}
```

**Token Akışı:**
1. Kullanıcı login olur
2. User Service JWT token üretir
3. Frontend token'ı localStorage'da saklar
4. Her istekte Authorization header'ında gönderir
5. API Gateway token'ı doğrular

### 10.2. Authorization (Yetkilendirme)

**Rol Hiyerarşisi:**
```
Admin > Organizer > User > Guest
```

**Yetki Matrisi:**

| İşlem | Guest | User | Organizer | Admin |
|-------|-------|------|-----------|-------|
| Etkinlik görüntüleme | ✓ | ✓ | ✓ | ✓ |
| Kayıt olma | ✓ | - | - | - |
| Giriş yapma | - | ✓ | ✓ | ✓ |
| Bilet satın alma | - | ✓ | - | - |
| Etkinlik oluşturma | - | - | ✓ | ✓ |
| Kendi etkinliğini düzenleme | - | - | ✓ | ✓ |
| Tüm etkinlikleri düzenleme | - | - | - | ✓ |
| Kullanıcı yönetimi | - | - | - | ✓ |
| Bilet atama/silme | - | - | - | ✓ |

### 10.3. Rate Limiting

**Redis Tabanlı Implementasyon:**
```python
def rate_limit_check(key: str, limit: int, window: int) -> (bool, int):
    current = redis.incr(key)
    if current == 1:
        redis.expire(key, window)
    remaining = max(0, limit - current)
    is_allowed = current <= limit
    return is_allowed, remaining
```

**Konfigürasyon:**
- Login: 5 deneme / 60 saniye / IP
- Register: 5 deneme / 60 saniye / IP

### 10.4. Diğer Güvenlik Önlemleri

- **Password Hashing:** bcrypt (12 rounds)
- **CORS:** Sadece izin verilen origin'ler
- **Input Validation:** Pydantic schema validation
- **SQL Injection:** SQLAlchemy ORM parametreli sorgular
- **Environment Variables:** Secret key'ler .env dosyasında

---

## 11. Deployment ve Altyapı

### 11.1. Docker Container Yapısı

| Container | Image | Port | Bağımlılıklar |
|-----------|-------|------|---------------|
| api-gateway | python:3.11-slim | 8000 | user-service, event-service, ticket-service, payment-service, notification-service |
| user-service | python:3.11-slim | 8001 | user-db, redis, rabbitmq |
| event-service | python:3.11-slim | 8002 | event-db, redis, rabbitmq |
| ticket-service | python:3.11-slim | 8003 | ticket-db, redis, rabbitmq, event-service |
| payment-service | python:3.11-slim | 8004 | payment-db, redis, rabbitmq, ticket-service |
| notification-service | python:3.11-slim | 8005 | notification-db, redis, rabbitmq |
| user-db | postgres:15-alpine | 5432 | - |
| event-db | postgres:15-alpine | 5433 | - |
| ticket-db | postgres:15-alpine | 5434 | - |
| payment-db | postgres:15-alpine | 5435 | - |
| notification-db | postgres:15-alpine | 5436 | - |
| redis | redis:7-alpine | 6379 | - |
| rabbitmq | rabbitmq:3-management | 5672, 15672 | - |

### 11.2. Docker Compose Orkestrasyon

**Servis Başlatma Sırası:**
1. Veritabanları (PostgreSQL x5)
2. Redis
3. RabbitMQ
4. Mikroservisler (user, event, ticket, payment, notification)
5. API Gateway

**Health Check Yapılandırması:**
- PostgreSQL: `pg_isready -U postgres`
- Redis: `redis-cli ping`
- RabbitMQ: `rabbitmq-diagnostics -q ping`

### 11.3. Network Yapısı

```
+------------------------------------------------------------------+
|                    microservices-network (bridge)                 |
+------------------------------------------------------------------+
|                                                                   |
|  [api-gateway]  [user-service]  [event-service]  [ticket-service] |
|       |               |               |               |           |
|       +---------------+---------------+---------------+           |
|                              |                                    |
|  [payment-service]  [notification-service]  [redis]  [rabbitmq]  |
|       |                      |                 |          |       |
|       +----------------------+-----------------+----------+       |
|                                                                   |
|  [user-db] [event-db] [ticket-db] [payment-db] [notification-db] |
|                                                                   |
+------------------------------------------------------------------+
```

### 11.4. Çalıştırma Komutları

```bash
# Tüm servisleri başlatma
docker-compose up -d --build

# Servisleri durdurma
docker-compose down

# Logları görüntüleme
docker-compose logs -f [service-name]

# Servis yeniden başlatma
docker-compose restart [service-name]

# Rebuild
docker-compose up -d --build [service-name]
```

---

## 12. Çözümün Değerlendirilmesi ve Tartışması

### 12.1. Mimari Kararların Değerlendirilmesi

#### Mikroservis Mimarisi Seçimi

**Avantajlar:**
- Her servis bağımsız deploy edilebilir
- Hata izolasyonu sağlanır
- Farklı takımlar paralel çalışabilir
- Teknoloji çeşitliliği mümkün
- Yatay ölçekleme kolay

**Dezavantajlar:**
- Dağıtık sistem karmaşıklığı
- Servisler arası iletişim maliyeti
- Veri tutarlılığı zorlukları
- DevOps yetenekleri gerektirir
- Debugging zorluğu

#### Database per Service Pattern

**Avantajlar:**
- Veri izolasyonu
- Bağımsız ölçekleme
- Servis özerkliği

**Dezavantajlar:**
- Cross-service sorgular zor
- Veri tekrarı olabilir
- Transaction yönetimi karmaşık

#### Event-Driven Architecture (RabbitMQ)

**Avantajlar:**
- Gevşek bağlılık (loose coupling)
- Asenkron işleme
- Yüksek throughput
- Dayanıklılık

**Dezavantajlar:**
- Eventual consistency
- Mesaj sırası garantisi gerektirebilir
- Debugging zorluğu

### 12.2. Teknoloji Seçimlerinin Değerlendirilmesi

| Teknoloji | Neden Seçildi | Alternatifler |
|-----------|---------------|---------------|
| FastAPI | Yüksek performans, otomatik dokümantasyon, modern Python | Flask, Django REST |
| PostgreSQL | ACID uyumluluk, güvenilirlik, ilişkisel veri | MongoDB, MySQL |
| RabbitMQ | Güvenilir mesajlaşma, kolay yönetim | Kafka, Redis Pub/Sub |
| Redis | Hızlı cache, rate limiting desteği | Memcached |
| Docker | Standart containerization, taşınabilirlik | Podman |
| JWT | Stateless authentication, yaygın kullanım | Session-based auth |

### 12.3. Karşılaşılan Zorluklar ve Çözümler

| Zorluk | Çözüm |
|--------|-------|
| Servisler arası iletişimde IP sorunu | X-Forwarded-For header eklendi |
| Rate limiting çalışmıyordu | Redis client singleton pattern uygulandı |
| Container'lar arası network erişimi | Docker Compose network yapılandırması |
| Kod değişiklikleri yansımıyordu | Docker rebuild gereksinimi anlaşıldı |
| CORS hataları | API Gateway'de CORS middleware eklendi |

### 12.4. Performans Değerlendirmesi

**Gözlemlenen Metrikler:**
- API yanıt süresi: ~50-200ms (yerel ortamda)
- Container başlatma süresi: ~30-60 saniye (tüm sistem)
- Bellek kullanımı: ~2-3 GB (tüm container'lar)

**Performans Optimizasyonları:**
- Redis ile rate limiting
- PostgreSQL connection pooling (SQLAlchemy)
- Asenkron işleme (FastAPI async/await)

### 12.5. Güvenlik Değerlendirmesi

**Uygulanan Güvenlik Önlemleri:**
- JWT tabanlı authentication
- bcrypt ile password hashing
- Role-based access control
- Rate limiting (brute-force koruması)
- CORS yapılandırması
- Input validation (Pydantic)

**Potansiyel Güvenlik İyileştirmeleri:**
- HTTPS (production için)
- API key validation
- Request signing
- Audit logging

---

## 13. İyileştirme Önerileri

### 13.1. Kısa Vadeli İyileştirmeler

1. **Unit Test Ekleme**
   - Her servis için test coverage
   - pytest kullanımı
   - Mocking ile bağımlılık izolasyonu

2. **API Versiyonlama**
   - /api/v1, /api/v2 gibi versiyonlama
   - Backward compatibility

3. **Logging İyileştirme**
   - Structured logging (JSON format)
   - Correlation ID ile distributed tracing
   - Log aggregation (ELK Stack)

4. **Health Check Geliştirme**
   - Dependency health checks
   - Readiness ve liveness probes

### 13.2. Orta Vadeli İyileştirmeler

1. **Service Mesh**
   - Istio veya Linkerd entegrasyonu
   - Traffic management
   - Service-to-service encryption (mTLS)

2. **Monitoring ve Alerting**
   - Prometheus + Grafana
   - Custom metrics
   - Alerting rules

3. **CI/CD Pipeline**
   - GitHub Actions veya GitLab CI
   - Automated testing
   - Automated deployment

4. **API Gateway İyileştirme**
   - Kong veya Traefik kullanımı
   - Rate limiting politikaları
   - Request/response transformation

### 13.3. Uzun Vadeli İyileştirmeler

1. **Kubernetes Migration**
   - Container orchestration
   - Auto-scaling
   - Self-healing

2. **Event Sourcing**
   - Olay tabanlı veri saklama
   - Audit trail
   - Temporal queries

3. **CQRS Tam Implementasyon**
   - Read/write model ayrımı
   - Farklı veritabanları (read: NoSQL, write: SQL)

4. **Multi-Region Deployment**
   - Geographic distribution
   - Data replication
   - Disaster recovery

### 13.4. Özellik Önerileri

| Özellik | Açıklama | Öncelik |
|---------|----------|---------|
| Gerçek ödeme entegrasyonu | Stripe, iyzico | Yüksek |
| E-posta doğrulama | Kayıt sonrası e-posta onayı | Orta |
| QR kod bilet | Mobil bilet gösterimi | Orta |
| Arama ve filtreleme | Elasticsearch entegrasyonu | Orta |
| Favori etkinlikler | Kullanıcı favorileri | Düşük |
| Sosyal giriş | Google, Facebook OAuth | Düşük |

---

## 14. Sonuç

Bu projede, mikroservis mimarisine dayalı bir **Etkinlik Bilet Satış Sistemi** başarıyla tasarlanmış ve geliştirilmiştir. Sistem, modern yazılım mimarisi prensiplerini uygulayarak ölçeklenebilir, dayanıklı ve bakımı kolay bir yapıda inşa edilmiştir.

### 14.1. Proje Çıktıları

- **6 bağımsız mikroservis** (User, Event, Ticket, Payment, Notification, API Gateway)
- **5 ayrı PostgreSQL veritabanı** (database per service pattern)
- **RabbitMQ** ile asenkron mesajlaşma
- **Redis** ile rate limiting
- **Docker Compose** ile containerization
- **Bootstrap 5** ile modern frontend arayüzü
- **JWT** tabanlı authentication
- **RBAC** ile yetkilendirme (user, admin, organizer)

### 14.2. Öğrenilen Dersler

1. Mikroservis mimarisi, monolitik yapılara göre daha fazla planlama ve koordinasyon gerektirir
2. Asenkron mesajlaşma, sistemin esnekliğini ve dayanıklılığını artırır
3. Container tabanlı deployment, geliştirme ve production ortamları arasında tutarlılık sağlar
4. API Gateway, cross-cutting concerns'ü merkezi bir noktada yönetmeyi kolaylaştırır
5. Rate limiting, güvenlik için kritik öneme sahiptir

### 14.3. Gelecek Çalışmalar

Projenin gelecek versiyonlarında:
- Kubernetes ortamına geçiş
- Gerçek ödeme sistemi entegrasyonu
- Mobil uygulama desteği
- Gelişmiş arama ve öneri sistemi
- Machine learning ile kişiselleştirilmiş öneriler

planlanmaktadır.

---

## Ekler

### Ek A: Proje Dizin Yapısı

```
YM-2025-Final_Project/
├── api-gateway/
│   ├── app/
│   │   ├── routes/
│   │   ├── utils/
│   │   ├── config.py
│   │   └── main.py
│   ├── Dockerfile
│   └── requirements.txt
├── services/
│   ├── user-service/
│   ├── event-service/
│   ├── ticket-service/
│   ├── payment-service/
│   └── notification-service/
├── frontend/
│   └── index.html
├── docs/
│   └── ARCHITECTURE.md
├── docker-compose.yml
└── README.md
```

### Ek B: API Dokümantasyonu

Her servisin API dokümantasyonuna aşağıdaki adreslerden erişilebilir:

- API Gateway: http://localhost:8000/docs
- User Service: http://localhost:8001/docs
- Event Service: http://localhost:8002/docs
- Ticket Service: http://localhost:8003/docs
- Payment Service: http://localhost:8004/docs
- Notification Service: http://localhost:8005/docs

### Ek C: Yönetim Arayüzleri

- RabbitMQ Management: http://localhost:15672 (guest/guest)

---

**Proje GitHub:** https://github.com/Yusufycelik/-YM-2025-Final_Project

**Hazırlayan:** Yusuf Yemliha Çelik

