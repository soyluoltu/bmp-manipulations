# BMP Dosya Formatı Yapısı

Bu belge, BMP dosya formatının detaylı yapısını ve veri gizleme için kullanılabilecek potansiyel alanları açıklar.

## BMP Dosya Yapısı Genel Bakış

BMP (Bitmap) dosya formatı aşağıdaki temel bileşenlerden oluşur:

```
+------------------------+
| Dosya Başlığı          | (14 bayt)
+------------------------+
| DIB Başlığı            | (40+ bayt, sürüme göre değişir)
+------------------------+
| Renk Paleti            | (İsteğe bağlı)
+------------------------+
| Bit Maskeleri          | (İsteğe bağlı)
+------------------------+
| Piksel Verileri        |
+------------------------+
| ICC Renk Profili       | (İsteğe bağlı, sadece BITMAPV5HEADER)
+------------------------+
| Kullanılmayan Alan     | (Metadata için potansiyel alan)
+------------------------+
```

## Dosya Başlığı (BITMAPFILEHEADER)

| Alan | Boyut | Açıklama | Veri Gizleme Potansiyeli |
|------|-------|----------|--------------------------|
| bfType | 2 bayt | "BM" dosya imzası (0x4D42) | Düşük (değiştirilmesi dosyanın tanınmasını engeller) |
| bfSize | 4 bayt | Toplam dosya boyutu | Orta (hafif modifikasyonlar mümkün) |
| bfReserved1 | 2 bayt | Rezerve edilmiş, genellikle 0 | Yüksek (tamamen kullanılabilir) |
| bfReserved2 | 2 bayt | Rezerve edilmiş, genellikle 0 | Yüksek (tamamen kullanılabilir) |
| bfOffBits | 4 bayt | Piksel verisi başlangıç offseti | Düşük (doğru referans için kritik) |

## DIB Başlığı (BITMAPINFOHEADER)

| Alan | Boyut | Açıklama | Veri Gizleme Potansiyeli |
|------|-------|----------|--------------------------|
| biSize | 4 bayt | Başlık boyutu | Düşük (başlık tipi için gerekli) |
| biWidth | 4 bayt | Görüntü genişliği (piksel) | Düşük (görüntü boyutu için kritik) |
| biHeight | 4 bayt | Görüntü yüksekliği (piksel) | Düşük (görüntü boyutu için kritik) |
| biPlanes | 2 bayt | Renk düzlemleri (her zaman 1) | Düşük (1 olması gerekir) |
| biBitCount | 2 bayt | Piksel başına bit sayısı | Düşük (renk derinliği için kritik) |
| biCompression | 4 bayt | Sıkıştırma yöntemi | Orta (bazı değerler değiştirilebilir) |
| biSizeImage | 4 bayt | Sıkıştırılmış görüntü boyutu | Orta (bazı görüntüleyiciler tarafından kullanılmaz) |
| biXPelsPerMeter | 4 bayt | Yatay çözünürlük | Yüksek (çoğu uygulama tarafından yok sayılır) |
| biYPelsPerMeter | 4 bayt | Dikey çözünürlük | Yüksek (çoğu uygulama tarafından yok sayılır) |
| biClrUsed | 4 bayt | Renk tablosundaki giriş sayısı | Orta (0 olabilir veya tam değer) |
| biClrImportant | 4 bayt | Önemli renklerin sayısı | Yüksek (çoğu uygulama tarafından yok sayılır) |

## Genişletilmiş DIB Başlıkları

### BITMAPV4HEADER (108 bayt)
BITMAPINFOHEADER'ın tüm alanlarını içerir ve aşağıdaki ek alanları ekler:

