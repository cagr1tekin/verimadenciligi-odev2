"""
Random Forest Classification with Precision, Recall, F1-Score, AUC
Bu script classification metrikleri hesaplar.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder, label_binarize
from sklearn.metrics import (
    classification_report, 
    confusion_matrix, 
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    roc_curve,
    auc
)
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

def load_and_preprocess_data(file_path):
    """Veriyi yükle ve ön işle."""
    print("="*70)
    print("VERİ YÜKLEME VE ÖN İŞLEME")
    print("="*70)
    
    df = pd.read_excel(file_path, engine='openpyxl')
    print(f"\n✓ Dosya yüklendi: {len(df)} satır, {len(df.columns)} sütun")
    
    # Gereksiz sütunları kaldır
    columns_to_drop = ['Urun_Adi', 'Urun_Linki']
    df = df.drop(columns=[col for col in columns_to_drop if col in df.columns])
    
    # Tamamen boş sütunları kaldır
    empty_cols = [col for col in df.columns if df[col].isnull().all()]
    if empty_cols:
        df = df.drop(columns=empty_cols)
        print(f"✓ Tamamen boş sütunlar kaldırıldı: {empty_cols}")
    
    # %90'dan fazla eksik değere sahip sütunları kaldır
    threshold = 0.9
    cols_to_drop = []
    for col in df.columns:
        missing_pct = df[col].isnull().sum() / len(df)
        if missing_pct > threshold:
            cols_to_drop.append(col)
    
    if cols_to_drop:
        df = df.drop(columns=cols_to_drop)
        print(f"✓ Yüksek eksiklik oranına sahip sütunlar kaldırıldı: {cols_to_drop}")
    
    # Eksik değerleri doldur
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if df[col].isnull().sum() > 0:
            df[col].fillna(df[col].median(), inplace=True)
    
    categorical_cols = df.select_dtypes(include=['object']).columns
    for col in categorical_cols:
        if df[col].isnull().sum() > 0:
            df[col].fillna(df[col].mode()[0] if len(df[col].mode()) > 0 else 'Unknown', inplace=True)
    
    # Kategorik değişkenleri encode et
    for col in categorical_cols:
        if col in df.columns:
            le = LabelEncoder()
            df[col] = le.fit_transform(df[col].astype(str))
    
    # Hala NaN varsa sil
    df = df.dropna()
    
    print(f"✓ Ön işleme tamamlandı: {len(df)} satır kaldı\n")
    
    return df

def convert_to_classification(df, target_col='Ek_Ozellikler', n_classes=3):
    """Regresyon hedefini classification hedefine çevir."""
    print("="*70)
    print("CLASSIFICATION PROBLEM DÖNÜŞÜMÜ")
    print("="*70)
    
    # Hedef değişkeni kategorilere böl
    if target_col in df.columns:
        y = df[target_col]
        
        # Quantile-based binning (eşit sayıda örnek)
        y_binned = pd.qcut(y, q=n_classes, labels=False, duplicates='drop')
        
        print(f"\n✓ Hedef değişken '{target_col}' {n_classes} sınıfa bölündü")
        print(f"\n📊 Sınıf Dağılımı:")
        class_counts = pd.Series(y_binned).value_counts().sort_index()
        for cls, count in class_counts.items():
            print(f"  - Sınıf {cls}: {count} örnek (%{count/len(y_binned)*100:.2f})")
        
        # X ve y'yi ayır
        X = df.drop(columns=[target_col])
        
        return X, y_binned, class_counts
    else:
        # Hedef bulunamazsa son sütunu kullan
        target_col = df.columns[-1]
        return convert_to_classification(df, target_col, n_classes)

def train_classification_model(X_train, X_test, y_train, y_test):
    """Random Forest Classifier eğit."""
    print("\n" + "="*70)
    print("RANDOM FOREST CLASSIFIER EĞİTİMİ")
    print("="*70)
    
    # Model
    clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=15,
        min_samples_split=10,
        min_samples_leaf=5,
        random_state=42,
        n_jobs=-1,
        class_weight='balanced'  # Dengesiz sınıflar için
    )
    
    print("\n🌲 Model eğitiliyor...")
    clf.fit(X_train, y_train)
    
    # Tahminler
    y_pred_train = clf.predict(X_train)
    y_pred_test = clf.predict(X_test)
    
    # Olasılıklar (AUC için gerekli)
    y_proba_train = clf.predict_proba(X_train)
    y_proba_test = clf.predict_proba(X_test)
    
    return clf, y_pred_train, y_pred_test, y_proba_train, y_proba_test

def calculate_metrics(y_true, y_pred, y_proba, dataset_name='Test', n_classes=None):
    """Tüm metrikleri hesapla."""
    print("\n" + "="*70)
    print(f"{dataset_name.upper()} SETİ - DETAYLI METRİKLER")
    print("="*70)
    
    # Accuracy
    accuracy = accuracy_score(y_true, y_pred)
    print(f"\n✅ Accuracy: {accuracy:.4f} (%{accuracy*100:.2f})")
    
    # Precision, Recall, F1-Score (weighted average)
    precision_weighted = precision_score(y_true, y_pred, average='weighted', zero_division=0)
    recall_weighted = recall_score(y_true, y_pred, average='weighted', zero_division=0)
    f1_weighted = f1_score(y_true, y_pred, average='weighted', zero_division=0)
    
    print(f"\n📊 WEIGHTED ORTALAMA:")
    print(f"  • Precision: {precision_weighted:.4f} (%{precision_weighted*100:.2f})")
    print(f"  • Recall:    {recall_weighted:.4f} (%{recall_weighted*100:.2f})")
    print(f"  • F1-Score:  {f1_weighted:.4f} (%{f1_weighted*100:.2f})")
    
    # Macro average
    precision_macro = precision_score(y_true, y_pred, average='macro', zero_division=0)
    recall_macro = recall_score(y_true, y_pred, average='macro', zero_division=0)
    f1_macro = f1_score(y_true, y_pred, average='macro', zero_division=0)
    
    print(f"\n📊 MACRO ORTALAMA:")
    print(f"  • Precision: {precision_macro:.4f} (%{precision_macro*100:.2f})")
    print(f"  • Recall:    {recall_macro:.4f} (%{recall_macro*100:.2f})")
    print(f"  • F1-Score:  {f1_macro:.4f} (%{f1_macro*100:.2f})")
    
    # Sınıf bazında metrikler
    print(f"\n📋 SINIF BAZINDA METRİKLER:")
    precision_per_class = precision_score(y_true, y_pred, average=None, zero_division=0)
    recall_per_class = recall_score(y_true, y_pred, average=None, zero_division=0)
    f1_per_class = f1_score(y_true, y_pred, average=None, zero_division=0)
    
    print(f"\n{'Sınıf':<10} {'Precision':<12} {'Recall':<12} {'F1-Score':<12}")
    print("-" * 46)
    for i in range(len(precision_per_class)):
        print(f"{i:<10} {precision_per_class[i]:<12.4f} {recall_per_class[i]:<12.4f} {f1_per_class[i]:<12.4f}")
    
    # AUC Score
    try:
        if n_classes is None:
            n_classes = len(np.unique(y_true))
        
        if n_classes == 2:
            # Binary classification
            auc_score = roc_auc_score(y_true, y_proba[:, 1])
            print(f"\n🎯 AUC-ROC Score: {auc_score:.4f} (%{auc_score*100:.2f})")
        else:
            # Multi-class classification (one-vs-rest)
            auc_score_ovr = roc_auc_score(y_true, y_proba, multi_class='ovr', average='weighted')
            auc_score_ovo = roc_auc_score(y_true, y_proba, multi_class='ovo', average='weighted')
            
            print(f"\n🎯 AUC-ROC Score (One-vs-Rest): {auc_score_ovr:.4f} (%{auc_score_ovr*100:.2f})")
            print(f"🎯 AUC-ROC Score (One-vs-One):  {auc_score_ovo:.4f} (%{auc_score_ovo*100:.2f})")
            
            auc_score = auc_score_ovr
    except Exception as e:
        print(f"\n⚠ AUC hesaplanamadı: {e}")
        auc_score = None
    
    # Classification Report
    print(f"\n📊 DETAYLI CLASSIFICATION REPORT:")
    print(classification_report(y_true, y_pred, zero_division=0))
    
    # Confusion Matrix
    cm = confusion_matrix(y_true, y_pred)
    print(f"\n📊 CONFUSION MATRIX:")
    print(cm)
    
    return {
        'accuracy': accuracy,
        'precision_weighted': precision_weighted,
        'recall_weighted': recall_weighted,
        'f1_weighted': f1_weighted,
        'precision_macro': precision_macro,
        'recall_macro': recall_macro,
        'f1_macro': f1_macro,
        'auc': auc_score,
        'confusion_matrix': cm,
        'precision_per_class': precision_per_class,
        'recall_per_class': recall_per_class,
        'f1_per_class': f1_per_class
    }

def plot_confusion_matrix(cm, filename='confusion_matrix_classification.png'):
    """Confusion matrix görselleştir."""
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', cbar=True, 
                square=True, linewidths=1, linecolor='black')
    plt.xlabel('Tahmin Edilen Sınıf', fontsize=14, fontweight='bold')
    plt.ylabel('Gerçek Sınıf', fontsize=14, fontweight='bold')
    plt.title('Confusion Matrix', fontsize=16, fontweight='bold', pad=20)
    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"\n✓ Confusion matrix kaydedildi: {filename}")
    plt.close()

def plot_roc_curves(y_test, y_proba, n_classes, filename='roc_curves.png'):
    """ROC eğrilerini çiz."""
    try:
        plt.figure(figsize=(10, 8))
        
        if n_classes == 2:
            # Binary classification
            fpr, tpr, _ = roc_curve(y_test, y_proba[:, 1])
            roc_auc = auc(fpr, tpr)
            
            plt.plot(fpr, tpr, color='darkorange', lw=2, 
                    label=f'ROC curve (AUC = {roc_auc:.2f})')
        else:
            # Multi-class: One-vs-Rest
            y_test_bin = label_binarize(y_test, classes=range(n_classes))
            
            for i in range(n_classes):
                fpr, tpr, _ = roc_curve(y_test_bin[:, i], y_proba[:, i])
                roc_auc = auc(fpr, tpr)
                plt.plot(fpr, tpr, lw=2, label=f'Sınıf {i} (AUC = {roc_auc:.2f})')
        
        plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--', label='Random (AUC = 0.50)')
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('False Positive Rate', fontsize=12, fontweight='bold')
        plt.ylabel('True Positive Rate', fontsize=12, fontweight='bold')
        plt.title('ROC Curves', fontsize=16, fontweight='bold', pad=20)
        plt.legend(loc="lower right")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"✓ ROC eğrileri kaydedildi: {filename}")
        plt.close()
    except Exception as e:
        print(f"⚠ ROC eğrileri çizilemedi: {e}")

def plot_metrics_comparison(train_metrics, test_metrics, filename='metrics_comparison.png'):
    """Train ve Test metriklerini karşılaştır."""
    metrics_names = ['Accuracy', 'Precision', 'Recall', 'F1-Score']
    train_values = [
        train_metrics['accuracy'],
        train_metrics['precision_weighted'],
        train_metrics['recall_weighted'],
        train_metrics['f1_weighted']
    ]
    test_values = [
        test_metrics['accuracy'],
        test_metrics['precision_weighted'],
        test_metrics['recall_weighted'],
        test_metrics['f1_weighted']
    ]
    
    x = np.arange(len(metrics_names))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(12, 6))
    bars1 = ax.bar(x - width/2, train_values, width, label='Train', color='skyblue', edgecolor='black')
    bars2 = ax.bar(x + width/2, test_values, width, label='Test', color='lightcoral', edgecolor='black')
    
    ax.set_ylabel('Skor', fontsize=12, fontweight='bold')
    ax.set_title('Train vs Test Metrikleri Karşılaştırması', fontsize=16, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(metrics_names, fontsize=11)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3, axis='y')
    ax.set_ylim([0, 1.1])
    
    # Değerleri bar'ların üzerine yaz
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.3f}', ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"✓ Metrik karşılaştırma grafiği kaydedildi: {filename}")
    plt.close()

def main():
    """Ana fonksiyon."""
    print("\n" + "="*70)
    print("TRENDYOL RANDOM FOREST CLASSIFICATION MODELİ")
    print("Precision, Recall, F1-Score, AUC Metrikleri")
    print("="*70)
    
    # 1. Veriyi yükle ve ön işle
    file_path = 'Trendyol_Wide_Veri_Seti_2732.xlsx'
    df = load_and_preprocess_data(file_path)
    
    # 2. Classification probleme dönüştür
    X, y, class_counts = convert_to_classification(df, target_col='Ek_Ozellikler', n_classes=3)
    n_classes = len(class_counts)
    
    # 3. Train-test split
    print("\n" + "="*70)
    print("VERİ BÖLME")
    print("="*70)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"\n✓ Train seti: {X_train.shape[0]} satır")
    print(f"✓ Test seti: {X_test.shape[0]} satır")
    
    # 4. Model eğitimi
    clf, y_pred_train, y_pred_test, y_proba_train, y_proba_test = train_classification_model(
        X_train, X_test, y_train, y_test
    )
    
    # 5. Train metrikleri
    train_metrics = calculate_metrics(y_train, y_pred_train, y_proba_train, 
                                     dataset_name='Train', n_classes=n_classes)
    
    # 6. Test metrikleri
    test_metrics = calculate_metrics(y_test, y_pred_test, y_proba_test, 
                                    dataset_name='Test', n_classes=n_classes)
    
    # 7. Görselleştirmeler
    print("\n" + "="*70)
    print("GÖRSELLEŞTİRMELER")
    print("="*70)
    
    plot_confusion_matrix(test_metrics['confusion_matrix'])
    plot_roc_curves(y_test, y_proba_test, n_classes)
    plot_metrics_comparison(train_metrics, test_metrics)
    
    # 8. Özellik önemleri
    print("\n" + "="*70)
    print("ÖZELLİK ÖNEMLERİ (Top 15)")
    print("="*70)
    
    importances = clf.feature_importances_
    indices = np.argsort(importances)[::-1]
    
    print()
    for i in range(min(15, len(X.columns))):
        print(f"  {i+1}. {X.columns[indices[i]]:<30} {importances[indices[i]]:.4f}")
    
    # 9. Model kaydet
    import joblib
    joblib.dump(clf, 'trendyol_rf_classifier.pkl')
    print(f"\n✓ Model kaydedildi: trendyol_rf_classifier.pkl")
    
    # 10. Özet
    print("\n" + "="*70)
    print("📊 ÖZET METRİKLER")
    print("="*70)
    
    auc_value = test_metrics['auc'] if test_metrics['auc'] else 0
    auc_percent = auc_value * 100
    
    print(f"""
    TEST SETİ SONUÇLARI:
    ════════════════════
    
    ✅ Accuracy:  {test_metrics['accuracy']:.4f} (%{test_metrics['accuracy']*100:.2f})
    
    📊 Weighted Average:
       • Precision: {test_metrics['precision_weighted']:.4f}
       • Recall:    {test_metrics['recall_weighted']:.4f}
       • F1-Score:  {test_metrics['f1_weighted']:.4f}
    
    🎯 AUC-ROC:   {auc_value:.4f} (%{auc_percent:.2f})
    
    ════════════════════
    """)
    
    print("="*70)
    print("✓ TÜM İŞLEMLER TAMAMLANDI!")
    print("="*70)
    
    return clf, train_metrics, test_metrics

if __name__ == "__main__":
    clf, train_metrics, test_metrics = main()
