"""
Test multilingual PDF export and AI generation prompt/fallback for FR, EN, DE.
"""
import sys
import os

# Add backend directory to path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, backend_dir)

from app.services.export_service import PDF_TRANSLATIONS, ExportService
from app.services.ai_service import AIService
from app.services.curriculum_topics import enrich_session_note

def test_translations_dict():
    print("Testing PDF_TRANSLATIONS...")
    for lang in ['fr', 'en', 'de']:
        assert lang in PDF_TRANSLATIONS, f"Missing {lang} in PDF_TRANSLATIONS"
        t = PDF_TRANSLATIONS[lang]
        assert 'days' in t and len(t['days']) == 7, f"Invalid days in {lang}"
        assert 'academic_types' in t and 'CM' in t['academic_types'], f"Missing academic_types in {lang}"
        assert 'task_types' in t and 'lecture_review' in t['task_types'], f"Missing task_types in {lang}"
        assert 'stats' in t and 'ai_sessions' in t['stats'], f"Missing stats in {lang}"
        # New 2-page & luminous PDF keys
        assert 'kpis' in t and 'total_workload' in t['kpis'], f"Missing kpis in {lang}"
        assert 'roadmap_title' in t, f"Missing roadmap_title in {lang}"
        assert 'ai_strategy_title' in t, f"Missing ai_strategy_title in {lang}"
        assert 'subject_goals_title' in t, f"Missing subject_goals_title in {lang}"
        assert 'session_details_title' in t, f"Missing session_details_title in {lang}"
        assert 'study_tips_title' in t and 'study_tips_content' in t, f"Missing study tips in {lang}"
        assert 'col_directives' in t and 'col_check' in t, f"Missing detailed session columns in {lang}"
        print(f"  [OK] PDF_TRANSLATIONS[{lang}] verified ({t['header_title']})")

def test_prompt_construction():
    print("Testing AIService._construct_prompt across FR, EN, DE...")
    ai = AIService(db=None)
    mock_planning_data = {
        'valid_slots': [{'day': 'Monday', 'start_time': '08:00', 'end_time': '12:00', 'duration_minutes': 240}],
        'subject_priorities': [{'subject_name': 'Math', 'exam_date': None, 'priority_score': 80.0, 'target_weekly_hours': 4}],
        'constraints': {'max_daily_hours': 6, 'required_breaks': [], 'fixed_slots': []}
    }
    
    # French
    prompt_fr = ai._construct_prompt(mock_planning_data, 20.0, {}, language="fr")
    assert "LANGUE DE SORTIE OBLIGATOIRE : FRANÇAIS" in prompt_fr, "French prompt missing language directive"
    
    # English
    prompt_en = ai._construct_prompt(mock_planning_data, 20.0, {}, language="en")
    assert "MANDATORY OUTPUT LANGUAGE: ENGLISH" in prompt_en, "English prompt missing language directive"
    
    # German
    prompt_de = ai._construct_prompt(mock_planning_data, 20.0, {}, language="de")
    assert "PFLICHT-AUSGABESPRACHE: DEUTSCH" in prompt_de, "German prompt missing language directive"
    
    print("  [OK] Prompt generation properly localized for FR, EN, DE")

