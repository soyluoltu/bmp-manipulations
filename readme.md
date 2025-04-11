# BMP Manipülatörü

Metadata işlemleri ve steganografi odaklı kapsamlı bir BMP dosya manipülasyon aracı.

![BMP Manipülatörü Logo](docs/logo.png)

[![Lisans: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Yapı Durumu](https://img.shields.io/github/workflow/status/soyluoltu/bmp-manipulator/CI)](https://github.com/soyluoltu/bmp-manipulator/actions)
[![Versiyon](https://img.shields.io/badge/version-1.0.0-brightgreen.svg)](https://github.com/soyluoltu/bmp-manipulator/releases)

## Giriş

BMP Manipülatörü, BMP (Bitmap) dosyalarıyla temel görüntü düzenlemenin ötesinde çalışmak için özelleştirilmiş bir kütüphanedir. BMP formatının genellikle gözden kaçan yönlerine odaklanır: başlıklar, metadata ve steganografi dahil çeşitli amaçlar için kullanılabilecek kullanılmayan alanlar.

## Temel Özellikler

- **Tam BMP Başlık Yönetimi**
  - BMP başlıklarının tüm yönlerini inceleme, değiştirme ve genişletme
  - Tüm BMP başlık versiyonları ve yapıları için destek
  - Başlık bütünlüğü için gelişmiş doğrulama

- **Genişletilmiş Metadata İşlemleri**
  - BMP dosyalarına özel metadata alanları ekleme
  - Mevcut metadataları çıkarma ve yorumlama
  - Standartlara uygun ve özel metadata formatları için destek

- **Steganografi Araç Seti**
  - Çoklu steganografi algoritmaları (LSB, Palet manipülasyonu, vb.)
  - Özelleştirilebilir veri gizleme stratejileri
  - Gizli veriler için şifreleme desteği
  - Steganaliz ve tespit için araçlar

- **Geliştirici Dostu Tasarım**
  - Programatik kullanım için temiz API
  - Kapsamlı CLI komutları
  - Detaylı belgelendirme ve örnekler

## BMP Yapısına Genel Bakış

BMP dosya formatı birkaç temel bileşenden oluşur:

1. **Dosya Başlığı (14 bayt)**
   - Dosya türü, boyutu ve piksel verisine offset

2. **DIB Başlığı (değişken boyut)**
   - Görüntü boyutları, renk derinliği ve sıkıştırma bilgisi
   - Farklı sürümleri: BITMAPINFOHEADER (40 bayt), BITMAPV4HEADER (108 bayt), BITMAPV5HEADER (124 bayt)

3. **Renk Paleti (isteğe bağlı)**
   - 8-bit veya daha düşük renk derinliğindeki görüntüler için

4. **Bit Maskesi (isteğe bağlı)**
   - Bazı renk formatları için

5. **Piksel Verisi**
   - Satır başına 4-baytlık hizalama gerektirir
   - Alt-üst yapılandırması (aşağıdan yukarıya doğru dizilir)

6. **ICC Renk Profili (isteğe bağlı, BITMAPV5HEADER ile)**
   - Renk yönetimi için

7. **Özel Metadata Alanları (bu proje ile)**
   - Standart yapıda tanımlanmayan ek veriler

## Metadata İşlemleri

BMP Manipülatörü, BMP dosyalarında bulunan standart metadata alanları dışında özel metadata eklemek için birkaç yöntem sunar:

### Metadata Ekleme Yöntemleri

1. **Başlık Genişletmesi**
   - DIB başlığının kullanılmayan alanlarını kullanma
   - BITMAPV5HEADER'ın rezerve edilmiş alanlarını kullanma

2. **Application Extension Blocks**
   - Piksel verisinden sonra özel bloklar ekleme
   - Uygulamaya özel tanımlayıcılar kullanma

3. **Metadata Bölümleri**
   - Dosya sonuna metadata eklemek için özel format
   - Başlıkta referans olmadan gizli veri saklama

### Metadata Formatları

- **Anahtar-Değer Çiftleri**
  - Basit metin tabanlı metadata
  - JSON formatında yapılandırılmış veriler

- **XMP Metadata**
  - Adobe XMP formatı ile uyumlu
  - Standartlaştırılmış metadata şemaları

- **Özel İkili Formatlar**
  - Özel uygulamalar için optimize edilmiş
  - Sıkıştırılmış veya şifrelenmiş metadata

## Steganografi Özellikleri

BMP Manipülatörü, çeşitli steganografi tekniklerini destekler:

### Desteklenen Teknikler

1. **En Az Önemli Bit (LSB) Steganografisi**
   - Piksel verilerinin en az önemli bitlerinde bilgi gizleme
   - Ayarlanabilir bit derinliği (1-4 bit)
   - Kanal seçimi (R, G, B veya tümü)

2. **Palet Tabanlı Steganografi**
   - Paletli BMP'lerde renkler arasındaki sıralamayı değiştirme
   - Görsel değişiklikler olmadan veri gizleme

3. **Başlık Alanı Steganografisi**
   - Kullanılmayan veya az kullanılan başlık alanlarında veri gizleme
   - Görüntü verisi etkilenmeden veri saklama

4. **Boş Alan Kullanımı**
   - Piksel verisi ve dosya sonu arasındaki boşluğu kullanma
   - Yüksek kapasite, düşük tespit edilebilirlik

### Güvenlik Özellikleri

- **Şifreleme Entegrasyonu**
  - AES-256, ChaCha20 gibi modern şifreleme algoritmaları
  - Steganografi öncesi veri şifreleme

- **Dağıtılmış Gizleme**
  - Verinin dosya genelinde dağıtılması
  - Tespit zorluğunu arttırma

- **Sahte Positif Enjeksiyonu**
  - Steganaliz araçlarını yanıltmak için sahte veri
  - Gerçek gizli veriyi maskeleme
