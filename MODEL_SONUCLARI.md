# Random Forest Model Sonuçları - Trendyol Veri Seti

## 📊 Veri Seti Bilgileri
- **Dosya**: Trendyol_Wide_Veri_Seti_2732.xlsx
- **Toplam Satır**: 2,732
- **Toplam Sütun**: 35 (işlendikten sonra 32)
- **Hedef Değişken**: Ek_Ozellikler
- **Problem Tipi**: Regression (Regresyon)

## 🔧 Veri Ön İşleme
1. **Gereksiz sütunlar kaldırıldı**: `Urun_Adi`
2. **Tamamen boş sütunlar silindi**: `Beden`, `Stil` (%100 eksik)
3. **Eksik değerler**:
   - Numerik değerler: Median ile dolduruldu
   - Kategorik değerler: Mode ile dolduruldu
4. **Kategorik değişkenler**: Label Encoding ile sayısallaştırıldı
   - `Urun_Linki`: 2,256 benzersiz değer

## 📈 Model Parametreleri
```python
RandomForestRegressor(
    n_estimators=100,      # 100 ağaç
    max_depth=20,          # Maksimum derinlik: 20
    min_samples_split=5,   # Bölünme için minimum örnek: 5
    min_samples_leaf=2,    # Yaprak için minimum örnek: 2
    random_state=42,
    n_jobs=-1              # Tüm CPU çekirdekleri kullanıldı
)
```

## 🎯 Model Performansı

### Train Seti Sonuçları
- **R² Score**: 0.7583 (75.83%)
- **MSE**: 1,335.65
- **RMSE**: 36.55
- **MAE**: 26.09

### Test Seti Sonuçları
- **R² Score**: 0.1679 (16.79%)
- **MSE**: 4,543.81
- **RMSE**: 67.41
- **MAE**: 48.81

### Cross-Validation (5-Fold)
- **CV R² Skorları**: [0.2248, 0.1706, 0.2811, 0.2845, 0.1702]
- **Ortalama CV R²**: 0.2262 (+/- 0.1006)

## 🏆 En Önemli 20 Özellik (Feature Importance)

| Sıra | Özellik | Önem Derecesi |
|------|---------|---------------|
| 1 | Urun_Linki | 0.1207 (12.07%) |
| 2 | Renk | 0.0788 (7.88%) |
| 3 | Kalıp | 0.0631 (6.31%) |
| 4 | Astar_Durumu | 0.0606 (6.06%) |
| 5 | Siluet | 0.0488 (4.88%) |
| 6 | Kategori | 0.0483 (4.83%) |
| 7 | Boy | 0.0482 (4.82%) |
| 8 | Koleksiyon | 0.0479 (4.79%) |
| 9 | Materyal_Kumas_Tipi | 0.0460 (4.60%) |
| 10 | Dokuma_Tipi_Detay | 0.0449 (4.49%) |
| 11 | Dokuma_Tipi | 0.0445 (4.45%) |
| 12 | Desen | 0.0428 (4.28%) |
| 13 | Baski_Nakis_Teknigi | 0.0414 (4.14%) |
| 14 | Ortam | 0.0362 (3.62%) |
| 15 | Kol_Boyu | 0.0310 (3.10%) |
| 16 | Kapama_Sekli | 0.0257 (2.57%) |
| 17 | Persona | 0.0225 (2.25%) |
| 18 | Cep | 0.0193 (1.93%) |
| 19 | Surdurulebilirlik_Detayi | 0.0184 (1.84%) |
| 20 | Sezon | 0.0179 (1.79%) |

## 📊 Oluşturulan Dosyalar
1. **trendyol_random_forest_model.pkl** - Eğitilmiş model dosyası
2. **feature_importance.png** - Özellik önem grafiği
3. **prediction_plot.png** - Gerçek vs Tahmin grafiği

## 💡 Model Değerlendirmesi

### ✅ Güçlü Yönler
- Train setinde yüksek performans (R²=0.76)
- 100 ağaç ile güçlü ensemble yapısı
- Tüm özelliklerin önem dereceleri hesaplandı
- Model başarıyla kaydedildi ve tekrar kullanılabilir

### ⚠️ İyileştirme Alanları
- **Overfitting**: Train (R²=0.76) ve test (R²=0.17) arasında büyük fark var
  - Model train verisine çok fazla özelleşmiş (overfit)
  - Test verisinde genelleme yapamıyor
  
### 🔧 Önerilen İyileştirmeler

1. **Özellik Mühendisliği**:
   - Çok fazla benzersiz değere sahip `Urun_Linki` özelliğini kaldırmayı deneyin
   - Daha az önemli özellikleri çıkarın
   - Yeni türetilmiş özellikler ekleyin

2. **Model Hiperparametrelerini Ayarlayın**:
   ```python
   # Overfitting'i azaltmak için:
   max_depth = 10-15       # Daha sığ ağaçlar
   min_samples_split = 10  # Daha fazla örnek gereksin
   min_samples_leaf = 5    # Yapraklarda daha fazla örnek
   max_features = 'sqrt'   # Her bölünmede daha az özellik kullan
   ```

3. **Farklı Modeller Deneyin**:
   - Gradient Boosting (XGBoost, LightGBM)
   - Ridge/Lasso Regression ile regularization
   - Ensemble yöntemleri (Stacking, Blending)

4. **Veri Artırma**:
   - Daha fazla veri toplayın
   - Dengesiz dağılımları düzeltin
   - Outlier (aykırı değer) analizi yapın

5. **Hiperparametre Optimizasyonu**:
   ```python
   # Script'te uncomment edin:
   best_model = hyperparameter_tuning(X_train, y_train, task_type)
   ```

## 📝 Kullanım Örneği

```python
import joblib
import pandas as pd

# Modeli yükle
model = joblib.load('trendyol_random_forest_model.pkl')

# Yeni veri ile tahmin
# X_new = ... (aynı özelliklere sahip yeni veri)
# predictions = model.predict(X_new)
```

## 🎓 Sonuç
Model başarıyla eğitildi ancak overfitting problemi var. Yukarıdaki öneriler uygulanarak model performansı iyileştirilebilir. Test seti için R² skorunun 0.50'nin üzerine çıkarılması hedeflenmelidir.

---
**Tarih**: 25 Aralık 2025  
**Model**: Random Forest Regressor  
**Scikit-learn Versiyonu**: 1.6.1
