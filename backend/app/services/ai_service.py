"""
AI Service for study plan generation

Supports:
- Ollama API (local development with Llama 3.2)
- Google Colab API (production with Llama 3.2 + LoRA)
"""
import asyncio
import hashlib
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime, date, timedelta, timezone
import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.generation_log import GenerationLog
from app.services.curriculum_topics import get_subject_prompt_context, is_note_vague, enrich_session_note


class AIService:
    """
    AI service client for generating study plan proposals.
    
    Supports both Ollama (local) and Google Colab (production) backends.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_AI_REQUESTS)
        self.timeout = settings.OLLAMA_TIMEOUT
        
        # Determine which backend to use
        self.use_colab = getattr(settings, 'AI_SERVICE_TYPE', 'ollama') == 'colab'
        
        if self.use_colab:
            self.base_url = getattr(settings, 'COLAB_API_URL', None)
            self.api_key = getattr(settings, 'COLAB_API_KEY', None)
            if not self.base_url:
                raise ValueError("COLAB_API_URL not configured")
        else:
            self.base_url = settings.OLLAMA_BASE_URL
            self.api_key = None
        
        self.model = settings.OLLAMA_MODEL  # llama3.2
        # Use at least 0.35 temperature to prevent deterministic loops and repetitive exercise copies
        configured_temp = float(getattr(settings, 'OLLAMA_TEMPERATURE', 0.2))
        self.temperature = max(configured_temp, 0.35)
        self.num_ctx = settings.OLLAMA_NUM_CTX
        
        # LoRA configuration
        self.lora_enabled = settings.LORA_ENABLED
        self.lora_adapter = settings.LORA_DEFAULT_ADAPTER if self.lora_enabled else None
    
    def _construct_prompt(
        self, 
        planning_data: Dict[str, Any],
        weekly_study_goal: float,
        user_preferences: Dict[str, Any],
        profile_context: Optional[Dict[str, Any]] = None,
        language: str = "fr"
    ) -> str:
        """
        Construct structured prompt for AI generation with enhanced context and language targeting.
        
        Args:
            planning_data: Output from PlanningEngine (may include academic_context
                           from AIContextService — Task 28.1/29.1).
            weekly_study_goal: Target weekly study hours
            user_preferences: User preferences (break duration, session length, etc.)
            profile_context: Additional profile context (semester dates, commitments, etc.)
            language: Target output language ('fr', 'en', 'de')
        
        Returns:
            Formatted prompt string
        """
        valid_slots = planning_data['valid_slots']
        subject_priorities = planning_data['subject_priorities']
        constraints = planning_data['constraints']
        
        lang_code = (language or "fr").lower()[:2]
        if lang_code == "en":
            lang_instruction = (
                "🌐 **MANDATORY OUTPUT LANGUAGE: ENGLISH**\n"
                "- Every session 'notes' field, learning objective, and the 'reasoning' field MUST be written in natural ENGLISH.\n"
                "- Keep course names recognizable, but write all explanatory, pedagogic and actionable instructions in English."
            )
            example_notes_1 = "Lecture Ch. 3: Sequence properties, limits and convergence theorems"
            example_notes_2 = "Practice Ch. 3: Problem sets on sequence limits and recurrence"
            example_reasoning = "Structured pedagogical progression starting with foundational theory followed by practical TD problem-solving"
        elif lang_code == "de":
            lang_instruction = (
                "🌐 **PFLICHT-AUSGABESPRACHE: DEUTSCH (German)**\n"
                "- Alle 'notes' (Notizen), Lernziele, Aufgabenbeschreibungen und das 'reasoning'-Feld MÜSSEN in natürlichem DEUTSCH verfasst sein.\n"
                "- Fachbegriffe beibehalten, aber alle Anweisungen, Zusammenfassungen und Lernziele auf Deutsch formulieren."
            )
            example_notes_1 = "Vorlesung Kap. 3: Folgen, Reihen und Konvergenzkriterien"
            example_notes_2 = "Übung Kap. 3: Aufgaben zu Grenzwerten und rekursiven Folgen"
            example_reasoning = "Didaktisch strukturierte Progression: Vertiefung der mathematischen Grundlagen gefolgt von gezielten Übungsaufgaben"
        else:
            lang_instruction = (
                "🌐 **LANGUE DE SORTIE OBLIGATOIRE : FRANÇAIS (French)**\n"
                "- Toutes les 'notes', les objectifs d'apprentissage et le champ 'reasoning' DOIVENT être rédigés en FRANÇAIS naturel.\n"
                "- Conservez les intitulés exacts mais formulez les explications et consignes en français."
            )
            example_notes_1 = "Cours Ch. 3 : Propriétés des suites et théorèmes de convergence"
            example_notes_2 = "TD Ch. 3 : Exercices 12, 14 (convergence) et problème 18 (suites récurrentes)"
            example_reasoning = "Progression pédagogique structurée avec théorie suivie de TD d'application"

        # System instruction forcing JSON-only output
        system_instruction = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a JSON API that generates study schedules. You MUST respond with ONLY valid JSON.
Rules:
- First character: {
- Last character: }
- NO markdown code blocks (no ```)
- NO explanatory text before or after the JSON
- NO "Here is..." or "Step 1:" phrases
- Put reasoning INSIDE the "reasoning" field of the JSON<|eot_id|>"""
        
        prompt = f"""{system_instruction}
<|start_header_id|>user<|end_header_id|>
Generate a weekly study schedule in JSON format.

**WEEKLY STUDY GOAL**: {weekly_study_goal} hours

{lang_instruction}
"""
        
        if profile_context:
            prompt += "\n**ACADEMIC CONTEXT**:\n"
            if profile_context.get('semester_start_date'):
                prompt += f"- Semester: {profile_context['semester_start_date']} to {profile_context.get('semester_end_date', 'TBD')}\n"
            if profile_context.get('exam_period_start'):
                prompt += f"- Exam Period starts: {profile_context['exam_period_start']}\n"
            if profile_context.get('total_course_hours_per_week'):
                prompt += f"- Class hours per week: {profile_context['total_course_hours_per_week']}h\n"
            if profile_context.get('other_commitments_hours'):
                prompt += f"- Other commitments: {profile_context['other_commitments_hours']}h/week\n"
            
            if profile_context.get('preferred_study_time'):
                prompt += f"- Preferred study time: {profile_context['preferred_study_time']}\n"
            if profile_context.get('study_pace'):
                prompt += f"- Study pace preference: {profile_context['study_pace']}\n"
        
        prompt += "\n**AVAILABLE TIME SLOTS**:\n"
        
        slots_by_day = {}
        for slot in valid_slots:
            day = slot['day']
            if day not in slots_by_day:
                slots_by_day[day] = []
            energy = f" [Energy: {slot.get('energy_level', 'medium')}]" if slot.get('energy_level') else ""
            slots_by_day[day].append(f"{slot['start_time']}-{slot['end_time']} ({slot['duration_minutes']}min){energy}")
        
        for day, slots in sorted(slots_by_day.items()):
            prompt += f"\n{day}:\n"
            for slot in slots:
                prompt += f"  - {slot}\n"
        
        prompt += f"\n**SUBJECTS** (ordered by priority):\n"
        for subj in subject_priorities:
            exam_info = f", exam: {subj['exam_date']}" if subj['exam_date'] else ""
            exam_type = f" ({subj['exam_type']})" if subj.get('exam_type') else ""
            ects_info = f", ECTS: {subj['ects_credits']}" if subj.get('ects_credits') else ""
            coef_info = f", coef: {subj['coefficient']}" if subj.get('coefficient') else ""
            mandatory = " [MANDATORY]" if subj.get('is_mandatory') else ""
            status = f" [{subj['validation_status'].upper()}]" if subj.get('validation_status') else ""
            progress = f", progress: {subj['current_progress']}%" if subj.get('current_progress') else ""
            
            prompt += f"- {subj['subject_name']}{mandatory}{status} (priority: {subj['priority_score']:.1f}, "
            prompt += f"target: {subj['target_weekly_hours']}h/week{ects_info}{coef_info}{exam_info}{exam_type}{progress})\n"
            
            if subj.get('weak_topics'):
                prompt += f"  Weak topics: {', '.join(subj['weak_topics'])}\n"
            
            key_concepts = get_subject_prompt_context(subj['subject_name'])
            if key_concepts:
                prompt += f"{key_concepts}\n"
        
        prompt += f"\n**CONSTRAINTS**:\n"
        
        # CRITICAL: List available AND forbidden days explicitly
        all_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        available_days = sorted(slots_by_day.keys())
        forbidden_days = [d for d in all_days if d not in available_days]
        
        prompt += f"\n⛔ HARD CONSTRAINT — ALLOWED DAYS (the student is ONLY free on these days):\n"
        prompt += f"  ✅ ALLOWED: {', '.join(available_days)}\n"
        if forbidden_days:
            prompt += f"  ❌ FORBIDDEN (student is NOT available, DO NOT USE): {', '.join(forbidden_days)}\n"
        prompt += f"  → Every session MUST have its \"day\" field set to one of: {', '.join(available_days)}\n"
        prompt += f"  → Any session on {', '.join(forbidden_days) if forbidden_days else 'N/A'} will be DELETED and wasted\n"
        
        if constraints['max_daily_hours']:
            prompt += f"- Maximum {constraints['max_daily_hours']} hours of study per day\n"
        
        for break_rule in constraints['required_breaks']:
            prompt += f"- Take {break_rule['duration_minutes']}min break after {break_rule['after_minutes']}min of study\n"
        
        if constraints['fixed_slots']:
            prompt += f"- {len(constraints['fixed_slots'])} fixed time slots already reserved\n"
        
        academic_schedule = planning_data.get("academic_schedule") or []
        if academic_schedule:
            prompt += f"\n🎓 **UNIVERSITY TIMETABLE (German Bologna Model: Vorlesung/CM, Übung/TD, Praktikum/TP)**:\n"
            prompt += "The student attends the following university sessions. DO NOT schedule personal study sessions during these times:\n"
            for cs in academic_schedule:
                room_str = f" in {cs['room_location']}" if cs.get('room_location') else ""
                code_str = f" ({cs['course_code']})" if cs.get('course_code') else ""
                group_str = f" [{cs.get('group_name')}]" if cs.get('group_name') else ""
                prompt += f"  - {cs['day_of_week']} {cs['start_time'][:5]}-{cs['end_time'][:5]}: {cs['course_name']}{code_str} [{cs['session_type']}]{group_str}{room_str}\n"
            prompt += "  👉 GERMAN PEDAGOGICAL ALIGNMENT RULES FOR AI:\n"
            prompt += "  - **CM (Vorlesung)**: Schedule synthesis & lecture review (Nachbereitung) within 24-48h after the lecture.\n"
            prompt += "  - **TD (Übung - 2h/week)**: Dynamic tutorial group. Schedule preparatory exercise problem-solving (Übungszettel Vorbereitung) BEFORE the TD slot so the student arrives prepared.\n"
            prompt += "  - **TP (Praktikum - 2h/week)**: Hands-on lab. Schedule pre-lab protocol reading before and lab report analysis after.\n"

        prompt += f"\n**USER PREFERENCES**:\n"
        if user_preferences:
            if 'preferred_study_times' in user_preferences:
                prompt += f"- Preferred times: {', '.join(user_preferences['preferred_study_times'])}\n"
            if 'session_length' in user_preferences:
                prompt += f"- Preferred session length: {user_preferences['session_length']} minutes\n"
            if 'break_duration' in user_preferences:
                prompt += f"- Preferred break duration: {user_preferences['break_duration']} minutes\n"

        # Task 29.1 — Inject enriched academic context from AIContextService
        academic_ctx = planning_data.get("academic_context")
        if academic_ctx:
            prompt += "\n**ACADEMIC TRACKING CONTEXT** (from academic management system):\n"

            # ECTS Progression
            prog = academic_ctx.get("academic_progress") or {}
            if prog.get("ects_obtained") is not None:
                prompt += (
                    f"- ECTS progress: {prog['ects_obtained']}/{prog.get('ects_required', '?')} "
                    f"({prog.get('progression_percentage', 0):.1f}% of degree complete)\n"
                )

            # Failed courses — highest priority
            failed = academic_ctx.get("failed_courses") or []
            if failed:
                prompt += f"- FAILED courses requiring urgent attention ({len(failed)}):\n"
                for fc in failed:
                    blocker = " [PREREQUISITE BLOCKER]" if fc.get("is_prerequisite_blocker") else ""
                    prompt += (
                        f"  * {fc['course_name']}{blocker} — "
                        f"{fc.get('attempt_count', 1)} attempt(s), "
                        f"{fc.get('days_since_first_failure', 0)} days since first failure\n"
                    )

            # Priority scores — inform session allocation
            priorities = academic_ctx.get("course_priorities") or []
            if priorities:
                prompt += "- Course priority scores (higher = allocate more time):\n"
                for p in priorities[:8]:  # Top 8 to keep prompt lean
                    prompt += (
                        f"  * {p['course_name']}: priority={p['priority_score']:.0f}/100, "
                        f"risk={p.get('risk_level', 'medium')}, "
                        f"recommended={p.get('recommended_weekly_hours', 2)}h/week, "
                        f"success_prob={p.get('success_probability', 50):.0f}%\n"
                    )

            # Upcoming exams — enforce proximity boost
            exams = academic_ctx.get("upcoming_exams") or []
            if exams:
                prompt += f"- Upcoming exams ({len(exams)} total):\n"
                for ex in exams[:5]:  # Next 5 exams
                    prompt += (
                        f"  * {ex['course_name']}: {ex['exam_date']} "
                        f"({ex.get('days_until', '?')} days away)"
                        f"{' — URGENT' if (ex.get('days_until') or 99) <= 7 else ''}\n"
                    )

            # Student profile context
            sp = academic_ctx.get("student_profile") or {}
            if sp.get("cursus_name"):
                prompt += f"- Academic track: {sp.get('cursus_name')} (semester {sp.get('current_semester', '?')})\n"

        prompt += f"""
**OPTIMIZATION INSTRUCTIONS**:
1. 🚨 ABSOLUTE RULE: EVERY session "day" MUST be one of: {', '.join(available_days)}. Sessions on other days = FATAL ERROR.
2. 🚨 CRITICAL: Sessions must fit within the exact time windows provided for each day
3. Prioritize MANDATORY and FAILED subjects (must validate)
4. Consider ECTS credits and coefficients (higher impact on grades)
5. Schedule difficult subjects during HIGH energy time slots
6. Focus on weak topics for each subject when planning sessions
7. Account for class hours and other commitments
8. Respect exam dates and types (projects need distributed time, exams need intensive review)
9. Distribute sessions across the week for spaced repetition
10. Respect all constraints (max daily hours, breaks, fixed slots)
11. Try to reach the weekly study goal of {weekly_study_goal} hours
12. Consider validation status and current progress
13. 🎯 COMPREHENSIVE SUBJECT COVERAGE: Every subject in the SUBJECTS list represents an active course the student MUST study. Make sure to schedule at least one study session for EVERY subject in the list during the week. Do NOT omit any subject. Distribute sessions so that higher-priority subjects (such as retake/failed subjects) receive more sessions, but all subjects have at least one session scheduled.

**PEDAGOGICAL PROGRESSION & DIVERSIFICATION RULES (CRITICAL)**:
1. 🚨 STRICT ANTI-REPETITION: Every single session for a subject MUST have UNIQUE, DIVERSE notes. NEVER repeat the same exercises or notes twice across the week.
2. PEDAGOGICAL PROGRESSION PER SUBJECT:
   - Session 1 on a subject: Focus on core theory comprehension, key definitions, formulas, and basic foundation drills.
   - Session 2 on a subject: Focus on intermediate problem-solving, TD exercises, and applied practice.
   - Session 3+ on a subject: Focus on advanced synthesis, multi-part problems, or timed exam simulations.
3. EXERCISE PRACTICE RULES:
   - When a subject has 2 or more sessions scheduled in the week, include both lecture_review and exercise_practice (with exercise_practice after lecture_review).
   - When a subject has 1 session due to total weekly hours constraints, assign the most appropriate task type (e.g. exercise_practice or lecture_review) with concrete actionable learning notes.
   - In "notes" for exercise_practice, specify concrete learning objectives tailored to the subject syllabus (e.g. mention specific theorems, formulas, or exercise themes).
4. 🚨 STRICT FORBIDDEN PLACEHOLDERS IN "notes" FIELD:
   - NEVER use vague templates like "Solve problems 7.3-8.16", "Review modules 2-10", "Review chapters 1-5", "Read textbook pages 50-100", or "Work on project milestone 1".
   - You MUST write PRECISE, ACTIONABLE learning objectives describing EXACTLY what the student is studying (e.g., "Exercices d'application : calcul d'intégrales multiples et dérivées partielles", "Conteneurisation Docker de l'API FastAPI et benchmark de latence").
5. UPCOMING EXAMS:
   - For subjects with upcoming exams, schedule "exam_preparation" sessions with past exam problems (annales).

**TASK TYPE GUIDE**:
- lecture_review: Re-reading notes, summarizing theory (first session on a topic)
- exercise_practice: Solving problems, applying theory — MANDATORY every week per subject
- exam_preparation: Mock exams, timed practice (close to exam dates)
- project_work: Assignments, lab reports
- reading: Textbooks, articles

⛔ **FINAL VERIFICATION BEFORE OUTPUT** ⛔:
Before generating your JSON, verify EVERY session:
- Is the "day" field one of [{', '.join(available_days)}]? If NOT → REMOVE that session.
- Is the time within the available slots for that day? If NOT → ADJUST or REMOVE.
- You have {len(available_days)} available days. Your output should have sessions ONLY on those days.

🚨 **CRITICAL JSON-ONLY OUTPUT RULE** 🚨:
You are a JSON generator, NOT a conversational assistant.
Your response will be parsed by json.loads() in Python.
Any text outside the JSON object will cause a FATAL ERROR.

**RULES**:
1. Start IMMEDIATELY with {{ (opening brace)
2. End with }} (closing brace)
3. NO ```json markdown blocks
4. NO explanations before the JSON
5. NO step-by-step reasoning outside the JSON
6. NO "Here is..." or "Let me..." phrases
7. Put your reasoning INSIDE the "reasoning" field

**CORRECT OUTPUT** (copy this pattern):
{{"sessions":[{{"day":"Monday","start_time":"09:00:00","end_time":"10:30:00","subject_name":"Mathematics","task_type":"lecture_review","notes":"{example_notes_1}"}},{{"day":"Wednesday","start_time":"14:00:00","end_time":"15:30:00","subject_name":"Mathematics","task_type":"exercise_practice","notes":"{example_notes_2}"}}],"total_hours":25.5,"reasoning":"{example_reasoning}"}}

**VALID TASK TYPES**: lecture_review, exercise_practice, exam_preparation, project_work, reading<|eot_id|>
<|start_header_id|>assistant<|end_header_id|>
{{"""
        
        return prompt
    
    def _fix_time_format(self, time_str: str) -> str:
        """
        Fix invalid time formats from AI (e.g., 24:15:00 → 00:15:00, 25:30:00 → 01:30:00)
        
        Args:
            time_str: Time string in format HH:MM:SS
        
        Returns:
            Corrected time string in valid HH:MM:SS format (00-23 hours)
        """
        try:
            parts = time_str.split(':')
            if len(parts) != 3:
                return time_str
            
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = int(parts[2])
            
            # Fix hours >= 24 (wrap around to next day)
            if hours >= 24:
                hours = hours % 24
                print(f"[AI_SERVICE] Fixed invalid hour: {time_str} → {hours:02d}:{minutes:02d}:{seconds:02d}")
            
            # Validate minutes and seconds
            if minutes >= 60:
                hours += minutes // 60
                minutes = minutes % 60
            
            if seconds >= 60:
                minutes += seconds // 60
                seconds = seconds % 60
            
            # Handle hour overflow after minute/second fixes
            if hours >= 24:
                hours = hours % 24
            
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        except (ValueError, IndexError):
            print(f"[AI_SERVICE] Warning: Could not parse time '{time_str}', returning as-is")
            return time_str
    
    def _extract_json_from_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON from AI response with multiple fallback strategies.
        
        The AI might return JSON wrapped in markdown code blocks or with extra text.
        This method tries to extract clean JSON using multiple approaches.
        
        Common issues handled:
        - Double braces: {{...}} → {...}
        - Markdown blocks: ```json ... ```
        - Extra whitespace and newlines
        - Explanatory text before/after JSON
        - Text after closing brace (Llama explaining steps)
        """
        import re
        from datetime import datetime, time
        
        # Log original response for debugging
        print(f"[AI_SERVICE] Raw response length: {len(response_text)} characters")
        if len(response_text) < 500:
            print(f"[AI_SERVICE] Raw response preview: {response_text[:500]}")
        
        # PRE-PROCESSING: Clean common issues BEFORE parsing
        
        # 1. Extract content from markdown code blocks FIRST (if present)
        # Pattern: ```json ... ``` or ``` ... ```
        markdown_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if markdown_match:
            print("[AI_SERVICE] Found markdown code block, extracting content")
            response_text = markdown_match.group(1).strip()
        else:
            # If no markdown blocks, just remove stray backticks
            response_text = re.sub(r'```json\s*', '', response_text)
            response_text = re.sub(r'```\s*', '', response_text)
        
        # 2. Fix double braces {{...}} → {...}
        response_text = response_text.replace('{{', '{').replace('}}', '}')
        
        # 3. Fix missing opening brace (Llama sometimes starts with "sessions": [...])
        response_text = response_text.strip()
        if not response_text.startswith('{') and ('"sessions"' in response_text or "'sessions'" in response_text):
            print("[AI_SERVICE] Missing opening brace detected, adding {")
            response_text = '{' + response_text
        
        # 4. Remove common prefixes (explanatory text before JSON)
        lines = response_text.split('\n')
        json_start_idx = -1
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('{'):
                json_start_idx = i
                break
        
        if json_start_idx > 0:
            print(f"[AI_SERVICE] Removed {json_start_idx} lines of prefix text")
            response_text = '\n'.join(lines[json_start_idx:])
        
        # 5. Ensure the response ends with }
        response_text = response_text.rstrip()
        if not response_text.endswith('}'):
            print("[AI_SERVICE] Missing closing brace detected, adding }")
            response_text = response_text + '}'
        
        # 6. Remove any text AFTER the last complete JSON object
        # Find the LAST } which should be the end of our JSON
        last_brace = response_text.rfind('}')
        if last_brace != -1 and last_brace < len(response_text) - 1:
            suffix = response_text[last_brace + 1:].strip()
            if suffix:
                print(f"[AI_SERVICE] Removing {len(suffix)} chars of suffix text after JSON")
                response_text = response_text[:last_brace + 1]
        
        def calculate_total_hours(plan_data: Dict[str, Any]) -> float:
            """Calculate total hours from sessions"""
            total_minutes = 0
            for session in plan_data.get('sessions', []):
                try:
                    start = datetime.strptime(session['start_time'], '%H:%M:%S').time()
                    end = datetime.strptime(session['end_time'], '%H:%M:%S').time()
                    
                    start_minutes = start.hour * 60 + start.minute
                    end_minutes = end.hour * 60 + end.minute
                    
                    duration = end_minutes - start_minutes
                    if duration < 0:
                        duration += 24 * 60  # Handle overnight sessions
                    
                    total_minutes += duration
                except:
                    pass
            
            return round(total_minutes / 60, 2)
        
        def fix_plan_data(plan_data: Dict[str, Any]) -> Dict[str, Any]:
            """Fix common issues in plan data"""
            
            # Fix invalid times in sessions (e.g., 24:15:00 → 00:15:00)
            if 'sessions' in plan_data:
                for session in plan_data['sessions']:
                    # Fix start_time
                    if 'start_time' in session:
                        session['start_time'] = self._fix_time_format(session['start_time'])
                    
                    # Fix end_time
                    if 'end_time' in session:
                        session['end_time'] = self._fix_time_format(session['end_time'])
            
            # Calculate total_hours if missing
            if 'total_hours' not in plan_data or plan_data['total_hours'] == 0:
                plan_data['total_hours'] = calculate_total_hours(plan_data)
            
            # Ensure diversity of exercises and notes across sessions for the same subject
            if 'sessions' in plan_data and isinstance(plan_data['sessions'], list):
                subject_counts = {}
                seen_notes = {}
                for session in plan_data['sessions']:
                    subj = session.get('subject_name', 'Matière')
                    ttype = session.get('task_type', 'exercise_practice')
                    subject_counts[subj] = subject_counts.get(subj, 0) + 1
                    s_idx = subject_counts[subj]

                    raw_note = str(session.get('notes', '')).strip()
                    # Check if this note was already seen for this subject or is a generic default
                    is_duplicate = (subj in seen_notes and raw_note.lower() in seen_notes[subj])
                    if is_duplicate or is_note_vague(raw_note):
                        session['notes'] = enrich_session_note(
                            subj, 
                            ttype, 
                            raw_note if not is_duplicate else None, 
                            session_index=s_idx - 1
                        )
                        print(f"[AI_SERVICE] Enriched note for {subj} (session #{s_idx}): {session['notes']}")

                    if subj not in seen_notes:
                        seen_notes[subj] = set()
                    if session.get('notes'):
                        seen_notes[subj].add(str(session['notes']).strip().lower())

            # Add reasoning if missing
            if 'reasoning' not in plan_data:
                plan_data['reasoning'] = "Study plan generated based on available time slots and priorities"
            
            return plan_data
        
        # Strategy 0: Try direct parsing after pre-processing (MOST COMMON CASE)
        try:
            result = json.loads(response_text.strip())
            if isinstance(result, dict) and 'sessions' in result:
                print("[AI_SERVICE] [OK] Strategy 0: Direct parse after pre-processing succeeded")
                return fix_plan_data(result)
        except json.JSONDecodeError as e:
            print(f"[AI_SERVICE] Strategy 0 failed: {e}")
            # If error is "Extra data" it means JSON is valid but followed by text
            if "Extra data" in str(e):
                print("[AI_SERVICE] Detected 'Extra data' - trying to extract just the JSON part")
                # Extract only up to the error position
                try:
                    result = json.loads(response_text[:e.pos].strip())
                    if isinstance(result, dict) and 'sessions' in result:
                        print("[AI_SERVICE] [OK] Strategy 0b: Extracted JSON before extra text")
                        return fix_plan_data(result)
                except:
                    pass
        
        # Strategy 0b: Find first complete JSON object (ignore everything after)
        # This handles: {"valid": "json"}## Extra text here
        try:
            # Find first { and try to parse incrementally
            start_idx = response_text.find("{")
            if start_idx != -1:
                # Count braces to find the complete JSON object
                depth = 0
                in_string = False
                escape_next = False
                
                for i in range(start_idx, len(response_text)):
                    char = response_text[i]
                    
                    if escape_next:
                        escape_next = False
                        continue
                    
                    if char == '\\':
                        escape_next = True
                        continue
                    
                    if char == '"' and not in_string:
                        in_string = True
                    elif char == '"' and in_string:
                        in_string = False
                    elif char == '{' and not in_string:
                        depth += 1
                    elif char == '}' and not in_string:
                        depth -= 1
                        if depth == 0:
                            # Found complete JSON object
                            json_str = response_text[start_idx:i+1]
                            try:
                                result = json.loads(json_str)
                                if isinstance(result, dict) and 'sessions' in result:
                                    print("[AI_SERVICE] [OK] Strategy 0b: Extracted complete JSON object (ignoring suffix)")
                                    return fix_plan_data(result)
                            except json.JSONDecodeError:
                                break
        except Exception as e:
            print(f"[AI_SERVICE] Strategy 0b exception: {e}")
        
        # Strategy 1: Try to find JSON in ```json code blocks
        if "```json" in response_text or "```" in response_text:
            match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if match:
                json_str = match.group(1).strip()
                try:
                    result = json.loads(json_str)
                    if isinstance(result, dict) and 'sessions' in result:
                        print("[AI_SERVICE] [OK] Strategy 1: Markdown block extraction succeeded")
                        return fix_plan_data(result)
                except json.JSONDecodeError:
                    pass
        
        # Strategy 2: Find the largest valid JSON object in the response
        brace_positions = [(m.start(), '{') for m in re.finditer(r'\{', response_text)]
        brace_positions += [(m.start(), '}') for m in re.finditer(r'\}', response_text)]
        brace_positions.sort()
        
        # Try to find matching braces
        for i, (start_pos, start_char) in enumerate(brace_positions):
            if start_char == '{':
                depth = 1
                for j in range(i + 1, len(brace_positions)):
                    pos, char = brace_positions[j]
                    if char == '{':
                        depth += 1
                    else:
                        depth -= 1
                        if depth == 0:
                            json_str = response_text[start_pos:pos + 1]
                            try:
                                result = json.loads(json_str)
                                # Validate it has expected structure
                                if isinstance(result, dict) and 'sessions' in result:
                                    print("[AI_SERVICE] [OK] Strategy 2: Brace matching succeeded")
                                    return fix_plan_data(result)
                            except json.JSONDecodeError:
                                continue
                            break
        
        # Strategy 3: Try simple extraction between first { and last }
        start_idx = response_text.find("{")
        end_idx = response_text.rfind("}") + 1
        
        if start_idx != -1 and end_idx > start_idx:
            json_str = response_text[start_idx:end_idx]
            try:
                result = json.loads(json_str)
                if isinstance(result, dict) and 'sessions' in result:
                    print("[AI_SERVICE] [OK] Strategy 3: Simple extraction succeeded")
                    return fix_plan_data(result)
            except json.JSONDecodeError:
                pass
        
        # Strategy 4: Last resort - log and return None
        print(f"[AI_SERVICE] [FAIL] All extraction strategies failed")
        print(f"[AI_SERVICE ERROR] Response length: {len(response_text)} characters")
        print(f"[AI_SERVICE ERROR] Full response:")
        print("="*70)
        print(response_text[:1000])  # First 1000 chars only
        print("="*70)
        
        return None
    
    def _compute_request_hash(self, prompt: str) -> str:
        """
        Compute SHA-256 hash of the request for logging and caching.
        """
        return hashlib.sha256(prompt.encode('utf-8')).hexdigest()
    
    async def _call_ollama_api(self, prompt: str) -> Dict[str, Any]:
        """
        Call Ollama API for generation.
        
        Args:
            prompt: Formatted prompt
        
        Returns:
            API response with generated text
        
        Raises:
            httpx.TimeoutException: If request times out
            httpx.HTTPError: If API returns error
        """
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_ctx": self.num_ctx,
            }
        }
        
        # Add LoRA adapter if enabled
        if self.lora_enabled and self.lora_adapter:
            payload["options"]["lora_adapter"] = self.lora_adapter
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
    
    async def _call_colab_api(self, prompt: str) -> Dict[str, Any]:
        """
        Call Google Colab API for generation.
        
        Args:
            prompt: Formatted prompt
        
        Returns:
            API response with generated text
        
        Raises:
            httpx.TimeoutException: If request times out
            httpx.HTTPError: If API returns error
        """
        url = f"{self.base_url}/generate"
        
        headers = {
            "ngrok-skip-browser-warning": "true",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        payload = {
            "prompt": prompt,
            "temperature": self.temperature,
            "max_tokens": self.num_ctx,
        }
        
        # Add LoRA adapter if enabled
        if self.lora_enabled and self.lora_adapter:
            payload["lora_adapter"] = self.lora_adapter
        
        try:
            print(f"[AI_SERVICE] Calling Colab API: {url}")
            print(f"[AI_SERVICE] Payload size: {len(str(payload))} bytes")
            print(f"[AI_SERVICE] Prompt length: {len(prompt)} chars")
            
            # Timeout granulaire : 30s pour connexion, 300s pour lecture, 30s pour écriture
            timeout = httpx.Timeout(connect=30.0, read=300.0, write=30.0, pool=30.0)
            
            print(f"[AI_SERVICE] Creating httpx client with timeout: connect=30s, read=300s...")
            
            async with httpx.AsyncClient(timeout=timeout) as client:
                print(f"[AI_SERVICE] Sending POST request to Colab...")
                import time
                start = time.time()
                
                response = await client.post(url, json=payload, headers=headers)
                
                elapsed = time.time() - start
                print(f"[AI_SERVICE] [OK] Response received in {elapsed:.2f}s - HTTP {response.status_code}")
                
                response.raise_for_status()
                
                result = response.json()
                print(f"[AI_SERVICE] [OK] JSON parsed successfully")
                
                # Log la taille de la réponse
                generated_text = result.get("generated_text", "")
                print(f"[AI_SERVICE] Generated text length: {len(generated_text)} chars")
                
                return result
                
        except httpx.TimeoutException as e:
            print(f"[AI_SERVICE] [ERROR] TIMEOUT: {e}")
            print(f"[AI_SERVICE] Cette erreur signifie que Colab prend plus de 5 minutes à répondre.")
            print(f"[AI_SERVICE] Vérifiez que le GPU Colab est actif et le modèle est chargé.")
            raise
        except httpx.HTTPError as e:
            print(f"[AI_SERVICE] [ERROR] HTTP Error: {e}")
            print(f"[AI_SERVICE] Response status: {e.response.status_code if hasattr(e, 'response') else 'N/A'}")
            print(f"[AI_SERVICE] Response body: {e.response.text[:500] if hasattr(e, 'response') else 'N/A'}")
            raise
        except Exception as e:
            print(f"[AI_SERVICE] [ERROR] Unexpected error calling Colab: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            raise

    async def _call_colab_stream_api(self, prompt: str) -> str:
        """
        Call Colab /generate_stream SSE endpoint and reassemble the full text.

        Consumes token-by-token SSE events — the HTTP connection stays alive
        throughout generation so there is NO read timeout even for very long
        outputs.  Returns the concatenated generated text when the 'done'
        event is received.

        Raises:
            ValueError: If the Colab server returns an 'error' event
            httpx.TimeoutException: If the connection itself cannot be established
        """
        url = f"{self.base_url}/generate_stream"
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "prompt": prompt,
            "temperature": self.temperature,
            "max_tokens": self.num_ctx,
        }
        if self.lora_enabled and self.lora_adapter:
            payload["lora_adapter"] = self.lora_adapter

        full_text = ""
        token_count = 0

        # Use a long connect timeout but NO read timeout — streaming stays alive
        limits = httpx.Limits(max_connections=5)
        timeout = httpx.Timeout(connect=30.0, read=None, write=30.0, pool=30.0)

        async with httpx.AsyncClient(timeout=timeout, limits=limits) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    raw = line[len("data:"):].strip()
                    if not raw:
                        continue
                    try:
                        event = json.loads(raw)
                    except json.JSONDecodeError:
                        continue

                    event_type = event.get("type", "")
                    if event_type == "token":
                        text = event.get("text", "")
                        full_text += text
                        token_count += 1
                    elif event_type == "done":
                        print(f"[AI_SERVICE] Stream done — {event.get('total_tokens', token_count)} tokens "
                              f"in {event.get('generation_time', '?')}s")
                        break
                    elif event_type == "error":
                        raise ValueError(f"Colab stream error: {event.get('message', 'unknown')}")

        return full_text

    async def generate_study_plan_stream(
        self,
        planning_data: Dict[str, Any],
        weekly_study_goal: float,
        user_preferences: Dict[str, Any],
        user_id: int,
        profile_context: Optional[Dict[str, Any]] = None,
        language: str = "fr"
    ):
        """
        Async generator that yields SSE-formatted strings for StreamingResponse.

        IMPORTANT: async with semaphore cannot wrap yield statements in Python.
        We acquire/release manually with try/finally instead.

        Events emitted:
          data: {"type": "status",  "status": "generating"}
          data: {"type": "token",   "text": "..."}        ← relayed from Colab
          data: {"type": "done",    "plan": {...}, "log_id": N}
          data: {"type": "error",   "message": "..."}
        """
        import json as _json

        def _sse(payload: dict) -> str:
            return f"data: {_json.dumps(payload, ensure_ascii=False)}\n\n"

        # Acquire semaphore manually (can't use 'async with' around yield)
        await self.semaphore.acquire()
        start_time = time.time()

        prompt = self._construct_prompt(
            planning_data, weekly_study_goal, user_preferences, profile_context, language=language
        )
        request_hash = self._compute_request_hash(prompt)

        print(f"\n[AI_SERVICE STREAM] user={user_id} | prompt={len(prompt)} chars "
              f"| backend={'Colab' if self.use_colab else 'Ollama'}")

        yield _sse({"type": "status", "status": "generating"})

        full_text = ""
        try:
            if self.use_colab:
                # ── Try /generate_stream first (SSE token-by-token) ──────
                stream_url = f"{self.base_url}/generate_stream"
                headers = {
                    "ngrok-skip-browser-warning": "true",
                }
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"
                payload = {
                    "prompt": prompt,
                    "temperature": self.temperature,
                    "max_tokens": self.num_ctx,
                }
                if self.lora_enabled and self.lora_adapter:
                    payload["lora_adapter"] = self.lora_adapter

                use_stream = True
                timeout = httpx.Timeout(connect=30.0, read=None, write=30.0, pool=30.0)

                try:
                    async with httpx.AsyncClient(timeout=timeout) as client:
                        async with client.stream("POST", stream_url, json=payload, headers=headers) as response:
                            if response.status_code == 404:
                                # Old Colab notebook — fallback to batch /generate
                                use_stream = False
                                print("[AI_SERVICE STREAM] /generate_stream not found on Colab -- falling back to /generate")
                            else:
                                response.raise_for_status()
                                async for line in response.aiter_lines():
                                    if not line.startswith("data:"):
                                        continue
                                    raw = line[len("data:"):].strip()
                                    if not raw:
                                        continue
                                    try:
                                        event = _json.loads(raw)
                                    except _json.JSONDecodeError:
                                        continue

                                    evt_type = event.get("type", "")
                                    if evt_type == "token":
                                        token_text = event.get("text", "")
                                        full_text += token_text
                                        yield _sse({"type": "token", "text": token_text})
                                    elif evt_type == "done":
                                        break
                                    elif evt_type == "error":
                                        raise ValueError(event.get("message", "Colab stream error"))
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 404:
                        use_stream = False
                        print("[AI_SERVICE STREAM] /generate_stream not found -- fallback to /generate")
                    else:
                        raise

                if not use_stream:
                    # ── Fallback: batch /generate (old Colab notebook) ───
                    print("[AI_SERVICE STREAM] Using batch /generate endpoint")
                    yield _sse({"type": "status", "status": "generating_batch"})
                    response_data = await self._call_colab_api(prompt)
                    full_text = response_data.get("generated_text", "")
                    print(f"[AI_SERVICE STREAM] Batch generation complete: {len(full_text)} chars")
                    
                    # Log the raw response for debugging
                    if len(full_text) < 1000:
                        print(f"[AI_SERVICE STREAM] Raw response: {full_text}")
                    else:
                        print(f"[AI_SERVICE STREAM] Raw response (first 500 chars): {full_text[:500]}")

            else:
                # ── Ollama batch (local dev) ─────────────────────────────
                response_data = await self._call_ollama_api(prompt)
                full_text = response_data.get("response", "")

            # ── Parse JSON from accumulated text ──────────────────────────
            plan_data = self._extract_json_from_response(full_text)
            if plan_data is None:
                raise ValueError("Failed to extract valid JSON from AI response")

            duration_ms = int((time.time() - start_time) * 1000)
            token_count = len(full_text.split())

            log = GenerationLog(
                user_id=user_id,
                request_hash=request_hash,
                success=True,
                duration_seconds=duration_ms / 1000.0,
                token_count=token_count,
                error_message=None,
                created_at=datetime.now(timezone.utc)
            )
            self.db.add(log)
            self.db.flush()

            print(f"[AI_SERVICE STREAM] Done in {duration_ms}ms | {token_count} tokens")

            yield _sse({
                "type": "done",
                "plan": plan_data,
                "duration_ms": duration_ms,
                "log_id": log.id,
            })

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            log = GenerationLog(
                user_id=user_id,
                request_hash=request_hash,
                success=False,
                duration_seconds=duration_ms / 1000.0,
                token_count=0,
                error_message=str(e),
                created_at=datetime.now(timezone.utc)
            )
            self.db.add(log)
            self.db.flush()
            print(f"[AI_SERVICE STREAM] Error: {e}")
            yield _sse({"type": "error", "message": str(e)})

        finally:
            # Always release the semaphore
            self.semaphore.release()


    
    async def generate_study_plan(
        self,
        planning_data: Dict[str, Any],
        weekly_study_goal: float,
        user_preferences: Dict[str, Any],
        user_id: int,
        profile_context: Optional[Dict[str, Any]] = None,
        language: str = "fr"
    ) -> Dict[str, Any]:
        """
        Generate study plan using AI with enhanced context.
        
        Args:
            planning_data: Output from PlanningEngine
            weekly_study_goal: Target weekly study hours
            user_preferences: User preferences
            user_id: User ID for logging
            profile_context: Additional profile context (semester dates, commitments, etc.)
            language: Target output language ('fr', 'en', 'de')
        
        Returns:
            Dictionary with:
                - success: bool
                - plan: Dict with sessions if successful
                - error: str if failed
                - log_id: int (generation log ID)
        
        Raises:
            Exception: If generation fails after retries
        """
        async with self.semaphore:
            start_time = time.time()
            
            prompt = self._construct_prompt(
                planning_data, 
                weekly_study_goal, 
                user_preferences,
                profile_context,
                language=language
            )
            request_hash = self._compute_request_hash(prompt)
            
            # Debug logging
            print(f"\n[AI_SERVICE] Generating plan for user {user_id} in language '{language}'")
            print(f"[AI_SERVICE] Prompt length: {len(prompt)} characters")
            print(f"[AI_SERVICE] Using backend: {'Colab' if self.use_colab else 'Ollama'}")
            
            try:
                # Call appropriate API
                if self.use_colab:
                    response = await self._call_colab_api(prompt)
                    response_text = response.get("generated_text", "")
                else:
                    response = await self._call_ollama_api(prompt)
                    response_text = response.get("response", "")
                
                print(f"[AI_SERVICE] Received response ({len(response_text)} chars)")
                print(f"[AI_SERVICE] Response preview: {response_text[:200]}...")
                
                # Extract JSON from response
                plan_data = self._extract_json_from_response(response_text)
                
                if plan_data is None:
                    raise ValueError("Failed to extract valid JSON from AI response")
                
                print(f"[AI_SERVICE] Successfully extracted JSON with {len(plan_data.get('sessions', []))} sessions")
                
                # Calculate duration and token count
                duration_ms = int((time.time() - start_time) * 1000)
                token_count = response.get("eval_count", 0) if not self.use_colab else len(response_text.split())
                
                # Log successful generation
                log = GenerationLog(
                    user_id=user_id,
                    request_hash=request_hash,
                    success=True,
                    duration_seconds=duration_ms / 1000.0,  # Convert ms to seconds
                    token_count=token_count,
                    error_message=None,
                    created_at=datetime.now(timezone.utc)
                )
                self.db.add(log)
                self.db.flush()  # Use flush() instead of commit() to avoid expiring shared session objects
                
                log_id = log.id  # Capture ID before any potential expiry
                
                return {
                    "success": True,
                    "plan": plan_data,
                    "log_id": log_id,
                    "duration_ms": duration_ms,
                    "generation_time": duration_ms / 1000.0
                }
            
            except Exception as e:
                # Calculate duration
                duration_ms = int((time.time() - start_time) * 1000)
                print(f"[AI_SERVICE] Remote AI call failed ({e}). Falling back to algorithmic plan generator...")
                try:
                    fallback_plan = self._generate_fallback_plan(planning_data, weekly_study_goal, language=language)
                    log = GenerationLog(
                        user_id=user_id,
                        request_hash=request_hash,
                        success=True,
                        duration_seconds=duration_ms / 1000.0,
                        token_count=0,
                        error_message=f"Algorithmic fallback used (AI unavailable: {str(e)[:200]})",
                        created_at=datetime.now(timezone.utc)
                    )
                    self.db.add(log)
                    self.db.flush()
                    return {
                        "success": True,
                        "plan": fallback_plan,
                        "log_id": log.id,
                        "duration_ms": duration_ms,
                        "generation_time": duration_ms / 1000.0,
                        "fallback": True
                    }
                except Exception as fallback_err:
                    print(f"[AI_SERVICE] Fallback generator failed: {fallback_err}")

                # Log failed generation if fallback also failed
                log = GenerationLog(
                    user_id=user_id,
                    request_hash=request_hash,
                    success=False,
                    duration_seconds=duration_ms / 1000.0,
                    token_count=0,
                    error_message=str(e),
                    created_at=datetime.now(timezone.utc)
                )
                self.db.add(log)
                self.db.flush()
                
                log_id = log.id
                
                return {
                    "success": False,
                    "error": str(e),
                    "log_id": log_id,
                    "duration_ms": duration_ms
                }

    def _generate_fallback_plan(
        self,
        planning_data: Dict[str, Any],
        weekly_study_goal: float,
        language: str = "fr",
    ) -> Dict[str, Any]:
        """
        Deterministic, high-quality fallback generator when AI model/Colab is offline.
        Uses valid slots from planning_data, prioritized subjects, and rich curriculum topics in the requested language.
        """
        from app.services.curriculum_topics import enrich_session_note

        valid_slots = planning_data.get("valid_slots", [])
        priorities = planning_data.get("subject_priorities", [])
        if not priorities or not valid_slots:
            raise ValueError("Cannot generate plan: no priorities or valid slots available")

        # Sort subjects by priority score descending
        sorted_subjects = sorted(priorities, key=lambda p: p.get("priority_score", 0), reverse=True)
        subject_names = [s["subject_name"] for s in sorted_subjects]

        # Break long slots into chunks of max 90-120 minutes with 15-minute breaks
        chunks = []
        for slot in valid_slots:
            day = slot["day"]
            st_str = slot["start_time"]
            et_str = slot["end_time"]
            st = datetime.strptime(st_str, "%H:%M:%S" if len(st_str) == 8 else "%H:%M").time()
            et = datetime.strptime(et_str, "%H:%M:%S" if len(et_str) == 8 else "%H:%M").time()
            dur = slot.get("duration_minutes", 0)
            if dur <= 0:
                continue

            current_start = datetime.combine(date.today(), st)
            slot_end = datetime.combine(date.today(), et)

            while current_start + timedelta(minutes=45) <= slot_end:
                remaining = (slot_end - current_start).total_seconds() / 60
                if remaining >= 150:
                    chunk_dur = 90
                elif remaining >= 90:
                    chunk_dur = 90
                elif remaining >= 60:
                    chunk_dur = 60
                else:
                    chunk_dur = int(remaining)

                chunk_end = current_start + timedelta(minutes=chunk_dur)
                chunks.append({
                    "day": day,
                    "start_time": current_start.strftime("%H:%M:%S"),
                    "end_time": chunk_end.strftime("%H:%M:%S"),
                    "duration_minutes": chunk_dur
                })
                # Add 15 min break
                current_start = chunk_end + timedelta(minutes=15)

        if not chunks:
            chunks = valid_slots

        # Assign subjects round-robin weighted by priority
        sessions = []
        subject_session_counts = {name: 0 for name in subject_names}
        total_minutes = 0
        target_minutes = (weekly_study_goal or 20.0) * 60

        task_cycle = ["lecture_review", "exercise_practice", "project_work", "exam_preparation"]

        for chunk in chunks:
            if total_minutes >= target_minutes and len(sessions) >= len(subject_names):
                break

            # Pick subject with lowest session count (ties broken by priority order)
            cand = min(subject_names, key=lambda name: subject_session_counts[name])
            subject_name = cand
            count = subject_session_counts[subject_name]

            task_type = task_cycle[count % len(task_cycle)]
            note = enrich_session_note(subject_name, task_type, "", language=language)

            sessions.append({
                "day": chunk["day"],
                "start_time": chunk["start_time"],
                "end_time": chunk["end_time"],
                "subject_name": subject_name,
                "task_type": task_type,
                "notes": note
            })

            subject_session_counts[subject_name] += 1
            total_minutes += chunk.get("duration_minutes", 60)

        total_hours = round(total_minutes / 60.0, 2)
        lang_code = (language or "fr").lower()[:2]
        reasonings = {
            "en": "Structured pedagogical plan: lecture reviews followed by practice exercises and applied projects.",
            "de": "Pädagogisch strukturierter Lernplan: Vorlesungswiederholung gefolgt von Übungsaufgaben und Anwendungsprojekten.",
            "fr": "Plan structuré par progression pédagogique : revues de cours suivies d'exercices pratiques et projets d'application."
        }
        return {
            "sessions": sessions,
            "total_hours": total_hours,
            "reasoning": reasonings.get(lang_code, reasonings["fr"])
        }
