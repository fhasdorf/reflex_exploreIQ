### GITHUB
git init (Initialisiert das lokale Git-Repository)
git add . (Fügt alle Dateien zur Staging-Area hinzu)
git commit -m "Erster Commit" (Committet die Dateien lokal)
git branch -M main (Benennt den Branch in 'main' um)
git remote add origin <IHRE_GITHUB_REPO_URL> (Verbindet den lokalen Ordner mit GitHub)

### TERMINAL
Virtuelle Umgebung erstellen
python -m venv .venv
..\\.venv\\Scripts\\Activate.ps1
reflex run


#Virtuelle Python-Umgebung in Ordnerstruktur
python -m venv .venv

# Aktivieren (Windows)
.venv\Scripts\activate

# requirements.txt erstellen pipregs
pipreqs . --force

# Pakete mit pip installieren
pip install -r requirements.txt

# Interpreter dauerhaft in VS Code
Strg+Shift+P und Python Interpreter auswählen

#Cache leeren
Remove-Item -Recurse -Force .web
reflex init
reflex run

