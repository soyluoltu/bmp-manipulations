import tkinter as tk
from tkinter import filedialog, ttk, messagebox, scrolledtext
import struct
import os
import time
from collections import Counter
import threading
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

class BMPAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("BMP Dosya & Renk Analiz Programı")
        self.root.geometry("1024x768")
        self.root.configure(bg="#f0f0f0")
        
        # Uygulama simgesi (opsiyonel)
        # self.root.iconbitmap("icon.ico")
        
        # Değişkenler
        self.file_path = tk.StringVar()
        self.status_text = tk.StringVar()
        self.status_text.set("Hazır. Lütfen bir BMP dosyası seçin.")
        self.image_data = None
        self.analysis_result = None
        self.color_distribution = None
        
        # Ana çerçeve
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Üst panel - Dosya seçimi
        self.file_frame = ttk.LabelFrame(self.main_frame, text="BMP Dosyası")
        self.file_frame.pack(fill="x", padx=5, pady=5)
        
        self.file_entry = ttk.Entry(self.file_frame, textvariable=self.file_path, width=70)
        self.file_entry.pack(side="left", padx=5, pady=5, fill="x", expand=True)
        
        self.browse_button = ttk.Button(self.file_frame, text="Dosya Seç", command=self.browse_file)
        self.browse_button.pack(side="left", padx=5, pady=5)
        
        self.analyze_button = ttk.Button(self.file_frame, text="Analiz Et", command=self.start_analysis)
        self.analyze_button.pack(side="left", padx=5, pady=5)
        
        # Orta panel - Analiz sonuçları
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Sekme 1: Görüntü ve Temel Bilgiler
        self.info_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.info_frame, text="Görüntü ve Bilgiler")
        
        # Görüntü ve Bilgiler için yatay düzen
        self.info_pane = ttk.PanedWindow(self.info_frame, orient="horizontal")
        self.info_pane.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Sol taraf - Görüntü
        self.image_frame = ttk.LabelFrame(self.info_pane, text="BMP Görüntüsü")
        self.info_pane.add(self.image_frame, weight=1)
        
        self.image_label = ttk.Label(self.image_frame)
        self.image_label.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Sağ taraf - Temel Bilgiler
        self.details_frame = ttk.LabelFrame(self.info_pane, text="Dosya Bilgileri")
        self.info_pane.add(self.details_frame, weight=1)
        
        self.details_text = scrolledtext.ScrolledText(self.details_frame, width=40, height=15, wrap=tk.WORD)
        self.details_text.pack(fill="both", expand=True, padx=5, pady=5)
        self.details_text.config(state="disabled")
        
        # Sekme 2: Renk Analizi
        self.color_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.color_frame, text="Renk Analizi")
        
        # Renk analizi için yatay düzen
        self.color_pane = ttk.PanedWindow(self.color_frame, orient="horizontal")
        self.color_pane.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Sol taraf - Renk Dağılımı Grafiği
        self.chart_frame = ttk.LabelFrame(self.color_pane, text="Renk Dağılımı")
        self.color_pane.add(self.chart_frame, weight=2)
        
        # Renk grafiği için placeholder
        self.figure = plt.Figure(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, self.chart_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Sağ taraf - En Çok Kullanılan Renkler Listesi
        self.color_list_frame = ttk.LabelFrame(self.color_pane, text="En Çok Kullanılan Renkler")
        self.color_pane.add(self.color_list_frame, weight=1)
        
        # Renk listesi için scrollbar
        self.color_list = ttk.Treeview(self.color_list_frame, columns=("color", "count", "percent"), show="headings")
        self.color_list.heading("color", text="RGB Değeri")
        self.color_list.heading("count", text="Piksel Sayısı")
        self.color_list.heading("percent", text="Yüzde (%)")
        
        self.color_list.column("color", width=100)
        self.color_list.column("count", width=80)
        self.color_list.column("percent", width=80)
        
        scrollbar = ttk.Scrollbar(self.color_list_frame, orient="vertical", command=self.color_list.yview)
        self.color_list.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        self.color_list.pack(side="left", fill="both", expand=True)
        
        # Durum çubuğu
        self.status_bar = ttk.Label(root, textvariable=self.status_text, relief="sunken", anchor="w")
        self.status_bar.pack(side="bottom", fill="x")
        
        # İleri düzey özellikler için menü
        self.create_menu()
        
    def create_menu(self):
        menubar = tk.Menu(self.root)
        
        # Dosya menüsü
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Aç", command=self.browse_file)
        file_menu.add_command(label="Analiz Et", command=self.start_analysis)
        file_menu.add_separator()
        file_menu.add_command(label="Çıkış", command=self.root.quit)
        menubar.add_cascade(label="Dosya", menu=file_menu)
        
        # Analiz menüsü
        analyze_menu = tk.Menu(menubar, tearoff=0)
        analyze_menu.add_command(label="Renk Analizi", command=self.show_color_analysis)
        analyze_menu.add_command(label="Rapor Oluştur", command=self.create_report)
        menubar.add_cascade(label="Analiz", menu=analyze_menu)
        
        # Yardım menüsü
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Hakkında", command=self.show_about)
        menubar.add_cascade(label="Yardım", menu=help_menu)
        
        self.root.config(menu=menubar)
    
    def browse_file(self):
        file_path = filedialog.askopenfilename(
            title="BMP Dosyası Seç",
            filetypes=[("BMP Dosyaları", "*.bmp"), ("Tüm Dosyalar", "*.*")]
        )
        
        if file_path:
            self.file_path.set(file_path)
            self.status_text.set(f"Dosya seçildi: {os.path.basename(file_path)}")
            
            # Dosya uzantısını kontrol et
            if not file_path.lower().endswith('.bmp'):
                messagebox.showwarning(
                    "Dosya Türü Uyarısı", 
                    "Seçilen dosya '.bmp' uzantılı değil. Dosya bir BMP dosyası olmayabilir."
                )
            
            # Seçilen dosyayı göster
            self.load_image_preview()
    
    def load_image_preview(self):
        try:
            file_path = self.file_path.get()
            if not file_path:
                return
            
            # PIL ile görüntüyü yükle
            img = Image.open(file_path)
            
            # Görüntüyü uygun boyuta getir
            width, height = img.size
            max_size = 400
            
            if width > max_size or height > max_size:
                ratio = min(max_size / width, max_size / height)
                new_width = int(width * ratio)
                new_height = int(height * ratio)
                img = img.resize((new_width, new_height), Image.LANCZOS)
            
            # Tkinter için görüntüyü hazırla
            self.image_data = ImageTk.PhotoImage(img)
            self.image_label.config(image=self.image_data)
            
            # Temel dosya bilgilerini göster
            file_size = os.path.getsize(file_path)
            file_size_kb = file_size / 1024
            file_size_mb = file_size_kb / 1024
            
            file_info = (
                f"Dosya: {os.path.basename(file_path)}\n"
                f"Boyut: {file_size:,} byte"
            )
            
            if file_size_kb >= 1:
                file_info += f" ({file_size_kb:.2f} KB)"
            if file_size_mb >= 1:
                file_info += f" ({file_size_mb:.2f} MB)"
            
            file_info += f"\nGenişlik: {width} piksel\nYükseklik: {height} piksel\n"
            
            self.update_details_text(file_info)
            
        except Exception as e:
            messagebox.showerror("Hata", f"Görüntü yüklenirken bir hata oluştu:\n{str(e)}")
            self.status_text.set("Hata: Görüntü yüklenemedi.")
    
    def update_details_text(self, text):
        self.details_text.config(state="normal")
        self.details_text.delete(1.0, tk.END)
        self.details_text.insert(tk.END, text)
        self.details_text.config(state="disabled")
    
    def start_analysis(self):
        file_path = self.file_path.get()
        if not file_path:
            messagebox.showinfo("Bilgi", "Lütfen önce bir BMP dosyası seçin.")
            return
        
        # Analizi arka planda çalıştır
        self.status_text.set("Analiz yapılıyor... Lütfen bekleyin.")
        self.analyze_button.config(state="disabled")
        
        # Analizi ayrı bir thread'de başlat
        thread = threading.Thread(target=self.run_analysis, daemon=True)
        thread.start()
    
    def run_analysis(self):
        try:
            file_path = self.file_path.get()
            start_time = time.time()
            
            # BMP analizi
            result = self.analyze_bmp_colors(file_path)
            
            if result:
                total_pixels, unique_color_count, color_distribution = result
                self.analysis_result = result
                self.color_distribution = color_distribution
                
                # GUI güncelleme işlemleri ana thread'de yapılmalı
                self.root.after(0, lambda: self.update_analysis_results(total_pixels, unique_color_count, color_distribution))
                
                elapsed_time = time.time() - start_time
                self.status_text.set(f"Analiz tamamlandı ({elapsed_time:.2f} saniye). {unique_color_count:,} benzersiz renk bulundu.")
            else:
                self.status_text.set("Analiz sırasında bir hata oluştu.")
        
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Analiz Hatası", f"Analiz sırasında bir hata oluştu:\n{str(e)}"))
            self.status_text.set("Hata: Analiz tamamlanamadı.")
        
        finally:
            self.root.after(0, lambda: self.analyze_button.config(state="normal"))
    
    def update_analysis_results(self, total_pixels, unique_color_count, color_distribution):
        # Dosya bilgilerini güncelle
        file_path = self.file_path.get()
        
        try:
            # BMP header bilgilerini oku
            width, height, data_offset, bit_depth = self.read_bmp_header(file_path)
            file_size = os.path.getsize(file_path)
            
            # Bilgileri güncelle
            file_info = (
                f"Dosya: {os.path.basename(file_path)}\n"
                f"Boyut: {file_size:,} byte ({file_size/1024:.2f} KB)\n"
                f"Genişlik: {width} piksel\n"
                f"Yükseklik: {abs(height)} piksel\n"
                f"Bit derinliği: {bit_depth} bit\n"
                f"Toplam piksel sayısı: {total_pixels:,}\n"
                f"Benzersiz renk sayısı: {unique_color_count:,}\n"
                f"Renk çeşitliliği oranı: {unique_color_count/total_pixels*100:.2f}%\n"
            )
            
            self.update_details_text(file_info)
            
            # Renk analizini güncelle
            self.update_color_analysis(total_pixels, color_distribution)
            
            # Renk analizi sekmesine geç
            self.notebook.select(1)
            
        except Exception as e:
            messagebox.showerror("Hata", f"Sonuçlar güncellenirken hata oluştu:\n{str(e)}")
    
    def update_color_analysis(self, total_pixels, color_distribution):
        # Renk listesini temizle
        for item in self.color_list.get_children():
            self.color_list.delete(item)
        
        # En çok kullanılan 100 rengi listele
        for i, (color, count) in enumerate(color_distribution.most_common(100)):
            percent = count / total_pixels * 100
            
            if isinstance(color, tuple) and len(color) >= 3:
                color_str = f"RGB{color[:3]}"
            else:
                color_str = f"İndeks: {color}"
            
            self.color_list.insert("", "end", values=(color_str, f"{count:,}", f"{percent:.4f}%"))
            
            # İlk rengi seç
            if i == 0:
                self.color_list.selection_set(self.color_list.get_children()[0])
        
        # Renk dağılımını görselleştir
        self.draw_color_chart(color_distribution, total_pixels)
    
    def draw_color_chart(self, color_distribution, total_pixels):
        self.figure.clear()
        
        # En çok kullanılan 10 renk için pasta grafiği
        ax = self.figure.add_subplot(111)
        
        top_colors = color_distribution.most_common(10)
        others_count = sum(count for _, count in color_distribution.most_common()[10:])
        
        if others_count > 0:
            top_colors.append(("Diğer Renkler", others_count))
        
        labels = []
        sizes = []
        colors_rgb = []
        
        for color, count in top_colors:
            if color == "Diğer Renkler":
                labels.append(color)
                colors_rgb.append("#CCCCCC")  # Gri renk
            else:
                if isinstance(color, tuple) and len(color) >= 3:
                    labels.append(f"RGB{color[:3]}")
                    # RGB değerlerini 0-1 aralığına normalize et
                    r, g, b = [c/255 for c in color[:3]]
                    colors_rgb.append((r, g, b))
                else:
                    labels.append(f"İndeks: {color}")
                    colors_rgb.append("#CCCCCC")  # Gri renk
            
            sizes.append(count)
        
        # Pasta dilimlerini yüzde olarak göster
        sizes_percent = [s / total_pixels * 100 for s in sizes]
        
        # Pasta grafiği çiz
        wedges, texts, autotexts = ax.pie(
            sizes_percent, 
            labels=None, 
            autopct='%1.1f%%',
            startangle=90,
            colors=colors_rgb
        )
        
        # Grafik başlığı ve ayarları
        ax.set_title('En Çok Kullanılan 10 Renk')
        ax.axis('equal')  # Dairesel görünüm için
        
        # Renk etiketlerini düzenle
        legend = ax.legend(wedges, labels, title="Renkler", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
        
        self.figure.tight_layout()
        self.canvas.draw()
    
    def show_color_analysis(self):
        if not self.color_distribution:
            messagebox.showinfo("Bilgi", "Lütfen önce bir BMP dosyası analiz edin.")
            return
        
        self.notebook.select(1)  # Renk analizi sekmesine geç
    
    def create_report(self):
        if not self.analysis_result:
            messagebox.showinfo("Bilgi", "Lütfen önce bir BMP dosyası analiz edin.")
            return
        
        # Rapor kaydetme dosya diyalogu
        file_path = filedialog.asksaveasfilename(
            title="Raporu Kaydet",
            defaultextension=".txt",
            filetypes=[("Metin Dosyaları", "*.txt"), ("Tüm Dosyalar", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            total_pixels, unique_color_count, color_distribution = self.analysis_result
            bmp_path = self.file_path.get()
            
            # BMP header bilgilerini oku
            width, height, data_offset, bit_depth = self.read_bmp_header(bmp_path)
            file_size = os.path.getsize(bmp_path)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("BMP DOSYA ANALİZ RAPORU\n")
                f.write("=" * 50 + "\n\n")
                
                f.write(f"Analiz Tarihi: {time.strftime('%d.%m.%Y %H:%M:%S')}\n\n")
                
                f.write("DOSYA BİLGİLERİ\n")
                f.write("-" * 30 + "\n")
                f.write(f"Dosya Adı: {os.path.basename(bmp_path)}\n")
                f.write(f"Dosya Yolu: {bmp_path}\n")
                f.write(f"Dosya Boyutu: {file_size:,} byte ({file_size/1024:.2f} KB)\n")
                f.write(f"Genişlik: {width} piksel\n")
                f.write(f"Yükseklik: {abs(height)} piksel\n")
                f.write(f"Bit Derinliği: {bit_depth} bit\n\n")
                
                f.write("RENK ANALİZİ\n")
                f.write("-" * 30 + "\n")
                f.write(f"Toplam Piksel Sayısı: {total_pixels:,}\n")
                f.write(f"Benzersiz Renk Sayısı: {unique_color_count:,}\n")
                f.write(f"Renk Çeşitliliği Oranı: {unique_color_count/total_pixels*100:.2f}%\n\n")
                
                f.write("EN ÇOK KULLANILAN RENKLER\n")
                f.write("-" * 30 + "\n")
                f.write(f"{'Renk':<20} {'Piksel Sayısı':<15} {'Yüzde (%)':<10}\n")
                f.write("-" * 50 + "\n")
                
                for i, (color, count) in enumerate(color_distribution.most_common(20)):
                    percent = count / total_pixels * 100
                    
                    if isinstance(color, tuple) and len(color) >= 3:
                        color_str = f"RGB{color[:3]}"
                    else:
                        color_str = f"İndeks: {color}"
                    
                    f.write(f"{color_str:<20} {count:<15,} {percent:<10.4f}\n")
            
            messagebox.showinfo("Bilgi", f"Rapor başarıyla kaydedildi:\n{file_path}")
            
        except Exception as e:
            messagebox.showerror("Hata", f"Rapor oluşturulurken bir hata oluştu:\n{str(e)}")
    
    def show_about(self):
        about_text = (
            "BMP Dosya Analiz Programı\n\n"
            "Bu program BMP dosyalarını analiz ederek dosyadaki benzersiz renkleri "
            "ve piksel dağılımlarını tespit eder.\n\n"
            "Geliştirilme Tarihi: Nisan 2025"
        )
        messagebox.showinfo("Hakkında", about_text)

    def read_bmp_header(self, file_path):
        """
        BMP dosyasının header bilgilerini okur ve görüntü boyutlarını döndürür.
        
        Args:
            file_path (str): BMP dosyasının yolu
            
        Returns:
            tuple: (genişlik, yükseklik, veri başlangıç offseti, bit derinliği)
        """
        with open(file_path, 'rb') as f:
            # BMP header (14 bytes)
            header = f.read(14)
            if len(header) < 14:
                raise ValueError("Geçersiz BMP dosyası: Header eksik")
            
            # BMP imzasını kontrol et
            if header[0:2] != b'BM':
                raise ValueError("Geçersiz BMP dosyası: BM imzası bulunamadı")
            
            # Veri offsetini al (piksel verisinin başladığı yer)
            data_offset = struct.unpack('<I', header[10:14])[0]
            
            # DIB header boyutu bilgisini al
            dib_header_size = struct.unpack('<I', f.read(4))[0]
            
            # DIB header'ı oku (boyutu değişebilir)
            f.seek(14)  # BMP header sonrasına git
            dib_header = f.read(dib_header_size)
            
            # Görüntü bilgilerini al
            width = struct.unpack('<i', dib_header[4:8])[0]
            height = struct.unpack('<i', dib_header[8:12])[0]
            bit_depth = struct.unpack('<H', dib_header[14:16])[0]
            
        return width, height, data_offset, bit_depth

    def analyze_bmp_colors(self, file_path):
        """
        BMP dosyasındaki benzersiz renkleri ve piksel sayısını analiz eder.
        
        Args:
            file_path (str): BMP dosyasının yolu
            
        Returns:
            tuple: (toplam piksel sayısı, benzersiz renk sayısı, renk dağılımı)
        """
        try:
            # BMP header bilgilerini oku
            width, height, data_offset, bit_depth = self.read_bmp_header(file_path)
            
            # Görüntünün toplam piksel sayısı
            total_pixels = width * abs(height)  # Height negatif olabilir (görüntü yönü)
            
            # Renk analizi için gerekli ayarlar
            bytes_per_pixel = bit_depth // 8
            row_size = ((width * bit_depth + 31) // 32) * 4  # Her satır 4 byte'a göre hizalanır
            
            # Benzersiz renkleri saymak için counter kullan
            unique_colors = Counter()
            
            with open(file_path, 'rb') as f:
                # Piksel verisinin başlangıcına git
                f.seek(data_offset)
                
                for y in range(abs(height)):
                    row_start = f.tell()
                    
                    for x in range(width):
                        # Piksel verisini oku
                        pixel_data = f.read(bytes_per_pixel)
                        
                        if len(pixel_data) < bytes_per_pixel:
                            print(f"Uyarı: Dosya beklenenden kısa ({y}/{height} satırında kesildi)")
                            break
                        
                        # Renk değeri olarak tüm pikseli bir tuple olarak kaydet
                        # BGR formatı için: (Blue, Green, Red)
                        if bit_depth == 24:  # 24-bit
                            blue, green, red = pixel_data
                            color = (red, green, blue)  # RGB formatında kaydet
                        elif bit_depth == 32:  # 32-bit (BGRA)
                            blue, green, red, alpha = pixel_data
                            color = (red, green, blue, alpha)
                        elif bit_depth == 8:  # 8-bit (indeksli)
                            color = pixel_data[0]
                        else:
                            # Diğer bit derinlikleri için basit bir yaklaşım
                            color = pixel_data
                        
                        # Rengi say
                        unique_colors[color] += 1
                    
                    # Satır sonuna git (padding var ise atla)
                    f.seek(row_start + row_size)
            
            # Analiz sonuçları
            unique_color_count = len(unique_colors)
            
            return total_pixels, unique_color_count, unique_colors
            
        except Exception as e:
            messagebox.showerror("Analiz Hatası", f"BMP analizi sırasında bir hata oluştu:\n{str(e)}")
            return None

def main():
    root = tk.Tk()
    app = BMPAnalyzerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()