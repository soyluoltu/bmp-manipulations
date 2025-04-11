#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BMP Manipülatörü
===============

BMP dosyalarında metadata işleme ve steganografi araçları.

Bu modül BMP dosyalarında başlık manipülasyonu, metadata ekleme/çıkarma
ve steganografi teknikleri için kapsamlı araçlar sunar.
"""

import os
import sys
import struct
import argparse
import json
import hashlib
import binascii
import base64
from datetime import datetime
from typing import Dict, List, Tuple, Union, Optional, BinaryIO, Any
from dataclasses import dataclass
from enum import Enum, auto

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

__version__ = "1.0.0"
__author__ = "BMP Manipülatör Ekibi"

# BMP Dosya Başlığı Yapısı
BMP_HEADER_FORMAT = '<2sIHHI'
BMP_HEADER_SIZE = 14

# DIB Başlık Tipleri
DIB_HEADER_SIZES = {
    12: 'BITMAPCOREHEADER',
    40: 'BITMAPINFOHEADER',
    52: 'BITMAPV2INFOHEADER',
    56: 'BITMAPV3INFOHEADER',
    108: 'BITMAPV4HEADER',
    124: 'BITMAPV5HEADER'
}

# Sıkıştırma Metodları
BI_COMPRESSION = {
    0: 'BI_RGB',         # Sıkıştırma yok
    1: 'BI_RLE8',        # 8-bit RLE sıkıştırma
    2: 'BI_RLE4',        # 4-bit RLE sıkıştırma
    3: 'BI_BITFIELDS',   # Bit alanları
    4: 'BI_JPEG',        # JPEG sıkıştırma
    5: 'BI_PNG',         # PNG sıkıştırma
    6: 'BI_ALPHABITFIELDS',  # Alfa bit alanları
    11: 'BI_CMYK',       # CMYK renk uzayı
    12: 'BI_CMYKRLE8',   # CMYK 8-bit RLE
    13: 'BI_CMYKRLE4'    # CMYK 4-bit RLE
}

# Metadata Blok İmzası
METADATA_SIGNATURE = b'BMPM'

# LSB Steganografi için varsayılan ayarlar
DEFAULT_LSB_DEPTH = 1  # Değiştirilecek bit sayısı
DEFAULT_LSB_CHANNELS = 3  # Tüm renkler (R, G, B)


class BMPError(Exception):
    """BMP işleme ile ilgili hatalar için özel istisna."""
    pass


class MetadataError(Exception):
    """Metadata işleme ile ilgili hatalar için özel istisna."""
    pass


class SteganographyError(Exception):
    """Steganografi işleme ile ilgili hatalar için özel istisna."""
    pass


class MetadataStorageMethod(Enum):
    """Metadata depolama yöntemleri."""
    HEADER_EXTENSION = auto()
    APPLICATION_BLOCK = auto()
    EOF_APPEND = auto()


class StegoMethod(Enum):
    """Desteklenen steganografi yöntemleri."""
    LSB = auto()
    PALETTE = auto()
    HEADER = auto()
    EOF = auto()


@dataclass
class BMPFileHeader:
    """BMP dosya başlığı yapısı."""
    signature: bytes      # 'BM'
    file_size: int        # Bayt olarak dosya boyutu
    reserved1: int        # Rezerve edilmiş (genellikle 0)
    reserved2: int        # Rezerve edilmiş (genellikle 0)
    pixel_offset: int     # Piksel verilerine offset


@dataclass
class DIBHeader:
    """DIB başlığı için temel sınıf."""
    header_size: int      # Başlık boyutu
    width: int            # Piksel olarak genişlik
    height: int           # Piksel olarak yükseklik
    planes: int           # Renk düzlemleri (her zaman 1)
    bit_count: int        # Piksel başına bit
    compression: int      # Sıkıştırma yöntemi
    image_size: int       # Görüntü verisi boyutu
    x_ppm: int            # X çözünürlüğü (piksel/metre)
    y_ppm: int            # Y çözünürlüğü (piksel/metre)
    colors_used: int      # Kullanılan renk sayısı
    colors_important: int # Önemli renk sayısı
    raw_data: bytes       # Tüm ham başlık verisi


class Metadata:
    """BMP dosyasına eklenecek metadata yöneticisi."""
    
    def __init__(self):
        self.entries = {}
        self.creation_date = datetime.now().isoformat()
    
    def add(self, key: str, value: Union[str, bytes, int, float, dict, list]) -> None:
        """Yeni bir metadata girişi ekler."""
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False)
        
        if not isinstance(value, (str, bytes, int, float)):
            raise MetadataError(f"Desteklenmeyen metadata değer tipi: {type(value)}")
        
        self.entries[key] = value
    
    def get(self, key: str) -> Any:
        """Belirtilen anahtara sahip metadata değerini döndürür."""
        if key not in self.entries:
            raise MetadataError(f"Metadata anahtarı bulunamadı: {key}")
        return self.entries[key]
    
    def remove(self, key: str) -> None:
        """Belirtilen anahtara sahip metadata girişini siler."""
        if key not in self.entries:
            raise MetadataError(f"Metadata anahtarı bulunamadı: {key}")
        del self.entries[key]
    
    def to_dict(self) -> Dict:
        """Metadata'yı sözlük olarak döndürür."""
        return {
            "creation_date": self.creation_date,
            "entries": self.entries
        }
    
    def to_bytes(self) -> bytes:
        """Metadata'yı ikili formata dönüştürür."""
        result = bytearray()
        
        # Giriş sayısını ekle (2 bayt)
        result.extend(struct.pack("<H", len(self.entries)))
        
        # Her girişi ekle
        for key, value in self.entries.items():
            key_bytes = key.encode('utf-8')
            
            # Değeri uygun formata dönüştür
            if isinstance(value, str):
                value_bytes = value.encode('utf-8')
            elif isinstance(value, bytes):
                value_bytes = value
            elif isinstance(value, (int, float)):
                value_bytes = str(value).encode('utf-8')
            else:
                raise MetadataError(f"Desteklenmeyen metadata değer tipi: {type(value)}")
            
            # Anahtar uzunluğu (2 bayt)
            result.extend(struct.pack("<H", len(key_bytes)))
            # Değer uzunluğu (4 bayt)
            result.extend(struct.pack("<I", len(value_bytes)))
            # Anahtar
            result.extend(key_bytes)
            # Değer
            result.extend(value_bytes)
        
        return bytes(result)
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'Metadata':
        """İkili veriden metadata oluşturur."""
        metadata = cls()
        
        # Girdi sayısını oku
        if len(data) < 2:
            raise MetadataError("Geçersiz metadata format: veri çok kısa")
        
        entry_count = struct.unpack("<H", data[:2])[0]
        position = 2
        
        for _ in range(entry_count):
            if position + 6 > len(data):
                raise MetadataError("Geçersiz metadata format: beklenmeyen dosya sonu")
            
            # Anahtar ve değer uzunluklarını oku
            key_length = struct.unpack("<H", data[position:position+2])[0]
            position += 2
            
            value_length = struct.unpack("<I", data[position:position+4])[0]
            position += 4
            
            if position + key_length + value_length > len(data):
                raise MetadataError("Geçersiz metadata format: eksik veri")
            
            # Anahtar ve değeri oku
            key = data[position:position+key_length].decode('utf-8')
            position += key_length
            
            value = data[position:position+value_length]
            position += value_length
            
            # UTF-8 metin olarak değeri çözmeyi dene
            try:
                value = value.decode('utf-8')
                
                # JSON olarak çözmeyi dene
                try:
                    value = json.loads(value)
                except json.JSONDecodeError:
                    pass  # Normal metin olarak bırak
                
            except UnicodeDecodeError:
                pass  # İkili veri olarak bırak
            
            metadata.add(key, value)
        
        return metadata


