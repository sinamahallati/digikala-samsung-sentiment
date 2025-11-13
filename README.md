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

High-level pipeline:

1. **Crawl** Digikala mobile category, filter **Samsung** products, and collect all associated comments.
2. **Preprocess** Persian comments (normalization with Shekar, cleaning, filtering).
3. **Embed** comments using ParsBERT.
4. **Train** an SVM classifier on embeddings.
5. **Analyze** model performance and sentiment distribution.

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
│   └── digikala_sentiment.ipynb
└── src/
    └── digikala_crawl.py

---


## 4. Quick Start

After cloning the repository :

```bash
# 1. crawl Digikala Samsung reviews
python src/digikala_crawl.py   --list-pages 5   --max-products 100   --per-product-pages 5   --per-product-max-comments 500   --delay 0.6   --debug

# 2. run the notebook for training & analysis
jupyter notebook notebooks/digikala_sentiment.ipynb
```

You can adjust crawl parameters depending on how much data you want and how polite you want to be with the server.

---

## 5. Crawling Digikala Samsung reviews

The script `src/digikala_crawl.py` calls Digikala's public APIs to:

- Enumerate all **mobile phone** products.
- Filter products whose brand is **Samsung**.
- Fetch product details and user comments.
- Save:
  - `Digikala_products.csv` – Samsung product info.
  - `Digikala_comments.csv` – user reviews for those products.

