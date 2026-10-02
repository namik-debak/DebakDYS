# Bozdemir Makine — Üretim Planlama

Makine üretimi için tarayıcı tabanlı Gantt planlama uygulaması. Excel yerine HTML; planlanan ve gerçekleşen tarihler yan yana izlenir.

## Süreç akışı

```
Satış & Pazarlama → Tasarım → Satın Alma → Üretim → Kalite Kontrol → Montaj & Otomasyon
```

| Aşama | Planlama mantığı |
| --- | --- |
| **Tasarım** | Montaj grupları (Pinol, Rulo, Dişli Kutusu, Şasi…) |
| **Üretim — Talaşlı imalat** | Ürün grupları (Ø18, flanş vb.) — tezgâh ayarı |
| **Üretim — Kaynak / Boyahane** | Ayrı alt süreçler |
| **Montaj & Otomasyon** | Tasarım ile aynı montaj grupları |

## Özellikler

- **Dashboard** — kim ne üzerinde, gecikme günü, süre katsayısı (gerçek / plan)
- **Gantt** — kesikli çubuk = planlanan, dolu = gerçekleşen; kırmızı = gecikme
- **CNC Tezgâh** — işler ürün grubuna göre kolonlarda
- **Projeler** — ilerleme ve gecikme özeti
- Veriler tarayıcı `localStorage` içinde saklanır; JSON dışa aktarma desteklenir

## Kurulum / çalıştırma

### Windows (önerilen)

`start.bat` dosyasına çift tıklayın. Sunucu `http://127.0.0.1:8765/` adresinde açılır.

### Manuel

```bash
cd planning   # veya depo kökü
python -m http.server 8765
```

Tarayıcıda: [http://127.0.0.1:8765/](http://127.0.0.1:8765/)

> Python 3 gerekir. Port doluysa `start.bat` eski süreci otomatik kapatır.

## Klasör yapısı

```
├── index.html          # Ana arayüz
├── start.bat           # Windows başlatıcı
├── css/
│   └── planning.css
└── js/
    ├── data.js         # Makine tipleri, gruplar, örnek projeler
    └── app.js          # Dashboard, Gantt, CNC, formlar
```

## Veriyi özelleştirme

`js/data.js` içinde düzenleyebilirsiniz:

- `machineTypes` — makine tipleri (7 çeşit)
- `assemblyGroups` — tasarım / montaj grupları
- `productGroups` — CNC ürün grupları
- `people` — sorumlular
- Örnek projeler — `createSampleProjects()`

Uygulama içinden **Sıfırla** ile örnek veriye dönülür; **Dışa Aktar** ile JSON alınır.

## Gereksinimler

- Modern tarayıcı (Chrome, Edge, Firefox)
- Python 3 (yalnızca yerel sunucu için; uygulama saf HTML/CSS/JS)

## Lisans

Özel kullanım — Bozdemir Makine.