class BMPFile:
    """BMP dosyası yükleme, işleme ve kaydetme işlemleri için ana sınıf."""
    
    def __init__(self, file_path: Optional[str] = None):
        self.file_path = file_path
        self.file_header: Optional[BMPFileHeader] = None
        self.dib_header: Optional[DIBHeader] = None
        self.pixel_data: Optional[bytes] = None
        self.palette: Optional[bytes] = None
        self.metadata: Optional[Metadata] = None
        self.raw_data: Optional[bytes] = None
        
        if file_path:
            self.load(file_path)
    
    def load(self, file_path: str) -> None:
        """BMP dosyasını yükler ve analiz eder."""
        self.file_path = file_path
        
        with open(file_path, 'rb') as f:
            self.raw_data = f.read()
        
        if len(self.raw_data) < BMP_HEADER_SIZE:
            raise BMPError("Geçersiz BMP dosyası: dosya çok küçük")
        
        # Dosya başlığını ayrıştır
        signature, file_size, reserved1, reserved2, pixel_offset = struct.unpack(
            BMP_HEADER_FORMAT, self.raw_data[:BMP_HEADER_SIZE]
        )
        
        if signature != b'BM':
            raise BMPError(f"Geçersiz BMP imzası: {signature}")
        
        self.file_header = BMPFileHeader(
            signature=signature,
            file_size=file_size,
            reserved1=reserved1,
            reserved2=reserved2,
            pixel_offset=pixel_offset
        )
        
        # DIB başlık boyutunu oku
        if len(self.raw_data) < BMP_HEADER_SIZE + 4:
            raise BMPError("Geçersiz BMP dosyası: DIB başlığı eksik")
        
        dib_size = struct.unpack('<I', self.raw_data[BMP_HEADER_SIZE:BMP_HEADER_SIZE+4])[0]
        
        if dib_size not in DIB_HEADER_SIZES:
            raise BMPError(f"Tanınmayan DIB başlık boyutu: {dib_size}")
        
        if len(self.raw_data) < BMP_HEADER_SIZE + dib_size:
            raise BMPError("Geçersiz BMP dosyası: DIB başlığı eksik")
        
        # Minimum BITMAPINFOHEADER formatı
        if dib_size >= 40:
            header_format = '<IiiHHIIiiII'
            dib_data = self.raw_data[BMP_HEADER_SIZE:BMP_HEADER_SIZE+40]
            
            try:
                (header_size, width, height, planes, bit_count,
                 compression, image_size, x_ppm, y_ppm,
                 colors_used, colors_important) = struct.unpack(header_format, dib_data)
            except struct.error as e:
                raise BMPError(f"DIB başlığı ayrıştırma hatası: {e}")
            
            self.dib_header = DIBHeader(
                header_size=header_size,
                width=width,
                height=abs(height),  # Yükseklik negatif olabilir - alt-üst olmayan görüntü
                planes=planes,
                bit_count=bit_count,
                compression=compression,
                image_size=image_size,
                x_ppm=x_ppm,
                y_ppm=y_ppm,
                colors_used=colors_used,
                colors_important=colors_important,
                raw_data=self.raw_data[BMP_HEADER_SIZE:BMP_HEADER_SIZE+dib_size]
            )
        else:
            # BITMAPCOREHEADER gibi eski formatları desteklemiyoruz
            raise BMPError(f"Desteklenmeyen BMP formatı: {DIB_HEADER_SIZES.get(dib_size, 'Bilinmeyen')}")
        
        # Renk paletini yükle
        if self.dib_header.bit_count <= 8:
            palette_start = BMP_HEADER_SIZE + dib_size
            palette_size = self.file_header.pixel_offset - palette_start
            
            if palette_size > 0:
                self.palette = self.raw_data[palette_start:palette_start+palette_size]
        
        # Piksel verisini yükle
        pixel_start = self.file_header.pixel_offset
        if pixel_start > len(self.raw_data):
            raise BMPError("Geçersiz piksel verisi offseti")
        
        self.pixel_data = self.raw_data[pixel_start:file_size]
        
        # Dosya sonunda metadata olup olmadığını kontrol et
        self._extract_metadata()
    
    def _extract_metadata(self) -> None:
        """Dosyadan metadata çıkarmayı dener."""
        if not self.raw_data or len(self.raw_data) <= self.file_header.file_size:
            return  # Metadata yok
        
        # Dosya sonunda BMPM imzasını ara
        eof_data = self.raw_data[self.file_header.file_size:]
        
        if len(eof_data) >= 16 and eof_data[:4] == METADATA_SIGNATURE:
            try:
                # Metadata blok boyutunu oku
                block_size = struct.unpack("<I", eof_data[4:8])[0]
                
                if block_size <= len(eof_data):
                    # Sürüm, şifreleme bayrakları vb. oku
                    version = struct.unpack("<H", eof_data[8:10])[0]
                    is_encrypted = eof_data[10] == 1
                    
                    # Şifreli metadata henüz desteklenmiyor
                    if is_encrypted and not CRYPTO_AVAILABLE:
                        print("UYARI: Şifreli metadata bulundu ama şifreleme kütüphanesi yüklü değil")
                        return
                    
                    # Metadata verilerini çıkar
                    metadata_data = eof_data[12:-4]  # Son 4 bayt sağlama toplamıdır
                    
                    # Sağlama toplamını doğrula
                    stored_checksum = struct.unpack("<I", eof_data[block_size-4:block_size])[0]
                    calculated_checksum = binascii.crc32(eof_data[:block_size-4]) & 0xFFFFFFFF
                    
                    if stored_checksum != calculated_checksum:
                        print("UYARI: Metadata sağlama toplamı eşleşmiyor, veri bozulmuş olabilir")
                    
                    # Şifreli veriyi çöz (burada uygulanmamış)
                    if is_encrypted:
                        # Bu şifreleme/şifre çözme için yer tutucudur
                        pass
                    
                    # Metadata'yı yükle
                    self.metadata = Metadata.from_bytes(metadata_data)
            except Exception as e:
                print(f"Metadata ayrıştırma hatası: {e}")
    
    def add_metadata(self, metadata: Metadata, method: MetadataStorageMethod = MetadataStorageMethod.EOF_APPEND,
                     password: Optional[str] = None) -> None:
        """BMP dosyasına metadata ekler."""
        self.metadata = metadata
        
        # Şimdilik sadece EOF_APPEND metodu destekleniyor
        if method != MetadataStorageMethod.EOF_APPEND:
            raise NotImplementedError(f"Henüz desteklenmeyen metadata depolama metodu: {method}")
    
    def save(self, output_path: str) -> None:
        """BMP dosyasını kaydeder, metadata dahil."""
        if not self.file_header or not self.dib_header or not self.pixel_data:
            raise BMPError("Kaydetmeden önce geçerli bir BMP yüklenmelidir")
        
        # Orijinal BMP verisi
        output_data = bytearray(self.raw_data[:self.file_header.file_size])
        
        # Metadata ekle (varsa)
        if self.metadata:
            metadata_bytes = self._prepare_metadata_block()
            output_data.extend(metadata_bytes)
        
        with open(output_path, 'wb') as f:
            f.write(output_data)
    
    def _prepare_metadata_block(self, password: Optional[str] = None) -> bytes:
        """Metadata bloğunu hazırlar."""
        if not self.metadata:
            return b''
        
        # Metadata verilerini hazırla
        metadata_data = self.metadata.to_bytes()
        is_encrypted = False
        
        # Şifreleme (eğer parola sağlanmışsa ve kriptografi kütüphanesi mevcutsa)
        if password and CRYPTO_AVAILABLE:
            metadata_data = self._encrypt_data(metadata_data, password)
            is_encrypted = True
        
        # Metadata başlığını oluştur
        header = bytearray()
        header.extend(METADATA_SIGNATURE)  # 4 bayt imza
        
        # Tüm blok boyutunu hesaplamak için geçici yer tutucu
        header.extend(b'\x00\x00\x00\x00')  # 4 bayt blok boyutu (şimdilik 0)
        
        # Sürüm, bayraklar vb.
        header.extend(struct.pack("<H", 1))  # 2 bayt sürüm numarası
        header.append(1 if is_encrypted else 0)  # 1 bayt şifreleme bayrağı
        header.append(0)  # 1 bayt rezerve
        
        # Metadata verilerini ekle
        full_block = bytearray(header)
        full_block.extend(metadata_data)
        
        # Sağlama toplamı hesapla ve ekle
        checksum = binascii.crc32(full_block) & 0xFFFFFFFF
        full_block.extend(struct.pack("<I", checksum))
        
        # Gerçek blok boyutunu güncelle
        block_size = len(full_block)
        full_block[4:8] = struct.pack("<I", block_size)
        
        return bytes(full_block)
    
    def _encrypt_data(self, data: bytes, password: str) -> bytes:
        """Veriyi şifreler."""
        if not CRYPTO_AVAILABLE:
            raise RuntimeError("Şifreleme için cryptography kütüphanesi gereklidir")
        
        # 16 baytlık rastgele tuz oluştur
        salt = os.urandom(16)
        
        # Anahtar türetme
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = kdf.derive(password.encode())
        
        # AES-GCM ile şifreleme
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, data, None)
        
        # Salt + nonce + şifreli metni birleştir
        return salt + nonce + ciphertext
    
    def _decrypt_data(self, encrypted_data: bytes, password: str) -> bytes:
        """Şifreli veriyi çözer."""
        if not CRYPTO_AVAILABLE:
            raise RuntimeError("Şifre çözme için cryptography kütüphanesi gereklidir")
        
        # Tuz ve nonce'yi ayır
        salt = encrypted_data[:16]
        nonce = encrypted_data[16:28]
        ciphertext = encrypted_data[28:]
        
        # Anahtarı türet
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = kdf.derive(password.encode())
        
        # AES-GCM ile şifre çözme
        aesgcm = AESGCM(key)
        
        try:
            return aesgcm.decrypt(nonce, ciphertext, None)
        except Exception:
            raise MetadataError("Şifre çözme başarısız: yanlış parola veya bozuk veri")
    
    @property
    def width(self) -> int:
        """Görüntü genişliğini döndürür."""
        return self.dib_header.width if self.dib_header else 0
    
    @property
    def height(self) -> int:
        """Görüntü yüksekliğini döndürür."""
        return self.dib_header.height if self.dib_header else 0
    
    @property
    def bits_per_pixel(self) -> int:
        """Piksel başına bit sayısını döndürür."""
        return self.dib_header.bit_count if self.dib_header else 0
    
    @property
    def file_size(self) -> int:
        """Dosya boyutunu döndürür."""
        return self.file_header.file_size if self.file_header else 0
    
    @property
    def pixel_data_offset(self) -> int:
        """Piksel verilerine offseti döndürür."""
        return self.file_header.pixel_offset if self.file_header else 0
    
    @property
    def compression_type(self) -> str:
        """Sıkıştırma türünü döndürür."""
        if not self.dib_header:
            return "Bilinmeyen"
        return BI_COMPRESSION.get(self.dib_header.compression, f"Bilinmeyen ({self.dib_header.compression})")
    
    @property
    def header_type(self) -> str:
        """Başlık tipini döndürür."""
        if not self.dib_header:
            return "Bilinmeyen"
        return DIB_HEADER_SIZES.get(self.dib_header.header_size, f"Bilinmeyen ({self.dib_header.header_size})")
    
    def get_info(self) -> Dict[str, Any]:
        """BMP dosyası hakkında bilgileri sözlük olarak döndürür."""
        if not self.file_header or not self.dib_header:
            return {"error": "BMP yüklenmedi"}
        
        info = {
            "file_name": os.path.basename(self.file_path) if self.file_path else "Bilinmeyen",
            "file_size": self.file_size,
            "header_type": self.header_type,
            "dimensions": f"{self.width}x{self.height}",
            "bit_depth": self.bits_per_pixel,
            "compression": self.compression_type,
            "has_metadata": self.metadata is not None
        }
        
        if self.metadata:
            info["metadata_keys"] = list(self.metadata.entries.keys())
        
        return info
    
    def extract_metadata(self, password: Optional[str] = None) -> Optional[Metadata]:
        """Dosyadan metadata çıkarır ve döndürür."""
        return self.metadata


