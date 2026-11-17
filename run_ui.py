import sys
import subprocess
import os

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(script_dir, "app_ui.py")
    
    print(f"🚀 Launching Streamlit Study Guide Assistant from: {app_path}")
    print(f"👉 Using Python interpreter: {sys.executable}")
    
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", app_path])
    except KeyboardInterrupt:
        print("\n👋 Streamlit server stopped.")
