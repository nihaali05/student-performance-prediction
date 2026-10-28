import os
import joblib
import numpy as np
import pandas as pd

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

MODEL_CACHE = None

def get_loaded_model():
    global MODEL_CACHE
    if MODEL_CACHE is not None:
        return MODEL_CACHE
        
    model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models', 'best_model.joblib')
    if os.path.exists(model_path):
        data = joblib.load(model_path)
        MODEL_CACHE = data
        return MODEL_CACHE
    else:
        # Train on the fly if model doesn't exist yet
        from ml.train import train_and_evaluate
        train_and_evaluate()
        data = joblib.load(model_path)
        MODEL_CACHE = data
        return MODEL_CACHE

def evaluate_rule_warnings(data_dict, predicted_score):
    warnings = []
    
    # 1. Attendance warning
    attendance = float(data_dict.get('attendance', 100))
    if attendance < 65:
        warnings.append({
            'code': 'ATTENDANCE_LOW',
            'type': 'Attendance Warning',
            'risk_level': 'ORANGE' if attendance < 50 else 'YELLOW',
            'message': f'Attendance is critically low at {attendance:.1f}%. Below required 65% benchmark.'
        })
        
    # 2. Academic warning
    internal_marks = float(data_dict.get('internal_marks', 100))
    recent_test = float(data_dict.get('recent_test_score', internal_marks))
    if internal_marks < 40 or recent_test < 40:
        warnings.append({
            'code': 'ACADEMIC_LOW',
            'type': 'Academic Warning',
            'risk_level': 'RED' if internal_marks < 35 else 'ORANGE',
            'message': f'Internal marks ({internal_marks:.1f}%) or recent test score ({recent_test:.1f}%) below passing threshold of 40%.'
        })
        
    # 3. Performance decline
    prev_sem = float(data_dict.get('prev_sem_score', internal_marks))
    if (prev_sem - recent_test) >= 15:
        warnings.append({
            'code': 'PERFORMANCE_DECLINE',
            'type': 'Performance Decline Warning',
            'risk_level': 'ORANGE',
            'message': f'Significant decline detected from previous semester ({prev_sem:.1f}%) to recent test ({recent_test:.1f}%).'
        })
        
    # 4. Assignment warning
    assignment_completion = float(data_dict.get('assignment_completion', 100))
    if assignment_completion < 60:
        warnings.append({
            'code': 'ASSIGNMENT_LOW',
            'type': 'Assignment Warning',
            'risk_level': 'YELLOW',
            'message': f'Assignment completion rate ({assignment_completion:.1f}%) is below recommended 60% threshold.'
        })
        
    # 5. High Risk warning from predicted score
    if predicted_score < 50:
        warnings.append({
            'code': 'HIGH_RISK_PREDICTED',
            'type': 'High Risk Warning',
            'risk_level': 'RED',
            'message': f'ML Model predicts final score of {predicted_score:.1f}/100, which triggers High Risk status.'
        })
        
    return warnings

def calculate_explainability(data_dict, predicted_score, model):
    # Benchmark averages
    benchmarks = {
        'attendance': 75.0,
        'internal_marks': 65.0,
        'assignment_score': 70.0,
        'quiz_score': 65.0,
        'study_hours': 12.0,
        'prev_gpa': 7.0,
        'prev_sem_score': 68.0,
        'assignment_completion': 75.0,
        'participation': 70.0,
        'backlogs': 0.0,
        'recent_test_score': 65.0
    }
    
    feature_importances = {}
    if hasattr(model, 'feature_importances_'):
        feature_importances = dict(zip(FEATURE_COLUMNS, model.feature_importances_))
    else:
        # Fallback uniform
        feature_importances = {f: 1.0/len(FEATURE_COLUMNS) for f in FEATURE_COLUMNS}
        
    positive_factors = []
    negative_factors = []
    shap_contributions = []
    
    labels_map = {
        'attendance': 'Class Attendance',
        'internal_marks': 'Internal Exam Marks',
        'assignment_score': 'Assignment Score',
        'quiz_score': 'Quiz Score',
        'study_hours': 'Weekly Study Hours',
        'prev_gpa': 'Previous Cumulative GPA',
        'prev_sem_score': 'Previous Sem Score',
        'assignment_completion': 'Assignment Completion Rate',
        'participation': 'Class Participation',
        'backlogs': 'Active Backlogs',
        'recent_test_score': 'Recent Test Score'
    }
    
    for feat in FEATURE_COLUMNS:
        val = float(data_dict.get(feat, benchmarks[feat]))
        bm = benchmarks[feat]
        imp = feature_importances.get(feat, 0.05)
        
        # Calculate impact relative to benchmark
        if feat == 'backlogs':
            diff = (bm - val) # higher backlogs is negative
        elif feat == 'study_hours':
            diff = (val - bm) / 5.0
        else:
            diff = (val - bm) / 10.0
            
        impact_value = round(diff * imp * 25.0, 2)
        
        shap_contributions.append({
            'feature': feat,
            'name': labels_map.get(feat, feat),
            'val': val,
            'impact': impact_value,
            'importance': round(float(imp), 4)
        })
        
        # Categorize impact magnitude
        abs_impact = abs(impact_value)
        if abs_impact >= 3.0:
            level = "High"
        elif abs_impact >= 1.2:
            level = "Medium"
        else:
            level = "Low"
            
        factor_obj = {
            'feature': feat,
            'name': labels_map.get(feat, feat),
            'value': val,
            'impact_level': level,
            'description': f"{labels_map.get(feat, feat)} is {val} (Benchmark: {bm})"
        }
        
        if impact_value > 0:
            positive_factors.append(factor_obj)
        elif impact_value < 0:
            negative_factors.append(factor_obj)
            
    # Sort factors by impact magnitude
    positive_factors.sort(key=lambda x: x['value'], reverse=True)
    negative_factors.sort(key=lambda x: x['value'])
    shap_contributions.sort(key=lambda x: abs(x['impact']), reverse=True)
    
    return {
        'positive_factors': positive_factors[:4],
        'negative_factors': negative_factors[:4],
        'feature_contributions': shap_contributions
    }