class LSBSteganography:
    """En Az Önemli Bit (LSB) steganografi sınıfı."""
    
    def __init__(self, bmp_file: BMPFile):
        self.bmp_file = bmp_file
        
        if not self.bmp_file.pixel_data:
            raise SteganographyError("Steganografi için piksel verisi gereklidir")
        
        # BMP formatı kontrolü
        if self.bmp_file.bits_per_pixel != 24 and self.bmp_file.bits_per_pixel != 32:
            raise SteganographyError(f"LSB steganografi sadece 24-bit veya 32-bit BMP dosyalarını destekler, şu anki: {self.bmp_file.bits_per_pixel}")
        
        if self.bmp_file.compression_type != "BI_RGB":
            raise SteganographyError(f"LSB steganografi sıkıştırmasız BMP dosyaları gerektirir, şu anki: {self.bmp_file.compression_type}")
    
    def calculate_capacity(self, bit_depth: int = DEFAULT_LSB_DEPTH, channels: int = DEFAULT_LSB_CHANNELS) -> int:
        """LSB steganografi ile saklanabilecek maksimum bayt sayısını hesaplar."""
        bytes_per_pixel = self.bmp_file.bits_per_pixel // 8
        usable_channels = min(channels, bytes_per_pixel)
        
        # Toplam bit kapasitesi
        total_bits = self.bmp_file.width * self.bmp_file.height * usable_channels * bit_depth
        
        # Kapasite baytlara dönüştürülür (8 bit = 1 bayt)
        byte_capacity = total_bits // 8
        
        # 4 baytlık veri uzunluğu bilgisi için alan ayır
        return max(0, byte_capacity - 4)
    
    def hide_data(self, data: bytes, bit_depth: int = DEFAULT_LSB_DEPTH, 
                 channels: int = DEFAULT_LSB_CHANNELS, password: Optional[str] = None) -> None:
        """Verilen veriyi BMP görüntüsünde gizler."""
        max_capacity = self.calculate_capacity(bit_depth, channels)
        
        if len(data) > max_capacity:
            raise SteganographyError(f"Veri çok büyük: {len(data)} bayt > {max_capacity} bayt (maksimum kapasite)")
        
        # Şifreleme (eğer parola sağlanmışsa)
        if password and CRYPTO_AVAILABLE:
            data = self._encrypt_data(data, password)
        
        # 4 baytlık veri uzunluğu + veri
        data_to_hide = struct.pack("<I", len(data)) + data
        
        # Veriyi bit dizisine dönüştür
        data_bits = []
        for byte in data_to_hide:
            for i in range(8):
                data_bits.append((byte >> i) & 1)
        
        # BMP piksel verisinin bir kopyasını oluştur
        new_pixel_data = bytearray(self.bmp_file.pixel_data)
        bytes_per_pixel = self.bmp_file.bits_per_pixel // 8
        usable_channels = min(channels, bytes_per_pixel)
        
        bit_index = 0
        total_bits = len(data_bits)
        
        # Her pikseldeki her kanalın her bitini güncelle
        for i in range(0, len(new_pixel_data), bytes_per_pixel):
            # Her kanal için
            for c in range(usable_channels):
                if i + c >= len(new_pixel_data):
                    break
                
                # Her bit için (belirtilen bit derinliğine göre)
                for b in range(bit_depth):
                    if bit_index >= total_bits:
                        break
                    
                    # En düşük önemli bit(ler)i değiştir
                    if data_bits[bit_index] == 1:
                        new_pixel_data[i + c] |= (1 << b)
                    else:
                        new_pixel_data[i + c] &= ~(1 << b)
                    
                    bit_index += 1
                    
                    if bit_index >= total_bits:
                        break
            
            if bit_index >= total_bits:
                break
        
        # Güncellenmiş piksel verisini BMP dosyasına kaydet
        self.bmp_file.pixel_data = bytes(new_pixel_data)
    
    def extract_data(self, bit_depth: int = DEFAULT_LSB_DEPTH, 
                    channels: int = DEFAULT_LSB_CHANNELS, 
                    password: Optional[str] = None) -> bytes:
        """BMP görüntüsündeki gizli veriyi çıkarır."""
        if not self.bmp_file.pixel_data:
            raise SteganographyError("Veri çıkarmak için piksel verisi gereklidir")
        
        bytes_per_pixel = self.bmp_file.bits_per_pixel // 8
        usable_channels = min(channels, bytes_per_pixel)
        
        # Önce 4 baytlık veri uzunluğunu çıkar
        length_bits = []
        bit_index = 0
        
        # Piksel verilerinden bitleri çıkar
        for i in range(0, len(self.bmp_file.pixel_data), bytes_per_pixel):
            for c in range(usable_channels):
                if i + c >= len(self.bmp_file.pixel_data):
                    break
                
                for b in range(bit_depth):
                    bit_value = (self.bmp_file.pixel_data[i + c] >> b) & 1
                    length_bits.append(bit_value)
                    
                    bit_index += 1
                    if bit_index >= 32:  # 4 bayt = 32 bit
                        break
                
                if bit_index >= 32:
                    break
            
            if bit_index >= 32:
                break
        
        # Bit dizisini 4 baytlık uzunluk değerine dönüştür
        length_bytes = bytearray(4)
        for i, bit in enumerate(length_bits):
            byte_index = i // 8
            bit_position = i % 8
            if bit:
                length_bytes[byte_index] |= (1 << bit_position)
        
        data_length = struct.unpack("<I", length_bytes)[0]
        
        # Maksimum kapasiteyi kontrol et
        max_capacity = self.calculate_capacity(bit_depth, channels)
        if data_length > max_capacity:
            raise SteganographyError(f"Geçersiz veri uzunluğu: {data_length} > {max_capacity}")
        
        # Şimdi gerçek veriyi çıkar
        data_bits = []
        bit_index = 32  # Veri uzunluğundan sonra başla
        bits_needed = data_length * 8
        
        for i in range(0, len(self.bmp_file.pixel_data), bytes_per_pixel):
            for c in range(usable_channels):
                if i + c >= len(self.bmp_file.pixel_data):
                    break
                
                for b in range(bit_depth):
                    if bit_index >= 32 + bits_needed:
                        break
                    
                    bit_value = (self.bmp_file.pixel_data[i + c] >> b) & 1
                    data_bits.append(bit_value)
                    
                    bit_index += 1
                
                if bit_index >= 32 + bits_needed:
                    break
            
            if bit_index >= 32 + bits_needed:
                break
        
        # Bit dizisini baytlara dönüştür
        extracted_data = bytearray(data_length)
        for i, bit in enumerate(data_bits[:bits_needed]):
            byte_index = i // 8
            bit_position = i % 8
            if bit:
                extracted_data[byte_index] |= (1 << bit_position)
        
        # Şifre çözme (eğer parola sağlanmışsa)
        if password and CRYPTO_AVAILABLE:
            try:
                extracted_data = self._decrypt_data(extracted_data, password)
            except Exception as e:
                raise SteganographyError(f"Şifre çözme hatası: {e}")
        
        return bytes(extracted_data)
    
    def _encrypt_data(self, data: bytes, password: str) -> bytes:
        """Veriyi şifreler."""
        if not CRYPTO_AVAILABLE:
            raise RuntimeError("Şifreleme için cryptography kütüphanesi gereklidir")
        
        # 16 baytlık rastgele tuz oluştur
        salt = os.urandom(16)
        
        # Anahtar türetme
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = kdf.derive(password.encode())
        
        # AES-GCM ile şifreleme
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, data, None)
        
        # Salt + nonce + şifreli metni birleştir
        return salt + nonce + ciphertext
    
    def _decrypt_data(self, encrypted_data: bytes, password: str) -> bytes:
        """Şifreli veriyi çözer."""
        if not CRYPTO_AVAILABLE:
            raise RuntimeError("Şifre çözme için cryptography kütüphanesi gereklidir")
        
        if len(encrypted_data) < 28:  # 16 (salt) + 12 (nonce) bayt minimum
            raise SteganographyError("Geçersiz şifreli veri: çok kısa")
        
        # Tuz ve nonce'yi ayır
        salt = encrypted_data[:16]
        nonce = encrypted_data[16:28]
        ciphertext = encrypted_data[28:]
        
        # Anahtarı türet
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = kdf.derive(password.encode())
        
        # AES-GCM ile şifre çözme
        aesgcm = AESGCM(key)
        
        try:
            return aesgcm.decrypt(nonce, ciphertext, None)
        except Exception:
            raise SteganographyError("Şifre çözme başarısız: yanlış parola veya bozuk veri")
    
    def hide_text(self, text: str, encoding: str = 'utf-8', **kwargs) -> None:
        """Metin mesajını BMP görüntüsünde gizler."""
        text_data = text.encode(encoding)
        self.hide_data(text_data, **kwargs)
    
    @staticmethod
    def extract_text(bmp_path: str, encoding: str = 'utf-8', **kwargs) -> str:
        """BMP görüntüsündeki gizli metni çıkarır."""
        bmp = BMPFile(bmp_path)
        stego = LSBSteganography(bmp)
        extracted_data = stego.extract_data(**kwargs)
        
        try:
            return extracted_data.decode(encoding)
        except UnicodeDecodeError:
            raise SteganographyError(f"{encoding} olarak metin çözme başarısız, farklı bir kodlama deneyin veya parola gerekebilir")


