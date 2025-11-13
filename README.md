# Digikala Samsung Review Sentiment (ParsBERT + SVM)

This repository contains a complete pipeline for crawling, preprocessing, and modeling sentiment on Persian reviews of **Samsung mobile phones** from **Digikala**, using **Shekar** for text normalization, **ParsBERT** for embeddings, and a **Support Vector Machine (SVM)** classifier.

---

## 1. Project Overview

Goal:

- Collect user reviews of Samsung phones from Digikala.
- Clean and normalize the Persian text.
- Use a transformer-based Persian language model (ParsBERT) to:
  - Generate weak/initial labels for comments.
  - Create dense sentence embeddings for each comment.
- Train a classical SVM classifier on these embeddings to predict **positive** / **negative** sentiment.
- Evaluate the model and provide analysis of the results.

---

## 2. Repository Structure

```text
.
├── README.md
├── requirements.txt
├── .gitignore
├── data/
│   ├── Digikala_products.csv
│   ├── Digikala_comments.csv
│   ├── digikala_comments_labeled.csv
│   └── parsbert_emb.npy
├── models/
│   └── svm_parsbert_pipeline.pkl
├── notebooks/
│   └── task.ipynb
└── src/
    └── digikala_crawl.py
