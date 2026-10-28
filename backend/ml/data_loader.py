import pandas as pd
import numpy as np
import os

def generate_synthetic_dataset(num_samples=1200, save_path=None):
    np.random.seed(42)
    
    # Feature distributions
    attendance = np.random.beta(a=7, b=2, size=num_samples) * 100
    attendance = np.clip(attendance, 35, 100)
    
    study_hours = np.random.gamma(shape=4, scale=3, size=num_samples)
    study_hours = np.clip(study_hours, 1, 35)
    
    prev_gpa = np.random.normal(loc=7.2, scale=1.3, size=num_samples)
    prev_gpa = np.clip(prev_gpa, 3.5, 10.0)
    
    prev_sem_score = prev_gpa * 9.5 + np.random.normal(0, 4, num_samples)
    prev_sem_score = np.clip(prev_sem_score, 35, 100)
    
    internal_marks = (attendance * 0.3 + prev_sem_score * 0.4 + study_hours * 1.2 + np.random.normal(0, 6, num_samples))
    internal_marks = np.clip(internal_marks, 25, 100)
    
    assignment_completion = (attendance * 0.5 + np.random.normal(35, 12, num_samples))
    assignment_completion = np.clip(assignment_completion, 20, 100)
    
    assignment_score = (assignment_completion * 0.7 + study_hours * 0.8 + np.random.normal(10, 5, num_samples))
    assignment_score = np.clip(assignment_score, 30, 100)
    
    quiz_score = (internal_marks * 0.6 + study_hours * 1.0 + np.random.normal(10, 8, num_samples))
    quiz_score = np.clip(quiz_score, 20, 100)
    
    participation = (attendance * 0.6 + np.random.normal(20, 10, num_samples))
    participation = np.clip(participation, 20, 100)
    
    # Backlogs correlate inversely with prev_gpa and attendance
    backlog_prob = np.clip(1.0 - (prev_gpa / 10.0 * 0.6 + attendance / 100.0 * 0.4), 0, 0.8)
    backlogs = np.random.binomial(n=4, p=backlog_prob)
    
    recent_test_score = (internal_marks * 0.5 + quiz_score * 0.3 + study_hours * 0.8 + np.random.normal(0, 5, num_samples))
    recent_test_score = np.clip(recent_test_score, 20, 100)
    
    # Formula for final performance score
    final_score = (
        0.22 * internal_marks +
        0.20 * recent_test_score +
        0.18 * attendance +
        0.15 * assignment_score +
        0.10 * quiz_score +
        0.08 * (prev_gpa * 10) +
        0.05 * (study_hours * 2.5) +
        0.02 * participation -
        3.5 * backlogs +
        np.random.normal(0, 3.5, num_samples)
    )
    final_score = np.clip(final_score, 20, 100)
    
    # Performance Category
    categories = []
    for s in final_score:
        if s >= 75:
            categories.append("High Performer")
        elif s >= 55:
            categories.append("Average Performer")
        else:
            categories.append("At Risk")
            
    # Risk Level
    risk_levels = []
    for idx in range(num_samples):
        sc = final_score[idx]
        att = attendance[idx]
        mks = internal_marks[idx]
        bg = backlogs[idx]
        
        if sc < 48 or (att < 60 and mks < 45) or bg >= 3:
            risk_levels.append("RED")
        elif sc < 62 or att < 68 or mks < 52 or bg == 2:
            risk_levels.append("ORANGE")
        elif sc < 75 or att < 75 or study_hours[idx] < 5 or bg == 1:
            risk_levels.append("YELLOW")
        else:
            risk_levels.append("GREEN")
            
    df = pd.DataFrame({
        'attendance': np.round(attendance, 1),
        'internal_marks': np.round(internal_marks, 1),
        'assignment_score': np.round(assignment_score, 1),
        'quiz_score': np.round(quiz_score, 1),
        'study_hours': np.round(study_hours, 1),
        'prev_gpa': np.round(prev_gpa, 2),
        'prev_sem_score': np.round(prev_sem_score, 1),
        'assignment_completion': np.round(assignment_completion, 1),
        'participation': np.round(participation, 1),
        'backlogs': backlogs,
        'recent_test_score': np.round(recent_test_score, 1),
        'final_score': np.round(final_score, 1),
        'performance_category': categories,
        'risk_level': risk_levels
    })
    
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        df.to_csv(save_path, index=False)
        print(f"Dataset successfully saved to {save_path} ({len(df)} rows)")
        
    return df

if __name__ == '__main__':
    dataset_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'dataset', 'student_performance.csv')
    generate_synthetic_dataset(save_path=dataset_path)
