import subprocess
import sys

def test_cli():
    inputs = [
        "1", "Operating Systems", "2", "n",
        "2", "DBMS", "n",
        "3", "Python", "1", "n",
        "4", "2", "sample_notes.txt", "1", "n",
        "5", "Web Development", "1", "1", "n",
        "6"
    ]
    input_str = "\n".join(inputs) + "\n"

    print("Running main.py simulation...")
    process = subprocess.Popen(
        [sys.executable, "main.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=r"C:\Users\vansh\.gemini\antigravity\scratch\study_guide_assistant"
    )

    stdout, stderr = process.communicate(input=input_str, timeout=30)
    print("Process return code:", process.returncode)

    if process.returncode != 0:
        print("STDERR:\n", stderr)
        sys.exit(1)

    assert "STUDY GUIDE VIRTUAL ASSISTANT" in stdout, "Missing banner"
    assert "Learning Roadmap: Operating Systems" in stdout, "Roadmap failed"
    assert "Curated Learning Resources: DBMS" in stdout, "Resources failed"
    assert "Conceptual Summary: Python" in stdout, "Summary failed"
    assert "File: sample_notes.txt" in stdout, "Notes summary failed"
    assert "Complete Study Guide: Web Development" in stdout, "Full guide failed"
    assert "Thank you for using the Study Guide Virtual Assistant" in stdout, "Exit failed"

    print("\n✅ CLI Simulation Passed Successfully! All menus and options working seamlessly.")

if __name__ == "__main__":
    test_cli()
