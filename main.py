import os
import sys
from assistant import StudyGuideAssistant
import ai_client
def print_banner(assistant: StudyGuideAssistant):
    ai_status = "✨ AI Mode (Google Gemini Active)" if ai_client.is_ai_available() else "🔌 Offline Mode (Built-in Knowledge Base)"
    print("\n" + "=" * 66)
    print("      🤖 STUDY GUIDE VIRTUAL ASSISTANT - AI LAB PROJECT 📚")
    print("=" * 66)
    print(f" Current Status : {ai_status}")
    print(" Topics Loaded  : " + ", ".join(assistant.list_available_topics()))
    print("=" * 66)


def prompt_level() -> str:
    print("\nSelect your current proficiency level:")
    print("  1. Beginner     (Complete journey from foundations to mastery)")
    print("  2. Intermediate (Jump past basics to architecture & core patterns)")
    print("  3. Advanced     (Focus on high performance, concurrency & capstone)")
    choice = input("Enter choice (1-3, default=1): ").strip()

    mapping = {"1": "beginner", "2": "intermediate", "3": "advanced"}
    return mapping.get(choice, "beginner")


def prompt_length() -> str:
    print("\nSelect desired summary length:")
    print("  1. Short    (2-3 high-level key takeaways)")
    print("  2. Medium   (Balanced 4-5 key concepts & examples - default)")
    print("  3. Detailed (Comprehensive breakdown with all nuances)")
    choice = input("Enter choice (1-3, default=2): ").strip()

    mapping = {"1": "short", "2": "medium", "3": "detailed"}
    return mapping.get(choice, "medium")


def prompt_save_file(assistant: StudyGuideAssistant, content: str, default_name: str):
    save_choice = input("\n💾 Would you like to save this to a file? (y/n, default=n): ").strip().lower()
    if save_choice in {"y", "yes"}:
        try:
            saved_path = assistant.save_study_guide(content, default_name)
            print(f"✅ Successfully saved to: {saved_path}")
        except Exception as e:
            print(f"❌ Could not save file: {e}")


def handle_roadmap(assistant: StudyGuideAssistant):
    print("\n--- 🗺️ GET LEARNING ROADMAP ---")
    topic = input("Enter a topic (e.g. Python, Machine Learning, Operating Systems): ").strip()
    if not topic:
        print("⚠️ Topic cannot be empty. Returning to menu.")
        return

    level = prompt_level()
    print(f"\n⏳ Generating {level.capitalize()} roadmap for '{topic}'...")
    result = assistant.get_roadmap(topic, level=level)
    md_output = assistant.format_roadmap_markdown(result)
    print("\n" + md_output)

    if result.get("success"):
        prompt_save_file(assistant, md_output, f"{result['topic']}_{level}_roadmap")


def handle_resources(assistant: StudyGuideAssistant):
    print("\n--- 📚 GET CURATED RESOURCES ---")
    topic = input("Enter a topic (e.g. DBMS, Web Development, DSA): ").strip()
    if not topic:
        print("⚠️ Topic cannot be empty. Returning to menu.")
        return

    print(f"\n⏳ Fetching curated resources for '{topic}'...")
    result = assistant.get_resources(topic)
    md_output = assistant.format_resources_markdown(result)
    print("\n" + md_output)

    if result.get("success"):
        prompt_save_file(assistant, md_output, f"{result['topic']}_resources")


def handle_topic_summary(assistant: StudyGuideAssistant):
    print("\n--- 📝 SUMMARIZE A TOPIC ---")
    topic = input("Enter a topic to summarize: ").strip()
    if not topic:
        print("⚠️ Topic cannot be empty. Returning to menu.")
        return

    length = prompt_length()
    print(f"\n⏳ Creating {length} conceptual summary for '{topic}'...")
    result = assistant.summarize_topic(topic, length=length)
    md_output = assistant.format_topic_summary_markdown(result)
    print("\n" + md_output)

    if result.get("success"):
        prompt_save_file(assistant, md_output, f"{result['topic']}_{length}_summary")


def handle_notes_summary(assistant: StudyGuideAssistant):
    print("\n--- 📋 SUMMARIZE MY NOTES ---")
    print("Choose note input method:")
    print("  1. Paste text directly")
    print("  2. Load from a .txt file (e.g. sample_notes.txt)")
    choice = input("Enter choice (1-2, default=2): ").strip()

    raw_text = ""
    source_name = "notes"

    if choice == "1":
        print("\nPaste your notes below (type 'EOF' on a new line and press Enter when finished):")
        lines = []
        while True:
            try:
                line = input()
                if line.strip() == "EOF":
                    break
                lines.append(line)
            except EOFError:
                break
        raw_text = "\n".join(lines).strip()
        source_name = "pasted_notes"
    else:
        default_file = "sample_notes.txt"
        file_path = input(f"Enter path to .txt file (press Enter for '{default_file}'): ").strip()
        if not file_path:
            file_path = default_file

        if not os.path.isabs(file_path):
            base_dir = os.path.dirname(os.path.abspath(__file__))
            candidate = os.path.join(base_dir, file_path)
            if os.path.exists(candidate):
                file_path = candidate

        if not os.path.exists(file_path):
            print(f"❌ File not found at: {file_path}")
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw_text = f.read()
            source_name = os.path.splitext(os.path.basename(file_path))[0]
            print(f"📖 Loaded {len(raw_text)} characters from {os.path.basename(file_path)}.")
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            return

    if not raw_text.strip():
        print("⚠️ No text content provided to summarize.")
        return

    # Choose summarization technique
    print("\nSelect summarization engine:")
    print("  1. Extractive (Classical NLP Word-Frequency - Offline, 100% explainable)")
    ai_status = "Available" if ai_client.is_ai_available() else "Requires API Key (Option 7)"
    print(f"  2. Generative LLM (Google Gemini AI - {ai_status})")
    sum_engine = input("Enter choice (1-2, default=1): ").strip()
    use_ai = (sum_engine == "2")

    length = prompt_length()
    print(f"\n⏳ Processing summary ({length} length)...")
    res = assistant.summarize_user_notes(
        raw_text,
        length=length,
        source_name=f"File: {source_name}.txt" if choice == "2" else "Pasted Notes",
        use_ai=use_ai
    )

    if res.get("success"):
        print("\n" + res["markdown"])
        prompt_save_file(assistant, res["markdown"], f"{source_name}_summary")
    else:
        print(f"❌ Failed: {res.get('error')}")


