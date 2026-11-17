# 🤖 Study Guide Virtual Assistant

A clean, beginner-friendly **Study Guide Virtual Assistant** built in Python for AI laboratory course assignments and viva demonstrations.

The assistant takes any technical topic (such as *Machine Learning*, *Operating Systems*, or *Data Structures & Algorithms*) and generates:
1. **🗺️ ROADMAP** – A structured, stage-by-stage learning path tailored to your proficiency level (Beginner, Intermediate, or Advanced).
2. **📚 RESOURCES** – Curated high-quality learning resources grouped by type with verified links.
3. **📝 SUMMARY** – A conceptual breakdown of any topic OR an extractive word-frequency summary of your own notes / `.txt` files with key terms highlighted.

---

## 🌟 Key Features

### 1. Adaptive Learning Roadmap
- **5 to 8 ordered stages** spanning Beginner → Intermediate → Advanced.
- Each stage includes:
  - Stage title and duration estimate (e.g., `1–2 weeks`)
  - 3–4 essential sub-topics to master
  - A concrete hands-on practice project or coding task
- **Level-aware filtering:**
  - *Beginner*: Complete end-to-end curriculum from foundational principles.
  - *Intermediate*: Fast-tracks past basic syntax directly into system design, architecture, and patterns.
  - *Advanced*: Concentrates strictly on performance tuning, concurrency, and production deployment.

### 2. Curated & Verified Resources
- Categorized into: **Free courses**, **YouTube channels**, **Books**, **Practice websites**, and **Documentation**.
- Each resource includes a name, an exact one-line reason it is valuable, and verified, authoritative links (e.g., Python Docs, MDN, Coursera, freeCodeCamp, LeetCode, GeeksforGeeks).
- Safe and hallucination-free: no broken or invented URLs.

### 3. Dual-Mode Summarization
- **Option A (Topic Overview):** Generates formal definitions, core concepts, real-world industry applications, and common beginner pitfalls. Select from *Short*, *Medium*, or *Detailed* depth.
- **Option B (Notes Summarizer):** Summarizes pasted notes or `.txt` files using an offline **Extractive Text Summarization algorithm based on Normalized Word Frequency Scoring**. Automatically highlights significant technical keywords.

### 4. Hybrid Architecture: Offline First + Optional Gemini AI
- **Offline Mode (Default):** Runs 100% locally with zero API keys and zero internet access using a rich JSON knowledge base (`data/topics.json`). Includes pre-filled guides for:
  - Python
  - Machine Learning
  - Data Structures & Algorithms
  - Operating Systems
  - DBMS
  - Web Development
- **Fuzzy Matching (`difflib`):** If a user misspells a topic (e.g., `"pythn"`, `"algos"`), the system suggests closest matching topics.
- **AI Mode (Optional):** If an environment variable `GEMINI_API_KEY` is present, the assistant dynamically calls Google Gemini (`gemini-1.5-flash`) via standard REST or SDK to generate roadmaps, resources, and summaries for **any** subject. If the API fails or is unreachable, it automatically falls back to offline mode.

### 5. Bonus Web Interface
- In addition to the CLI, an interactive **Streamlit Web UI** (`app_ui.py`) is included.

---

## 📁 Project Structure

```text
study_guide_assistant/
├── main.py              # CLI entry point, interactive menu and flow
├── assistant.py         # Core orchestrator: roadmap, resources, and summary logic
├── summarizer.py        # Offline extractive text summarizer (word-frequency algorithm)
├── ai_client.py         # Optional Gemini API integration with automatic offline fallback
├── app_ui.py            # Optional Streamlit Web UI for interactive browser experience
├── data/
│   └── topics.json      # Built-in offline knowledge base with 6 core CS topics
├── sample_notes.txt     # Sample lecture notes to demonstrate the note summarizer
├── requirements.txt     # Dependencies list (standard library runs out-of-the-box)
├── outputs/             # Directory where exported .md study guides are saved
└── README.md            # Comprehensive documentation, viva notes, and lab report guide
```

---

## 🚀 Setup & Installation

### Prerequisites
- Python 3.9+ installed on Windows, macOS, or Linux.
- **Zero mandatory external dependencies:** The core CLI and extractive summarizer use standard Python libraries (`json`, `re`, `difflib`, `collections`, `urllib`).

### 1. Clone or Navigate to the Project
```bash
cd study_guide_assistant
```

### 2. (Optional) Install Dependencies
For the optional Streamlit Web UI or Google Generative AI SDK:
```bash
pip install -r requirements.txt
```

### 3. (Optional) Set up AI Mode
To enable dynamic Gemini AI generation for arbitrary topics:

**Windows (PowerShell):**
```powershell
$env:GEMINI_API_KEY="your_actual_gemini_api_key_here"
```

**Linux / macOS:**
```bash
export GEMINI_API_KEY="your_actual_gemini_api_key_here"
```

> **Note:** If `GEMINI_API_KEY` is not set, the assistant runs in offline mode without errors.

---

## 💻 How to Run

### 1. Command-Line Interface (Default)
```bash
python main.py
```

### 2. Interactive Web UI (Streamlit)
On Windows, use `python -m streamlit` (since standalone `streamlit` may not be in system PATH):
```bash
python -m streamlit run app_ui.py
```
*Or use the convenient launcher script:*
```bash
python run_ui.py
```
*(On Windows, you can also simply double-click `run_ui.bat`)*

### 3. Native Desktop GUI (Tkinter)
Zero browser, zero servers, zero port conflicts:
```bash
python gui.py
```

---

## 🖥️ Sample Usage & Output

