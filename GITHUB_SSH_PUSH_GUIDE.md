# رفع مشروع Python إلى GitHub عبر SSH — دليل تعليمي كامل

> المصادقة بمفتاح Ed25519 + الرفع إلى `git@github.com:althqafyjhad-collab/data_pipeline_SQLITE.git`

---

## فهرس المحتويات

1. [نظرة عامة: لماذا SSH بدل HTTPS؟](#1-نظرة-عامة)
2. [كيف تعمل مصادقة SSH؟ (الأساس العلمي)](#2-كيف-تعمل-مصادقة-ssh)
3. [المتطلبات](#3-المتطلبات)
4. [الخطوة 1 — توليد مفتاح SSH](#4-الخطوة-1-توليد-مفتاح-ssh)
5. [الخطوة 2 — تشغيل وكيل SSH (ssh-agent)](#5-الخطوة-2-وكيل-ssh)
6. [الخطوة 3 — إضافة المفتاح العام إلى GitHub](#6-الخطوة-3-إضافة-المفتاح-إلى-github)
7. [الخطوة 4 — التحقق من المصادقة](#7-الخطوة-4-التحقق-من-المصادقة)
8. [الخطوة 5 — تهيئة المستودع محليًا (git init)](#8-الخطوة-5-تهيئة-المستودع)
9. [الخطوة 6 — إنشاء .gitignore](#9-الخطوة-6-ملف-gitignore)
10. [الخطوة 7 — الالتزام الأول (commit)](#10-الخطوة-7-الالتزام-الأول)
11. [الخطوة 8 — ربط المستودع البعيد والرفع (push)](#11-الخطوة-8-الربط-والرفع)
12. [الخطوة 9 — التحقق بعد الرفع](#12-الخطوة-9-التحقق)
13. [جداول مرجعية سريعة](#13-جداول-مرجعية-سريعة)
14. [أخطاء شائعة وحلولها](#14-الأخطاء-الشائعة)

---

## 1. نظرة عامة

### لماذا نستخدم SSH؟

| المعيار | HTTPS | SSH |
|---------|-------|-----|
| المصادقة | اسم مستخدم + **Token** | **مفتاح** خاص/عام |
| الأمان | كلمة مرور كل مرة | لا تُرسل كلمة مرور أبدًا |
| الراحة | تحتاج إعادة إدخال | تُسرّع لمرة واحدة |
| التشفير | TLS | TLS (Diffie-Hellman) + توقيع |

`git@github.com:althqafyjhad-collab/data_pipeline_SQLITE.git` هو **عنوان SSH** (يسبقه `git@`)، بينما HTTPS يبدأ بـ `https://github.com/...`.

---

## 2. كيف تعمل مصادقة SSH؟

المبدأ جوهره **التشفير بمفتاح عام** (Public-Key Cryptography):

```
┌──────────────────────────┐        ┌──────────────────────────┐
│  جهازك (العميل)           │        │  GitHub (الخادم)          │
│                          │        │                          │
│  المفتاح الخاص (سري)     │───────▶│  المفتاح العام (متاح)    │
│  id_ed25519              │        │  أُضيف في إعدادات الحساب  │
└──────────────────────────┘        └──────────────────────────┘
```

**تسلسل المصافحة (Handshake):**

1. يرسل العميل **طلب اتصال** لـ `git@github.com` على منفذ 22.
2. GitHub يرسل **تحديًا (challenge)** نصًا عشوائيًا.
3. العميل **يوقّع** التحدي بالمفتاح الخاص → الصيغة: `(m, Signature=H(m)^d)`.
4. GitHub **يتحقق** بالتوقيع المرفق بالمفتاح العام (الذي أضفته لتوه).
5. إذا نجح → `Hi username! You've successfully authenticated`.

> لا يُتبادل المفتاح الخاص أبدًا؛ فقط يُستعمل للتحقق من ملكية المفتاح العام المقابل.

**مفاتيح المنزل موثقة (Host Verification):** عند أول اتصال، يُخزَّن `github.com` في `known_hosts` (إصبع SHA256) ليتأكد العميل أنه يتصل بـ GitHub الحقيقي — وهذا يمنع هجمات Man-in-the-Middle.

---

## 3. المتطلبات

| المكوّن | كيف تتحقق منه |
|---------|---------------|
| Git مثبت | `git --version` |
| OpenSSH مثبت | `ssh -V` (مدمج مع Windows 10+) |
| حساب GitHub + أعضاء في المشروع | صلاحية push في `althqafyjhad-collab/data_pipeline_SQLITE` |

---

## 4. الخطوة 1 — توليد مفتاح SSH

### لماذا Ed25519؟

- **أسرع وأصغر** من RSA.
- **أكثر أمانًا** ضد هجمات الحوسبة الكمية (Curve25519).
- خوارزمية حديثة تدعمها GitHub منذ 2021.

### التوليد

```powershell
ssh-keygen -t ed25519 -C "بريدك أو جهازك@اسم_الجهاز" -f "$env:USERPROFILE\.ssh\id_ed25519"
```

مثال مطابق لما نفذناه:

```powershell
ssh-keygen -t ed25519 -C "brho_omy@desktop-00vu5ce" -f "$env:USERPROFILE\.ssh\id_ed25519"
```

**ملاحظات:**
- `-t ed25519` → نوع الخوارزمية.
- `-C "comment"` → تعليق تعريفي (يظهر في نهاية المفتاح).
- `-f <path>` → مسار الحفظ (الافتراضي `~/.ssh/id_ed25519`).
- يُسأل عن **Passphrase** (كلمة مرور إضافية لتشفير المفتاح الخاص) — يمكن تركها فارغة بالضغط Enter.

### الناتج

```
C:\Users\اسمك\.ssh\
├── id_ed25519      ← المفتاح الخاص (سري — لا تشاركه أبدًا!)
└── id_ed25519.pub  ← المفتاح العام (تُضيفه إلى GitHub)
```

تحقق من الملفات:

```powershell
Get-ChildItem "$env:USERPROFILE\.ssh\"
```

> **تحذير أمني:** المفتاح الخاص `id_ed25519` هو هويتك الرقمية. لا ترفعه إلى GitHub ولا تشاركه بأي وسيلة.

---

## 5. الخطوة 2 — وكيل SSH

`ssh-agent` يخزن المفتاح الخاص في الذاكرة مؤقتًا لتفادي إدخال passphrase عند كل عملية push.

### تفعيل الخدمة (Windows)

```powershell
Get-Service ssh-agent                          # التحقق من حالتها
Set-Service -Name ssh-agent -StartupType Automatic
Start-Service -Name ssh-agent
```

### إضافة المفتاح للوكيل

```powershell
ssh-add "$env:USERPROFILE\.ssh\id_ed25519"
```

> الوكيل ليس إلزاميًا في كل الأنظمة، لكنه يريحك من إعادة المصادقة أثناء الجلسة.

---

## 6. الخطوة 3 — إضافة المفتاح إلى GitHub

### 6.1 اعرض المفتاح العام

```powershell
Get-Content "$env:USERPROFILE\.ssh\id_ed25519.pub"
```

ينتج مثلاً:

```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGXqqxDxbdiT80BBa66rHVav5hN+nBbd+bOnHYkgFiAN brho_omy@desktop-00vu5ce
```

### 6.2 الصقه في GitHub

1. افتح https://github.com/settings/ssh/new (أو: Settings ← SSH and GPG keys ← New SSH key).
2. **Title:** أي اسم (مثل `My-PC`).
3. **Key type:** اختر `Authentication Key` (وليس Signing Key).
4. **Key:** الصق المفتاح العام كاملًا.
5. اضغط **Add SSH key**، وأكّد بكلمة مرور حسابك.

> استخدام **Authentication Key** الصحيح يسمح بالقراءة/الكتابة على المستودعات؛ بينما **Signing Key** مخصص لتوقيع الـ commits فقط.

---

## 7. الخطوة 4 — التحقق من المصادقة

### الاختبار

```powershell
ssh -T git@github.com
```

**أول مرة فقط:** ستُسأل `Are you sure you want to continue connecting (yes/no)؟` — اكتب `yes` لإضافة github.com إلى `known_hosts`.

**الناتج على النجاح:**

```
Hi althqafyjhad-collab! You've successfully authenticated,
but GitHub does not provide shell access.
```

> عبارة "does not provide shell access" **طبيعية تمامًا** — GitHub لا يعطي صدفة تفاعلية؛ يسمح فقط بأوامر git.

### تحقق من المفاتيح المسجلة

```powershell
ssh-add -l              # قائمة المفاتيح في الوكيل
Get-Content "$env:USERPROFILE\.ssh\known_hosts"   # المضيفون الموثوقون
```

---

## 8. الخطوة 5 — تهيئة المستودع

انتقل إلى مجلد المشروع ثم:

```powershell
git init
```

- ينشئ مجلدًا خفيًا `.git/` يحوي تاريخ المشروع.
- الفروع الافتراضية قد تكون `master` — سنعيد التسمية لاحقًا إلى `main`.

افحص الحالة:

```powershell
git status --short
```

**قبل الالتزام، تأكد أنك في المسار الصحيح** وأن الملفات المطلوبة تظهر (`.env` والـ logs لا يجب أن تظهر إن كان `.gitignore` يعمل).

---

## 9. الخطوة 6 — ملف .gitignore

يمنع رفع الملفات الحساسة/المولدة. مثال جاهز:

```gitignore
# =====================
# Secrets & environment
# =====================
.env
*.env
.env.local

# =====================
# Python
# =====================
__pycache__/
*.py[cod]
*.egg-info/
.venv/
venv/

# =====================
# Generated / runtime data
# =====================
logs/
*.log
data/processed/

# =====================
# OS / editor
# =====================
.DS_Store
Thumbs.db
.idea/
.vscode/
```

> انتبه: `.env.example` **لا يُهمَل** (لا يبدأ بنقطة+env وحده؛ النمط `.env` لا يطابقه لأنه `*.env` فقط)، وهذا صحيح — قالب الإعدادات مسموح نشره، أما قيم حقيقية فممنوعة.

---

## 10. الخطوة 7 — الالتزام الأول

### إضافة الملفات إلى منطقة التجهيز (Staging)

```powershell
git add .
```

- `git add <file>` → إضافة ملف محدد.
- `git add .` → إضافة كل الملفات غير المستثناة في `.gitignore`.

### إنشاء الالتزام

```powershell
git commit -m "first commit"
```

> **نصيحة منهجية:** رسالة الالتزام تخاطب المراجع المستقبلي — صف "ماذا ولِماذا" بالإنجليزية أو العربية، بضمير الأمر، ضمن وصف واحد مختصر.

### إعادة تسمية الفرع إلى main

```powershell
git branch -M main
```

- `-M` تعني Move (إعادة تسمية) بقوة، حتى لو وُجد فرع آخر بالاسم.

---

## 11. الخطوة 8 — ربط المستودع البعيد والرفع

### إضافة الوجهة البعيدة

```powershell
git remote add origin git@github.com:althqafyjhad-collab/data_pipeline_SQLITE.git
```

تحقق:

```powershell
git remote -v
# origin  git@github.com:.../data_pipeline_SQLITE.git (fetch)
# origin  git@github.com:.../data_pipeline_SQLITE.git (push)
```

### الرفع الأول

```powershell
git push -u origin main
```

- `-u` (أو `--set-upstream`) يربط فرع `main` المحلي بـ `origin/main` بحيث تستخدم `git push` وحدها لاحقًا.
- الناتج الناجح:

```
branch 'main' set up to track 'origin/main'.
To github.com:althqafyjhad-collab/data_pipeline_SQLITE.git
 * [new branch]      main -> main
```

---

## 12. الخطوة 9 — التحقق

### من الجهاز

```powershell
git status                       # up to date with origin/main
git log --oneline                # عرض الالتزامات
git ls-remote --heads origin     # قائمة فروع الخادم البعيد
```

### من المتصفح

افتح `https://github.com/althqafyjhad-collab/data_pipeline_SQLITE` — ستجد:

- رمز `main` في الأعلى (بدل master).
- ملفات المشروع: `src/`, `requirements.txt`, `POSTGRESQL_CONNECTION_GUIDE.md`, `.gitignore` إلخ.
- التزام `first commit` بـ 8 ملفات.

---

## 13. جداول مرجعية سريعة

### أوامر SSH

| الأمر | الوظيفة |
|-------|---------|
| `ssh-keygen -t ed25519 -C "تعليق"` | توليد مفتاح |
| `ssh-add -l` | عرض المفاتيح المحمّلة |
| `ssh-add ~/.ssh/id_ed25519` | إضافة مفتاح للوكيل |
| `ssh -T git@github.com` | اختبار المصادقة |
| `ssh -vT git@github.com` | اختبار بشرح تفصيلي (Debug) |

### أوامر Git

| الأمر | الوظيفة |
|-------|---------|
| `git init` | إنشاء مستودع محلي |
| `git status` | حالة العمل |
| `git add .` | تجهيز الكل |
| `git commit -m "رسالة"` | التزام |
| `git branch -M main` | تسمية الفرع |
| `git remote add origin <url>` | إضافة البعيد |
| `git remote -v` | عرض البعيد |
| `git push -u origin main` | الرفع الأول مع الربط |
| `git push` | الرفع اللاحق |
| `git pull` | سحب التحديثات |

---

## 14. الأخطاء الشائعة

| الخطأ | السبب | الحل |
|-------|-------|------|
| `Permission denied (publickey)` | المفتاح العام غير مضاف للحساب | أضف `id_ed25519.pub` في إعدادات GitHub |
| `Host key verification failed` | github.com غير موثوق بعد | أول اتصال أجب `yes`، أو استخدم `StrictHostKeyChecking=accept-new` |
| `Identity file ... not accessible` | مسار مكسور في core.sshCommand | `git config --global --unset core.sshCommand` |
| `remote origin already exists` | مستودع بعيد مكرر | `git remote remove origin` ثم أعد الإضافة |
| `! [rejected] ... fetch first` | يوجد تاريخ مختلف على البعيد | `git pull --rebase origin main` ثم push |
| `failed to push some refs` | فرع بعيد محدث بلا تاريخ محلي | سحب ودمج ثم إعادة الرفع |

---

## الخلاصة

المسار الكامل الذي طبقناه:

```
توليد مفتاح  →  إضافة عامه لحساب GitHub  →  اختبار ssh -T
  →  git init  →  .gitignore  →  add + commit  →  branch -M main
  →  remote add origin  →  push -u origin main  →  التحقق
```

- **SSH يتفوق على HTTPS**: لا كلمة مرور، ولا Token، مصادقة مفتاحية آمنة وتشفير قوي.
- **المفتاح الخاص سري ومحلي**؛ **العام فقط** يُشارك مع GitHub.
- كل رفعة لاحقة بعد هذا الإعداد لا تتطلب سوى `git add` + `git commit` + `git push`.