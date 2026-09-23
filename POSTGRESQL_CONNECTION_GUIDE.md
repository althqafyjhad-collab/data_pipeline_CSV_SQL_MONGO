# ربط مشروع Python بقاعدة بيانات PostgreSQL — دليل تعليمي ومرجع عملي

> قراءة جدول `students` من قاعدة بيانات `university_tranining` باستخدام psycopg2 و SQLAlchemy

---

## فهرس المحتويات

1. [نظرة عامة على معمارية المشروع](#1-نظرة-عامة)
2. [المتطلبات الأساسية](#2-المتطلبات-الأساسية)
3. [تثبيت المكتبات اللازمة](#3-تثبيت-المكتبات)
4. [إنشاء قاعدة البيانات وجداولها في PostgreSQL](#4-إنشاء-قاعدة-البيانات)
5. [تهيئة الإعدادات: `.env` ومتغيرات البيئة](#5-إعدادات-الاتصال)
6. [الطريقة الأولى: psycopg2 (المشغّل منخفض المستوى)](#6-psycopg2)
7. [الطريقة الثانية: SQLAlchemy (الخيار الموصى به)](#7-sqlalchemy)
8. [قراءة جدول students داخل المشروع (خطوة بخطوة)](#8-قراءة-جدول-students)
9. [دمج PostgreSQL في خط الإنتاج `pipeline.py`](#9-دمج-في-pipeline)
10. [قراءة جداول أخرى / استعلامات JOIN](#10-جداول-أخرى)
11. [أفضل الممارسات (Best Practices)](#11-أفضل-الممارسات)
12. [قائمة أخطاء شائعة وحلولها](#12-الأخطاء-الشائعة)
13. [تمارين مقترحة للتعلّم](#13-تمارين-مقترحة)

---

## 1. نظرة عامة

المشروع الحالي هو **خط إنتاج بيانات (Data Pipeline)** مبنيّ على Python و pandas، يقوم بـ:

```
استخراج (Extract)  →  تحويل وتنظيف (Transform/Clean)  →  حفظ (Load)
```

**المشكلة الأصلية:** كان الكود يستخدم SQLite (قاعدة محلية في ملف) لإنشاء اتصال ثم يقرأ من CSV بشكل أساسي.

**الهدف من هذا الدليل:** تحويل مصدر البيانات الرئيسي ليكون قاعدة بيانات **PostgreSQL** تُسمّى `university_tranining`، بحيث نقرأ جدول `students` مباشرةً ونمرّر البيانات إلى نفس خطّ التنظيف دون تغيير المنطق.

### هندسة الحل

```
┌─────────────────────┐     ┌──────────────────────┐     ┌─────────────────────┐
│   PostgreSQL Server │────▶│  src/db.py           │────▶│  src/pipeline.py    │
│   university_tranining│     │  (طبقة الاتصال)     │     │  (ETL pipeline)     │
│   جدول: students     │     │  psycopg2 / SQLAlchemy│     │  تحويل وتنظيف       │
└─────────────────────┘     └──────────────────────┘     └──────────┬──────────┘
                                                                    ▼
                                                   data/processed/students_ml_ready.csv
```

---

## 2. المتطلبات الأساسية

| المكوّن | الدور |
|---------|-------|
| **PostgreSQL 14+** | خادم قواعد البيانات |
| **Python 3.9+** | لغة البرمجة |
| **psycopg2 / psycopg2-binary** | المشغّل الرسمي للاتصال بـ PostgreSQL من Python |
| **SQLAlchemy 2.x** | طبقة تجريد فوق المشغّل، موصى بها مع pandas |
| **pandas** | قراءة البيانات إلى DataFrame |
| **python-dotenv** | قراءة متغيرات البيئة من ملف `.env` |

> ملاحظة: `psycopg2-binary` يحتوي على الملفات التنفيذية جاهزة (لا حاجة لمترجم C)، وهو الأنسب للتعلّم. في بيئة الإنتاج يُفضَّل `psycopg2` المثبّت من المصدر.

### التحقق من تثبيت PostgreSQL

افتح الطرفية `psql` واكتب:

```sql
SELECT version();
```

يجب أن ترى نسخة PostgreSQL. كما تأكّد أن الخدمة تعمل على المنفذ الافتراضي **5432**.

---

## 3. تثبيت المكتبات

أضف هذه الأسطر إلى `requirements.txt`:

```
pandas>=2.2
psycopg2-binary>=2.9
sqlalchemy>=2.0
python-dotenv>=1.0
```

ثم نفّذ من داخل مجلد المشروع:

```bash
pip install -r requirements.txt
```

> هذا الأمر سيحمّل كل ما تحتاجه: مشغّل PostgreSQL + أداة الاتصال + pandas.

---

## 4. إنشاء قاعدة البيانات

افتح `psql` كمستخدم `postgres`:

```bash
psql -U postgres
```

### 4.1 إنشاء قاعدة البيانات

```sql
CREATE DATABASE university_tranining;
```

> انتبه للإملاء: `university_tranining` (بأحرف مشابهة للاسم في الكود الأصلي).

### 4.2 توصيل بالقاعدة الجديدة

```bash
\c university_tranining
```

### 4.3 إنشاء جدول students

```sql
CREATE TABLE students (
    student_id  INTEGER PRIMARY KEY,
    full_name   VARCHAR(100) NOT NULL,
    age         INTEGER,
    gpa         NUMERIC(3,2),
    attendance  INTEGER,
    city        VARCHAR(100)
);
```

### 4.4 إدخال بيانات تجريبية

```sql
INSERT INTO students (student_id, full_name, age, gpa, attendance, city) VALUES
(1001, 'Ahmed Ali',      22, 3.50, 92, 'Sanaa'),
(1002, 'Sara Mohammed',  21, 3.80, 96, 'Sanaa'),
(1003, 'Khaled Hassan',  23, NULL, 88, 'Dhamar'),
(1004, 'Mona Saleh',     20, 4.20, 94, 'Ibb'),
(1005, 'Ali Ahmed',      -5, 2.90, 75, 'Taiz'),
(1006, 'Huda Omar',      22, 3.20, 105,'Sanaa'),
(1008, 'Mohammed Noor',  21, 3.90, NULL,'Dhamar');
```

### 4.5 التحقق

```sql
SELECT * FROM students;
```

---

## 5. إعدادات الاتصال

### لماذا لا نضع بيانات الاتصال داخل الكود؟

وضع كلمة المرور داخل الملف المصدري خطر أمني، ويصعّب تغيير البيئة (تطوير → إنتاج). الحل: **متغيرات البيئة** + ملف `.env`.

### 5.1 إنشاء ملف `.env`

انقل من القالب:

```bash
copy .env.example .env
```

محتوياته:

```dotenv
PGHOST=localhost
PGPORT=5432
PGDATABASE=university_tranining
PGUSER=postgres
PGPASSWORD=postgres
```

### 5.2 دور `python-dotenv`

عند استدعاء `load_dotenv()` في بداية `db.py`، تُقرأ المتغيرات من `.env` إلى `os.environ` تلقائيًا قبل استخدامها.

---

## 6. psycopg2 — المشغّل منخفض المستوى

### 6.1 ما هو؟

`psycopg2` هو مشغّل (Driver) ناطق ببروتوكول PostgreSQL الخام. يعطي تحكّمًا مباشرًا في الاتصال والاستعلام عبر كائن `connection` و `cursor`.

### 6.2 الاتصال

```python
from psycopg2 import connect

conn = connect(
    host="localhost",
    port="5432",
    dbname="university_tranining",
    user="postgres",
    password="postgres",
)
```

> تُعرض القيم هنا للتوضيح فقط؛ في الكود الفعلي نقرأها من متغيرات البيئة.

### 6.3 تنفيذ استعلام

```python
cur = conn.cursor()
cur.execute("SELECT * FROM students;")
rows = cur.fetchall()
columns = [d[0] for d in cur.description]

import pandas as pd
df = pd.DataFrame(rows, columns=columns)

cur.close()
conn.close()   # لا تنسَ إغلاق الاتصال!
```

### 6.4 الاتصال الذكي (Context Manager)

الطريقة الأفضل هي استخدام `with`، لأنها تُغلق الاتصال تلقائيًا حتى لو حصل استثناء:

```python
from psycopg2 import connect
import pandas as pd

conn = connect(host="localhost", dbname="university_tranining",
               user="postgres", password="postgres")

with conn:
    df = pd.read_sql_query("SELECT * FROM students;", conn)

# عند الخروج من with: يُرتكب العمل أو يُتراجع، لكن الاتصال يبقى مفتوحًا
conn.close()
```

### 6.5 قيمة psycopg2 في مشروعنا

في `src/db.py` استخدمنا psycopg2 لبناء استعلامات آمنة ضد حقن SQL عبر `sql.Identifier`:

```python
from psycopg2 import sql

query = sql.SQL("SELECT {cols} FROM {table}").format(
    cols=sql.SQL(", ").join(sql.Identifier(c) for c in columns),
    table=sql.Identifier(table_name),
)
```

> `sql.Identifier` يعامل أسماء الجداول والأعمدة كأسماء (وليس كنصّ مضمّن)، فيمنع تلاعب المستخدم بجدولة الاستعلام.

---

## 7. SQLAlchemy — طبقة التجريد الموصى بها

### 7.1 لماذا SQLAlchemy؟

- **Engine (المحرّك):** يدير **تجمّع اتصالات (Connection Pool)**، فلا نعيد فتح اتصال في كل مرة.
- **توافق مع pandas:** دوال `pd.read_sql_table` و `pd.read_sql_query` تعمل معها مباشرة.
- **جدولة (Dialects):** نفس الكود يعمل مع PostgreSQL و MySQL و SQLite بتبديل السلسلة فقط.

### 7.2 بناء المحرّك

```python
from sqlalchemy import create_engine

url = (
    "postgresql+psycopg2://postgres:postgres@localhost:5432/university_tranining"
)
engine = create_engine(url, pool_pre_ping=True)
```

`postgresql+psycopg2://` تعني: استخدام بروتوكول PostgreSQL مع المشغّل psycopg2.

- `pool_pre_ping=True`: يفحص صحة الاتصال قبل إعادة استخدامه من التجمّع.

### 7.3 اختبار الاتصال

```python
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text("SELECT 1"))
    print(result.scalar())  # 1
```

### 7.4 جرد الجداول (Introspection)

```python
from sqlalchemy import inspect

inspector = inspect(engine)
tables = inspector.get_table_names()
print(tables)  # ['students', ...]
```

### 7.5 القراءة في pandas

نختار حسب ما نريد:

```python
# قراءة كل الجدول
df = pd.read_sql_table("students", engine)

# قراءة بأعمدة محددة وشروط
query = "SELECT student_id, full_name FROM students WHERE age >= 18"
df = pd.read_sql_query(query, engine)
```

| الدالة | التوقيت المناسب |
|--------|-----------------|
| `pd.read_sql_table` | جدول كامل دون تغيير |
| `pd.read_sql_query` | استعلام مخصّص / JOIN / تجميع |

---

## 8. قراءة جدول students مؤيّداً بما نطلب

في `src/db.py` توجد دالة عالية المستوى مخصّصة:

```python
def load_students_table(
    engine: Optional[Engine] = None,
    columns: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    Convenience wrapper: load the `students` table from PostgreSQL.
    """
    engine = engine or get_engine()
    return read_table_sqlalchemy("students", columns=columns)
```

### تجربة مباشرة

```python
from src.db import load_students_table

df = load_students_table()
print(df.shape)
print(df.head())
```

ستحصل على DataFrame يحتوي كل صفوف `students`.

### هل تتطابق الأعمدة مع توقّع خطّ التنظيف؟

خطّ التنظيف يتوقع أعمدة: `student_id, name, age, gpa, attendance, city`.

- الجدول في قاعدة البيانات استخدمنا عمودًا باسم `full_name`.
- لذلك عند دمج القراءة في الـ pipeline يجب إعادة تسمية العمود:

```python
df = df.rename(columns={"full_name": "name"})
```

> صُمّم هذا الدليل بحيث تُنشئ الجدول باسم `full_name` (كما في استعلام المشروع الأصلي). لو كانت قاعدة بياناتك تستخدم `name` أصلًا، فلن تحتاج لإعادة التسمية.

---

## 9. دمج PostgreSQL في `pipeline.py`

نفّذنا التعديلات التالية على `src/pipeline.py`:

### 9.1 الاستيراد من الوحدة الجديدة

```python
from db import (
    get_engine,
    ping_sqlalchemy,
    load_students_table,
)

STUDENTS_TABLE = "students"
```

### 9.2 استبدال دالة التحميل

قبل:
```python
connection = sqlite3.connect("university_tranining.db")  # اتصال ملغي
df = pd.read_csv(RAW_FILE)
```

بعد:
```python
def load_data(file_path: Path = RAW_FILE) -> pd.DataFrame:
    engine = get_engine()

    if not ping_sqlalchemy():
        logger.warning("PostgreSQL unreachable; falling back to CSV")
        return _load_csv(file_path)

    df = load_students_table(engine)

    if df.empty:
        raise ValueError("Students table is empty.")

    logger.info(f"Loaded {len(df)} rows ... from PostgreSQL")
    return df
```

- `get_engine()` → محرّك من `db.py`.
- `ping_sqlalchemy()` → تأكّد من أن الخادم متاح.
- `load_students_table(engine)` → قراءة الجدول.
- `_load_csv` → خطة بديلة اختيارية إن تعطّل PostgreSQL.

### 9.3 دورة حياة الخط

```python
def run_pipeline():
    df = load_data()             # Extract : PostgreSQL -> DataFrame
    validate_schema(df)          # تحقق من الأعمدة المطلوبة
    df = convert_data_types(df)  # تحويل الأنواع الرقمية
    df = clean_data(df)          # تنظيف (تكرار، قيم، نص)
    validate_data(df)            # تحقق نهائي
    save_data(df, OUTPUT_FILE)   # Load : حفظ CSV
```

### 9.4 التشغيل

من داخل مجلد `src` (حتى يجد `import db`):

```bash
python pipeline.py
```

أو من جذر المشروع عبر الاستيراد المطلق:

```bash
python -m src.pipeline   # إن جعلنا src حزمة
```

مخرجات متوقعة في `logs/pipeline.log`:

```
2026-..-.. | INFO | Loading students table from PostgreSQL database
2026-..-.. | INFO | Loaded 7 rows and 6 columns from PostgreSQL table 'students'
2026-..-.. | INFO | Pipeline completed successfully.
```

---

## 10. قراءة جداول أخرى واستعلامات JOIN

لدينا في `db.py` دالة عامة لأي استعلام:

```python
def read_query_sqlalchemy(query: str) -> pd.DataFrame:
    return pd.read_sql_query(query, engine)
```

### 10.1 مثال: متوسط درجات كل طالب (JOIN)

```python
from src.db import run_pipeline_query

df = run_pipeline_query()   # يستخدم STUDENT_AVERAGE_QUERY
print(df)
```

الاستعلام (موجود في `db.py`):

```sql
SELECT
    s.student_id,
    s.full_name,
    c.course_name,
    AVG(a.score) AS average_score
FROM assessments a
INNER JOIN students s  ON a.student_id = s.student_id
INNER JOIN courses c   ON a.course_id  = c.course_id
GROUP BY s.student_id, s.full_name, c.course_id, c.course_name;
```

> يتطلب هذا الاستعلام وجود جداول `assessments` و `courses` في القاعدة.

### 10.2 جرد الجداول المتاحة

```python
from src.db import list_tables_sqlalchemy
print(list_tables_sqlalchemy())
```

---

## 11. أفضل الممارسات

| الممارسة | لماذا؟ |
|----------|--------|
| **لا تضع كلمات المرور في الكود** | استخدم `.env` ومتغيرات البيئة |
| **أضِف `.env` إلى `.gitignore`** | حتى لا تُرفَع الأسرار إلى git |
| **استخدم Connection Pool** | SQLAlchemy Engine يدير الاتصالات بذكاء |
| **أغلق الاتصالات** | `with` يضمن الإغلاق التلقائي |
| **منع SQL Injection** | استخدم `sql.Identifier` وليس تجميع نصي للاستعلامات المبنية |
| **تعامل مع `NULL` من القاعدة** | املأ القيم المفقودة قبل التحويل الرقمي |
| **سجّل (Log) كل مرحلة** | يساعد على تتبّع الأخطاء |
| **التحقق من حجم النتائج** | `df.empty` فحص قبل متابعة العمل |

> أمان: أضف `.env` إلى `.gitignore`:
> ```
> .env
> ```

---

## 12. الأخطاء الشائعة

| الخطأ | السبب | الحل |
|-------|-------|------|
| `connection refused` | PostgreSQL لا يعمل أو منفذ مختلف | شغّل الخدمة، تحقق من `PGPORT` |
| `database "university_tranining" does not exist` | القاعدة غير منشأة | نفّذ `CREATE DATABASE` |
| `password authentication failed` | كلمة مرور خاطئة | تحقق من `PGUSER`/`PGPASSWORD` |
| `ModuleNotFoundError: psycopg2` | المكتبة غير مثبّتة | `pip install psycopg2-binary` |
| `relation "students" does not exist` | اسم الجدول أو schema خاطئ | تحقق من `list_tables()` |
| `'name' columns mismatch` | الاسم في الجدول `full_name` | `rename(columns={'full_name':'name'})` |
| `duplicate key value` عند INSERT | مفتاح أساسي مكرر | تحقق من `student_id` |

---

## 13. تمارين مقترحة للتعلّم

1. **اتصل عبر psycopg2 فقط** (بدون pandas) واطبع عدد الطلاب.
2. **ارسم توزيع الـ GPA** من بيانات PostgreSQL مباشرة (matplotlib).
3. **أنشئ استعلام تجميع جديد** يعيد عدد الطلاب حسب كل مدينة.
4. **أضف دالة كتابة** إلى `db.py` تقوم بإدخال صف جديد في `students` باستخدام `INSERT`.
5. **بدّل مصدر البيانات إلى MySQL** بكتابة URL مختلف (راجع فكرة Dialects في SQLAlchemy).

---

## الخلاصة

- **psycopg2** = المشغّل الأساسي الصريح للاتصال.
- **SQLAlchemy** = طبقة تجريد توفر Engine وتجمّع اتصالات وقراءة محكمة مع pandas.
- **المشروع الآن** يقرأ `students` مباشرةً من PostgreSQL ويتغذّى بنفس خطّ التنظيف، مع خطة بديلة عبر CSV.
- كل الإعدادات أُخفيت خلف متغيرات البيئة، والكود منظّم في وحدة `db.py` مستقلة قابلة لإعادة الاستخدام.

**الملفات الناتجة عن هذا الدليل:**

```
├── .env.example          # قالب إعدادات الاتصال
├── requirements.txt      # المكتبات المطلوبة
└── src/
    ├── db.py             # طبقة اتصال PostgreSQL (جديد)
    └── pipeline.py       # خط الإنتاج (مُعدّل للقراءة من PostgreSQL)
```