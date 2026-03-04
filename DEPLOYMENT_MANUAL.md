# Deployment Manual

## 1. Подготовка окружения

Требуется Python 3.11+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Подготовка входных данных

Поместите сохраненные документы в папку `data/raw/`.
Поддерживаемые форматы:

- `.txt`
- `.html`
- `.htm`

## 3. Запуск

```bash
python src/process_documents.py
```

При необходимости можно передать собственные каталоги:

```bash
python src/process_documents.py \
  --input-dir data/raw \
  --tokens-dir data/results/tokens \
  --lemmas-dir data/results/lemmas
```

## 4. Результаты

Для каждого файла из `data/raw/` будут созданы:

- `data/results/tokens/<имя_документа>_tokens.txt`
- `data/results/lemmas/<имя_документа>_lemmas.txt`

Проверяющий может:

- запустить код по шагам выше;
- или сразу посмотреть готовые результаты в `data/results/`.