def main():
    """BMP Manipülatörü için ana komut satırı arayüzü."""
    parser = argparse.ArgumentParser(description="BMP Manipülatörü - BMP dosyalarını değiştirme ve steganografi aracı")
    subparsers = parser.add_subparsers(dest="command", help="Komut")
    
    # info komutu
    parser_info = subparsers.add_parser("info", help="BMP dosyası hakkında bilgi göster")
    parser_info.add_argument("file", help="BMP dosya yolu")
    
    # metadata komutları
    parser_metadata = subparsers.add_parser("metadata", help="Metadata işlemleri")
    metadata_subparsers = parser_metadata.add_subparsers(dest="metadata_command", help="Metadata komutu")
    
    # metadata add komutu
    parser_metadata_add = metadata_subparsers.add_parser("add", help="BMP dosyasına metadata ekle")
    parser_metadata_add.add_argument("file", help="BMP dosya yolu")
    parser_metadata_add.add_argument("--key", required=True, help="Metadata anahtarı")
    parser_metadata_add.add_argument("--value", required=True, help="Metadata değeri")
    parser_metadata_add.add_argument("--output", help="Çıktı dosya yolu (belirtilmezse orijinal dosya üzerine yazılır)")
    parser_metadata_add.add_argument("--password", help="Metadata şifreleme parolası")
    
    # metadata extract komutu
    parser_metadata_extract = metadata_subparsers.add_parser("extract", help="BMP dosyasından metadata çıkar")
    parser_metadata_extract.add_argument("file", help="BMP dosya yolu")
    parser_metadata_extract.add_argument("--password", help="Metadata şifre çözme parolası")
    
    # stego komutları
    parser_stego = subparsers.add_parser("stego", help="Steganografi işlemleri")
    stego_subparsers = parser_stego.add_subparsers(dest="stego_command", help="Steganografi komutu")
    
    # stego hide komutu
    parser_stego_hide = stego_subparsers.add_parser("hide", help="BMP dosyasında veri gizle")
    parser_stego_hide.add_argument("file", help="Taşıyıcı BMP dosya yolu")
    group = parser_stego_hide.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", help="Gizlenecek metin")
    group.add_argument("--file", help="Gizlenecek dosya yolu", dest="hide_file")
    parser_stego_hide.add_argument("--output", required=True, help="Çıktı BMP dosya yolu")
    parser_stego_hide.add_argument("--bit-depth", type=int, default=DEFAULT_LSB_DEPTH, help=f"Bit derinliği (varsayılan: {DEFAULT_LSB_DEPTH})")
    parser_stego_hide.add_argument("--channels", type=int, default=DEFAULT_LSB_CHANNELS, help=f"Kullanılacak renk kanalı sayısı (varsayılan: {DEFAULT_LSB_CHANNELS})")
    parser_stego_hide.add_argument("--password", help="Veri şifreleme parolası")
    
    # stego extract komutu
    parser_stego_extract = stego_subparsers.add_parser("extract", help="BMP dosyasından gizli veri çıkar")
    parser_stego_extract.add_argument("file", help="BMP dosya yolu")
    parser_stego_extract.add_argument("--output", help="Çıktı dosya yolu (belirtilmezse metin olarak göster)")
    parser_stego_extract.add_argument("--bit-depth", type=int, default=DEFAULT_LSB_DEPTH, help=f"Bit derinliği (varsayılan: {DEFAULT_LSB_DEPTH})")
    parser_stego_extract.add_argument("--channels", type=int, default=DEFAULT_LSB_CHANNELS, help=f"Kullanılacak renk kanalı sayısı (varsayılan: {DEFAULT_LSB_CHANNELS})")
    parser_stego_extract.add_argument("--password", help="Veri şifre çözme parolası")
    
    # Argümanları ayrıştır
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == "info":
            bmp = BMPFile(args.file)
            info = bmp.get_info()
            
            print(f"BMP Dosya Bilgisi: {info['file_name']}")
            print(f"Boyut: {info['file_size']} bayt")
            print(f"Başlık tipi: {info['header_type']}")
            print(f"Boyutlar: {info['dimensions']}")
            print(f"Renk derinliği: {info['bit_depth']} bit")
            print(f"Sıkıştırma: {info['compression']}")
            
            if info['has_metadata']:
                print(f"Metadata: Var (Anahtarlar: {', '.join(info['metadata_keys'])})")
            else:
                print("Metadata: Yok")
        
        elif args.command == "metadata":
            if args.metadata_command == "add":
                bmp = BMPFile(args.file)
                
                # Mevcut metadata'yı yükle veya yeni oluştur
                metadata = bmp.extract_metadata() or Metadata()
                
                # Yeni metadata ekle
                metadata.add(args.key, args.value)
                
                # BMP'ye metadata ekle
                bmp.add_metadata(metadata, password=args.password)
                
                # Kaydet
                output_path = args.output or args.file
                bmp.save(output_path)
                
                print(f"Metadata eklendi: {args.key}={args.value}")
                print(f"Dosya kaydedildi: {output_path}")
            
            elif args.metadata_command == "extract":
                bmp = BMPFile(args.file)
                metadata = bmp.extract_metadata(password=args.password)
                
                if metadata:
                    print("BMP Metadata:")
                    for key, value in metadata.entries.items():
                        print(f"  {key}: {value}")
                else:
                    print("Metadata bulunamadı")
            
            else:
                parser_metadata.print_help()
        
        elif args.command == "stego":
            if args.stego_command == "hide":
                bmp = BMPFile(args.file)
                stego = LSBSteganography(bmp)
                
                if args.text:
                    # Metin gizle
                    stego.hide_text(args.text, bit_depth=args.bit_depth, 
                                  channels=args.channels, password=args.password)
                    print(f"Metin mesajı gizlendi ({len(args.text)} karakter)")
                
                elif args.hide_file:
                    # Dosya gizle
                    with open(args.hide_file, "rb") as f:
                        file_data = f.read()
                    
                    stego.hide_data(file_data, bit_depth=args.bit_depth, 
                                  channels=args.channels, password=args.password)
                    print(f"Dosya gizlendi: {args.hide_file} ({len(file_data)} bayt)")
                
                # Kaydet
                bmp.save(args.output)
                print(f"Steganografi uygulanmış BMP kaydedildi: {args.output}")
            
            elif args.stego_command == "extract":
                bmp = BMPFile(args.file)
                stego = LSBSteganography(bmp)
                
                extracted_data = stego.extract_data(bit_depth=args.bit_depth, 
                                                 channels=args.channels, 
                                                 password=args.password)
                
                if args.output:
                    # Veriyi dosyaya kaydet
                    with open(args.output, "wb") as f:
                        f.write(extracted_data)
                    print(f"Çıkarılan veri dosyaya kaydedildi: {args.output} ({len(extracted_data)} bayt)")
                else:
                    # Veriyi metin olarak yazdırmayı dene
                    try:
                        text = extracted_data.decode("utf-8")
                        print("Çıkarılan metin:")
                        print(text)
                    except UnicodeDecodeError:
                        print(f"Çıkarılan veri metin değil. Boyut: {len(extracted_data)} bayt")
                        print("Veriyi kaydetmek için --output parametresini kullanın")
            
            else:
                parser_stego.print_help()
        
        else:
            parser.print_help()
    
    except Exception as e:
        print(f"HATA: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())