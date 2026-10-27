"""
3 Farklı Model Karşılaştırması: KNN, Naive Bayes, Random Forest
Sadece Wide Dataset kullanılır.
Ortalama metrikler ve confusion matrix çıktıları verilir.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, cross_val_predict
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
    f1_score,
    roc_auc_score
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
    for cat, count in cat_counts.items():
        cat_name = CATEGORY_NAMES.get(cat, str(cat))
        print(f"   {cat} ({cat_name}): {count} örnek")
    
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
    print(f"   - Örnek sayısı: {len(df)}")
    
    return X, y

def train_knn(X_train, X_test, y_train, y_test):
    """K-Nearest Neighbors modelini eğit."""
    print(f"\n{'='*70}")
    print("1️⃣  K-NEAREST NEIGHBORS (KNN)")
    print(f"{'='*70}")
    
    # Model
    knn = KNeighborsClassifier(n_neighbors=5, weights='distance', n_jobs=-1)
    
    print("\n🔄 Model eğitiliyor...")
    knn.fit(X_train, y_train)
    
    # Tahminler
    y_pred_train = knn.predict(X_train)
    y_pred_test = knn.predict(X_test)
    
    # Olasılıklar
    y_proba_train = knn.predict_proba(X_train)
    y_proba_test = knn.predict_proba(X_test)
    
    # Metrikler
    train_metrics = calculate_metrics(y_train, y_pred_train, y_proba_train, "KNN - Train")
    test_metrics = calculate_metrics(y_test, y_pred_test, y_proba_test, "KNN - Test")
    
    return knn, train_metrics, test_metrics

def train_naive_bayes(X_train, X_test, y_train, y_test):
    """Naive Bayes modelini eğit."""
    print(f"\n{'='*70}")
    print("2️⃣  NAIVE BAYES (GAUSSIAN)")
    print(f"{'='*70}")
    
    # Model
    nb = GaussianNB()
    
    print("\n🔄 Model eğitiliyor...")
    nb.fit(X_train, y_train)
    
    # Tahminler
    y_pred_train = nb.predict(X_train)
    y_pred_test = nb.predict(X_test)
    
    # Olasılıklar
    y_proba_train = nb.predict_proba(X_train)
    y_proba_test = nb.predict_proba(X_test)
    
    # Metrikler
    train_metrics = calculate_metrics(y_train, y_pred_train, y_proba_train, "Naive Bayes - Train")
    test_metrics = calculate_metrics(y_test, y_pred_test, y_proba_test, "Naive Bayes - Test")
    
    return nb, train_metrics, test_metrics

def train_random_forest(X_train, X_test, y_train, y_test):
    """Random Forest modelini eğit."""
    print(f"\n{'='*70}")
    print("3️⃣  RANDOM FOREST")
    print(f"{'='*70}")
    
    # Model
    rf = RandomForestClassifier(
        n_estimators=100,
        max_depth=20,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
        class_weight='balanced'
    )
    
    print("\n🔄 Model eğitiliyor...")
    rf.fit(X_train, y_train)
    
    # Tahminler
    y_pred_train = rf.predict(X_train)
    y_pred_test = rf.predict(X_test)
    
    # Olasılıklar
    y_proba_train = rf.predict_proba(X_train)
    y_proba_test = rf.predict_proba(X_test)
    
    # Metrikler
    train_metrics = calculate_metrics(y_train, y_pred_train, y_proba_train, "Random Forest - Train")
    test_metrics = calculate_metrics(y_test, y_pred_test, y_proba_test, "Random Forest - Test")
    
    return rf, train_metrics, test_metrics

def calculate_metrics(y_true, y_pred, y_proba, model_name):
    """Metrikleri hesapla."""
    print(f"\n📊 {model_name.upper()}")
    
    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred, average='weighted', zero_division=0)
    recall = recall_score(y_true, y_pred, average='weighted', zero_division=0)
    f1 = f1_score(y_true, y_pred, average='weighted', zero_division=0)
    
    try:
        auc = roc_auc_score(y_true, y_proba, multi_class='ovr', average='weighted')
    except:
        auc = None
    
    cm = confusion_matrix(y_true, y_pred)
    
    print(f"   • Accuracy:  {accuracy:.4f} (%{accuracy*100:.2f})")
    print(f"   • Precision: {precision:.4f} (%{precision*100:.2f})")
    print(f"   • Recall:    {recall:.4f} (%{recall*100:.2f})")
    print(f"   • F1-Score:  {f1:.4f} (%{f1*100:.2f})")
    if auc:
        print(f"   • AUC-ROC:   {auc:.4f} (%{auc*100:.2f})")
    
    return {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'auc': auc,
        'confusion_matrix': cm,
        'model_name': model_name
    }

def plot_confusion_matrices(metrics_list, dataset_type='Test'):
    """Üç modelin confusion matrix'ini yan yana göster."""
    fig, axes = plt.subplots(1, 3, figsize=(20, 6))
    
    colors = ['Blues', 'Greens', 'Oranges']
    
    for idx, metrics in enumerate(metrics_list):
        cm = metrics['confusion_matrix']
        model_name = metrics['model_name'].split(' - ')[0]
        
        sns.heatmap(cm, annot=True, fmt='d', cmap=colors[idx], cbar=True, 
                    square=True, ax=axes[idx], linewidths=1, linecolor='black')
        axes[idx].set_xlabel('Tahmin', fontsize=12, fontweight='bold')
        axes[idx].set_ylabel('Gerçek', fontsize=12, fontweight='bold')
        axes[idx].set_title(f'{model_name}', fontsize=14, fontweight='bold')
    
    plt.suptitle(f'Confusion Matrices - {dataset_type} Set', fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(f'confusion_matrices_{dataset_type.lower()}.png', dpi=300, bbox_inches='tight')
    print(f"\n✓ Confusion matrices kaydedildi: confusion_matrices_{dataset_type.lower()}.png")
    plt.close()

def plot_model_comparison(train_metrics_list, test_metrics_list):
    """Modellerin performansını karşılaştır."""
    model_names = ['KNN', 'Naive Bayes', 'Random Forest']
    metrics_names = ['Accuracy', 'Precision', 'Recall', 'F1-Score']
    
    # Test metrikleri
    test_values = []
    for metric_name in ['accuracy', 'precision', 'recall', 'f1']:
        values = [m[metric_name] for m in test_metrics_list]
        test_values.append(values)
    
    # Grafik
    x = np.arange(len(model_names))
    width = 0.2
    
    fig, ax = plt.subplots(figsize=(14, 7))
    
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A']
    
    for i, (metric_name, values) in enumerate(zip(metrics_names, test_values)):
        offset = width * (i - 1.5)
        bars = ax.bar(x + offset, values, width, label=metric_name, 
                     color=colors[i], edgecolor='black', linewidth=1.5)
        
        # Değerleri yazdır
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                   f'{height:.3f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    ax.set_ylabel('Skor', fontsize=14, fontweight='bold')
    ax.set_xlabel('Model', fontsize=14, fontweight='bold')
    ax.set_title('Model Performans Karşılaştırması (Test Set)', fontsize=16, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(model_names, fontsize=12, fontweight='bold')
    ax.legend(fontsize=11, loc='lower right')
    ax.grid(True, alpha=0.3, axis='y', linestyle='--')
    ax.set_ylim([0, 1.1])
    
    plt.tight_layout()
    plt.savefig('model_comparison.png', dpi=300, bbox_inches='tight')
    print(f"✓ Model karşılaştırma grafiği kaydedildi: model_comparison.png")
    plt.close()

def calculate_average_metrics(metrics_list):
    """Üç modelin ortalama metriklerini hesapla."""
    avg_metrics = {}
    
    for key in ['accuracy', 'precision', 'recall', 'f1', 'auc']:
        values = [m[key] for m in metrics_list if m[key] is not None]
        avg_metrics[key] = np.mean(values) if values else None
    
    return avg_metrics

def print_summary_table(knn_test, nb_test, rf_test, avg_metrics):
    """Özet tablosunu yazdır."""
    print(f"\n{'='*70}")
    print("📊 ÖZET TABLO - TEST SETİ SONUÇLARI")
    print(f"{'='*70}\n")
    
    print(f"{'Model':<20} {'Accuracy':<12} {'Precision':<12} {'Recall':<12} {'F1-Score':<12}")
    print("="*68)
    print(f"{'KNN':<20} {knn_test['accuracy']:<12.4f} {knn_test['precision']:<12.4f} {knn_test['recall']:<12.4f} {knn_test['f1']:<12.4f}")
    print(f"{'Naive Bayes':<20} {nb_test['accuracy']:<12.4f} {nb_test['precision']:<12.4f} {nb_test['recall']:<12.4f} {nb_test['f1']:<12.4f}")
    print(f"{'Random Forest':<20} {rf_test['accuracy']:<12.4f} {rf_test['precision']:<12.4f} {rf_test['recall']:<12.4f} {rf_test['f1']:<12.4f}")
    print("="*68)
    print(f"{'ORTALAMA':<20} {avg_metrics['accuracy']:<12.4f} {avg_metrics['precision']:<12.4f} {avg_metrics['recall']:<12.4f} {avg_metrics['f1']:<12.4f}")
    print("="*68)
    
    print(f"\n{'='*70}")
    print("🎯 ORTALAMA METRİKLER (3 MODEL)")
    print(f"{'='*70}")
    print(f"""
    ╔════════════════════════════════════════╗
    ║   TEST SETİ - ORTALAMA SONUÇLAR        ║
    ╠════════════════════════════════════════╣
    ║                                        ║
    ║  ✅ Accuracy:   {avg_metrics['accuracy']:.4f} ({avg_metrics['accuracy']*100:.2f}%)     ║
    ║  📊 Precision:  {avg_metrics['precision']:.4f} ({avg_metrics['precision']*100:.2f}%)     ║
    ║  📊 Recall:     {avg_metrics['recall']:.4f} ({avg_metrics['recall']*100:.2f}%)     ║
    ║  📊 F1-Score:   {avg_metrics['f1']:.4f} ({avg_metrics['f1']*100:.2f}%)     ║
    ║                                        ║
    ╚════════════════════════════════════════╝
    """)

def main():
    """Ana fonksiyon."""
    print("\n" + "="*70)
    print("3 MODEL KARŞILAŞTIRMASI: KNN, NAIVE BAYES, RANDOM FOREST")
    print("Dataset: Trendyol_Wide_Veri_Seti_2732.xlsx")
    print("7 Kategori: T-shirt, Kazak, Hırka, Gömlek, Ceket, Pantolon, Eşofman")
    print("="*70)
    
    # Veriyi yükle
    X, y = load_and_preprocess_data('Trendyol_Wide_Veri_Seti_2732.xlsx')
    
    # Train-test split (Daha fazla veriyle eğitim için %90-%10)
    print(f"\n{'='*70}")
    print("VERİ BÖLME (90% Train, 10% Test)")
    print(f"{'='*70}")
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.1, random_state=42, stratify=y
    )
    
    print(f"\n✓ Train seti: {X_train.shape[0]} satır")
    print(f"✓ Test seti: {X_test.shape[0]} satır")
    
    # Model 1: KNN
    knn_model, knn_train, knn_test = train_knn(X_train, X_test, y_train, y_test)
    
    # Model 2: Naive Bayes
    nb_model, nb_train, nb_test = train_naive_bayes(X_train, X_test, y_train, y_test)
    
    # Model 3: Random Forest
    rf_model, rf_train, rf_test = train_random_forest(X_train, X_test, y_train, y_test)
    
    # Ortalama metrikleri hesapla
    avg_train = calculate_average_metrics([knn_train, nb_train, rf_train])
    avg_test = calculate_average_metrics([knn_test, nb_test, rf_test])
    
    # Özet tablo
    print_summary_table(knn_test, nb_test, rf_test, avg_test)
    
    # Görselleştirmeler
    print(f"\n{'='*70}")
    print("GÖRSELLEŞTİRMELER")
    print(f"{'='*70}")
    
    plot_confusion_matrices([knn_test, nb_test, rf_test], dataset_type='Test')
    plot_model_comparison([knn_train, nb_train, rf_train], [knn_test, nb_test, rf_test])
    
    # Detaylı confusion matrices yazdır
    print(f"\n{'='*70}")
    print("CONFUSION MATRICES (Test Set)")
    print(f"{'='*70}")
    
    print("\n1️⃣  KNN:")
    print(knn_test['confusion_matrix'])
    
    print("\n2️⃣  Naive Bayes:")
    print(nb_test['confusion_matrix'])
    
    print("\n3️⃣  Random Forest:")
    print(rf_test['confusion_matrix'])
    
    print(f"\n{'='*70}")
    print("✓ TÜM İŞLEMLER TAMAMLANDI!")
    print(f"{'='*70}")
    
    return {
        'knn': {'train': knn_train, 'test': knn_test},
        'nb': {'train': nb_train, 'test': nb_test},
        'rf': {'train': rf_train, 'test': rf_test},
        'average': {'train': avg_train, 'test': avg_test}
    }

if __name__ == "__main__":
    results = main()
