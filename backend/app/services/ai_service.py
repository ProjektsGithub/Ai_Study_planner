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
from datetime import datetime, timezone
import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.generation_log import GenerationLog


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
        self.temperature = settings.OLLAMA_TEMPERATURE
        self.num_ctx = settings.OLLAMA_NUM_CTX
        
        # LoRA configuration
        self.lora_enabled = settings.LORA_ENABLED
        self.lora_adapter = settings.LORA_DEFAULT_ADAPTER if self.lora_enabled else None
    
    def _construct_prompt(
        self, 
        planning_data: Dict[str, Any],
        weekly_study_goal: float,
        user_preferences: Dict[str, Any],
        profile_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Construct structured prompt for AI generation with enhanced context.
        
        Args:
            planning_data: Output from PlanningEngine (may include academic_context
                           from AIContextService — Task 28.1/29.1).
            weekly_study_goal: Target weekly study hours
            user_preferences: User preferences (break duration, session length, etc.)
            profile_context: Additional profile context (semester dates, commitments, etc.)
        
        Returns:
            Formatted prompt string
        """
        valid_slots = planning_data['valid_slots']
        subject_priorities = planning_data['subject_priorities']
        constraints = planning_data['constraints']
        
        prompt = f"""You are an AI study planner. Generate a weekly study schedule based on the following data.

**WEEKLY STUDY GOAL**: {weekly_study_goal} hours
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
        
        prompt += f"\n**CONSTRAINTS**:\n"
        if constraints['max_daily_hours']:
            prompt += f"- Maximum {constraints['max_daily_hours']} hours of study per day\n"
        
        for break_rule in constraints['required_breaks']:
            prompt += f"- Take {break_rule['duration_minutes']}min break after {break_rule['after_minutes']}min of study\n"
        
        if constraints['fixed_slots']:
            prompt += f"- {len(constraints['fixed_slots'])} fixed time slots already reserved\n"
        
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
1. Prioritize MANDATORY and FAILED subjects (must validate)
2. Consider ECTS credits and coefficients (higher impact on grades)
3. Schedule difficult subjects during HIGH energy time slots
4. Focus on weak topics for each subject when planning sessions
5. Account for class hours and other commitments
6. Respect exam dates and types (projects need distributed time, exams need intensive review)
7. Distribute sessions across the week for spaced repetition
8. Respect all constraints (max daily hours, breaks, fixed slots)
9. Try to reach the weekly study goal of {weekly_study_goal} hours
10. Consider validation status and current progress

**MANDATORY EXERCISE RULE** (CRITICAL):
- Every subject MUST have at least ONE session with task_type "exercise_practice" per week
- exercise_practice sessions must come AFTER lecture_review sessions for the same subject
- In the "notes" of exercise_practice sessions, list 2-3 specific exercises (e.g. "Solve problems 5.1, 5.3; Practice integration by parts")
- For subjects with upcoming exams, add "exam_preparation" sessions in the last days before the exam

**TASK TYPE GUIDE**:
- lecture_review: Re-reading notes, summarizing theory (first session on a topic)
- exercise_practice: Solving problems, applying theory — MANDATORY every week per subject
- exam_preparation: Mock exams, timed practice (close to exam dates)
- project_work: Assignments, lab reports
- reading: Textbooks, articles

**CRITICAL OUTPUT REQUIREMENTS**:
- You MUST respond with ONLY valid JSON
- Do NOT include any explanatory text before or after the JSON
- Do NOT use markdown code blocks (no ```)
- Start your response directly with {{
- End your response directly with }}

**OUTPUT FORMAT**:
{{
  "sessions": [
    {{
      "day": "Monday",
      "start_time": "09:00:00",
      "end_time": "10:30:00",
      "subject_name": "Mathematics",
      "task_type": "lecture_review",
      "notes": "Review integration techniques chapter 5"
    }},
    {{
      "day": "Wednesday",
      "start_time": "14:00:00",
      "end_time": "15:30:00",
      "subject_name": "Mathematics",
      "task_type": "exercise_practice",
      "notes": "Solve exercises 5.1, 5.3, 5.7; Practice integration by parts"
    }}
  ],
  "total_hours": 25.5,
  "reasoning": "Brief explanation of the schedule strategy"
}}

**VALID TASK TYPES**: lecture_review, exercise_practice, exam_preparation, project_work, reading

**EXAMPLE**:
{{"sessions":[{{"day":"Monday","start_time":"09:00:00","end_time":"11:00:00","subject_name":"Math","task_type":"lecture_review","notes":"Review chapter 3"}},{{"day":"Wednesday","start_time":"14:00:00","end_time":"15:30:00","subject_name":"Math","task_type":"exercise_practice","notes":"Solve exercises 3.1-3.5; Practice separation of variables"}}],"total_hours":3.5,"reasoning":"Theory then practice"}}

Now generate the JSON study plan (JSON only, no other text):"""
        
        return prompt
    
    def _extract_json_from_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON from AI response with multiple fallback strategies.
        
        The AI might return JSON wrapped in markdown code blocks or with extra text.
        This method tries to extract clean JSON using multiple approaches.
        
        Common issues handled:
        - Double braces: {{...}} → {...}
        - Markdown blocks: ```json ... ```
        - Extra whitespace and newlines
        """
        import re
        from datetime import datetime, time
        
        # PRE-PROCESSING: Clean common issues BEFORE parsing
        # 1. Remove markdown code blocks
        response_text = re.sub(r'```json\s*', '', response_text)
        response_text = re.sub(r'```\s*', '', response_text)
        
        # 2. Fix double braces {{...}} → {...}
        # This is aggressive: replaces ALL double braces, not just at start/end
        # Llama sometimes outputs {{...}} instead of {...} throughout the JSON
        response_text = response_text.replace('{{', '{').replace('}}', '}')
        
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
            # Calculate total_hours if missing
            if 'total_hours' not in plan_data or plan_data['total_hours'] == 0:
                plan_data['total_hours'] = calculate_total_hours(plan_data)
            
            # Add reasoning if missing
            if 'reasoning' not in plan_data:
                plan_data['reasoning'] = "Study plan generated based on available time slots and priorities"
            
            return plan_data
        
        # Strategy 0: Try direct parsing after pre-processing (MOST COMMON CASE)
        try:
            result = json.loads(response_text)
            if isinstance(result, dict) and 'sessions' in result:
                print("[AI_SERVICE] [OK] Strategy 0: Direct parse after pre-processing succeeded")
                return fix_plan_data(result)
        except json.JSONDecodeError:
            pass
        
        # Strategy 1: Try to find JSON in ```json code blocks (PRIORITY)
        if "```json" in response_text or "```" in response_text:
            # Already cleaned by pre-processing, but try again with regex
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
        print(response_text)
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
        
        headers = {}
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
        
        async with httpx.AsyncClient(timeout=300.0) as client:  # 5 min — large prompts need time
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()

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
        profile_context: Optional[Dict[str, Any]] = None
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
            planning_data, weekly_study_goal, user_preferences, profile_context
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
                    yield _sse({"type": "status", "status": "generating_batch"})
                    response_data = await self._call_colab_api(prompt)
                    full_text = response_data.get("generated_text", "")

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
        profile_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate study plan using AI with enhanced context.
        
        Args:
            planning_data: Output from PlanningEngine
            weekly_study_goal: Target weekly study hours
            user_preferences: User preferences
            user_id: User ID for logging
            profile_context: Additional profile context (semester dates, commitments, etc.)
        
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
                profile_context
            )
            request_hash = self._compute_request_hash(prompt)
            
            # Debug logging
            print(f"\n[AI_SERVICE] Generating plan for user {user_id}")
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
                
                # Log failed generation
                log = GenerationLog(
                    user_id=user_id,
                    request_hash=request_hash,
                    success=False,
                    duration_seconds=duration_ms / 1000.0,  # Convert ms to seconds
                    token_count=0,
                    error_message=str(e),
                    created_at=datetime.now(timezone.utc)
                )
                self.db.add(log)
                self.db.flush()  # Use flush() instead of commit() to avoid expiring shared session objects
                
                log_id = log.id  # Capture ID before any potential expiry
                
                return {
                    "success": False,
                    "error": str(e),
                    "log_id": log_id,
                    "duration_ms": duration_ms
                }
