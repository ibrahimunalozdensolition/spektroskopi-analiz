# Spektroskopi Sistemi Kullanım Kılavuzu

## Ana Kontroller (Sol taraftaki yönetim paneli):

**Start:** Kalibre edilmiş verilerin görüntülenmesi ve grafik ekranlarının oluşması için gereklidir. Aynı zamanda veri kayıtları başlatılır.

**Stop:** Stop tuşuna basılınca verilerin kaydı durdurulur.

**Calibration:** 4 adet sensörden gelen verilerin kalibrasyonu sağlanır.

**Export:** Start butonuna basıldığı andan stop tuşuna basılan ana kadar olan tüm veriler CSV formatında dışa aktarılır ve Excel dosyası ile açılabilir hale getirilir. 

## Grafik Pencereleri:

**Raw Data:** Seçilen sensörlerden gelen ham verileri mV cinsinden ekrana yansıtır.

**Calibrated Data:** Sensörlerden gelen veriler kalibrasyon ekranında yapılan kalibrasyon işlemi sonucunda oluşan işlenmiş verileri gösterir. 


## Gerçek Zamanlı Panel:

4 adet sensörden gelen verileri hem kalibre edilmiş hem de ham şeklinde gösteren panel.

Tam ekran yapılması durumunda en-boy oranını bozmadan büyüme gösterir. Veriler kaydırılabilir formattadır. Bu ekranda 4 adet sensör beraber yukarı-aşağı kaydırılabilir, grafiklerin rahat görülümü sağlanır.

## Özel Veri Üretici

Formül tabanlı veri üretim paneli kullanım şekli:

### Kullanım Adımları:
1. İlk başta üretmek istediğiniz verinin adını yazınız ve formülünü yazınız.

### Formül Yazarken Kullanabileceğiniz Operatörler ve Fonksiyonlar:
- **Operatörler:** +, -, *, /, (, )
- **Fonksiyonlar:** abs, max, min, sqrt, pow

### Formül Yazarken Kullanabileceğiniz Değişkenler:
- UV_360nm (ch1)
- Blue_450nm (ch2) 
- IR_850nm (ch3)
- IR_940nm (ch4)

### Formül Yazarken Kullanabileceğiniz Birimler:
- mV, Prime_İndex, mol/L, Litre

### Örnek Formüller:
- `ch1 + ch2 + ch3`
- `ch1 * 2.5 + ch2 * 1.8`
- `(ch1 + ch2) / 2`
- `ch1 - ch2`
- `abs(ch1 - ch3)`
- `max(ch1, ch2, ch3, ch4)`
- `sqrt(ch1 * ch1 + ch2 * ch2)`
- `ch1 * 0.85 + ch2 * 1.15 - 0.05`

### Live Modu:
Formül yazarken formülün sonucunu canlı olarak gösterir. Üretilen formülün çıktısının alınması için hem verinin ekran üzerinden çift tıklanarak seçili hale getirilmesi hem de live modun açılması gerekmektedir. Bu işlemin yapılmasının sebebi işlemci yükünü azaltarak kapasitesi düşük bilgisayarlarda performans sağlamaktır. 

### Kontroller:
Bu program ile yapılan başka bir denklemi içeriye aktarma ya da halihazırda var olan denklemi dışarıya aktarma işlemi. Bu uygulamanın olduğu başka programlarda kullanmak için. 

## Veri Kaydetme:

Panelin amacı seçilen süre kadar (varsayılan olarak 15 saniye) 4 sensör için veri kaydı yapmaktır.

Bu veriler raw_data ve cal_data olarak incelenir. Eğer eşik %10'dan fazla ya da %10'dan az ya da bu iki değerin arasındaysa buna göre bir pop-up şeklinde çıktı verir.

Hangi çıktının verilmesi isteniyorsa bu yazılar `config` klasörünün içinde bulunan `status_messages.json` dosyası ile düzenlenir.

### Düzenlenme Şekli:
- `sensor_order` kısmında yazdığı gibi 4 adet sensörün adının yazıldığı sırada durumlar yazılır.
- ":" işareti kullanımının ardından çift tırnak içine yazılan mesaj, istenilen durum elde edildiği zaman gösterilir. 

### Karşılaştırma:
Karşılaştırma için yapılması gereken comparison kısmında iki adet istenilen veri seçilir ve "Compare Selected Records" tuşuna basılır. Ardından karşılaştırma işlemi gerçekleştirilmiş olur.

## Hakkında Ekranı

About ekranı geliştirici olan İbrahim ÜNAL hakkında hem mail adresi hem de geliştirme motivasyonu hakkında bilgi verir. Uygulama özellikleri hakkında da kısa bir bilgilendirme manifestosu şeklindedir. 


## LED İsimlerini Değiştirme:

Ana sayfada bulunan `app_settings.json` dosyasında bulunan `led_names` kısmından isim değişikliği yapılabilir durumdadır.

":" işaretinden sonra gelen kısma (tırnak işaretinin içi için geçerli bu durum) verilen isim, uygulamanın yeniden başlatılması ile uygulanacaktır. 

