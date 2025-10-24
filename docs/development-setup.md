# Development Environment Setup

## 1. Python Environment (via Miniforge)

```
brew install miniforge
conda init zsh && exec $SHELL
conda create -n chatbot python=3.12 -y
conda activate chatbot
python -m pip install --upgrade pip
```

---

## 2. Pre-commit Setup

```
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

---


These instructions ensure a consistent local environment for development and code quality checks.
