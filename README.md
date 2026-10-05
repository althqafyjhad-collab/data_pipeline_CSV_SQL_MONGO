# Student Data Pipeline — Project Documentation

> التوثيق الكامل للمشروع: البنية، خطوط المعالجة، طريقة التشغيل، وإدارة الاتصال بقاعدة البيانات.

---

## 1. نظرة عامة على المشروع

المشروع يحوّل بيانات الطلاب إلى **مجموعات بيانات جاهزة لتعلّم الآلة (ML-Ready)**.
المصادر مختلفة تمامًا، ولذلك فُصل كل مصدر في **خط معالجة مستقل**:

| الخط | المصدر | عدد الصفوف | ملف الإخراج |
|------|--------|-----------|-------------|
| **CSV** | ملف `data/raw/students_raw.csv` | 100 | `data/processed/students_ml_ready.csv` |
| **SQL** | PostgreSQL `advanced_sql_training_db` | 100 | `data/processed/students_sql_ml_ready.csv` |
| **MongoDB** | MongoDB `student_db.students` | 100 | `data/processed/students_mongo_ml_ready.csv` |

**لماذا الفصل؟**
- المصادر لها **بنى مختلفة**؛ فرض نسخة واحدة عليها ينتج كودًا هشًّا.
- كل خط يعمل ويفشل بشكل مستقل دون التأثير على الآخر.
- فصل القراءة عن المعالجة عن الإخراج يجعل كل وحدة **قابلة للاختبار وحدها**.

---

## 2. بنية المشروع

```
student_data_pipeline/
├── run_all.py                     ← تشغيل كل الخطوط بأمر واحد
├── requirements.txt
├── .env.example                   ← نموذج متغيرات البيئة
├── data/
│   ├── raw/
│   │   └── students_raw.csv       ← مصدر خط CSV
│   └── processed/                 ← المخرجات (git-ignored)
├── logs/                          ← سجل مستقل لكل خط
└── src/
    ├── common/                    ← وحدات مشتركة بين كل الخطوط
    │   ├── paths.py               ← كل المسارات في مكان واحد
    │   ├── logging_setup.py       ← إعداد السجل
    │   ├── schemas.py             ← قواعد التحقق لكل مصدر
    │   ├── display.py             ← عرض البيانات في الكونسول
    │   └── sample_data.py         ← مولّد بيانات عشوائية (~100 طالب)
    └── pipelines/
        ├── csv/
        │   ├── extractor.py       ← [قراءة] من CSV فقط
        │   ├── processor.py       ← [معالجة] تنظيف وتحويل وتحقق
        │   ├── writer.py          ← [إخراج] حفظ في CSV فقط
        │   ├── seed.py            ← تعبئة ملف CSV ببيانات عشوائية
        │   └── pipeline.py        ← تنسيق المراحل الثلاث
        ├── sql/
        │   ├── config.py          ← إعدادات الاتصال
        │   ├── extractor.py       ← [قراءة] من PostgreSQL فقط
        │   ├── processor.py       ← [معالجة]
        │   ├── writer.py          ← [إخراج]
        │   ├── seed.py            ← تعبئة القاعدة ببيانات عشوائية
        │   └── pipeline.py        ← تنسيق المراحل الثلاث
        └── mongo/
            ├── config.py          ← إعدادات اتصال MongoDB
            ├── extractor.py       ← [قراءة] من MongoDB فقط (pymongo)
            ├── processor.py       ← [معالجة]
            ├── writer.py          ← [إخراج]
            ├── seed.py            ← تعبئة المجموعة ببيانات عشوائية
            └── pipeline.py        ← تنسيق المراحل الثلاث
```

---

## 3. مبدأ التصميم: فصل القراءة عن الإخراج

كل خط موزّع على ثلاث وحدات مستقلة، ولكل وحدة **مسؤولية واحدة**:

| الوحدة | المسؤولية | ما لا تفعله |
|--------|-----------|-------------|
| `extractor.py` | **القراءة فقط** من المصدر | لا ينظّف ولا يكتب |
| `processor.py` | **المعالجة فقط** (تحويل، تنظيف، تحقق) | لا يقرأ من المصدر ولا يكتب |
| `writer.py` | **الإخراج فقط** إلى الملف | لا يقرأ ولا ينظّف |

### كيف يعمل هذا عمليًا؟

الكود في `extractor.py` لا يعرف شيئًا عن CSV، فقط:
```python
df = pd.read_csv(file_path)   # قراءة
return df                      # لا معالجة، لا كتابة
```

