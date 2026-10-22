# SummarAI — Abstractive Text Summarization System

SummarAI is a beginner-friendly Information Retrieval mini project. It accepts an article or passage and uses the pretrained `sshleifer/distilbart-cnn-12-6` Transformer model to generate a new, concise summary.

## Features

- Real abstractive summarization with Hugging Face Transformers and PyTorch
- Short, medium, and long generation targets (approximate word ranges)
- Responsive Bootstrap 5 interface with live counts
- Copy, download, sample text, loading, validation, and error states
- JSON API, health endpoint, and deterministic route tests
- No database, API key, Node.js, or paid service required

## How it works

The input is normalized without removing context, tokenized, and passed to DistilBART's encoder-decoder Transformer. The encoder builds a contextual representation; the decoder generates a new summary based on that representation. This differs from extractive summarization, which selects sentences already present in the source.

`Input Text → Tokenization → Transformer Model → Summary Generation → Output Summary`

The project relates to Information Retrieval by transforming retrieved or user-provided information into a shorter representation that is easier to read while preserving the important ideas.

## Folder structure

```text
app.py                 Flask routes and API validation
summarizer.py          Model lifecycle and inference service
templates/index.html   User interface
static/css/style.css   Responsive styling
static/js/script.js    Browser interactions
tests/test_app.py      Route tests with mocked inference
```

## Windows installation

Open PowerShell in this folder:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

Open <http://127.0.0.1:5000/> in a browser. The first normal startup downloads the model and tokenizer from Hugging Face; this requires internet access and several hundred MB of disk space. Later runs use the local Hugging Face cache. CPU inference can take from a few seconds to over a minute depending on the input and laptop.

If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope Process Bypass` for the current terminal, then activate again.

## Tests

```powershell
.\.venv\Scripts\Activate.ps1
python -m pytest
```

Tests set `SUMMARIZER_LOAD_ON_STARTUP=0` and mock inference, so they do not download model weights.

## API

### `GET /api/health`

Returns model readiness:

```json
{"success": true, "status": "ready", "model": "sshleifer/distilbart-cnn-12-6", "model_error": null}
```

### `POST /api/summarize`

Request:

```json
{"text": "A long article with at least twenty words ...", "summary_length": "medium"}
```

`summary_length` is `short`, `medium`, or `long`. The input limit is 80,000 characters and 1,024 model tokens (longer tokenized input is truncated with a response metadata flag). Very short input is rejected because it cannot be summarized meaningfully.

Successful responses include `summary` and `statistics` containing original and summary word/character counts, compression ratio, processing time, and whether token truncation occurred. Errors use `{ "success": false, "error": "..." }` with an appropriate HTTP status.

## Limitations and future work

The model may produce inaccurate or biased wording and approximate length targets are not exact guarantees. CPU generation is slower than GPU inference, and the model is limited to its supported input context. Future enhancements could add multilingual models, configurable model selection, evaluation metrics such as ROUGE, and secure user accounts.
