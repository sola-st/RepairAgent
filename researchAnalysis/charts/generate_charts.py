#!/usr/bin/env python3
"""Generate research analysis charts for E17/E34 experiments."""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import os

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# Color palette
COLORS = {
    'correct': '#2ecc71',
    'incorrect': '#e74c3c',
    'plausible': '#3498db',
    'attempted': '#bdc3c7',
    'stuck_loop': '#e74c3c',
    'compile_error': '#e67e22',
    'test_failure': '#f1c40f',
    'wrong_direction': '#9b59b6',
    'timeout': '#95a5a6',
}

plt.rcParams.update({
    'font.size': 12,
    'figure.facecolor': 'white',
    'axes.facecolor': 'white',
    'savefig.bbox': 'tight',
    'savefig.dpi': 150,
})


def chart1_e17_vs_e34_comparison():
    """Bar chart: E17 vs E34 plausible and correct counts."""
    fig, ax = plt.subplots(figsize=(8, 5))

    categories = ['Plausible\nPatches', 'Correct\nPatches', 'Precision\n(Correct/Plausible)', 'Recall\n(Correct/98)']
    e17_vals = [16, 7, 43.8, 7.1]
    e34_vals = [24, 13, 54.2, 14.3]

    x = np.arange(len(categories))
    width = 0.35

    bars1 = ax.bar(x - width/2, e17_vals, width, label='E17 (Baseline)', color='#3498db', edgecolor='white')
    bars2 = ax.bar(x + width/2, e34_vals, width, label='E34 (Spec-Guided)', color='#2ecc71', edgecolor='white')

    ax.set_ylabel('Count / Percentage')
    ax.set_title('E17 vs E34: Repair Performance Comparison')
    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.legend()

    # Add value labels on bars
    for bar in bars1:
        h = bar.get_height()
        ax.annotate(f'{h}' if h > 1 else f'{h}%',
                    xy=(bar.get_x() + bar.get_width() / 2, h),
                    xytext=(0, 3), textcoords="offset points",
                    ha='center', va='bottom', fontsize=10)
    for bar in bars2:
        h = bar.get_height()
        ax.annotate(f'{h}' if h > 1 else f'{h}%',
                    xy=(bar.get_x() + bar.get_width() / 2, h),
                    xytext=(0, 3), textcoords="offset points",
                    ha='center', va='bottom', fontsize=10)

    ax.set_ylim(0, max(e17_vals + e34_vals) * 1.2)
    fig.savefig(os.path.join(OUT_DIR, 'e17_vs_e34_comparison.png'))
    plt.close(fig)
    print("Created e17_vs_e34_comparison.png")


def chart2_failure_categories_pie():
    """Pie chart: unfixed bug failure category distribution."""
    fig, ax = plt.subplots(figsize=(8, 6))

    labels = ['STUCK_LOOP\n(43)', 'COMPILE_ERROR\n(10)', 'TEST_FAILURE\n(7)',
              'WRONG_DIRECTION\n(5)', 'TIMEOUT\n(2)']
    sizes = [43, 10, 7, 5, 2]
    colors = [COLORS['stuck_loop'], COLORS['compile_error'], COLORS['test_failure'],
              COLORS['wrong_direction'], COLORS['timeout']]
    explode = (0.05, 0, 0, 0, 0)

    wedges, texts, autotexts = ax.pie(sizes, explode=explode, labels=labels, colors=colors,
                                       autopct='%1.1f%%', startangle=140,
                                       textprops={'fontsize': 11})
    for t in autotexts:
        t.set_fontsize(10)
        t.set_fontweight('bold')

    ax.set_title('Unfixed Bug Failure Categories (66 bugs)', fontsize=14)
    fig.savefig(os.path.join(OUT_DIR, 'failure_categories_pie.png'))
    plt.close(fig)
    print("Created failure_categories_pie.png")


def chart3_project_breakdown():
    """Stacked bar: per-project breakdown of correct/incorrect/unfixed."""
    fig, ax = plt.subplots(figsize=(10, 6))

    projects = ['Time', 'Math', 'Lang', 'Compress', 'Collections', 'Codec', 'Csv']
    # Bug counts per project in 98-bug pool
    total =      [12, 30, 25, 16,  8, 5, 2]
    # E34 correct patches per project
    correct_e34 = [2,  4,  4,  3,  0, 0, 1]
    # E34 incorrect plausible per project
    incorrect_e34 = [1, 5, 3, 1, 0, 0, 0]
    # Unfixed per project
    unfixed = [t - c - i for t, c, i in zip(total, correct_e34, incorrect_e34)]

    x = np.arange(len(projects))
    width = 0.6

    ax.bar(x, correct_e34, width, label='Correct patches', color=COLORS['correct'])
    ax.bar(x, incorrect_e34, width, bottom=correct_e34, label='Incorrect plausible', color=COLORS['incorrect'])
    ax.bar(x, unfixed, width, bottom=[c+i for c, i in zip(correct_e34, incorrect_e34)],
           label='Unfixed', color=COLORS['attempted'])

    ax.set_ylabel('Number of Bugs')
    ax.set_title('E34 Results by Project (98 bugs)')
    ax.set_xticks(x)
    ax.set_xticklabels(projects)
    ax.legend()

    # Add total labels
    for i, t in enumerate(total):
        ax.annotate(f'n={t}', xy=(i, t), xytext=(0, 3),
                    textcoords="offset points", ha='center', fontsize=9, color='gray')

    fig.savefig(os.path.join(OUT_DIR, 'project_breakdown.png'))
    plt.close(fig)
    print("Created project_breakdown.png")


