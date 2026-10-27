"""
Random Forest Classification - Doğru Kategori Tahmini
7 Kategori: T-shirt, Kazak, Hırka, Gömlek, Ceket, Pantolon, Eşofman
Her iki veri setinden ortalama metrikler hesaplanır.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
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

# Kategori mapping
CATEGORY_MAPPING = {
    0: 'T-shirt',
    1: 'Kazak',
    3: 'Hırka',
    4: 'Gömlek',
    5: 'Ceket',
    6: 'Pantolon',
    7: 'Eşofman'
}

CATEGORY_NAMES = ['T-shirt', 'Kazak', 'Hırka', 'Gömlek', 'Ceket', 'Pantolon', 'Eşofman']

def load_and_preprocess_data(file_path):
    """Veriyi yükle ve ön işle."""
    print(f"\n📂 Dosya yükleniyor: {file_path}")
    
    df = pd.read_excel(file_path, engine='openpyxl')
    print(f"   ✓ {len(df)} satır, {len(df.columns)} sütun")
    
    # Kategori sütununu kontrol et
    if 'Kategori' not in df.columns:
        raise ValueError("Kategori sütunu bulunamadı!")
    
    # Kategori dağılımını göster
    print(f"\n   📊 Kategori dağılımı:")
    cat_counts = df['Kategori'].value_counts().sort_index()
    for cat, count in cat_counts.items():
        cat_name = CATEGORY_MAPPING.get(cat, str(cat))
        print(f"      {cat} ({cat_name}): {count} örnek")
    
    # Gereksiz sütunları kaldır
    columns_to_drop = ['Urun_Adi', 'Urun_Linki']
    df = df.drop(columns=[col for col in columns_to_drop if col in df.columns])
    
    # Tamamen boş sütunları kaldır
    empty_cols = [col for col in df.columns if df[col].isnull().all()]
    if empty_cols:
        df = df.drop(columns=empty_cols)
    
    # %90'dan fazla eksik değere sahip sütunları kaldır
    threshold = 0.9
    cols_to_drop = []
    for col in df.columns:
        if col != 'Kategori':  # Hedef değişkeni koruyoruz
            missing_pct = df[col].isnull().sum() / len(df)
            if missing_pct > threshold:
                cols_to_drop.append(col)
    
    if cols_to_drop:
        df = df.drop(columns=cols_to_drop)
    
    # Eksik değerleri doldur
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if col != 'Kategori' and df[col].isnull().sum() > 0:
            df[col].fillna(df[col].median(), inplace=True)
    
    categorical_cols = df.select_dtypes(include=['object']).columns
    for col in categorical_cols:
        if df[col].isnull().sum() > 0:
            df[col].fillna(df[col].mode()[0] if len(df[col].mode()) > 0 else 'Unknown', inplace=True)
    
    # Kategorik değişkenleri encode et (Kategori hariç)
    for col in categorical_cols:
        if col in df.columns and col != 'Kategori':
            le = LabelEncoder()
            df[col] = le.fit_transform(df[col].astype(str))
    
    # Hala NaN varsa sil (Kategori olmayan satırlar)
    df = df.dropna(subset=['Kategori'])
    
    # X ve y'yi ayır
    X = df.drop(columns=['Kategori'])
    y = df['Kategori']
    
    print(f"   ✓ Ön işleme tamamlandı: {len(df)} satır, {len(X.columns)} özellik")
    
    return X, y

def train_and_evaluate_model(X, y, dataset_name):
    """Model eğit ve değerlendir."""
    print(f"\n{'='*70}")
    print(f"MODEL EĞİTİMİ - {dataset_name}")
    print(f"{'='*70}")
    
    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"\n✓ Train seti: {X_train.shape[0]} satır")
    print(f"✓ Test seti: {X_test.shape[0]} satır")
    
    # Model
    clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=20,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
        class_weight='balanced'
    )
    
    print(f"\n🌲 Random Forest eğitiliyor...")
    clf.fit(X_train, y_train)
    
    # Tahminler
    y_pred_train = clf.predict(X_train)
    y_pred_test = clf.predict(X_test)
    
    # Olasılıklar
    y_proba_train = clf.predict_proba(X_train)
    y_proba_test = clf.predict_proba(X_test)
    
    # Train metrikleri
    train_metrics = calculate_metrics(y_train, y_pred_train, y_proba_train, 
                                      dataset_name=f"{dataset_name} - TRAIN")
    
    # Test metrikleri
    test_metrics = calculate_metrics(y_test, y_pred_test, y_proba_test, 
                                     dataset_name=f"{dataset_name} - TEST")
    
    return clf, train_metrics, test_metrics, y_test, y_pred_test, y_proba_test

def calculate_metrics(y_true, y_pred, y_proba, dataset_name='Test'):
    """Tüm metrikleri hesapla."""
    print(f"\n{'='*70}")
    print(f"{dataset_name.upper()} - METRİKLER")
    print(f"{'='*70}")
    
    # Accuracy
    accuracy = accuracy_score(y_true, y_pred)
    
    # Precision, Recall, F1-Score
    precision_weighted = precision_score(y_true, y_pred, average='weighted', zero_division=0)
    recall_weighted = recall_score(y_true, y_pred, average='weighted', zero_division=0)
    f1_weighted = f1_score(y_true, y_pred, average='weighted', zero_division=0)
    
    precision_macro = precision_score(y_true, y_pred, average='macro', zero_division=0)
    recall_macro = recall_score(y_true, y_pred, average='macro', zero_division=0)
    f1_macro = f1_score(y_true, y_pred, average='macro', zero_division=0)
    
    print(f"\n✅ Accuracy: {accuracy:.4f} (%{accuracy*100:.2f})")
    print(f"\n📊 WEIGHTED:")
    print(f"   • Precision: {precision_weighted:.4f}")
    print(f"   • Recall:    {recall_weighted:.4f}")
    print(f"   • F1-Score:  {f1_weighted:.4f}")
    
    print(f"\n📊 MACRO:")
    print(f"   • Precision: {precision_macro:.4f}")
    print(f"   • Recall:    {recall_macro:.4f}")
    print(f"   • F1-Score:  {f1_macro:.4f}")
    
    # AUC Score
    try:
        n_classes = len(np.unique(y_true))
        auc_score = roc_auc_score(y_true, y_proba, multi_class='ovr', average='weighted')
        print(f"\n🎯 AUC-ROC: {auc_score:.4f} (%{auc_score*100:.2f})")
    except Exception as e:
        auc_score = None
        print(f"\n⚠ AUC hesaplanamadı: {e}")
    
    # Sınıf bazında metrikler
    precision_per_class = precision_score(y_true, y_pred, average=None, zero_division=0)
    recall_per_class = recall_score(y_true, y_pred, average=None, zero_division=0)
    f1_per_class = f1_score(y_true, y_pred, average=None, zero_division=0)
    
    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred)
    
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

def calculate_average_metrics(metrics_list):
    """İki veri setinin ortalama metriklerini hesapla."""
    avg_metrics = {}
    
    # Ortalama hesapla
    for key in ['accuracy', 'precision_weighted', 'recall_weighted', 'f1_weighted',
                'precision_macro', 'recall_macro', 'f1_macro', 'auc']:
        values = [m[key] for m in metrics_list if m[key] is not None]
        avg_metrics[key] = np.mean(values) if values else None
    
    return avg_metrics

def plot_combined_confusion_matrix(cm1, cm2, dataset1_name, dataset2_name):
    """İki veri setinin confusion matrix'ini yan yana göster."""
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    
    # Dataset 1
    sns.heatmap(cm1, annot=True, fmt='d', cmap='Blues', cbar=True, 
                square=True, ax=axes[0], linewidths=1)
    axes[0].set_xlabel('Tahmin', fontsize=12, fontweight='bold')
    axes[0].set_ylabel('Gerçek', fontsize=12, fontweight='bold')
    axes[0].set_title(f'Confusion Matrix - {dataset1_name}', fontsize=14, fontweight='bold')
    
    # Dataset 2
    sns.heatmap(cm2, annot=True, fmt='d', cmap='Greens', cbar=True, 
                square=True, ax=axes[1], linewidths=1)
    axes[1].set_xlabel('Tahmin', fontsize=12, fontweight='bold')
    axes[1].set_ylabel('Gerçek', fontsize=12, fontweight='bold')
    axes[1].set_title(f'Confusion Matrix - {dataset2_name}', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('combined_confusion_matrices.png', dpi=300, bbox_inches='tight')
    print(f"\n✓ Birleşik confusion matrix kaydedildi: combined_confusion_matrices.png")
    plt.close()

def plot_average_metrics(avg_train, avg_test):
    """Ortalama metrikleri görselleştir."""
    metrics_names = ['Accuracy', 'Precision\n(Weighted)', 'Recall\n(Weighted)', 'F1-Score\n(Weighted)', 'AUC-ROC']
    train_values = [
        avg_train['accuracy'],
        avg_train['precision_weighted'],
        avg_train['recall_weighted'],
        avg_train['f1_weighted'],
        avg_train['auc'] if avg_train['auc'] else 0
    ]
    test_values = [
        avg_test['accuracy'],
        avg_test['precision_weighted'],
        avg_test['recall_weighted'],
        avg_test['f1_weighted'],
        avg_test['auc'] if avg_test['auc'] else 0
    ]
    
    x = np.arange(len(metrics_names))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(14, 7))
    bars1 = ax.bar(x - width/2, train_values, width, label='Train (Ortalama)', 
                   color='skyblue', edgecolor='black', linewidth=1.5)
    bars2 = ax.bar(x + width/2, test_values, width, label='Test (Ortalama)', 
                   color='lightcoral', edgecolor='black', linewidth=1.5)
    
    ax.set_ylabel('Skor', fontsize=14, fontweight='bold')
    ax.set_title('2 Veri Setinin Ortalama Performans Metrikleri', fontsize=16, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(metrics_names, fontsize=11)
    ax.legend(fontsize=12, loc='lower right')
    ax.grid(True, alpha=0.3, axis='y', linestyle='--')
    ax.set_ylim([0, 1.1])
    
    # Değerleri bar'ların üzerine yaz
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                   f'{height:.3f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('average_metrics_comparison.png', dpi=300, bbox_inches='tight')
    print(f"✓ Ortalama metrik grafiği kaydedildi: average_metrics_comparison.png")
    plt.close()

def main():
    """Ana fonksiyon."""
    print("\n" + "="*70)
    print("TRENDYOL RANDOM FOREST CLASSIFICATION")
    print("7 Kategori: T-shirt, Kazak, Hırka, Gömlek, Ceket, Pantolon, Eşofman")
    print("İki veri setinden ortalama metrikler")
    print("="*70)
    
    # Dataset 1: Trendyol_Urun_Veri_Seti_2732.xlsx
    print("\n" + "="*70)
    print("DATASET 1: TRENDYOL_URUN_VERI_SETI_2732.xlsx")
    print("="*70)
    
    X1, y1 = load_and_preprocess_data('Trendyol_Urun_Veri_Seti_2732.xlsx')
    clf1, train_metrics1, test_metrics1, y_test1, y_pred_test1, y_proba_test1 = train_and_evaluate_model(
        X1, y1, "Dataset 1"
    )
    
    # Dataset 2: Trendyol_Wide_Veri_Seti_2732.xlsx
    print("\n\n" + "="*70)
    print("DATASET 2: TRENDYOL_WIDE_VERI_SETI_2732.xlsx")
    print("="*70)
    
    X2, y2 = load_and_preprocess_data('Trendyol_Wide_Veri_Seti_2732.xlsx')
    clf2, train_metrics2, test_metrics2, y_test2, y_pred_test2, y_proba_test2 = train_and_evaluate_model(
        X2, y2, "Dataset 2"
    )
    
    # Ortalama metrikleri hesapla
    print("\n\n" + "="*70)
    print("📊 ORTALAMA METRİKLER (2 VERİ SETİ)")
    print("="*70)
    
    avg_train = calculate_average_metrics([train_metrics1, train_metrics2])
    avg_test = calculate_average_metrics([test_metrics1, test_metrics2])
    
    print("\n" + "="*70)
    print("TRAIN SETİ - ORTALAMA")
    print("="*70)
    print(f"\n✅ Accuracy:  {avg_train['accuracy']:.4f} (%{avg_train['accuracy']*100:.2f})")
    print(f"\n📊 WEIGHTED:")
    print(f"   • Precision: {avg_train['precision_weighted']:.4f} (%{avg_train['precision_weighted']*100:.2f})")
    print(f"   • Recall:    {avg_train['recall_weighted']:.4f} (%{avg_train['recall_weighted']*100:.2f})")
    print(f"   • F1-Score:  {avg_train['f1_weighted']:.4f} (%{avg_train['f1_weighted']*100:.2f})")
    print(f"\n📊 MACRO:")
    print(f"   • Precision: {avg_train['precision_macro']:.4f} (%{avg_train['precision_macro']*100:.2f})")
    print(f"   • Recall:    {avg_train['recall_macro']:.4f} (%{avg_train['recall_macro']*100:.2f})")
    print(f"   • F1-Score:  {avg_train['f1_macro']:.4f} (%{avg_train['f1_macro']*100:.2f})")
    if avg_train['auc']:
        print(f"\n🎯 AUC-ROC:   {avg_train['auc']:.4f} (%{avg_train['auc']*100:.2f})")
    
    print("\n" + "="*70)
    print("TEST SETİ - ORTALAMA")
    print("="*70)
    print(f"\n✅ Accuracy:  {avg_test['accuracy']:.4f} (%{avg_test['accuracy']*100:.2f})")
    print(f"\n📊 WEIGHTED:")
    print(f"   • Precision: {avg_test['precision_weighted']:.4f} (%{avg_test['precision_weighted']*100:.2f})")
    print(f"   • Recall:    {avg_test['recall_weighted']:.4f} (%{avg_test['recall_weighted']*100:.2f})")
    print(f"   • F1-Score:  {avg_test['f1_weighted']:.4f} (%{avg_test['f1_weighted']*100:.2f})")
    print(f"\n📊 MACRO:")
    print(f"   • Precision: {avg_test['precision_macro']:.4f} (%{avg_test['precision_macro']*100:.2f})")
    print(f"   • Recall:    {avg_test['recall_macro']:.4f} (%{avg_test['recall_macro']*100:.2f})")
    print(f"   • F1-Score:  {avg_test['f1_macro']:.4f} (%{avg_test['f1_macro']*100:.2f})")
    if avg_test['auc']:
        print(f"\n🎯 AUC-ROC:   {avg_test['auc']:.4f} (%{avg_test['auc']*100:.2f})")
    
    # Görselleştirmeler
    print("\n" + "="*70)
    print("GÖRSELLEŞTİRMELER")
    print("="*70)
    
    plot_combined_confusion_matrix(
        test_metrics1['confusion_matrix'], 
        test_metrics2['confusion_matrix'],
        'Urun Dataset',
        'Wide Dataset'
    )
    
    plot_average_metrics(avg_train, avg_test)
    
    # Final Özet
    print("\n" + "="*70)
    print("📊 FİNAL ÖZET - ORTALAMA TEST METRİKLERİ")
    print("="*70)
    print(f"""
    ╔════════════════════════════════════════╗
    ║   TEST SETİ - ORTALAMA SONUÇLAR        ║
    ╠════════════════════════════════════════╣
    ║                                        ║
    ║  ✅ Accuracy:   {avg_test['accuracy']:.4f} ({avg_test['accuracy']*100:.2f}%)     ║
    ║                                        ║
    ║  📊 Precision:  {avg_test['precision_weighted']:.4f} ({avg_test['precision_weighted']*100:.2f}%)     ║
    ║  📊 Recall:     {avg_test['recall_weighted']:.4f} ({avg_test['recall_weighted']*100:.2f}%)     ║
    ║  📊 F1-Score:   {avg_test['f1_weighted']:.4f} ({avg_test['f1_weighted']*100:.2f}%)     ║
    ║                                        ║
    ║  🎯 AUC-ROC:    {avg_test['auc']:.4f} ({avg_test['auc']*100:.2f}%)     ║
    ║                                        ║
    ╚════════════════════════════════════════╝
    
    7 Kategori:
    • 0: T-shirt
    • 1: Kazak
    • 3: Hırka
    • 4: Gömlek
    • 5: Ceket
    • 6: Pantolon
    • 7: Eşofman
    """)
    
    print("="*70)
    print("✓ TÜM İŞLEMLER TAMAMLANDI!")
    print("="*70)
    
    return avg_train, avg_test

if __name__ == "__main__":
    avg_train, avg_test = main()