def handle_full_guide(assistant: StudyGuideAssistant):
    print("\n--- 🎓 GENERATE FULL STUDY GUIDE (ALL THREE) ---")
    topic = input("Enter a topic (e.g. Machine Learning, Python, DBMS): ").strip()
    if not topic:
        print("⚠️ Topic cannot be empty. Returning to menu.")
        return

    level = prompt_level()
    length = prompt_length()

    print(f"\n⏳ Compiling full study guide for '{topic}' ({level.capitalize()} level, {length} summary)...")
    result = assistant.get_full_study_guide(topic, level=level, length=length)

    print("\n" + result["markdown"])

    if result.get("success"):
        prompt_save_file(assistant, result["markdown"], f"{result['topic']}_full_study_guide")


def handle_ai_tutor(assistant: StudyGuideAssistant):
    print("\n--- 🤖 ASK AI TUTOR (LLM DOUBT SOLVER) ---")
    if not ai_client.is_ai_available():
        print("⚠️ Gemini AI Key is currently not set.")
        print("💡 You can get a free key at https://aistudio.google.com/app/apikey (takes 30 seconds).")
        key_input = input("Enter your Gemini API key now (or press Enter to return): ").strip()
        if key_input:
            ai_client.set_api_key(key_input)
            print("✅ Key configured for this session!")
        else:
            return

    question = input("\nAsk any computer science question or concept (e.g. 'Explain Recursion simply with an analogy'): ").strip()
    if not question:
        print("⚠️ Question cannot be empty.")
        return

    print(f"\n⏳ Asking Google Gemini LLM: '{question}'...")
    res = assistant.ask_ai_tutor(question)
    if res.get("success"):
        print("\n" + "=" * 50)
        print("🤖 AI TUTOR RESPONSE")
        print("=" * 50)
        print(res["answer"])
        print("=" * 50)
        prompt_save_file(assistant, res["answer"], "ai_tutor_explanation")
    else:
        print(f"\n❌ Error: {res.get('error')}")


def handle_set_api_key(assistant: StudyGuideAssistant):
    print("\n--- 🔑 CONFIGURE GOOGLE GEMINI API KEY ---")
    current_key = ai_client.get_api_key()
    if current_key:
        masked = current_key[:6] + "..." + current_key[-4:]
        print(f"Current Key: {masked} (Active)")
    else:
        print("Current Key: None (Running in Offline Mode)")

    print("\nHow to get a 100% Free Gemini API key:")
    print("  1. Visit: https://aistudio.google.com/app/apikey")
    print("  2. Sign in with any Google account.")
    print("  3. Click 'Create API key' and copy it here.")
    print("  (No credit card required. Free tier includes 15 requests per minute!)")

    new_key = input("\nEnter your Gemini API key (or press Enter to cancel): ").strip()
    if new_key:
        ai_client.set_api_key(new_key, save_to_file=True)
        print("✅ API key successfully configured and saved to api_key.txt!")
        print("✨ AI Mode is now active for all topics, AI Tutor, and Summaries!")
    else:
        print("No change made.")


def main():
    assistant = StudyGuideAssistant()
    print_banner(assistant)

    while True:
        print("\n" + "-" * 40)
        print("               MAIN MENU")
        print("-" * 40)
        print("  1. Get resources")
        print("  2. Get roadmap")
        print("  3. Summarize a topic")
        print("  4. Summarize my notes")
        print("  5. Full study guide (all three)")
        print("  6. Ask AI Tutor (LLM Doubt Solver)")
        print("  7. Configure Gemini API Key")
        print("  8. Exit")
        print("-" * 40)

        choice = input("Enter your choice (1-8): ").strip()

        if choice == "1":
            handle_resources(assistant)
        elif choice == "2":
            handle_roadmap(assistant)
        elif choice == "3":
            handle_topic_summary(assistant)
        elif choice == "4":
            handle_notes_summary(assistant)
        elif choice == "5":
            handle_full_guide(assistant)
        elif choice == "6":
            handle_ai_tutor(assistant)
        elif choice == "7":
            handle_set_api_key(assistant)
        elif choice == "8":
            print("\n👋 Thank you for using the Study Guide Virtual Assistant! Happy learning!\n")
            sys.exit(0)
        elif not choice:
            print("⚠️ Empty input. Please enter a number between 1 and 8.")
        else:
            print(f"⚠️ Invalid choice '{choice}'. Please enter a number from 1 to 8.")


if __name__ == "__main__":
    main()
