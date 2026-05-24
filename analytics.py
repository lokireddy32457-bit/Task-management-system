"""
Analytics Module — uses Pandas & NumPy to compute task statistics.
"""
import pandas as pd
import numpy as np
from models import Task


def get_task_analytics(user_id: int) -> dict:
    """
    Fetch all tasks for the given user and compute analytics
    using Pandas DataFrames and NumPy operations.
    """
    tasks = Task.query.filter_by(user_id=user_id).all()

    if not tasks:
        return {
            'total_tasks':           0,
            'completed_tasks':       0,
            'pending_tasks':         0,
            'in_progress_tasks':     0,
            'completion_percentage': 0.0,
            'priority_breakdown':    {'low': 0, 'medium': 0, 'high': 0},
            'status_breakdown':      {'pending': 0, 'in_progress': 0, 'completed': 0},
        }

    # ── Build DataFrame ────────────────────────────────────────────────────────
    data = [
        {
            'id':           t.id,
            'title':        t.title,
            'priority':     t.priority,
            'status':       t.status,
            'created_date': t.created_date,
        }
        for t in tasks
    ]
    df = pd.DataFrame(data)

    # ── NumPy computations ─────────────────────────────────────────────────────
    total          = len(df)
    completed      = int(np.sum(df['status'] == 'completed'))
    pending        = int(np.sum(df['status'] == 'pending'))
    in_progress    = int(np.sum(df['status'] == 'in_progress'))

    completion_pct = float(np.round((completed / total) * 100, 2)) if total > 0 else 0.0

    # ── Pandas groupby breakdowns ──────────────────────────────────────────────
    priority_counts = df['priority'].value_counts().to_dict()
    status_counts   = df['status'].value_counts().to_dict()

    priority_breakdown = {
        'low':    priority_counts.get('low', 0),
        'medium': priority_counts.get('medium', 0),
        'high':   priority_counts.get('high', 0),
    }
    status_breakdown = {
        'pending':     status_counts.get('pending', 0),
        'in_progress': status_counts.get('in_progress', 0),
        'completed':   status_counts.get('completed', 0),
    }

    return {
        'total_tasks':           total,
        'completed_tasks':       completed,
        'pending_tasks':         pending,
        'in_progress_tasks':     in_progress,
        'completion_percentage': completion_pct,
        'priority_breakdown':    priority_breakdown,
        'status_breakdown':      status_breakdown,
    }
