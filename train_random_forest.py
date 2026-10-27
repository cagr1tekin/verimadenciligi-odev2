"""
Random Forest Model Training for Trendyol Dataset
Bu script Trendyol_Wide_Veri_Seti_2732.xlsx dosyasını kullanarak Random Forest modeli eğitir.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    classification_report, 
    confusion_matrix, 
    accuracy_score,
    mean_squared_error,
    r2_score,
    mean_absolute_error
)
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

def load_and_explore_data(file_path):
    """Veriyi yükle ve keşfet."""
    print("="*70)
    print("VERİ YÜKLEME VE KEŞİF")
    print("="*70)
    
    df = pd.read_excel(file_path, engine='openpyxl')
    print(f"\n✓ Dosya yüklendi: {file_path}")
    print(f"  - Toplam satır sayısı: {len(df)}")
    print(f"  - Toplam sütun sayısı: {len(df.columns)}")
    
    print("\n📊 Sütun İsimleri:")
    for i, col in enumerate(df.columns, 1):
        print(f"  {i}. {col}")
    
    print("\n📈 Veri Türleri:")
    print(df.dtypes)
    
    print("\n📉 Eksik Veri Analizi:")
    missing = df.isnull().sum()
    missing_percent = (missing / len(df)) * 100
    missing_df = pd.DataFrame({
        'Eksik_Sayisi': missing,
        'Eksik_Yuzdesi': missing_percent
    })
    missing_df = missing_df[missing_df['Eksik_Sayisi'] > 0].sort_values('Eksik_Sayisi', ascending=False)
    if len(missing_df) > 0:
        print(missing_df)
    else:
        print("  ✓ Hiç eksik veri yok!")
    
    print("\n📋 İlk 5 Satır:")
    print(df.head())
    
    return df

def preprocess_data(df):
    """Veriyi ön işle."""
    print("\n" + "="*70)
    print("VERİ ÖN İŞLEME")
    print("="*70)
    
    # Orijinal veriyi kopyala
    df_processed = df.copy()
    
    # 1. Gereksiz sütunları kaldır
    columns_to_drop = []
    for col in ['Unnamed: 0', 'id', 'ID', 'Urun_Adi', 'url', 'URL']:
        if col in df_processed.columns:
            columns_to_drop.append(col)
    
    if columns_to_drop:
        df_processed = df_processed.drop(columns=columns_to_drop)
        print(f"\n✓ Gereksiz sütunlar kaldırıldı: {columns_to_drop}")
    
    # 2. Tamamen boş olan sütunları kaldır (tüm değerleri NaN olan)
    print("\n📊 Tamamen boş sütunları kaldırma:")
    empty_cols = [col for col in df_processed.columns if df_processed[col].isnull().all()]
    if empty_cols:
        df_processed = df_processed.drop(columns=empty_cols)
        print(f"  ✓ Tamamen boş sütunlar kaldırıldı: {empty_cols}")
    else:
        print("  ✓ Tamamen boş sütun yok")
    
    # 3. Eksik değerleri temizle
    print("\n📊 Eksik değer işleme:")
    initial_rows = len(df_processed)
    
    # %90'dan fazla eksik değere sahip sütunları kaldır
    threshold = 0.9
    cols_to_drop = []
    for col in df_processed.columns:
        missing_pct = df_processed[col].isnull().sum() / len(df_processed)
        if missing_pct > threshold:
            cols_to_drop.append(col)
    
    if cols_to_drop:
        df_processed = df_processed.drop(columns=cols_to_drop)
        print(f"  ✓ %{threshold*100}'dan fazla eksik değerli sütunlar kaldırıldı: {cols_to_drop}")
    
    # Numerik sütunlar için median ile doldur
    numeric_cols = df_processed.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if df_processed[col].isnull().sum() > 0:
            median_val = df_processed[col].median()
            df_processed[col].fillna(median_val, inplace=True)
            print(f"  - {col}: Median ile dolduruldu ({median_val:.2f})")
    
    # Kategorik sütunlar için mode ile doldur veya 'Unknown' ile
    categorical_cols = df_processed.select_dtypes(include=['object']).columns
    for col in categorical_cols:
        if df_processed[col].isnull().sum() > 0:
            if len(df_processed[col].dropna()) > 0:
                mode_val = df_processed[col].mode()[0] if len(df_processed[col].mode()) > 0 else 'Unknown'
            else:
                mode_val = 'Unknown'
            df_processed[col].fillna(mode_val, inplace=True)
            print(f"  - {col}: Mode/Unknown ile dolduruldu ({mode_val})")
    
    # Hala NaN varsa o satırları sil
    rows_before = len(df_processed)
    df_processed = df_processed.dropna()
    rows_dropped = rows_before - len(df_processed)
    
    print(f"\n✓ Eksik değer temizliği tamamlandı.")
    print(f"  - Kalan satır: {len(df_processed)}")
    print(f"  - Silinen satır: {rows_dropped}")
    
    # 4. Kategorik değişkenleri encode et
    print("\n🔄 Kategorik değişkenler encode ediliyor:")
    label_encoders = {}
    
    # Kategorik sütunları yeniden belirle (sütunlar değişmiş olabilir)
    categorical_cols = df_processed.select_dtypes(include=['object']).columns
    
    for col in categorical_cols:
        if col in df_processed.columns:
            le = LabelEncoder()
            df_processed[col] = le.fit_transform(df_processed[col].astype(str))
            label_encoders[col] = le
            print(f"  - {col}: {len(le.classes_)} benzersiz değer encode edildi")
    
    if len(label_encoders) == 0:
        print("  ✓ Encode edilecek kategorik sütun yok")
    
    return df_processed, label_encoders

def detect_target_column(df):
    """Hedef sütunu otomatik olarak tespit et."""
    print("\n" + "="*70)
    print("HEDEF SÜTUN TESPİTİ")
    print("="*70)
    
    # Olası hedef sütun isimleri
    possible_targets = ['Fiyat', 'fiyat', 'price', 'Price', 'FIYAT', 'Puan', 'puan', 'rating', 'Rating']
    
    for target in possible_targets:
        if target in df.columns:
            print(f"\n✓ Hedef sütun bulundu: {target}")
            print(f"  - Veri tipi: {df[target].dtype}")
            print(f"  - Min: {df[target].min():.2f}")
            print(f"  - Max: {df[target].max():.2f}")
            print(f"  - Ortalama: {df[target].mean():.2f}")
            print(f"  - Medyan: {df[target].median():.2f}")
            
            # Benzersiz değer sayısını kontrol et
            unique_count = df[target].nunique()
            print(f"  - Benzersiz değer sayısı: {unique_count}")
            
            # Regresyon mu Classification mı?
            if unique_count < 20:
                print(f"  ⚠ Az benzersiz değer ({unique_count}) - Classification olarak işlenebilir")
                task_type = 'classification'
            else:
                print(f"  ✓ Çok benzersiz değer ({unique_count}) - Regression problemi")
                task_type = 'regression'
            
            return target, task_type
    
    # Hiçbir hedef bulunamazsa, son sütunu hedef olarak al
    target = df.columns[-1]
    print(f"\n⚠ Otomatik hedef tespit edilemedi. Son sütun hedef olarak seçildi: {target}")
    
    unique_count = df[target].nunique()
    if unique_count < 20:
        task_type = 'classification'
    else:
        task_type = 'regression'
    
    print(f"  - Problem tipi: {task_type}")
    
    return target, task_type

def train_random_forest(X_train, X_test, y_train, y_test, task_type='regression'):
    """Random Forest modelini eğit."""
    print("\n" + "="*70)
    print("RANDOM FOREST MODELİ EĞİTİMİ")
    print("="*70)
    
    if task_type == 'regression':
        print("\n🌲 Random Forest Regressor eğitiliyor...")
        
        # Temel model
        rf_model = RandomForestRegressor(
            n_estimators=100,
            max_depth=20,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1,
            verbose=1
        )
        
        # Model eğitimi
        rf_model.fit(X_train, y_train)
        
        # Tahminler
        y_pred_train = rf_model.predict(X_train)
        y_pred_test = rf_model.predict(X_test)
        
        # Performans metrikleri
        print("\n" + "="*70)
        print("MODEL PERFORMANS METRİKLERİ")
        print("="*70)
        
        print("\n📊 Train Seti:")
        print(f"  - R² Score: {r2_score(y_train, y_pred_train):.4f}")
        print(f"  - MSE: {mean_squared_error(y_train, y_pred_train):.4f}")
        print(f"  - RMSE: {np.sqrt(mean_squared_error(y_train, y_pred_train)):.4f}")
        print(f"  - MAE: {mean_absolute_error(y_train, y_pred_train):.4f}")
        
        print("\n📊 Test Seti:")
        print(f"  - R² Score: {r2_score(y_test, y_pred_test):.4f}")
        print(f"  - MSE: {mean_squared_error(y_test, y_pred_test):.4f}")
        print(f"  - RMSE: {np.sqrt(mean_squared_error(y_test, y_pred_test)):.4f}")
        print(f"  - MAE: {mean_absolute_error(y_test, y_pred_test):.4f}")
        
        # Cross-validation
        print("\n🔄 5-Fold Cross Validation yapılıyor...")
        cv_scores = cross_val_score(rf_model, X_train, y_train, cv=5, 
                                    scoring='r2', n_jobs=-1)
        print(f"  - CV R² Skorları: {cv_scores}")
        print(f"  - CV Ortalama R²: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
        
    else:  # classification
        print("\n🌲 Random Forest Classifier eğitiliyor...")
        
        # Temel model
        rf_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=20,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1,
            verbose=1
        )
        
        # Model eğitimi
        rf_model.fit(X_train, y_train)
        
        # Tahminler
        y_pred_train = rf_model.predict(X_train)
        y_pred_test = rf_model.predict(X_test)
        
        # Performans metrikleri
        print("\n" + "="*70)
        print("MODEL PERFORMANS METRİKLERİ")
        print("="*70)
        
        print("\n📊 Train Seti:")
        print(f"  - Accuracy: {accuracy_score(y_train, y_pred_train):.4f}")
        
        print("\n📊 Test Seti:")
        print(f"  - Accuracy: {accuracy_score(y_test, y_pred_test):.4f}")
        
        print("\n📋 Classification Report:")
        print(classification_report(y_test, y_pred_test))
        
        print("\n📊 Confusion Matrix:")
        print(confusion_matrix(y_test, y_pred_test))
        
        # Cross-validation
        print("\n🔄 5-Fold Cross Validation yapılıyor...")
        cv_scores = cross_val_score(rf_model, X_train, y_train, cv=5, 
                                    scoring='accuracy', n_jobs=-1)
        print(f"  - CV Accuracy Skorları: {cv_scores}")
        print(f"  - CV Ortalama Accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
    
    return rf_model, y_pred_test

def feature_importance_analysis(model, feature_names, top_n=20):
    """Özellik önem analizi yap."""
    print("\n" + "="*70)
    print("ÖZELLİK ÖNEM ANALİZİ")
    print("="*70)
    
    # Feature importance
    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1]
    
    print(f"\n🏆 En Önemli {min(top_n, len(feature_names))} Özellik:")
    for i in range(min(top_n, len(feature_names))):
        print(f"  {i+1}. {feature_names[indices[i]]}: {importances[indices[i]]:.4f}")
    
    # Görselleştirme
    plt.figure(figsize=(12, 8))
    plt.title(f'Top {min(top_n, len(feature_names))} Feature Importances', fontsize=16, fontweight='bold')
    plt.barh(range(min(top_n, len(feature_names))), 
             importances[indices[:min(top_n, len(feature_names))]], 
             align='center', color='skyblue')
    plt.yticks(range(min(top_n, len(feature_names))), 
               [feature_names[i] for i in indices[:min(top_n, len(feature_names))]])
    plt.xlabel('Önem Derecesi', fontsize=12)
    plt.ylabel('Özellikler', fontsize=12)
    plt.gca().invert_yaxis()
    plt.tight_layout()
    plt.savefig('feature_importance.png', dpi=300, bbox_inches='tight')
    print("\n✓ Özellik önem grafiği kaydedildi: feature_importance.png")
    
def plot_predictions(y_test, y_pred, task_type='regression'):
    """Tahminleri görselleştir."""
    print("\n" + "="*70)
    print("TAHMİN GÖRSELLEŞTİRME")
    print("="*70)
    
    if task_type == 'regression':
        plt.figure(figsize=(10, 6))
        plt.scatter(y_test, y_pred, alpha=0.5, s=10)
        plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 
                 'r--', lw=2, label='Perfect Prediction')
        plt.xlabel('Gerçek Değerler', fontsize=12)
        plt.ylabel('Tahmin Edilen Değerler', fontsize=12)
        plt.title('Gerçek vs Tahmin Edilen Değerler', fontsize=16, fontweight='bold')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig('prediction_plot.png', dpi=300, bbox_inches='tight')
        print("\n✓ Tahmin grafiği kaydedildi: prediction_plot.png")
    else:
        # Confusion matrix görselleştirmesi
        from sklearn.metrics import confusion_matrix
        cm = confusion_matrix(y_test, y_pred)
        plt.figure(figsize=(10, 8))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', cbar=True)
        plt.xlabel('Tahmin Edilen', fontsize=12)
        plt.ylabel('Gerçek', fontsize=12)
        plt.title('Confusion Matrix', fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig('confusion_matrix.png', dpi=300, bbox_inches='tight')
        print("\n✓ Confusion matrix kaydedildi: confusion_matrix.png")

def hyperparameter_tuning(X_train, y_train, task_type='regression'):
    """Hiperparametre optimizasyonu yap (opsiyonel)."""
    print("\n" + "="*70)
    print("HİPERPARAMETRE OPTİMİZASYONU (GridSearchCV)")
    print("="*70)
    print("\n⚠ Bu işlem uzun sürebilir...")
    
    param_grid = {
        'n_estimators': [50, 100, 200],
        'max_depth': [10, 20, 30, None],
        'min_samples_split': [2, 5, 10],
        'min_samples_leaf': [1, 2, 4]
    }
    
    if task_type == 'regression':
        base_model = RandomForestRegressor(random_state=42, n_jobs=-1)
        scoring = 'r2'
    else:
        base_model = RandomForestClassifier(random_state=42, n_jobs=-1)
        scoring = 'accuracy'
    
    grid_search = GridSearchCV(
        estimator=base_model,
        param_grid=param_grid,
        cv=3,
        scoring=scoring,
        n_jobs=-1,
        verbose=2
    )
    
    grid_search.fit(X_train, y_train)
    
    print("\n✓ En iyi parametreler:")
    for param, value in grid_search.best_params_.items():
        print(f"  - {param}: {value}")
    
    print(f"\n✓ En iyi CV skoru: {grid_search.best_score_:.4f}")
    
    return grid_search.best_estimator_

def save_model(model, filename='random_forest_model.pkl'):
    """Modeli kaydet."""
    import joblib
    joblib.dump(model, filename)
    print(f"\n✓ Model kaydedildi: {filename}")

def main():
    """Ana fonksiyon."""
    print("\n" + "="*70)
    print("TRENDYOL RANDOM FOREST MODELİ EĞİTİMİ")
    print("="*70)
    
    # 1. Veriyi yükle
    file_path = 'Trendyol_Wide_Veri_Seti_2732.xlsx'
    df = load_and_explore_data(file_path)
    
    # 2. Veriyi ön işle
    df_processed, label_encoders = preprocess_data(df)
    
    # 3. Hedef sütunu tespit et
    target_column, task_type = detect_target_column(df_processed)
    
    # 4. X ve y'yi ayır
    print("\n" + "="*70)
    print("VERİ BÖLME (Train/Test Split)")
    print("="*70)
    
    X = df_processed.drop(columns=[target_column])
    y = df_processed[target_column]
    
    print(f"\n✓ Özellikler (X): {X.shape}")
    print(f"✓ Hedef (y): {y.shape}")
    
    # 5. Train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    print(f"\n✓ Train seti: {X_train.shape[0]} satır")
    print(f"✓ Test seti: {X_test.shape[0]} satır")
    
    # 6. Model eğitimi
    model, y_pred = train_random_forest(X_train, X_test, y_train, y_test, task_type)
    
    # 7. Özellik önem analizi
    feature_importance_analysis(model, X.columns.tolist())
    
    # 8. Tahminleri görselleştir
    plot_predictions(y_test, y_pred, task_type)
    
    # 9. Model kaydet
    save_model(model, 'trendyol_random_forest_model.pkl')
    
    print("\n" + "="*70)
    print("✓ TÜM İŞLEMLER TAMAMLANDI!")
    print("="*70)
    
    # Kullanıcıya seçenek sun
    print("\n🔧 Ek İşlemler:")
    print("  1. Hiperparametre optimizasyonu yapmak ister misiniz? (Uzun sürebilir)")
    print("     Yapmak için aşağıdaki satırı uncomment edin:")
    print("     # best_model = hyperparameter_tuning(X_train, y_train, task_type)")
    
    return model, X_train, X_test, y_train, y_test, df_processed

if __name__ == "__main__":
    model, X_train, X_test, y_train, y_test, df_processed = main()
