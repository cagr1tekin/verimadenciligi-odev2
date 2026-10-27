"""
3 Farklı Model Karşılaştırması: KNN, Naive Bayes, Random Forest
10-Fold Cross Validation ile TÜM 2732 veri kullanılır.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import cross_val_score, cross_val_predict, StratifiedKFold
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    classification_report, 
    confusion_matrix, 
    accuracy_score,
    precision_score,
    recall_score,
    f1_score
)
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# Kategori isimleri
CATEGORY_NAMES = {
    0: 'T-shirt',
    1: 'Kazak', 
    3: 'Hırka',
    4: 'Gömlek',
    5: 'Ceket',
    6: 'Pantolon',
    7: 'Eşofman'
}

def load_and_preprocess_data(file_path):
    """Veriyi yükle ve ön işle."""
    print(f"\n{'='*70}")
    print("VERİ YÜKLEME VE ÖN İŞLEME")
    print(f"{'='*70}")
    print(f"\n📂 Dosya: {file_path}")
    
    df = pd.read_excel(file_path, engine='openpyxl')
    print(f"✓ {len(df)} satır, {len(df.columns)} sütun yüklendi")
    
    # Kategori dağılımı
    print(f"\n📊 Kategori Dağılımı:")
    cat_counts = df['Kategori'].value_counts().sort_index()
    total = len(df)
    for cat, count in cat_counts.items():
        cat_name = CATEGORY_NAMES.get(cat, str(cat))
        print(f"   {cat} ({cat_name}): {count} örnek (%{count/total*100:.1f})")
    
    # Gereksiz sütunları kaldır
    columns_to_drop = ['Urun_Adi', 'Urun_Linki']
    df = df.drop(columns=[col for col in columns_to_drop if col in df.columns])
    
    # Tamamen boş sütunları kaldır
    empty_cols = [col for col in df.columns if df[col].isnull().all()]
    if empty_cols:
        df = df.drop(columns=empty_cols)
        print(f"✓ Tamamen boş sütunlar kaldırıldı: {empty_cols}")
    
    # %90'dan fazla eksik sütunları kaldır
    threshold = 0.9
    cols_to_drop = []
    for col in df.columns:
        if col != 'Kategori':
            missing_pct = df[col].isnull().sum() / len(df)
            if missing_pct > threshold:
                cols_to_drop.append(col)
    
    if cols_to_drop:
        df = df.drop(columns=cols_to_drop)
        print(f"✓ Yüksek eksiklik oranına sahip sütunlar kaldırıldı: {cols_to_drop}")
    
    # Eksik değerleri doldur
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if col != 'Kategori' and df[col].isnull().sum() > 0:
            df[col].fillna(df[col].median(), inplace=True)
    
    categorical_cols = df.select_dtypes(include=['object']).columns
    for col in categorical_cols:
        if df[col].isnull().sum() > 0:
            df[col].fillna(df[col].mode()[0] if len(df[col].mode()) > 0 else 'Unknown', inplace=True)
    
    # Kategorik değişkenleri encode et
    for col in categorical_cols:
        if col in df.columns and col != 'Kategori':
            le = LabelEncoder()
            df[col] = le.fit_transform(df[col].astype(str))
    
    # NaN kontrolü
    df = df.dropna(subset=['Kategori'])
    
    # X ve y'yi ayır
    X = df.drop(columns=['Kategori'])
    y = df['Kategori']
    
    print(f"\n✓ Ön işleme tamamlandı")
    print(f"   - Özellik sayısı: {X.shape[1]}")
    print(f"   - Toplam örnek sayısı: {len(df)}")
    
    return X, y

def evaluate_model_cv(model, X, y, model_name):
    """10-Fold Cross Validation ile model değerlendir."""
    print(f"\n{'='*70}")
    print(f"{model_name}")
    print(f"{'='*70}")
    
    # 10-Fold Cross Validation
    cv = StratifiedKFold(n_splits=10, shuffle=True, random_state=42)
    
    print(f"\n🔄 10-Fold Cross Validation yapılıyor...")
    print(f"   Her fold'da ~{len(y)//10} örnek test, ~{len(y)-(len(y)//10)} örnek train\n")
    
    # Her metrik için cross validation
    accuracy_scores = cross_val_score(model, X, y, cv=cv, scoring='accuracy', n_jobs=-1)
    precision_scores = cross_val_score(model, X, y, cv=cv, scoring='precision_weighted', n_jobs=-1)
    recall_scores = cross_val_score(model, X, y, cv=cv, scoring='recall_weighted', n_jobs=-1)
    f1_scores = cross_val_score(model, X, y, cv=cv, scoring='f1_weighted', n_jobs=-1)
    
    # Tahminler (tüm veri için)
    y_pred = cross_val_predict(model, X, y, cv=cv, n_jobs=-1)
    
    # Confusion Matrix
    cm = confusion_matrix(y, y_pred)
    
    # Sonuçları yazdır
    print(f"📊 10-FOLD CROSS VALIDATION SONUÇLARI:")
    print(f"\n   Accuracy:")
    print(f"      • Her fold: {[f'{s:.4f}' for s in accuracy_scores]}")
    print(f"      • Ortalama: {accuracy_scores.mean():.4f} ± {accuracy_scores.std():.4f}")
    
    print(f"\n   Precision (Weighted):")
    print(f"      • Her fold: {[f'{s:.4f}' for s in precision_scores]}")
    print(f"      • Ortalama: {precision_scores.mean():.4f} ± {precision_scores.std():.4f}")
    
    print(f"\n   Recall (Weighted):")
    print(f"      • Her fold: {[f'{s:.4f}' for s in recall_scores]}")
    print(f"      • Ortalama: {recall_scores.mean():.4f} ± {recall_scores.std():.4f}")
    
    print(f"\n   F1-Score (Weighted):")
    print(f"      • Her fold: {[f'{s:.4f}' for s in f1_scores]}")
    print(f"      • Ortalama: {f1_scores.mean():.4f} ± {f1_scores.std():.4f}")
    
    return {
        'model_name': model_name,
        'accuracy_mean': accuracy_scores.mean(),
        'accuracy_std': accuracy_scores.std(),
        'precision_mean': precision_scores.mean(),
        'precision_std': precision_scores.std(),
        'recall_mean': recall_scores.mean(),
        'recall_std': recall_scores.std(),
        'f1_mean': f1_scores.mean(),
        'f1_std': f1_scores.std(),
        'confusion_matrix': cm,
        'y_true': y,
        'y_pred': y_pred
    }

def plot_confusion_matrices(results_list):
    """Üç modelin confusion matrix'ini yan yana göster."""
    fig, axes = plt.subplots(1, 3, figsize=(20, 6))
    
    colors = ['Blues', 'Greens', 'Oranges']
    model_names_short = ['KNN', 'Naive Bayes', 'Random Forest']
    
    for idx, (results, color, name) in enumerate(zip(results_list, colors, model_names_short)):
        cm = results['confusion_matrix']
        acc = results['accuracy_mean']
        
        sns.heatmap(cm, annot=True, fmt='d', cmap=color, cbar=True, 
                    square=True, ax=axes[idx], linewidths=1, linecolor='black')
        axes[idx].set_xlabel('Tahmin Edilen', fontsize=12, fontweight='bold')
        axes[idx].set_ylabel('Gerçek', fontsize=12, fontweight='bold')
        axes[idx].set_title(f'{name}\nAccuracy: {acc:.4f}', fontsize=14, fontweight='bold')
    
    plt.suptitle('Confusion Matrices - 10-Fold CV (Tüm 2732 Veri)', fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig('confusion_matrices_10fold_cv.png', dpi=300, bbox_inches='tight')
    print(f"\n✓ Confusion matrices kaydedildi: confusion_matrices_10fold_cv.png")
    plt.close()

def plot_model_comparison(results_list):
    """Modellerin performansını karşılaştır."""
    model_names = ['KNN', 'Naive Bayes', 'Random Forest']
    metrics_names = ['Accuracy', 'Precision', 'Recall', 'F1-Score']
    
    # Değerleri ve std'leri topla
    values = []
    errors = []
    for metric in ['accuracy_mean', 'precision_mean', 'recall_mean', 'f1_mean']:
        metric_values = [r[metric] for r in results_list]
        values.append(metric_values)
        
        metric_std = metric.replace('_mean', '_std')
        metric_errors = [r[metric_std] for r in results_list]
        errors.append(metric_errors)
    
    # Grafik
    x = np.arange(len(model_names))
    width = 0.2
    
    fig, ax = plt.subplots(figsize=(14, 7))
    
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A']
    
    for i, (metric_name, vals, errs) in enumerate(zip(metrics_names, values, errors)):
        offset = width * (i - 1.5)
        bars = ax.bar(x + offset, vals, width, yerr=errs, label=metric_name, 
                     color=colors[i], edgecolor='black', linewidth=1.5, capsize=5)
        
        # Değerleri yazdır
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.02,
                   f'{height:.3f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    ax.set_ylabel('Skor', fontsize=14, fontweight='bold')
    ax.set_xlabel('Model', fontsize=14, fontweight='bold')
    ax.set_title('Model Performans Karşılaştırması (10-Fold CV - 2732 Veri)', fontsize=16, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(model_names, fontsize=12, fontweight='bold')
    ax.legend(fontsize=11, loc='lower right')
    ax.grid(True, alpha=0.3, axis='y', linestyle='--')
    ax.set_ylim([0, 1.15])
    
    plt.tight_layout()
    plt.savefig('model_comparison_10fold_cv.png', dpi=300, bbox_inches='tight')
    print(f"✓ Model karşılaştırma grafiği kaydedildi: model_comparison_10fold_cv.png")
    plt.close()

def print_summary_table(results_list):
    """Özet tablosunu yazdır."""
    print(f"\n{'='*70}")
    print("📊 ÖZET TABLO - 10-FOLD CROSS VALIDATION SONUÇLARI")
    print(f"{'='*70}\n")
    
    print(f"{'Model':<20} {'Accuracy':<15} {'Precision':<15} {'Recall':<15} {'F1-Score':<15}")
    print("="*80)
    
    for results in results_list:
        name = results['model_name'].split(' -')[0].replace('1️⃣  ', '').replace('2️⃣  ', '').replace('3️⃣  ', '')
        print(f"{name:<20} {results['accuracy_mean']:.4f}±{results['accuracy_std']:.4f}   "
              f"{results['precision_mean']:.4f}±{results['precision_std']:.4f}   "
              f"{results['recall_mean']:.4f}±{results['recall_std']:.4f}   "
              f"{results['f1_mean']:.4f}±{results['f1_std']:.4f}")
    
    # Ortalama
    avg_acc = np.mean([r['accuracy_mean'] for r in results_list])
    avg_prec = np.mean([r['precision_mean'] for r in results_list])
    avg_rec = np.mean([r['recall_mean'] for r in results_list])
    avg_f1 = np.mean([r['f1_mean'] for r in results_list])
    
    print("="*80)
    print(f"{'ORTALAMA':<20} {avg_acc:.4f}         {avg_prec:.4f}         {avg_rec:.4f}         {avg_f1:.4f}")
    print("="*80)
    
    print(f"\n{'='*70}")
    print("🎯 ORTALAMA METRİKLER (3 MODEL)")
    print(f"{'='*70}")
    print(f"""
    ╔════════════════════════════════════════╗
    ║  10-FOLD CV ORTALAMA SONUÇLAR          ║
    ║  (Tüm 2732 veri kullanıldı)            ║
    ╠════════════════════════════════════════╣
    ║                                        ║
    ║  ✅ Accuracy:   {avg_acc:.4f} ({avg_acc*100:.2f}%)     ║
    ║  📊 Precision:  {avg_prec:.4f} ({avg_prec*100:.2f}%)     ║
    ║  📊 Recall:     {avg_rec:.4f} ({avg_rec*100:.2f}%)     ║
    ║  📊 F1-Score:   {avg_f1:.4f} ({avg_f1*100:.2f}%)     ║
    ║                                        ║
    ╚════════════════════════════════════════╝
    """)

def main():
    """Ana fonksiyon."""
    print("\n" + "="*70)
    print("3 MODEL KARŞILAŞTIRMASI - 10-FOLD CROSS VALIDATION")
    print("KNN, NAIVE BAYES, RANDOM FOREST")
    print("Dataset: Trendyol_Wide_Veri_Seti_2732.xlsx")
    print("Tüm 2732 veri kullanılır - Her fold'da ~273 test, ~2459 train")
    print("="*70)
    
    # Veriyi yükle
    X, y = load_and_preprocess_data('Trendyol_Wide_Veri_Seti_2732.xlsx')
    
    print(f"\n{'='*70}")
    print("10-FOLD CROSS VALIDATION")
    print(f"{'='*70}")
    print(f"\n✅ Tüm {len(X)} örnek kullanılacak")
    print(f"✅ 10 farklı fold'da değerlendirme")
    print(f"✅ Her modelde toplam {len(X)} tahmin yapılacak\n")
    
    # Modelleri hazırla
    knn = KNeighborsClassifier(n_neighbors=5, weights='distance', n_jobs=-1)
    nb = GaussianNB()
    rf = RandomForestClassifier(n_estimators=100, max_depth=20, min_samples_split=5, 
                                min_samples_leaf=2, random_state=42, n_jobs=-1, 
                                class_weight='balanced')
    
    # Model 1: KNN
    knn_results = evaluate_model_cv(knn, X, y, "1️⃣  K-NEAREST NEIGHBORS (KNN)")
    
    # Model 2: Naive Bayes
    nb_results = evaluate_model_cv(nb, X, y, "2️⃣  NAIVE BAYES (GAUSSIAN)")
    
    # Model 3: Random Forest
    rf_results = evaluate_model_cv(rf, X, y, "3️⃣  RANDOM FOREST")
    
    results_list = [knn_results, nb_results, rf_results]
    
    # Özet tablo
    print_summary_table(results_list)
    
    # Görselleştirmeler
    print(f"\n{'='*70}")
    print("GÖRSELLEŞTİRMELER")
    print(f"{'='*70}")
    
    plot_confusion_matrices(results_list)
    plot_model_comparison(results_list)
    
    # Detaylı confusion matrices yazdır
    print(f"\n{'='*70}")
    print("CONFUSION MATRICES (10-Fold CV - Tüm 2732 Veri)")
    print(f"{'='*70}")
    
    print("\n1️⃣  KNN:")
    print(knn_results['confusion_matrix'])
    print(f"   Toplam tahmin: {knn_results['confusion_matrix'].sum()}")
    
    print("\n2️⃣  Naive Bayes:")
    print(nb_results['confusion_matrix'])
    print(f"   Toplam tahmin: {nb_results['confusion_matrix'].sum()}")
    
    print("\n3️⃣  Random Forest:")
    print(rf_results['confusion_matrix'])
    print(f"   Toplam tahmin: {rf_results['confusion_matrix'].sum()}")
    
    print(f"\n{'='*70}")
    print("✓ TÜM İŞLEMLER TAMAMLANDI!")
    print(f"{'='*70}")
    
    return results_list

if __name__ == "__main__":
    results = main()
