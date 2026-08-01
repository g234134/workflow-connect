import subprocess, sys
venv_pip = r"D:\大唐三省六部\07_Knowledge\commercial\.venv\Scripts\pip.exe"
result = subprocess.run([venv_pip, "install", "fastapi", "uvicorn", "python-multipart"], capture_output=True, text=True)
print(result.stdout[-500:] if result.stdout else "(no stdout)")
print(result.stderr[-500:] if result.stderr else "(no stderr)")
print(f"RC: {result.returncode}")