def generate_smart_recommendations(data_dict, predicted_score, negative_factors):
    recommendations = []
    
    att = float(data_dict.get('attendance', 100))
    if att < 75:
        target_classes = int(np.ceil((75 - att) * 0.4)) + 3
        recommendations.append({
            'category': 'Attendance Improvement',
            'action': f"Attend next {target_classes} consecutive lectures to cross 75% mandatory threshold.",
            'priority': 'High' if att < 65 else 'Medium'
        })
        
    mks = float(data_dict.get('internal_marks', 100))
    if mks < 60:
        recommendations.append({
            'category': 'Academic Remediation',
            'action': "Schedule 1-on-1 tutoring for core internal subjects and review model test papers.",
            'priority': 'High' if mks < 45 else 'Medium'
        })
        
    hrs = float(data_dict.get('study_hours', 15))
    if hrs < 10:
        recommendations.append({
            'category': 'Study Habit Optimization',
            'action': f"Increase weekly self-study duration from {hrs:.1f} hrs to at least 12-15 hrs.",
            'priority': 'Medium'
        })
        
    asg = float(data_dict.get('assignment_completion', 100))
    if asg < 70:
        recommendations.append({
            'category': 'Assignment Support',
            'action': "Complete overdue assignments and utilize lab teaching assistant hours for code submission.",
            'priority': 'Medium'
        })
        
    bg = int(data_dict.get('backlogs', 0))
    if bg > 0:
        recommendations.append({
            'category': 'Backlog Clearance Plan',
            'action': f"Enroll in backlog preparatory bootcamp to clear {bg} pending course backlog(s).",
            'priority': 'High'
        })
        
    if not recommendations:
        recommendations.append({
            'category': 'Performance Maintenance',
            'action': "Maintain current study consistency and participate in advanced peer mentoring.",
            'priority': 'Low'
        })
        
    return recommendations

def predict_student_performance(input_data):
    model_data = get_loaded_model()
    model = model_data['model']
    model_name = model_data['model_name']
    
    # Format input array
    row = []
    for col in FEATURE_COLUMNS:
        val = float(input_data.get(col, 0))
        row.append(val)
        
    df_input = pd.DataFrame([row], columns=FEATURE_COLUMNS)
    predicted_score = float(model.predict(df_input)[0])
    predicted_score = round(max(0.0, min(100.0, predicted_score)), 1)
    
    # Categorize
    if predicted_score >= 75:
        category = "High Performer"
    elif predicted_score >= 55:
        category = "Average Performer"
    else:
        category = "At Risk"
        
    # Determine Risk Level
    att = float(input_data.get('attendance', 100))
    mks = float(input_data.get('internal_marks', 100))
    bg = int(input_data.get('backlogs', 0))
    
    if predicted_score < 48 or (att < 60 and mks < 45) or bg >= 3:
        risk_level = "RED"
    elif predicted_score < 62 or att < 68 or mks < 52 or bg == 2:
        risk_level = "ORANGE"
    elif predicted_score < 75 or att < 75 or float(input_data.get('study_hours', 10)) < 5 or bg == 1:
        risk_level = "YELLOW"
    else:
        risk_level = "GREEN"
        
    # Confidence calculation based on data variance
    confidence = round(85.0 + (min(att, mks) * 0.1) - (bg * 2.0), 1)
    confidence = max(70.0, min(98.5, confidence))
    
    # XAI Explainability
    xai = calculate_explainability(input_data, predicted_score, model)
    
    # Rule Warnings
    rule_warnings = evaluate_rule_warnings(input_data, predicted_score)
    
    # Smart Recommendations
    recommendations = generate_smart_recommendations(input_data, predicted_score, xai['negative_factors'])
    
    return {
        'predicted_score': predicted_score,
        'performance_category': category,
        'risk_level': risk_level,
        'confidence': confidence,
        'model_used': model_name,
        'xai': xai,
        'rule_warnings': rule_warnings,
        'recommendations': recommendations
    }

if __name__ == '__main__':
    sample = {
        'attendance': 55.0,
        'internal_marks': 42.0,
        'assignment_score': 60.0,
        'quiz_score': 50.0,
        'study_hours': 4.0,
        'prev_gpa': 5.8,
        'prev_sem_score': 55.0,
        'assignment_completion': 50.0,
        'participation': 40.0,
        'backlogs': 2,
        'recent_test_score': 38.0
    }
    res = predict_student_performance(sample)
    print("Prediction Output Sample:", res['predicted_score'], res['risk_level'])