والكود في `writer.py` لا يعرف شيئًا عن قاعدة البيانات:
```python
df.to_csv(output_path, index=False)   # كتابة فقط
```

هذه الوحدات يمكن اختبارها واستبدالها منفردة دون لمس بقية الخط.

---

## 4. بيانات كل خط (Schemas)

### 4.1 خط CSV — `data/raw/students_raw.csv`

المدخل: `student_id, name, age, gpa, attendance, city` (6 أعمدة)

المعالجة:
1. حذف الصفوف المكرّرة و`student_id` المكرّر
2. تنظيف المسافات وتوحيد حالة الأحرف في `name` و`city`
3. **إبطال القيم خارج النطاق** → `gpa` (0–4)، `age` (16–80)، `attendance` (0–100)
4. **ملء الفراغات بالوسيط (median)**
5. تحقق نهائي من عدم وجود NULL أو تكرار

المخرج: نفس الأعمدة الستة بعد التنظيف.

### 4.2 خط SQL — قاعدة `advanced_sql_training_db`

المدخل: جدول `students` مدمجًا مع استعلام ملخص لكل طالب.

**استعلام الملخص** يجمع ميزات ML لكل طالب:
```sql
COUNT(DISTINCT e.course_id)                              AS total_courses,
COUNT(DISTINCT CASE WHEN e.enrollment_status = 'Completed'
    THEN e.course_id END)                                AS completed_courses,
ROUND(AVG(a.score) FILTER (WHERE a.score IS NOT NULL), 2) AS average_score
```
> `FILTER (WHERE ...)` يتجاهل درجات `Final` الفارغة (NULL) عمدًا بدل إفساد المتوسط.

المعالجة:
1. حذف التكرارات
2. تحويل `student_id`, `enrollment_year`, `total_courses`, `completed_courses`, `average_score` إلى أرقام
3. تحويل `birth_date` إلى تاريخ
4. توحيد `gender` من `M`/`F` إلى `Male`/`Female`
5. معالجة المدينة `Sana'a` بعناية (تفادي تحويلها إلى `Sana'A`)

**المخرج النهائي** (10 أعمدة):
```
student_id, full_name, gender, birth_date, city,
enrollment_year, status, total_courses, completed_courses, average_score
```

---

## 5. التشغيل

### 5.1 المتطلبات

```powershell
python -m pip install -r requirements.txt
```

المتطلبات في `requirements.txt`:
```
pandas>=2.2
psycopg2-binary>=2.9
SQLAlchemy>=2.0
python-dotenv>=1.0
```

### 5.2 إعداد الاتصال بقاعدة البيانات

انسخ ملف النموذج ثم عدّله:
```powershell
Copy-Item .env.example .env
```

محتوى `.env`:
```ini
PGHOST=localhost
PGPORT=5432
PGDATABASE=advanced_sql_training_db
PGUSER=postgres
PGPASSWORD=postgres

MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_DATABASE=student_db
MONGO_COLLECTION=students
# اتركهما فارغين إذا كان الخادم بلا مصادقة
MONGO_USER=
MONGO_PASSWORD=
```

> ⚠️ ملف `.env` **لا يُرفع** إلى Git (مُستثنى في `.gitignore`).
> لا يوجد `.env`؟ القيم الافتراضية داخل `config.py` لكل خط تعمل مباشرة.

### 5.3 تشغيل خط واحد

```powershell
# خط CSV (لا يحتاج قاعدة بيانات)
python src/pipelines/csv/pipeline.py

# خط SQL (يحتاج قاعدة بيانات تعمل)
python src/pipelines/sql/pipeline.py

# خط MongoDB (يحتاج MongoDB يعمل)
python src/pipelines/mongo/pipeline.py
```

### 5.4 تشغيل كل الخطوط معًا

```powershell
python run_all.py
```

### 5.5 عرض البيانات في الكونسول

عرض البيانات في الكونسول هو **الوضع الافتراضي**، فلا حاجة إلى أي معيار إضافي:

```powershell
# خط واحد فقط
python src/pipelines/csv/pipeline.py
python src/pipelines/sql/pipeline.py
python src/pipelines/mongo/pipeline.py

# كل الخطوط معًا
python run_all.py
```

لإخفاء البيانات وعرض النتيجة فقط، أضف `--quiet`:

```powershell
python run_all.py --quiet
python src/pipelines/csv/pipeline.py --quiet
```

> السجلات التفصيلية لا تظهر في الكونسول إطلاقًا؛ تُكتب في ملفات `logs/*.log`.
> لذلك لا يختلط الإخراج بالبيانات.

**مثال من مخرجات خط CSV:**

