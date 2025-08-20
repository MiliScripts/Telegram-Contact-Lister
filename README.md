# 📇 Telegram Contact Exporter (Kurigram)

A tiny, dependency-light Python utility that

- logs into **your own** Telegram account (via [Kurigram](https://github.com/KurimuzonAkuma/Kurigram), a Pyrogram fork),
- exports your **contact list** to  
  ▸ `contacts.csv` (spreadsheet-friendly)  
  ▸ `contacts.vcf` (import directly into any phone),
- asks every time *“Still this account?”* so you can switch numbers on demand,
- stores nothing except a local YAML config and the two export files.


---

## ⚡ Quick start

```bash
# 1. Clone
git clone https://github.com/MiliScripts/Telegram-Contact-Lister.git
cd Telegram-Contact-Lister

# 2. Install deps
pip install -r requirements.txt

# 3. Run
python contacts.py
