# Document Search Engine (TF‑IDF + Cosine + Boolean) with a graphical interface (GUI) [Full Guide]

This project implements a small **document search engine** in Python. It supports:

- **Vector model (TF‑IDF)** with **cosine similarity** ranking
- **Boolean model** with operators **ET / OU / SAUF** (AND / OR / NOT)
- **Tokenization** delete the stop-list, replace the plural word and conjugated verbs with their root
- A **Tkinter GUI** that shows results with document and a dynamic **score**
- **Orthographic correction** (difflib) for query terms (given query/input)
- **Synonym expansion** (for the vector model)
- **evaluation curve** (recall/Accuracy) to analyze the performance of our system
- **Query history** (historique.txt) and **similar query suggestions**
- **Contextual re-ranking** (“Affiner”) based on a selected relevant document
- A small AI algorithm that can display the image related to the given query.

---

## How it works

### 1) Data preprocessing
Documents are created from text files located in `files/*.txt` and compiled into a single corpus file: `data.txt`.

- Preprocessing script: `Prep&Creer.py` (it generates `data.txt`)
- Each file becomes a dictionary of `{term: occurrences}`.

### 2) Models
Implemented in `MoteurRecherche.py`:

- **TF (Term Frequency)** per document
- **IDF (Inverse Document Frequency)** across the corpus
- **TF‑IDF** weights
- **Cosine similarity** between query TF‑IDF vector and each document vector

Boolean search provides matching document sets using:
- `ET` (intersection)
- `OU` (union)
- `SAUF` (difference)

### 3) Query understanding + GUI
Implemented  in `interface_graphique.py`:

- Detect search mode: `auto` (if the vect or bool model not selected) / forced `vect` / forced `bool`
- Correct query tokens using difflib against the TF‑IDF vocabulary
- Expand synonyms for the `vect` model
- Apply a user-controlled **horizontal scroll bar** on similarity score
- Show thumbnails from the `files/` folder when Pillow is installed

---

## Repository structure

- `interface_graphique.py` — Tkinter application (main UI)
- `MoteurRecherche.py` — TF‑IDF, cosine similarity, boolean model
- `preTreatmentQuary.py` — query preprocessing (stopwords, normalization, stemming/lemmatization)
- `recherche_multimodale.py` — multimodal/interactive console visualization helpers
- `Prep&Creer.py` — builds `data.txt` from `files/*.txt`
- `data.txt` — generated document index used by the search engine
- `historique.txt` — stored query history for suggestions
- `files/` — document texts (`*.txt`) and media (`*.jpg/.png`) thumbnails

---

## Requirements
### You should install : 
- `tkinter` (usually included with Python on Windows)
```bash
  sudo apt update && sudo apt install -y python3-tk
```
 - `Pillow` (for graphical interface)
 ```bash
  python3 -m pip install Pillow
```
- `nltk` (used in preprocessing `Prep&Creer.py`; if you run it again)
```bash
  pip install nltk
```
- `matplotlib` / `numpy` (for evaluation graph)
```bash
  python -m pip install -U matplotlib
```
```bash
  py -m pip install numpy
```
---

## Usage

### Run the GUI
On Windows:

```bash
python interface_graphique.py
```

### Generate/update `data.txt` (optional)
```bash
python Prep&Creer.py
```

This will read `files/*.txt` and rebuild the corpus index in `data.txt`.

---

## Notes
- ### IMPORTANT⚠️:
the document search engine designed solely for the French language❗
- Document images are searched in `files/` using base names (eg: `AI.jpg`, `cuisine.png`, etc.).
- The evaluation tab is meant for demonstration with the built-in `TESTS_EVALUATION` set.
