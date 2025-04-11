# BMP Manipülatörü - Örnek Kullanım

Bu belge, BMP Manipülatörü uygulamasının nasıl kullanılacağını göstermektedir.

## Kurulum

```bash
# Git deposunu klonla
git clone https://github.com/soyluoltu/bmp-manipulator.git
cd bmp-manipulator

# Bağımlılıkları kur
pip install -r requirements.txt
```

## Temel BMP Dosya Bilgilerini Görüntüleme

BMP dosyası hakkında temel bilgileri görüntülemek için:

```bash
python bmp_manipulator.py info ornek.bmp
```

**Örnek Çıktı:**
```
BMP Dosya Bilgisi: ornek.bmp
Boyut: 230454 bayt
Başlık tipi: BITMAPINFOHEADER
Boyutlar: 800x600
Renk derinliği: 24 bit
Sıkıştırma: BI_RGB
Metadata: Yok
```

## Metadata İşlemleri

### Metadata Ekleme

BMP dosyasına metadata eklemek için:

```bash
python bmp_manipulator.py metadata add ornek.bmp --key "Başlık" --value "Test Görüntüsü" --output cikti.bmp
```

Şifreli metadata eklemek için:

```bash
python bmp_manipulator.py metadata add ornek.bmp --key "Gizli Not" --value "Bu bir gizli nottur" --password "gizli123" --output cikti.bmp
```

Birden fazla metadata eklemek için komutu birkaç kez çalıştırın:

```bash
python bmp_manipulator.py metadata add cikti.bmp --key "Yazar" --value "BMP Test Ekibi"
python bmp_manipulator.py metadata add cikti.bmp --key "Tarih" --value "2023-11-01"
```

### Metadata Çıkarma

BMP dosyasındaki metadata'yı görmek için:

```bash
python bmp_manipulator.py metadata extract cikti.bmp
```

**Örnek Çıktı:**
```
BMP Metadata:
  Başlık: Test Görüntüsü
  Yazar: BMP Test Ekibi
  Tarih: 2023-11-01
```

Şifreli metadata'yı çıkarmak için:

```bash
python bmp_manipulator.py metadata extract cikti.bmp --password "gizli123"
```

## Steganografi İşlemleri

### Metin Gizleme

BMP dosyasında metin gizlemek için:

```bash
python bmp_manipulator.py stego hide ornek.bmp --text "Bu gizli bir mesajdır. BMP dosyasının içine gizlenmiştir." --output gizli_mesaj.bmp
```

Daha yüksek bit derinliği ve şifreleme ile:

```bash
python bmp_manipulator.py stego hide ornek.bmp --text "Önemli gizli bilgi" --bit-depth 2 --channels 3 --password "super_gizli" --output guvenli_mesaj.bmp
```

### Dosya Gizleme

BMP dosyasında başka bir dosya gizlemek için:

```bash
python bmp_manipulator.py stego hide ornek.bmp --file gizli_belge.pdf --output gizli_dosya.bmp
```

### Gizli Metni Çıkarma

BMP dosyasından gizli metni çıkarmak için:

```bash
python bmp_manipulator.py stego extract gizli_mesaj.bmp
```

**Örnek Çıktı:**
```
Çıkarılan metin:
Bu gizli bir mesajdır. BMP dosyasının içine gizlenmiştir.
```

Şifreli gizli metni çıkarmak için:

```bash
python bmp_manipulator.py stego extract guvenli_mesaj.bmp --password "super_gizli"
```

### Gizli Dosyayı Çıkarma

BMP dosyasından gizli dosyayı çıkarmak için:

```bash
python bmp_manipulator.py stego extract gizli_dosya.bmp --output cikti.pdf
```

**Örnek Çıktı:**
```
Çıkarılan veri dosyaya kaydedildi: cikti.pdf (42512 bayt)
```

## İleri Düzey Kullanım

### Python API Kullanımı

BMP Manipülatörü'nü bir Python kütüphanesi olarak kendi programlarınızda kullanabilirsiniz:

```python
from bmp_manipulator import BMPFile, Metadata, LSBSteganography

# BMP yükle ve analiz et
bmp = BMPFile("ornek.bmp")
print(f"Görüntü boyutu: {bmp.width}x{bmp.height}")

# Metadata ekle
meta = Metadata()
meta.add("Uygulama", "Python API Örneği")
meta.add("İşleme Zamanı", "2023-11-01 15:30:00")
bmp.add_metadata(meta)

# Steganografi uygula
stego = LSBSteganography(bmp)
stego.hide_text("Python API ile gizlenmiş mesaj", password="test123")

# Dosyayı kaydet
bmp.save("api_ornegi.bmp")

# Gizli veriyi çıkar
extracted_bmp = BMPFile("api_ornegi.bmp")
stego_extract = LSBSteganography(extracted_bmp)
extracted_text = stego_extract.extract_data(password="test123").decode("utf-8")
print(f"Çıkarılan mesaj: {extracted_text}")
```

### Özel Bit Derinliği ve Kanal Seçimi

Steganografi işlemlerinde özel bit derinliği ve kanal seçimi yapabilirsiniz:

```bash
# Sadece mavi kanala veri gizleme (1 kanal), 2 bit derinliğinde
python bmp_manipulator.py stego hide ornek.bmp --text "Sadece mavi kanalda" --bit-depth 2 --channels 1 --output mavi_kanal.bmp

# Çıkarma işleminde aynı parametreleri kullanın
python bmp_manipulator.py stego extract mavi_kanal.bmp --bit-depth 2 --channels 1
```

### Metadata ve Steganografiyi Birlikte Kullanma

Aynı dosyada hem metadata hem de steganografi kullanabilirsiniz:

```bash
# Önce metadata ekle
python bmp_manipulator.py metadata add ornek.bmp --key "Başlık" --value "Çift Gizli Dosya" --output cift_gizli.bmp

# Sonra steganografi uygula
python bmp_manipulator.py stego hide cift_gizli.bmp --text "İki kat gizli mesaj" --output cift_gizli.bmp

# Her iki veriyi de çıkar
python bmp_manipulator.py metadata extract cift_gizli.bmp
python bmp_manipulator.py stego extract cift_gizli.bmp
```

## Güvenlik Önerileri

1. Önemli veriler için her zaman şifreleme kullanın.
2. Yüksek kapasiteli veri gizlemek gerekiyorsa, büyük boyutlu BMP dosyaları kullanın.
3. Steganografi için bit-derinliğini düşük tutun (1-2) ki görüntüde fark edilebilir değişiklikler olmasın.
4. Görsel analiz araçlarına karşı koruma için LSB yöntemlerini dikkatli kullanın.
5. Maksimum güvenlik için şifreli metadata ve şifreli steganografiyi birlikte kullanın.

## Hata Ayıklama

Bir hata durumunda daha fazla bilgi görmek için Python'un `-v` bayrağını kullanabilirsiniz:

```bash
python -v bmp_manipulator.py stego extract hatali.bmp
```

## Desteklenen BMP Formatları

BMP Manipülatörü aşağıdaki BMP formatlarını destekler:

- 24-bit RGB (LSB steganografi için)
- 32-bit RGBA (LSB steganografi için)
- 8-bit paletli (Palet steganografi için)
- BITMAPINFOHEADER (40 bayt)
- BITMAPV4HEADER (108 bayt)  
- BITMAPV5HEADER (124 bayt)

BITMAPCOREHEADER (12 bayt) ve sıkıştırılmış BMP dosyaları desteklenmemektedir.