| Alan | Boyut | Açıklama | Veri Gizleme Potansiyeli |
|------|-------|----------|--------------------------|
| bV4RedMask | 4 bayt | Kırmızı kanal maskesi | Orta (maskeler belirli değerlere sahip olmalı) |
| bV4GreenMask | 4 bayt | Yeşil kanal maskesi | Orta (maskeler belirli değerlere sahip olmalı) |
| bV4BlueMask | 4 bayt | Mavi kanal maskesi | Orta (maskeler belirli değerlere sahip olmalı) |
| bV4AlphaMask | 4 bayt | Alfa kanal maskesi | Orta (maskeler belirli değerlere sahip olmalı) |
| bV4CSType | 4 bayt | Renk uzayı tipi | Yüksek (çoğu uygulama tarafından yok sayılır) |
| bV4Endpoints | 36 bayt | Renk uzayı endpoint'leri | Yüksek (çoğu uygulama tarafından yok sayılır) |
| bV4GammaRed | 4 bayt | Kırmızı gamma | Yüksek (çoğu uygulama tarafından yok sayılır) |
| bV4GammaGreen | 4 bayt | Yeşil gamma | Yüksek (çoğu uygulama tarafından yok sayılır) |
| bV4GammaBlue | 4 bayt | Mavi gamma | Yüksek (çoğu uygulama tarafından yok sayılır) |

### BITMAPV5HEADER (124 bayt)
BITMAPV4HEADER'ın tüm alanlarını içerir ve aşağıdaki ek alanları ekler:

| Alan | Boyut | Açıklama | Veri Gizleme Potansiyeli |
|------|-------|----------|--------------------------|
| bV5Intent | 4 bayt | Render amacı | Yüksek (çoğu uygulama tarafından yok sayılır) |
| bV5ProfileData | 4 bayt | ICC profil verisi offseti | Orta (ICC profil kullanılıyorsa doğru olmalı) |
| bV5ProfileSize | 4 bayt | ICC profil verisi boyutu | Orta (ICC profil kullanılıyorsa doğru olmalı) |
| bV5Reserved | 4 bayt | Rezerve edilmiş | Yüksek (tamamen kullanılabilir) |

## Renk Paleti

8-bit ve daha düşük renk derinliğindeki BMP dosyaları için renk paleti bulunur:

| Yapı | Boyut | Açıklama | Veri Gizleme Potansiyeli |
|------|-------|----------|--------------------------|
| Palet Girişleri | Her giriş için 4 bayt (B,G,R,Rezerve) | Renk değerleri | Orta (Renk sırasını hafifçe değiştirilebilir) |
| Rezerve Edilmiş Bayt | 1 bayt (her girişte) | Kullanılmayan, genellikle 0 | Yüksek (tamamen kullanılabilir) |

## Piksel Verileri

Piksel verileri, görüntünün gerçek içeriğini temsil eder:

| Özellik | Açıklama | Veri Gizleme Potansiyeli |
|---------|----------|--------------------------|
| LSB Steganografi | En az önemli bitlerin değiştirilmesi | Yüksek (görsel etkisi minimal) |
| Satır Dolgusu | Her satır 4 baytlık sınıra yuvarlanır, dolgu baytları eklenir | Yüksek (tamamen kullanılabilir) |
| Sıra | Görüntü alt-üst (aşağıdan yukarıya) olarak depolanır | Düşük (standart davranış) |

## Dosya Sonu (EOF) Sonrası Veriler

| Özellik | Açıklama | Veri Gizleme Potansiyeli |
|---------|----------|--------------------------|
| EOF Sonrası Veriler | Belirtilen dosya boyutundan sonraki veri | Çok Yüksek (çoğu BMP görüntüleyici tarafından yok sayılır) |

## Veri Gizleme Stratejileri

### 1. Rezerve Edilmiş Alanlar Kullanımı

```
// Dosya başlığındaki rezerve edilmiş alanları kullanma
bfReserved1 ve bfReserved2 → 4 bayt veri depolama kapasitesi

// BITMAPV5HEADER'daki rezerve edilmiş alanı kullanma 
bV5Reserved → 4 bayt ek depolama
```

### 2. LSB Steganografi

En az önemli bit steganografisi, görüntü piksellerinin en az önemli bitlerini değiştirerek veri gizler:

```
// Örnek LSB kodlama
orijinal_piksel = 10101100₂
gizlenecek_bit  =        1₂
yeni_piksel     = 10101101₂
```