### 1. Generating a Roadmap (CLI)
```text
Select your current proficiency level:
  1. Beginner     (Complete journey from foundations to mastery)
  2. Intermediate (Jump past basics to architecture & core patterns)
  3. Advanced     (Focus on high performance, concurrency & capstone)
Enter choice (1-3, default=1): 2

## 🗺️ Learning Roadmap: Machine Learning
Target Level: Intermediate  |  Source: Offline Knowledge Base
> Intermediate Level: Foundations skipped; focusing on core architecture, design patterns, and advanced concepts.

### Stage 3: Classification, Regression & Tree Models [Intermediate]
- ⏱️ Estimated Duration: 3 weeks
- 📚 Core Sub-topics:
  - K-Nearest Neighbors (KNN) and Support Vector Machines (SVM)
  - Decision Trees, Entropy, and Information Gain
  - Ensemble methods: Random Forests, Bagging, and Boosting (XGBoost, LightGBM)
  - Cross-validation, bias-variance tradeoff, and hyperparameter tuning (GridSearchCV)
- 🛠️ Practice Project / Hands-on Task: Train a Random Forest and XGBoost model to predict customer churn, achieving >85% F1-score.
```

### 2. Summarizing Notes (`sample_notes.txt`)
```text
Choose note input method:
  1. Paste text directly
  2. Load from a .txt file (e.g. sample_notes.txt)
Enter choice (1-2, default=2): 2

Select desired summary length:
  1. Short    (2-3 high-level key takeaways)
  2. Medium   (Balanced 4-5 key concepts & examples - default)
  3. Detailed (Comprehensive breakdown with all nuances)
Enter choice (1-3, default=2): 2

### 📋 File: sample_notes.txt (Medium Length)
*Compressed from 17 sentences down to 5 key points.*

Key Identified Terms: `learning`, `model`, `neural`, `loss`, `data`, `networks`

Key Takeaways:
- In contrast, **machine** **learning** takes input **data** along with expected outputs to discover underlying patterns, algorithms, and statistical relationships.
- Supervised **learning** is the most widely deployed category of **machine** **learning** in industry today.
- Bias refers to error introduced by approximating a real-world problem with an overly simplistic **model**, which frequently leads to underfitting where the **model** fails to capture key relationships.
- An artificial **neural** network consists of interconnected nodes called artificial neurons organized into an input layer, one or more hidden layers, and an output layer.
- Training a **neural** network involves iteratively optimizing its weights using the backpropagation algorithm combined with gradient descent.
```

### 3. Handling Unknown Topics with Fuzzy Matching
```text
Enter a topic: algos

❌ Topic 'algos' was not found in the offline knowledge base.

🔍 Did you mean one of these?
- Data Structures & Algorithms
```

---

## 🔬 How the Extractive Summarizer Works (Viva & Lab Explanation)

The note summarizer implements **Frequency-Based Extractive Summarization**:
1. **Sentence Tokenization:** The input text is parsed into individual sentences using regex delimiters while preserving punctuation and capitalization.
2. **Word Cleaning & Stopword Elimination:** Text is converted to lowercase and punctuation is stripped. Non-informative structural words (*the, is, and, which*) are filtered using a built-in stopword dictionary.
3. **Normalized Word Frequencies:** A frequency distribution counts occurrences of each content word. Each word count is normalized ($W_{norm} = \frac{\text{count}}{\text{max\_count}}$) so scores range between $0.0$ and $1.0$.
4. **Sentence Scoring with Length Normalization:** Each sentence is scored by summing the normalized weights of its constituent words, divided by a length factor ($\text{len}^{0.7}$) to prevent long run-on sentences from unfairly dominating.
5. **Top-N Extraction & Narrative Order:** Sentences are ranked by score; the top $N$ sentences (based on chosen length) are sorted back into their original chronological order so the summary reads coherently.
6. **Keyword Highlighting:** High-frequency technical terms are detected and bolded in Markdown.

---

## 🎓 Viva & Lab Exam Explanation (Ready to Read)

> *"Our Study Guide Virtual Assistant is a hybrid educational tool designed to structure technical learning paths and synthesize course materials. It operates in two modes: an offline-first mode powered by a structured JSON knowledge base, and an optional online AI mode that queries Google Gemini for unlisted topics. When an unknown topic is requested offline, the system employs difflib fuzzy matching to suggest the closest matches. For note summarization, rather than relying on black-box generative models, it utilizes an explainable extractive text summarization pipeline: the text is tokenized into sentences, stopwords are removed, and a normalized word frequency distribution is computed. Each sentence is scored based on the significance of its keywords with a length penalty, and the top-ranking sentences are restored in their original narrative sequence with key terms highlighted. If an API key is provided, the assistant can dynamically generate guides for any topic, and automatically falls back to offline operation if network or quota errors occur."*

---

## 🔮 Possible Future Improvements

1. **TF-IDF & TextRank Scoring:** Upgrade the extractive summarizer from raw word frequency to TF-IDF (Term Frequency - Inverse Document Frequency) or Graph-based TextRank (PageRank applied to sentence similarity matrices).
2. **Flashcard Generator:** Automatically convert summary bullet points and roadmap tasks into Anki-compatible `.csv` flashcards.
3. **Interactive Quiz Engine:** Generate multiple-choice self-assessment questions based on the selected topic and level.
4. **PDF / Word Document Ingestion:** Allow users to directly upload lecture slide PDFs or DOCX files in addition to `.txt` files.
5. **Progress Tracking Database:** Add a SQLite database to let students check off completed roadmap stages and log daily study hours.