```
============================================================
CSV PIPELINE
============================================================
input : ...\data\raw\students_raw.csv
output: ...\data\processed\students_ml_ready.csv

--- INPUT (raw file) ---
rows: 103 | columns: 6
   student_id           name  age  gpa  attendance    city
0        1001      Ahmed Ali   22  3.5        92.0   Sanaa
1        1002  Sara Mohammed   21  3.8        96.0   Sanaa
2        1003  Khaled Hassan   23  NaN        88.0  Dhamar
3        1004     Mona Saleh   20  4.2        94.0     Ibb
4        1005     Ali Ahmed   -5  2.9        75.0    Taiz

--- AFTER TYPE CONVERSION ---
rows: 103 | columns: 6
   (same data, now all numeric columns cast)

--- AFTER CLEANING ---
rows: 100 | columns: 6
   student_id           name   age   gpa  attendance    city
0        1001      Ahmed Ali  22.0  3.50        92.0   Sanaa
1        1002  Sara Mohammed  21.0  3.80        96.0   Sanaa
2        1003  Khaled Hassan  23.0  2.91        88.0  Dhamar
3        1004     Mona Saleh  20.0  2.91        94.0     Ibb
4        1005     Ali Ahmed  22.0  2.90        75.0    Taiz

============================================================
CSV PIPELINE RESULT
============================================================
rows written: 100
saved to    : ...\data\processed\students_ml_ready.csv
```

**ما يُعرض في الكونسول:** كل خطوة على حدة:
- `INPUT` — البيانات الخام كما قُرئت من المصدر
- `AFTER TYPE CONVERSION` — بعد تحويل الأنواع
- `AFTER CLEANING` — بعد إزالة التكرارات وتصحيح القيم
- `AFTER DROPPING INTERNAL FIELDS` (MongoDB فقط) — بعد إسقاط `_id`, `__v`, التواريخ
- `RESULT` — ملخص نهائي (عدد الصفوف + المسار)

**للتحكم في عدد الصفوف المعروضة:** عدّل `PREVIEW_ROWS` في `src/common/display.py`.

### 5.6 تعبئة البيانات (~100 طالب)

كل مصدر فيه سكربت تعبئة مستقل يضيف بيانات عشوائية حقيقية إلى المصدر
(المولّد في `src/common/sample_data.py` ببذرة ثابتة، فتُنتج نفس البيانات في كل تشغيل):

```powershell
# CSV: ينتج 103 صفوف (~100 + 3 تكرارات لاختبار التنظيف)
python src/pipelines/csv/seed.py

# PostgreSQL: يضيف طلابًا وتسجيلات وتقييمات
python src/pipelines/sql/seed.py

# MongoDB: يضيف مستندات إلى student_db.students
python src/pipelines/mongo/seed.py
```

السكربتات **لا تفرض عددًا صارمًا**: تضيف فقط ما ينقص للوصول إلى ~100 طالب،
فهي آمنة لإعادة التشغيل. الترقيم يبدأ من `max(student_id) + 1` في كل مصدر،
والتسجيلات والتقييمات تُولّد بأرقام طلاب موجودة فعلًا لتفادي أي orphan.

| المصدر | بعد التعبئة | ملاحظات |
|--------|-------------|---------|
| CSV | 100 صف نظيف | 103 خام − 3 تكرارات |
| PostgreSQL | 100 طالب، 8 مواد، 388 تسجيل، 1164 تقييم | 17 درجة NULL مقصودة لاختبار التحقق |
| MongoDB | 100 مستند | 6 حقول بعد التنظيف |

### 5.7 سجلات التنفيذ

كل خط يكتب في سجله الخاص، فلا تختلط السجلات:

| الخط | السجل |
|------|-------|
| CSV | `logs/pipeline_csv.log` |
| SQL | `logs/pipeline_sql.log` |
| MongoDB | `logs/pipeline_mongo.log` |

كل سجل يوثّق المراحل: `[read]` → `[schema]` → `[clean]` → `[validate]` → `[write]`.

---

## 6. استكشاف قواعد البيانات مباشرة

### PostgreSQL

```powershell
psql -U postgres -h 127.0.0.1 -p 5432 -d advanced_sql_training_db
```

مثال — أعلى 5 طلاب بالمتوسط:
```sql
SELECT student_id, full_name, ROUND(AVG(score), 2) AS average_score
FROM assessments
WHERE score IS NOT NULL
GROUP BY student_id, full_name
ORDER BY average_score DESC
LIMIT 5;
```

### MongoDB