24-bit BMP içinde her piksel 3 bayt (R, G, B) kullanır. Her baytın en az önemli biti değiştirilebilir:

- 800x600 çözünürlüğünde 24-bit BMP → 800 x 600 x 3 = 1,440,000 bayt
- LSB kullanılarak gizlenebilecek veri → 1,440,000 ÷ 8 = 180,000 bayt (175 KB)

### 3. Renk Paleti Manipülasyonu

8-bit BMP dosyaları için, renk paletindeki sıralama değiştirilebilir:

```
// Orijinal palet
Giriş 0: (255, 0, 0) → Kırmızı
Giriş 1: (0, 255, 0) → Yeşil
...

// Sıra ile veri kodlama
Giriş 1: (0, 255, 0) → Yeşil  // Değiştirilmiş sıra = bit 1
Giriş 0: (255, 0, 0) → Kırmızı // = bit 0
...
```

### 4. Başlık Alanlarının Manipülasyonu

```
// Çözünürlük alanlarını kullanma
biXPelsPerMeter = 3780 → Orijinal değer (96 DPI)
biXPelsPerMeter = 3781 → Gizli veri içerir (fark görsel olarak algılanamaz)
```

### 5. Dosya Sonu Verileri

```
// BMP dosyasının sonuna veri ekleme
[Normal BMP Dosyası - bfSize bayt] + [Gizli Veri]
```

## Metadata Blok Formatı

BMP Manipülatörü, dosya sonuna standartlaştırılmış özel metadata blokları ekler:

```
+------------------------+
| Blok İşareti           | (4 bayt) - "BMPM" imzası
+------------------------+
| Blok Boyutu            | (4 bayt) - Tüm bloğun boyutu
+------------------------+
| Sürüm                  | (2 bayt) - Metadata format sürümü
+------------------------+
| Şifreleme Bayrağı      | (1 bayt) - 0=Şifresiz, 1=Şifreli
+------------------------+
| Rezerve                | (1 bayt) - Gelecek kullanım için
+------------------------+
| Metadata Sayısı        | (2 bayt) - Takip eden giriş sayısı
+------------------------+
| Metadata Girişleri     | (Değişken)
+------------------------+
| Sağlama Toplamı        | (4 bayt) - CRC32 sağlama toplamı
+------------------------+
```

Her metadata girişi şu formattadır:

```
+------------------------+
| Anahtar Uzunluğu       | (2 bayt)
+------------------------+
| Değer Uzunluğu         | (4 bayt)
+------------------------+
| Anahtar                | (Değişken - UTF-8)
+------------------------+
| Değer                  | (Değişken - Binary/UTF-8)
+------------------------+
```

## Şifreleme Entegrasyonu

BMP Manipülatörü, gizli verileri şifrelemek için aşağıdaki yöntemleri destekler:

1. **AES-256-GCM**
   - Anahtar türetme: PBKDF2 (100,000 iterasyon)
   - Doğrulama etiketi: 16 bayt

2. **ChaCha20-Poly1305**
   - Hızlı şifreleme ve doğrulama
   - 12 bayt nonce

3. **XChaCha20-Poly1305**
   - 24 bayt nonce ile genişletilmiş sürüm
   - Daha yüksek güvenlik marjı

## Steganaliz Direnci

BMP Manipülatörü, aşağıdaki teknikleri kullanarak steganaliz direncini artırır:

1. **Dağınık Gömme**
   - Gizli veri rastgele dağıtılır
   - Tekdüze LSB değişiklikleri yerine Hamming ağırlığı korunur

2. **İstatistiksel Gürültü Enjeksiyonu**
   - Doğal görüntü gürültüsünü taklit eden modeller
   - Renk histogramında değişiklikleri en aza indirme

3. **Yalancı Veri Karıştırma**
   - Sahte veri enjeksiyonu ile gerçek verinin yerini gizleme
   - Steganaliz araçlarını yanıltmak için tuzaklar

4. **İmza Kaçınma**
   - Bilinen steganografi imzalarından kaçınma
   - Format özelliklerine sıkı uyum sağlama