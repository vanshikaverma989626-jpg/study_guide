import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys

from assistant import StudyGuideAssistant
import ai_client


class StudyGuideGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Study Guide Virtual Assistant - Desktop UI")
        self.root.geometry("880x680")
        self.root.minsize(720, 520)

        self.assistant = StudyGuideAssistant()

        self._build_header()
        self._build_notebook()
        self._build_output_area()

    def _build_header(self):
        header_frame = ttk.Frame(self.root, padding=10)
        header_frame.pack(fill=tk.X)

        title = ttk.Label(header_frame, text="🎓 Study Guide Virtual Assistant", font=("Helvetica", 13, "bold"))
        title.pack(side=tk.LEFT)

        status_text = "✨ Gemini LLM Active" if ai_client.is_ai_available() else "🔌 Offline Mode (Local KB)"
        self.status_lbl = ttk.Label(header_frame, text=status_text, foreground="green" if ai_client.is_ai_available() else "#0055aa")
        self.status_lbl.pack(side=tk.RIGHT)

        btn_key = ttk.Button(header_frame, text="🔑 Set API Key", command=self._on_set_api_key)
        btn_key.pack(side=tk.RIGHT, padx=8)

    def _on_set_api_key(self):
        win = tk.Toplevel(self.root)
        win.title("Configure Gemini API Key")
        win.geometry("460x160")
        win.transient(self.root)

        ttk.Label(win, text="Enter your Google Gemini API Key:", font=("Helvetica", 10, "bold")).pack(pady=8)
        entry = ttk.Entry(win, width=50, show="*")
        curr = ai_client.get_api_key() or ""
        entry.insert(0, curr)
        entry.pack(pady=5)

        def save():
            key = entry.get().strip()
            if key:
                ai_client.set_api_key(key, save_to_file=True)
                self.status_lbl.config(text="✨ Gemini LLM Active", foreground="green")
                messagebox.showinfo("Saved", "API Key configured successfully and saved!")
                win.destroy()
            else:
                messagebox.showwarning("Empty", "Please enter an API key.")

        ttk.Button(win, text="Save Key", command=save).pack(pady=10)

    def _build_notebook(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.X, padx=10, pady=5)

        # Tab 1: Roadmap
        tab1 = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab1, text="🗺️ Roadmap")
        ttk.Label(tab1, text="Topic:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.entry_roadmap_topic = ttk.Entry(tab1, width=28)
        self.entry_roadmap_topic.insert(0, "Machine Learning")
        self.entry_roadmap_topic.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(tab1, text="Level:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.combo_level = ttk.Combobox(tab1, values=["Beginner", "Intermediate", "Advanced"], state="readonly", width=14)
        self.combo_level.set("Beginner")
        self.combo_level.grid(row=0, column=3, padx=5, pady=5)

        btn_rm = ttk.Button(tab1, text="Generate Roadmap", command=self._on_generate_roadmap)
        btn_rm.grid(row=0, column=4, padx=10, pady=5)

        # Tab 2: Resources
        tab2 = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab2, text="📚 Resources")
        ttk.Label(tab2, text="Topic:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.entry_res_topic = ttk.Entry(tab2, width=32)
        self.entry_res_topic.insert(0, "Data Structures & Algorithms")
        self.entry_res_topic.grid(row=0, column=1, padx=5, pady=5)

        btn_res = ttk.Button(tab2, text="Get Resources", command=self._on_get_resources)
        btn_res.grid(row=0, column=2, padx=10, pady=5)

        # Tab 3: Topic Summary
        tab3 = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab3, text="📝 Topic Summary")
        ttk.Label(tab3, text="Topic:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.entry_sum_topic = ttk.Entry(tab3, width=28)
        self.entry_sum_topic.insert(0, "Operating Systems")
        self.entry_sum_topic.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(tab3, text="Length:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.combo_sum_len = ttk.Combobox(tab3, values=["Short", "Medium", "Detailed"], state="readonly", width=12)
        self.combo_sum_len.set("Medium")
        self.combo_sum_len.grid(row=0, column=3, padx=5, pady=5)

        btn_sum = ttk.Button(tab3, text="Summarize Topic", command=self._on_summarize_topic)
        btn_sum.grid(row=0, column=4, padx=10, pady=5)

        # Tab 4: Note Summarizer
        tab4 = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab4, text="📋 Summarize Notes")
        ttk.Label(tab4, text="Length:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.combo_notes_len = ttk.Combobox(tab4, values=["Short", "Medium", "Detailed"], state="readonly", width=12)
        self.combo_notes_len.set("Medium")
        self.combo_notes_len.grid(row=0, column=1, padx=5, pady=5)

        btn_load = ttk.Button(tab4, text="Load .txt File...", command=self._on_load_notes_file)
        btn_load.grid(row=0, column=2, padx=5, pady=5)

        btn_sum_notes = ttk.Button(tab4, text="Extractive Summary", command=lambda: self._on_summarize_notes_text(use_ai=False))
        btn_sum_notes.grid(row=0, column=3, padx=5, pady=5)

        btn_ai_notes = ttk.Button(tab4, text="🤖 AI Generative Summary", command=lambda: self._on_summarize_notes_text(use_ai=True))
        btn_ai_notes.grid(row=0, column=4, padx=5, pady=5)

        # Tab 5: Full Guide
        tab5 = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab5, text="🎓 Full Study Guide")
        ttk.Label(tab5, text="Topic:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.entry_full_topic = ttk.Entry(tab5, width=25)
        self.entry_full_topic.insert(0, "Python")
        self.entry_full_topic.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(tab5, text="Level:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.combo_full_lvl = ttk.Combobox(tab5, values=["Beginner", "Intermediate", "Advanced"], state="readonly", width=12)
        self.combo_full_lvl.set("Beginner")
        self.combo_full_lvl.grid(row=0, column=3, padx=5, pady=5)

        btn_full = ttk.Button(tab5, text="Generate Full Guide", command=self._on_generate_full_guide)
        btn_full.grid(row=0, column=4, padx=10, pady=5)

        # Tab 6: Ask AI Tutor
        tab6 = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab6, text="🤖 Ask AI Tutor")
        ttk.Label(tab6, text="Doubt / Question:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.entry_tutor = ttk.Entry(tab6, width=38)
        self.entry_tutor.insert(0, "Explain Paging in OS with an analogy")
        self.entry_tutor.grid(row=0, column=1, padx=5, pady=5)

        btn_tutor = ttk.Button(tab6, text="Ask Gemini LLM", command=self._on_ask_tutor)
        btn_tutor.grid(row=0, column=2, padx=10, pady=5)

    def _build_output_area(self):
        output_frame = ttk.LabelFrame(self.root, text="Results & Markdown Preview", padding=10)
        output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        scroll = ttk.Scrollbar(output_frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.text_area = tk.Text(output_frame, wrap=tk.WORD, yscrollcommand=scroll.set, font=("Consolas", 10))
        self.text_area.pack(fill=tk.BOTH, expand=True)
        scroll.config(command=self.text_area.yview)

        btn_frame = ttk.Frame(self.root, padding=8)
        btn_frame.pack(fill=tk.X)

        btn_save = ttk.Button(btn_frame, text="💾 Save Output to File...", command=self._on_save_file)
        btn_save.pack(side=tk.RIGHT, padx=10)

        btn_clear = ttk.Button(btn_frame, text="Clear", command=lambda: self.text_area.delete("1.0", tk.END))
        btn_clear.pack(side=tk.RIGHT)

    def _display_content(self, text: str):
        self.text_area.delete("1.0", tk.END)
        self.text_area.insert(tk.END, text)

    def _on_generate_roadmap(self):
        topic = self.entry_roadmap_topic.get().strip()
        level = self.combo_level.get().lower()
        if not topic:
            messagebox.showwarning("Input Required", "Please enter a topic.")
            return
        res = self.assistant.get_roadmap(topic, level=level)
        self._display_content(self.assistant.format_roadmap_markdown(res))

    def _on_get_resources(self):
        topic = self.entry_res_topic.get().strip()
        if not topic:
            messagebox.showwarning("Input Required", "Please enter a topic.")
            return
        res = self.assistant.get_resources(topic)
        self._display_content(self.assistant.format_resources_markdown(res))

    def _on_summarize_topic(self):
        topic = self.entry_sum_topic.get().strip()
        length = self.combo_sum_len.get().lower()
        if not topic:
            messagebox.showwarning("Input Required", "Please enter a topic.")
            return
        res = self.assistant.summarize_topic(topic, length=length)
        self._display_content(self.assistant.format_topic_summary_markdown(res))

    def _on_load_notes_file(self):
        path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                self._display_content(content)
                messagebox.showinfo("Loaded", f"Loaded {os.path.basename(path)} into the viewer.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to read file: {e}")

    def _on_summarize_notes_text(self, use_ai: bool = False):
        raw_text = self.text_area.get("1.0", tk.END).strip()
        if not raw_text:
            messagebox.showwarning("Input Required", "Paste notes into the text area or load a .txt file first.")
            return
        length = self.combo_notes_len.get().lower()
        res = self.assistant.summarize_user_notes(raw_text, length=length, source_name="Notes", use_ai=use_ai)
        if res.get("success"):
            self._display_content(res["markdown"])
        else:
            messagebox.showerror("Error", res.get("error", "Failed to summarize notes."))

    def _on_ask_tutor(self):
        doubt = self.entry_tutor.get().strip()
        if not doubt:
            messagebox.showwarning("Input Required", "Please enter a doubt/question.")
            return
        res = self.assistant.ask_ai_tutor(doubt)
        if res.get("success"):
            self._display_content(res["answer"])
        else:
            messagebox.showerror("AI Error", res.get("error", "Failed to get AI response."))

    def _on_generate_full_guide(self):
        topic = self.entry_full_topic.get().strip()
        level = self.combo_full_lvl.get().lower()
        if not topic:
            messagebox.showwarning("Input Required", "Please enter a topic.")
            return
        res = self.assistant.get_full_study_guide(topic, level=level, length="medium")
        self._display_content(res["markdown"])

    def _on_save_file(self):
        content = self.text_area.get("1.0", tk.END).strip()
        if not content:
            messagebox.showwarning("Empty", "No content to save.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".md",
            filetypes=[("Markdown Files", "*.md"), ("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                messagebox.showinfo("Saved", f"File saved successfully to:\n{path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {e}")


def main():
    root = tk.Tk()
    app = StudyGuideGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