def test_fallback_and_enrichment():
    print("Testing enrich_session_note and _generate_fallback_plan across FR, EN, DE...")
    # Enrichment
    note_fr = enrich_session_note("Statistiques", "exercise_practice", "", language="fr")
    note_en = enrich_session_note("Statistiques", "exercise_practice", "", language="en")
    note_de = enrich_session_note("Statistiques", "exercise_practice", "", language="de")
    
    assert "Exercices" in note_fr, f"FR note unexpected: {note_fr}"
    assert "Practical exercises" in note_en, f"EN note unexpected: {note_en}"
    assert "Praktische Anwendungsübungen" in note_de, f"DE note unexpected: {note_de}"
    print(f"  [OK] FR Note: {note_fr}")
    print(f"  [OK] EN Note: {note_en}")
    print(f"  [OK] DE Note: {note_de}")
    
    # Fallback plan
    ai = AIService(db=None)
    mock_planning_data = {
        'valid_slots': [{'day': 'Monday', 'start_time': '09:00', 'end_time': '11:00', 'duration_minutes': 120}],
        'subject_priorities': [{'subject_name': 'Algèbre', 'priority_score': 90.0, 'target_weekly_hours': 2}],
    }
    fb_en = ai._generate_fallback_plan(mock_planning_data, 2.0, language="en")
    assert "Structured pedagogical plan" in fb_en["reasoning"], f"EN fallback reasoning unexpected: {fb_en['reasoning']}"
    
    fb_de = ai._generate_fallback_plan(mock_planning_data, 2.0, language="de")
    assert "Pädagogisch strukturierter Lernplan" in fb_de["reasoning"], f"DE fallback reasoning unexpected: {fb_de['reasoning']}"
    
    fb_fr = ai._generate_fallback_plan(mock_planning_data, 2.0, language="fr")
    assert "Plan structuré par progression" in fb_fr["reasoning"], f"FR fallback reasoning unexpected: {fb_fr['reasoning']}"
    print("  [OK] Fallback plan reasoning localized for FR, EN, DE")

def test_pdf_flowables():
    print("Testing PDF flowables building in FR, EN, DE...")
    from unittest.mock import MagicMock
    from datetime import date, time
    from reportlab.lib.pagesizes import landscape, A4

    mock_plan = MagicMock()
    mock_plan.week_start = date(2026, 9, 14)
    mock_plan.edited = False

    mock_session = MagicMock()
    mock_session.day = 'Monday'
    mock_session.start_time = time(9, 0)
    mock_session.end_time = time(10, 30)
    mock_session.subject = MagicMock()
    mock_session.subject.name = 'Math'
    mock_session.task_type = 'lecture_review'
    mock_session.completed = False

    mock_academic = MagicMock()
    mock_academic.day_of_week = 'Tuesday'
    mock_academic.start_time = time(14, 0)
    mock_academic.end_time = time(16, 0)
    mock_academic.course_name = 'Operating Systems'
    mock_academic.session_type = 'CM'
    mock_academic.room_location = 'Amphi A'

    service = ExportService(db=None)

    for lang in ['fr', 'en', 'de']:
        service.lang = lang
        service.t = PDF_TRANSLATIONS[lang]
        stats = service._build_stats([mock_session], [mock_academic], mock_plan)
        assert len(stats) == 1, f"Failed building stats for {lang}"
        
        cal = service._build_calendar([mock_session], [mock_academic], {'Math': ('#4F46E5', '#EEF2FF')}, landscape(A4), 40)
        assert len(cal) > 0, f"Failed building calendar for {lang}"

        legend = service._build_legend({'Math': ('#4F46E5', '#EEF2FF')}, has_academic=True)
        assert len(legend) > 0, f"Failed building legend for {lang}"

        # Test Page 2 flowables
        ai_strat = service._build_ai_strategy(mock_plan, landscape(A4), 40)
        assert len(ai_strat) > 0, f"Failed building AI strategy for {lang}"

        subj_goals = service._build_subject_goals([], [mock_session], mock_plan, landscape(A4), 40)
        assert len(subj_goals) > 0, f"Failed building subject goals for {lang}"

        detailed_sessions = service._build_detailed_sessions([mock_session], {'Math': ('#4F46E5', '#EEF2FF')}, landscape(A4), 40)
        assert len(detailed_sessions) > 0, f"Failed building detailed sessions for {lang}"

        study_tips = service._build_study_tips(landscape(A4), 40)
        assert len(study_tips) > 0, f"Failed building study tips for {lang}"

        print(f"  [OK] Successfully built Page 1 & Page 2 flowables for lang='{lang}'")

if __name__ == "__main__":
    test_translations_dict()
    test_pdf_flowables()
    test_prompt_construction()
    test_fallback_and_enrichment()
    print("\nALL LOCALIZATION TESTS PASSED SUCCESSFULLY!")
