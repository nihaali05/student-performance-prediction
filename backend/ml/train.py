import os
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
try:
    from ml.data_loader import generate_synthetic_dataset
except ImportError:
    from data_loader import generate_synthetic_dataset

FEATURE_COLUMNS = [
    'attendance',
    'internal_marks',
    'assignment_score',
    'quiz_score',
    'study_hours',
    'prev_gpa',
    'prev_sem_score',
    'assignment_completion',
    'participation',
    'backlogs',
    'recent_test_score'
]

TARGET_COLUMN = 'final_score'

def train_and_evaluate():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    dataset_path = os.path.join(base_dir, 'dataset', 'student_performance.csv')
    
    if not os.path.exists(dataset_path):
        df = generate_synthetic_dataset(1200, dataset_path)
    else:
        df = pd.read_csv(dataset_path)
        
    X = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    models = {
        'Linear Regression': LinearRegression(),
        'Random Forest': RandomForestRegressor(n_estimators=100, random_state=42, max_depth=10),
        'Gradient Boosting (XGBoost Alt)': GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, random_state=42, max_depth=5)
    }
    
    results = {}
    best_r2 = -float('inf')
    best_model = None
    best_model_name = None
    
    for name, model in models.items():
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        
        mse = mean_squared_error(y_test, y_pred)
        rmse = float(np.sqrt(mse))
        r2 = float(r2_score(y_test, y_pred))
        mae = float(mean_absolute_error(y_test, y_pred))
        
        # Calculate feature importances if available
        if hasattr(model, 'feature_importances_'):
            importances = dict(zip(FEATURE_COLUMNS, [float(x) for x in model.feature_importances_]))
        elif hasattr(model, 'coef_'):
            coef_sum = sum(abs(model.coef_))
            importances = dict(zip(FEATURE_COLUMNS, [float(abs(c)/coef_sum) for c in model.coef_]))
        else:
            importances = {}
            
        results[name] = {
            'rmse': round(rmse, 4),
            'r2': round(r2, 4),
            'mae': round(mae, 4),
            'feature_importances': importances
        }
        
        if r2 > best_r2:
            best_r2 = r2
            best_model = model
            best_model_name = name
            
    # Save best model
    models_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')
    os.makedirs(models_dir, exist_ok=True)
    
    model_path = os.path.join(models_dir, 'best_model.joblib')
    metadata_path = os.path.join(models_dir, 'model_metadata.json')
    
    joblib.dump({
        'model': best_model,
        'model_name': best_model_name,
        'feature_columns': FEATURE_COLUMNS,
        'best_r2': best_r2
    }, model_path)
    
    metadata = {
        'best_model_name': best_model_name,
        'best_r2': round(best_r2, 4),
        'metrics': results,
        'feature_columns': FEATURE_COLUMNS
    }
    
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
        
    print(f"Training Complete!")
    print(f"Best Model: {best_model_name} with R²: {best_r2:.4f}")
    return metadata

if __name__ == '__main__':
    train_and_evaluate()
