"""
assistant.py
============
Core Study Guide Virtual Assistant logic.

Coordinates:
- Knowledge base loading (data/topics.json)
- Topic fuzzy matching using difflib
- Hybrid execution: Offline Knowledge Base + Optional Gemini AI Client
- Roadmap generation and level-based filtering (Beginner, Intermediate, Advanced)
- Resource curation grouped by type with verified links
- Topic summaries and notes summarization (via summarizer.py)
- Markdown formatting and file saving to outputs/
"""

import difflib
import json
import os
import re
from typing import Dict, Any, List, Optional, Tuple

import ai_client
import summarizer


class StudyGuideAssistant:
    """
    Virtual Assistant for generating learning roadmaps, curated resources,
    and structured summaries.
    """

    def __init__(self, data_path: Optional[str] = None):
        """
        Initializes the assistant and loads the offline knowledge base.
        """
        if data_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            data_path = os.path.join(base_dir, "data", "topics.json")

        self.data_path = data_path
        self.knowledge_base = self._load_knowledge_base()

    def _load_knowledge_base(self) -> Dict[str, Any]:
        """
        Loads topics from the JSON knowledge base file.
        """
        if not os.path.exists(self.data_path):
            print(f"[Warning] Knowledge base file not found at: {self.data_path}")
            return {"topics": {}}

        try:
            with open(self.data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("topics", {})
        except Exception as e:
            print(f"[Error] Failed to read knowledge base: {e}")
            return {"topics": {}}

    def list_available_topics(self) -> List[str]:
        """
        Returns a sorted list of canonical topic names in the offline knowledge base.
        """
        return [info["canonical_name"] for info in self.knowledge_base.values()]

    def find_topic(self, query: str) -> Tuple[Optional[str], Optional[Dict[str, Any]], List[str]]:
        """
        Resolves a user topic query against the knowledge base.

        Returns:
            (topic_key, topic_data, suggestions)
            - If exact/alias match found: returns (key, data, [])
            - If not found: returns (None, None, [closest suggestions via difflib])
        """
        if not query or not query.strip():
            return None, None, []

        q_clean = query.strip().lower()

        # 1. Direct key match
        if q_clean in self.knowledge_base:
            return q_clean, self.knowledge_base[q_clean], []

        # 2. Check canonical names and aliases (exact match)
        for key, data in self.knowledge_base.items():
            if q_clean == data.get("canonical_name", "").lower():
                return key, data, []
            for alias in data.get("aliases", []):
                if q_clean == alias.lower():
                    return key, data, []

        # 3. Whole-word / phrase match (e.g. user entered "study dbms" or "web dev guide")
        for key, data in self.knowledge_base.items():
            cname = data.get("canonical_name", "").lower()
            if re.search(rf"\b{re.escape(cname)}\b", q_clean):
                return key, data, []
            for alias in data.get("aliases", []):
                if re.search(rf"\b{re.escape(alias.lower())}\b", q_clean):
                    return key, data, []

        # 4. Fuzzy match using difflib for closest suggestions
        all_candidates = []
        name_to_key = {}
        for key, data in self.knowledge_base.items():
            cname = data.get("canonical_name", key)
            if cname not in all_candidates:
                all_candidates.append(cname)
            name_to_key[cname.lower()] = key
            for alias in data.get("aliases", []):
                if alias not in all_candidates:
                    all_candidates.append(alias)
                name_to_key[alias.lower()] = key

        matches = difflib.get_close_matches(q_clean, all_candidates, n=3, cutoff=0.4)
        suggested_canonicals = []
        for m in matches:
            matched_key = name_to_key.get(m.lower())
            if matched_key and matched_key in self.knowledge_base:
                cname = self.knowledge_base[matched_key]["canonical_name"]
                if cname not in suggested_canonicals:
                    suggested_canonicals.append(cname)

        return None, None, suggested_canonicals

    # =========================================================================
    # 1. ROADMAP FEATURE
    # =========================================================================

    def get_roadmap(self, topic_query: str, level: str = "beginner") -> Dict[str, Any]:
        """
        Generates or retrieves a learning roadmap filtered by user proficiency level.

        Args:
            topic_query: Topic name (e.g. "Machine Learning", "Python")
            level: "beginner", "intermediate", or "advanced"

        Returns:
            Dict containing topic name, mode (offline/AI), filtered stages, and summary.
        """
        level = level.lower().strip()
        if level not in {"beginner", "intermediate", "advanced"}:
            level = "beginner"

        key, data, suggestions = self.find_topic(topic_query)

        raw_stages = []
        canonical_name = topic_query.strip().title()
        mode_used = "Offline Knowledge Base"

        if data:
            raw_stages = data.get("roadmap", [])
            canonical_name = data.get("canonical_name", canonical_name)
        else:
            # Topic not in local database -> Try Gemini AI mode if key available
            if ai_client.is_ai_available():
                print(f"[AI Mode] Topic '{topic_query}' not in local DB. Querying Gemini AI...")
                ai_stages = ai_client.generate_roadmap_ai(topic_query)
                if ai_stages:
                    raw_stages = ai_stages
                    mode_used = "Gemini AI Generated"
                else:
                    print("[Notice] AI generation failed. Falling back to suggestions.")

        if not raw_stages:
            return {
                "success": False,
                "topic": topic_query,
                "suggestions": suggestions,
                "error": f"Topic '{topic_query}' was not found in the offline knowledge base.",
                "available_topics": self.list_available_topics()
            }

        # Filter stages according to the requested proficiency level:
        # - Beginner: Shows the complete roadmap from foundations to advanced (all stages)
        # - Intermediate: Skips elementary basics (stages 1-2) to start at intermediate principles
        # - Advanced: Focuses directly on advanced specialized concepts and capstone projects
        if level == "intermediate":
            filtered_stages = [s for s in raw_stages if s.get("level", "").lower() in {"intermediate", "advanced"}]
            # Fallback if no specific tags
            if not filtered_stages:
                filtered_stages = raw_stages[2:] if len(raw_stages) > 2 else raw_stages
            level_note = "Intermediate Level: Foundations skipped; focusing on core architecture, design patterns, and advanced concepts."
        elif level == "advanced":
            filtered_stages = [s for s in raw_stages if s.get("level", "").lower() == "advanced"]
            if not filtered_stages:
                filtered_stages = raw_stages[-2:] if len(raw_stages) >= 2 else raw_stages
            level_note = "Advanced Level: Focusing exclusively on production-grade systems, concurrency, optimization, and capstone deployment."
        else:
            filtered_stages = raw_stages
            level_note = "Beginner Level: Complete end-to-end learning path from initial setup to advanced mastery."

        return {
            "success": True,
            "topic": canonical_name,
            "level": level.capitalize(),
            "level_note": level_note,
            "mode": mode_used,
            "total_stages": len(filtered_stages),
            "stages": filtered_stages
        }

    def format_roadmap_markdown(self, roadmap_result: Dict[str, Any]) -> str:
        """
        Formats roadmap dictionary into clean, presentation-ready Markdown.
        """
        if not roadmap_result.get("success"):
            return self._format_not_found(roadmap_result)

        topic = roadmap_result["topic"]
        level = roadmap_result["level"]
        mode = roadmap_result["mode"]
        lines = [
            f"## Learning Roadmap: {topic}",
            f"**Target Level:** {level}  |  **Source:** {mode}",
            f"> *{roadmap_result['level_note']}*",
            ""
        ]

        for s in roadmap_result["stages"]:
            st_num = s.get("stage_number", "")
            st_lvl = s.get("level", "")
            title = s.get("title", "")
            time_est = s.get("time_estimate", "")
            subtopics = s.get("subtopics", [])
            task = s.get("practice_task", "")

            lines.append(f"### Stage {st_num}: {title} [{st_lvl}]")
            lines.append(f"- **Estimated Time:** {time_est}")
            lines.append("- **Core Subtopics:**")
            for sub in subtopics:
                if isinstance(sub, dict):
                    sname = sub.get("name", sub.get("title", "Topic"))
                    sdesc = sub.get("description", "")
                    lines.append(f"  - **{sname}**: {sdesc}" if sdesc else f"  - **{sname}**")
                else:
                    lines.append(f"  - {sub}")
            if task:
                lines.append(f"- **Hands-on Practice Task:** {task}")
            lines.append("")

        return "\n".join(lines)

    # =========================================================================
    # 2. RESOURCES FEATURE
    # =========================================================================

    def get_resources(self, topic_query: str) -> Dict[str, Any]:
        """
        Retrieves 4-6 curated learning resources grouped by type.
        """
        key, data, suggestions = self.find_topic(topic_query)
        resources_list = []
        canonical_name = topic_query.strip().title()
        mode_used = "Offline Knowledge Base"

        if data:
            resources_list = data.get("resources", [])
            canonical_name = data.get("canonical_name", canonical_name)
        else:
            if ai_client.is_ai_available():
                print(f"[AI Mode] Topic '{topic_query}' not in local DB. Fetching resources from Gemini...")
                ai_res = ai_client.generate_resources_ai(topic_query)
                if ai_res:
                    resources_list = ai_res
                    mode_used = "Gemini AI Generated"

        if not resources_list:
            return {
                "success": False,
                "topic": topic_query,
                "suggestions": suggestions,
                "error": f"No resources available for '{topic_query}' in offline mode.",
                "available_topics": self.list_available_topics()
            }

        # Group resources by type
        grouped: Dict[str, List[Dict[str, str]]] = {}
        for r in resources_list:
            rtype = r.get("type", "General")
            grouped.setdefault(rtype, []).append(r)

        return {
            "success": True,
            "topic": canonical_name,
            "mode": mode_used,
            "total_resources": len(resources_list),
            "grouped_resources": grouped,
            "raw_resources": resources_list
        }

    def format_resources_markdown(self, resources_result: Dict[str, Any]) -> str:
        """
        Formats resources dictionary into clean Markdown grouped by type.
        """
        if not resources_result.get("success"):
            return self._format_not_found(resources_result)

        topic = resources_result["topic"]
        mode = resources_result["mode"]
        lines = [
            f"## Curated Learning Resources: {topic}",
            f"**Source:** {mode}  |  **Total Links:** {resources_result['total_resources']}",
            ""
        ]

        grouped = resources_result["grouped_resources"]
        for rtype, items in grouped.items():
            lines.append(f"### {rtype}")
            for item in items:
                name = item.get("name", "Resource")
                reason = item.get("reason", "")
                url = item.get("url", "").strip()

                if url:
                    lines.append(f"- **[{name}]({url})**")
                else:
                    lines.append(f"- **{name}**")
                if reason:
                    lines.append(f"  *{reason}*")
            lines.append("")

        return "\n".join(lines)

    # =========================================================================
    # 3. SUMMARY FEATURE (Topic Overview & Notes Extractive Summarizer)
    # =========================================================================

    def summarize_topic(self, topic_query: str, length: str = "medium") -> Dict[str, Any]:
        """
        Generates a concise conceptual overview of a topic:
        Definition, Key Concepts, Real-World Uses, and Common Mistakes.
        """
        length = length.lower().strip()
        if length not in {"short", "medium", "detailed"}:
            length = "medium"

        key, data, suggestions = self.find_topic(topic_query)
        summary_data = None
        canonical_name = topic_query.strip().title()
        mode_used = "Offline Knowledge Base"

        if data:
            summary_data = data.get("summary", {})
            canonical_name = data.get("canonical_name", canonical_name)
        else:
            if ai_client.is_ai_available():
                print(f"[AI Mode] Topic '{topic_query}' not in local DB. Generating summary via Gemini...")
                ai_sum = ai_client.generate_summary_ai(topic_query)
                if ai_sum:
                    summary_data = ai_sum
                    mode_used = "Gemini AI Generated"

        if not summary_data:
            return {
                "success": False,
                "topic": topic_query,
                "suggestions": suggestions,
                "error": f"Topic '{topic_query}' could not be summarized in offline mode.",
                "available_topics": self.list_available_topics()
            }

        definition = summary_data.get("definition", "")
        key_concepts = summary_data.get("key_concepts", [])
        real_world_uses = summary_data.get("real_world_uses", [])
        common_mistakes = summary_data.get("common_mistakes", [])

        # Filter content according to length option:
        # - short: Definition + 2 key concepts + 1 real-world use
        # - medium: Definition + 4 key concepts + 2 real-world uses + 2 common mistakes
        # - detailed: Full definition + all key concepts + all real-world uses + all common mistakes
        if length == "short":
            key_concepts = key_concepts[:2]
            real_world_uses = real_world_uses[:1]
            common_mistakes = []
        elif length == "medium":
            key_concepts = key_concepts[:4]
            real_world_uses = real_world_uses[:3]
            common_mistakes = common_mistakes[:2]

        return {
            "success": True,
            "topic": canonical_name,
            "mode": mode_used,
            "length": length.capitalize(),
            "definition": definition,
            "key_concepts": key_concepts,
            "real_world_uses": real_world_uses,
            "common_mistakes": common_mistakes
        }

    def format_topic_summary_markdown(self, summary_result: Dict[str, Any]) -> str:
        """
        Formats topic overview into structured Markdown.
        """
        if not summary_result.get("success"):
            return self._format_not_found(summary_result)

        topic = summary_result["topic"]
        length = summary_result["length"]
        mode = summary_result["mode"]

        lines = [
            f"## Conceptual Overview: {topic}",
            f"**Detail Level:** {length}  |  **Source:** {mode}",
            "",
            "### 1. Definition",
            f"> {summary_result['definition']}",
            "",
            "### 2. Key Concepts"
        ]

        for kc in summary_result["key_concepts"]:
            if isinstance(kc, dict):
                cname = kc.get("name", kc.get("concept", "Concept"))
                cdesc = kc.get("description", kc.get("details", ""))
                lines.append(f"- **{cname}**: {cdesc}")
            else:
                lines.append(f"- {kc}")
        lines.append("")

        if summary_result["real_world_uses"]:
            lines.append("### 3. Real-World Applications")
            for rwu in summary_result["real_world_uses"]:
                if isinstance(rwu, dict):
                    aname = rwu.get("application", rwu.get("use", "Application"))
                    adesc = rwu.get("description", "")
                    lines.append(f"- **{aname}**: {adesc}")
                else:
                    lines.append(f"- {rwu}")
            lines.append("")

        if summary_result["common_mistakes"]:
            lines.append("### 4. Common Beginner Pitfalls & Traps")
            for cm in summary_result["common_mistakes"]:
                if isinstance(cm, dict):
                    mname = cm.get("mistake", cm.get("trap", "Mistake"))
                    mcorr = cm.get("solution", cm.get("correction", cm.get("description", "")))
                    lines.append(f"- **{mname}**: {mcorr}")
                else:
                    lines.append(f"- {cm}")
            lines.append("")

        return "\n".join(lines)

    def summarize_user_notes(self, text_or_filepath: str, length: str = "medium", source_name: Optional[str] = None, use_ai: bool = False) -> Dict[str, Any]:
        """
        Summarizes raw notes pasted by the user or loaded from a .txt file.
        Supports both:
          - Offline Extractive word-frequency scoring (default)
          - Generative LLM Summarization (if use_ai=True and API key set)
        """
        source_description = source_name or "Pasted Text"
        text_content = text_or_filepath

        # Check if the input is a valid file path
        if os.path.exists(text_or_filepath) and os.path.isfile(text_or_filepath):
            try:
                with open(text_or_filepath, "r", encoding="utf-8") as f:
                    text_content = f.read()
                    source_description = f"File: {os.path.basename(text_or_filepath)}"
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to read file '{text_or_filepath}': {e}"
                }

        # Optional LLM Generative Summary
        if use_ai and ai_client.is_ai_available():
            ai_sum = ai_client.generate_notes_summary_ai(text_content, length=length)
            if ai_sum:
                return {
                    "success": True,
                    "source": source_description,
                    "mode": "Generative LLM (Google Gemini)",
                    "raw_text_length": len(text_content),
                    "markdown": ai_sum
                }

        # Default: Explainable Extractive Summary
        summary_dict = summarizer.summarize_text(text_content, length=length)
        formatted_md = summarizer.format_summary_markdown(summary_dict, title=source_description)

        return {
            "success": True,
            "source": source_description,
            "mode": "Extractive Word-Frequency",
            "raw_text_length": len(text_content),
            "summary_dict": summary_dict,
            "markdown": formatted_md
        }

    def ask_ai_tutor(self, question: str) -> Dict[str, Any]:
        """
        Sends a study question or doubt to the Gemini LLM Tutor.
        """
        if not ai_client.is_ai_available():
            return {
                "success": False,
                "error": "Gemini API key is not configured. Please enter your API key first (Option 7 in main menu)."
            }

        answer = ai_client.ask_ai_tutor(question)
        if not answer:
            return {
                "success": False,
                "error": "Could not connect to Gemini LLM. Please check your internet connection or API key."
            }

        return {
            "success": True,
            "question": question,
            "answer": answer
        }

    # =========================================================================
    # 4. FULL STUDY GUIDE
    # =========================================================================

    def get_full_study_guide(self, topic: str, level: str = "beginner", length: str = "medium") -> Dict[str, Any]:
        """
        Compiles the Roadmap, Resources, and Summary into one comprehensive guide.
        """
        roadmap_res = self.get_roadmap(topic, level=level)
        resources_res = self.get_resources(topic)
        summary_res = self.summarize_topic(topic, length=length)

        success = roadmap_res.get("success") or resources_res.get("success") or summary_res.get("success")
        suggestions = roadmap_res.get("suggestions", [])

        full_md_sections = []
        title_topic = roadmap_res.get("topic") or resources_res.get("topic") or topic.strip().title()

        full_md_sections.append(f"# 🎓 Complete Study Guide: {title_topic}")
        full_md_sections.append(f"*Generated by Study Guide Virtual Assistant*\n---\n")

        if summary_res.get("success"):
            full_md_sections.append(self.format_topic_summary_markdown(summary_res))
            full_md_sections.append("\n---\n")

        if roadmap_res.get("success"):
            full_md_sections.append(self.format_roadmap_markdown(roadmap_res))
            full_md_sections.append("\n---\n")

        if resources_res.get("success"):
            full_md_sections.append(self.format_resources_markdown(resources_res))

        full_markdown = "\n".join(full_md_sections)

        return {
            "success": success,
            "topic": title_topic,
            "roadmap": roadmap_res,
            "resources": resources_res,
            "summary": summary_res,
            "suggestions": suggestions,
            "markdown": full_markdown
        }

    # =========================================================================
    # 5. UTILITIES (Save File, Error Formatting)
    # =========================================================================

    def save_study_guide(self, content: str, topic_name: str, output_dir: Optional[str] = None) -> str:
        """
        Saves the generated markdown study guide to outputs/<topic>_study_guide.md.
        """
        if output_dir is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            output_dir = os.path.join(base_dir, "outputs")

        os.makedirs(output_dir, exist_ok=True)

        clean_slug = re.sub(r"[^\w\-]+", "_", topic_name.lower().strip()).strip("_")
        if not clean_slug:
            clean_slug = "study_guide"
        filename = f"{clean_slug}_study_guide.md"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return filepath

    def _format_not_found(self, result: Dict[str, Any]) -> str:
        """
        Helper to construct friendly suggestion text when a topic is missing.
        """
        topic = result.get("topic", "Unknown")
        suggestions = result.get("suggestions", [])
        available = result.get("available_topics", [])

        lines = [
            f"❌ **Topic '{topic}' was not found in the offline knowledge base.**",
            ""
        ]
        if suggestions:
            lines.append(f"🔍 **Did you mean one of these?**")
            for s in suggestions:
                lines.append(f"- **{s}**")
            lines.append("")
        elif available:
            lines.append("📋 **Currently available offline topics:**")
            for t in available:
                lines.append(f"- {t}")
            lines.append("")

        lines.append("💡 *Tip: You can set the GEMINI_API_KEY environment variable to dynamically query any topic in AI mode!*")
        return "\n".join(lines)
