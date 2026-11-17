"""
test_suite.py
=============
Automated test suite verifying all required features:
1. 3 Topics tested (Roadmap, Resources, Summary)
2. Note summarizer on sample_notes.txt (Short, Medium, Detailed)
3. Unknown topic test with fuzzy matching (difflib)
4. Markdown saving to outputs/
"""

import os
import sys
from assistant import StudyGuideAssistant
import summarizer


def run_tests():
    print("=" * 60)
    print("🧪 STARTING STUDY GUIDE ASSISTANT VERIFICATION SUITE")
    print("=" * 60)

    assistant = StudyGuideAssistant()
    passed = 0
    total = 0

    # -------------------------------------------------------------
    # Test 1: Machine Learning (Intermediate Roadmap)
    # -------------------------------------------------------------
    total += 1
    print("\n[Test 1] Testing Topic 1: Machine Learning (Intermediate Roadmap)...")
    res_ml = assistant.get_roadmap("Machine Learning", level="intermediate")
    assert res_ml["success"] is True, "Failed to get Machine Learning roadmap"
    assert res_ml["level"] == "Intermediate"
    assert len(res_ml["stages"]) >= 3, f"Expected at least 3 intermediate stages, got {len(res_ml['stages'])}"
    for stg in res_ml["stages"]:
        assert "stage_number" in stg and "title" in stg and "practice_task" in stg
    md_ml = assistant.format_roadmap_markdown(res_ml)
    assert "Learning Roadmap: Machine Learning" in md_ml
    print(f"  ✅ Machine Learning Intermediate Roadmap OK ({len(res_ml['stages'])} stages returned).")
    passed += 1

    # -------------------------------------------------------------
    # Test 2: Operating Systems (Resources & Summary)
    # -------------------------------------------------------------
    total += 1
    print("\n[Test 2] Testing Topic 2: Operating Systems (Resources & Conceptual Summary)...")
    res_os = assistant.get_resources("Operating Systems")
    assert res_os["success"] is True, "Failed to get OS resources"
    assert res_os["total_resources"] >= 4, f"Expected at least 4 resources, got {res_os['total_resources']}"
    assert "Free courses" in res_os["grouped_resources"] or "Documentation" in res_os["grouped_resources"]
    md_res = assistant.format_resources_markdown(res_os)
    assert "Curated Learning Resources: Operating Systems" in md_res

    # Test summary lengths
    sum_short = assistant.summarize_topic("Operating Systems", length="short")
    sum_med = assistant.summarize_topic("Operating Systems", length="medium")
    sum_det = assistant.summarize_topic("Operating Systems", length="detailed")
    assert sum_short["success"] and sum_med["success"] and sum_det["success"]
    assert len(sum_short["key_concepts"]) <= len(sum_med["key_concepts"]) <= len(sum_det["key_concepts"])
    print(f"  ✅ Operating Systems Resources OK ({res_os['total_resources']} resources) and Summary depth scaling OK.")
    passed += 1

    # -------------------------------------------------------------
    # Test 3: Python (Full Study Guide + File Export)
    # -------------------------------------------------------------
    total += 1
    print("\n[Test 3] Testing Topic 3: Python (Full Guide & File Saving)...")
    res_py = assistant.get_full_study_guide("Python", level="beginner", length="medium")
    assert res_py["success"] is True
    assert "Complete Study Guide: Python" in res_py["markdown"]
    assert "Learning Roadmap" in res_py["markdown"]
    assert "Curated Learning Resources" in res_py["markdown"]

    saved_path = assistant.save_study_guide(res_py["markdown"], "python_test")
    assert os.path.exists(saved_path), f"File not saved at {saved_path}"
    with open(saved_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert len(content) > 500
    print(f"  ✅ Python Full Study Guide OK. Saved and verified at: {saved_path}")
    passed += 1

    # -------------------------------------------------------------
    # Test 4: Extractive Summarizer on sample_notes.txt
    # -------------------------------------------------------------
    total += 1
    print("\n[Test 4] Testing Extractive Summarizer on sample_notes.txt...")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sample_file = os.path.join(base_dir, "sample_notes.txt")
    assert os.path.exists(sample_file), "sample_notes.txt does not exist!"

    for length_opt, expected_bullets in [("short", 3), ("medium", 5), ("detailed", 8)]:
        sum_notes = assistant.summarize_user_notes(sample_file, length=length_opt)
        assert sum_notes["success"] is True, f"Failed note summary for length {length_opt}"
        s_dict = sum_notes["summary_dict"]
        assert len(s_dict["summary_bullets"]) <= expected_bullets
        assert len(s_dict["key_terms"]) > 0
        assert "**" in sum_notes["markdown"], "Key terms were not bolded in summary"
        print(f"  ✅ {length_opt.capitalize()} Note Summary OK: {s_dict['summary_sentences_count']} bullets from {s_dict['total_sentences']} sentences. Top terms: {s_dict['key_terms'][:4]}")
    passed += 1

    # -------------------------------------------------------------
    # Test 5: Unknown Topic & Fuzzy Matching (difflib)
    # -------------------------------------------------------------
    total += 1
    print("\n[Test 5] Testing Unknown Topics and Fuzzy Matching...")
    # Misspelled topic: "algos" -> should suggest "Data Structures & Algorithms"
    _, _, sugg_algo = assistant.find_topic("algos")
    assert "Data Structures & Algorithms" in sugg_algo, f"Expected 'Data Structures & Algorithms' in suggestions, got {sugg_algo}"
    print(f"  ✅ Fuzzy matching 'algos' successfully suggested: {sugg_algo}")

    # Misspelled topic: "pythn" -> should match directly or suggest Python
    key_py, data_py, sugg_py = assistant.find_topic("pythn")
    assert (data_py is not None) or ("Python" in sugg_py), f"Expected match or suggestion for 'pythn', got {sugg_py}"
    print(f"  ✅ Fuzzy matching 'pythn' handled successfully.")

    # Completely unknown topic
    res_unknown = assistant.get_roadmap("Quantum Astrophysics")
    assert res_unknown["success"] is False
    assert "available_topics" in res_unknown
    md_unknown = assistant.format_roadmap_markdown(res_unknown)
    assert "was not found in the offline knowledge base" in md_unknown
    print(f"  ✅ Completely unknown topic handled gracefully with available topic fallback.")
    passed += 1

    print("\n" + "=" * 60)
    print(f"🎉 ALL TESTS PASSED! ({passed}/{total})")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()