def chart4_spec_effectiveness():
    """Horizontal bar: spec quality vs outcome for unfixed bugs."""
    fig, ax = plt.subplots(figsize=(9, 5))

    categories = ['Correctly located\nbuggy code', 'Insufficient\ndetail', 'Misleading\nspec']
    counts = [48, 12, 6]
    pcts = [72.7, 18.2, 9.1]
    colors = ['#2ecc71', '#f39c12', '#e74c3c']

    bars = ax.barh(categories, counts, color=colors, edgecolor='white', height=0.5)

    for bar, pct in zip(bars, pcts):
        w = bar.get_width()
        ax.annotate(f'{w} ({pct}%)', xy=(w, bar.get_y() + bar.get_height()/2),
                    xytext=(5, 0), textcoords="offset points",
                    ha='left', va='center', fontsize=11, fontweight='bold')

    ax.set_xlabel('Number of Unfixed Bugs')
    ax.set_title('Spec Quality for 66 Unfixed Bugs')
    ax.set_xlim(0, 60)
    ax.invert_yaxis()
    fig.savefig(os.path.join(OUT_DIR, 'spec_effectiveness.png'))
    plt.close(fig)
    print("Created spec_effectiveness.png")


def chart5_correct_patches_venn():
    """Show overlap between E17 and E34 correct patches."""
    fig, ax = plt.subplots(figsize=(8, 5))

    # E17 only correct: Math-38, Lang-61 (2)
    # E34 only correct: Time-7, Math-100, Lang-11, Lang-35, Compress-3, Compress-12, Compress-14, Csv-5 (8)
    # Both: Time-15, Math-3, Math-53, Math-98, Lang-45 (5)

    e17_only = 2
    both = 5
    e34_only = 8

    # Draw as grouped bar
    labels = ['E17 only\n(Math-38, Lang-61)', 'Both\n(5 bugs)', 'E34 only\n(8 bugs)']
    vals = [e17_only, both, e34_only]
    colors = ['#3498db', '#8e44ad', '#2ecc71']

    bars = ax.bar(labels, vals, color=colors, edgecolor='white', width=0.5)
    for bar, v in zip(bars, vals):
        ax.annotate(str(v), xy=(bar.get_x() + bar.get_width()/2, bar.get_height()),
                    xytext=(0, 5), textcoords="offset points", ha='center', fontsize=14, fontweight='bold')

    ax.set_ylabel('Number of Correct Patches')
    ax.set_title('Correct Patch Overlap: E17 vs E34 (15 unique total)')
    ax.set_ylim(0, 12)
    fig.savefig(os.path.join(OUT_DIR, 'correct_patches_overlap.png'))
    plt.close(fig)
    print("Created correct_patches_overlap.png")


def chart6_match_type_distribution():
    """Donut chart: exact match vs semantically equivalent."""
    fig, ax = plt.subplots(figsize=(6, 6))

    labels = ['Exact Match (7)', 'Sem. Equivalent (8)']
    sizes = [7, 8]
    colors = ['#2980b9', '#27ae60']

    wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors,
                                       autopct='%1.1f%%', startangle=90,
                                       pctdistance=0.75, textprops={'fontsize': 12})
    # Make donut
    centre_circle = plt.Circle((0, 0), 0.50, fc='white')
    ax.add_artist(centre_circle)
    ax.text(0, 0, '15\ncorrect', ha='center', va='center', fontsize=16, fontweight='bold')

    ax.set_title('Correct Patch Match Types', fontsize=14)
    fig.savefig(os.path.join(OUT_DIR, 'match_type_distribution.png'))
    plt.close(fig)
    print("Created match_type_distribution.png")


if __name__ == '__main__':
    os.makedirs(OUT_DIR, exist_ok=True)
    chart1_e17_vs_e34_comparison()
    chart2_failure_categories_pie()
    chart3_project_breakdown()
    chart4_spec_effectiveness()
    chart5_correct_patches_venn()
    chart6_match_type_distribution()
    print("\nAll charts generated successfully!")