> `mongosh` غير مثبّت على هذا الجهاز (يوجد `mongod.exe` فقط)، فاستخدم Python عبر pymongo:

```powershell
python -c "from pipelines.mongo.extractor import get_collection; c=get_collection(); print('total:', c.count_documents({}))"
```

أو افتح صدفة تفاعلية:
```powershell
python
```
```python
from pipelines.mongo.extractor import get_collection

collection = get_collection()
print("total:", collection.count_documents({}))              # 100
print("with gpa >= 3:", collection.count_documents({"gpa": {"$gte": 3}}))  # 42

for doc in collection.find({}, {"_id": 0, "name": 1}).limit(5):
    print(doc)
```

استعلامات مفيدة عبر `extractor.py`:
```python
from pipelines.mongo.extractor import extract_students

# كل الطلاب بمعدل 3 فأكثر
high_achievers = extract_students(query={"gpa": {"$gte": 3}})

# فقط حقول الاسم والمدينة
names = extract_students(projection={"name": 1, "city": 1})
```

تعبئة المجموعة ببيانات عشوائية (~100 طالب):
```powershell
python src/pipelines/mongo/seed.py
```

---

## 7. التعامل مع الأخطاء

| المشكلة | السبب | الحل |
|---------|-------|------|
| `ModuleNotFoundError: No module named 'dotenv'` | الحزمة غير مثبتة | `python -m pip install -r requirements.txt` |
| `ModuleNotFoundError: No module named 'pymongo'` | مكتبة MongoDB غير مثبتة | `python -m pip install pymongo` |
| `ModuleNotFoundError: No module named 'pandas'` | نفس المشكلة | نفس الحل |
| `MongoDB is unreachable` | خدمة MongoDB متوقفة | `Get-Service MongoDB` ثم `Start-Service MongoDB` |
| `ServerSelectionTimeoutError` | المنفذ 27017 محجوب أو إعدادات خاطئة | تحقق من `MONGO_HOST`/`MONGO_PORT` |
| `Connection refused` / `ping` فشل | خادم PostgreSQL متوقف | شغّل الخدمة، وتأكد من `PGHOST`/`PGPORT` |
| `password authentication failed` | كلمة مرور خاطئة | صحّح `PGPASSWORD` في `.env` |
| `database ... does not exist` | القاعدة غير موجودة | أنشئها أو غيّر `PGDATABASE` |
| `Missing required columns: [...]` | تغيّرت بنية المصدر | راجع القسم 4 وحدّث القوائم في `src/common/schemas.py` |
| `psycopg2` لا يعمل | بناء بايثون مختلف | استخدم `psycopg2-binary` دائمًا (وليس `psycopg2`) |

**فحص سريع للاتصال:**
```powershell
# PostgreSQL
psql -U postgres -h 127.0.0.1 -p 5432 -d advanced_sql_training_db -c "SELECT 1;"

# MongoDB (عبر pymongo)
python -c "from pipelines.mongo.extractor import ping; print('mongo ok' if ping() else 'mongo down')"
```

---

## 8. إضافة خط مصدر جديد

البنية مصمّمة للتوسّع. لخط جديد أنشئ مجلدًا بنفس الأنماط:

```
src/pipelines/<اسم>/
├── extractor.py     ← اقرأ من المصدر
├── processor.py     ← عالج البيانات
├── writer.py        ← اكتب النتيجة
└── pipeline.py      ← نسّق المراحل
```

ثم أضف أعمدته إلى `src/common/schemas.py` وأدرج دالة التشغيل في `run_all.py`.

---

## 9. ملاحظات تقنية

- **الأسرار:** تُقرأ من متغيرات البيئة فقط، ولا يوجد أي كلمة مرور داخل الكود.
- **`pool_pre_ping=True`:** يضمن أن يعيد SQLAlchemy الاتصال تلقائيًا إذا سقطت قاعدة البيانات.
- **الاستعلامات تُبنى عبر pandas/SQLAlchemy** مع قيم مُمرَّرة من ملفاتنا فقط، فلا مدخلات مستخدم خارجية.
- **`.gitignore`** يستثني `*.md` و`.env` و`data/processed/` و`logs/` — فتُحفظ الأسرار والمخرجات خارج المستودع.

---

## 10. مراجع

- [دليل الاتصال بـ PostgreSQL](POSTGRESQL_CONNECTION_GUIDE.md) — شرح مفصّل لإعداد الاتصال والمشكلات الشائعة
- [دليل استخدام GitHub عبر SSH](GITHUB_SSH_PUSH_GUIDE.md) — إنشاء المفتاح والمصادقة والرفع