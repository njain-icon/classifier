# 📘 Custom Presidio Entity Recognizers

This repository contains **custom Presidio Analyzer recognizers** implemented using `PatternRecognizer`. These recognizers detect structured identifiers and sensitive attributes using **regex rules combined with contextual keywords** for improved precision.

---

## Presidio Supported Entities
1. Social Security Number (SSN)
2. Driver's License Number (DL)
3. Email Address
4. Phone Number
5. Bank Account Number
6. Routing Number



## 📦 Included New Entities

1. Business Tax ID (EIN)
2. Department of Defense (DoD) ID
3. Date of Birth (DOB)
4. Service Number
5. Employee / Staff ID
6. Medical License Number
7. VA Claim Number

---

## 1️⃣ Business Tax ID Recognizer (`BUSINESS_TAX_ID`)

### Description

Detects **Business / Practice Tax Identification Numbers (EIN)** issued by the IRS.

### Supported Formats

* `12-3456789`
* `123456789`

### Regex Rules

| Pattern Name    | Regex                 | Confidence |
| --------------- | --------------------- | ---------- |
| EIN_WITH_HYPHEN | `\\b\\d{2}-\\d{7}\\b` | 0.8        |
| EIN_NO_HYPHEN   | `\\b\\d{9}\\b`        | 0.6        |

### Context Keywords

```
ein, tax id, tax identification, business tax,
practice tax, employer identification, irs
```

### Example

> The company EIN is **12-3456789**.

---

## 2️⃣ DoD ID Recognizer (`DOD_ID`)

### Description

Detects **Department of Defense (DoD) ID Numbers** assigned to military personnel.

### Supported Format

* 10-digit numeric ID

### Regex Rule

| Pattern Name | Regex           | Confidence |
| ------------ | --------------- | ---------- |
| DOD_ID       | `\\b\\d{10}\\b` | 1.0        |

### Context Keywords

```
dod id, department of defense,
military id, dod number, DOD
```

### Example

> Verify the DoD ID **1234567890**.

---

## 3️⃣ Date of Birth Recognizer (`DATE_OF_BIRTH`)

### Description

Detects **Date of Birth (DOB)** values and validates them.

### Supported Formats

* `DD-MM-YYYY`
* `DD/MM/YYYY`
* `DD.MM.YYYY`
* `YYYY-MM-DD`

### Regex Rules

| Pattern Name | Regex                       |                     |                    |                             |
| ------------ | --------------------------- | ------------------- | ------------------ | --------------------------- |
| DOB_DDMMYYYY | `(0[1-9]                    | [12][0-9]           | 3[01])[-/.](0[1-9] | 1[0-2])[-/.]([12][0-9]{3})` |
| DOB_YYYYMMDD | `([12][0-9]{3})[-/.](0[1-9] | 1[0-2])[-/.](0[1-9] | [12][0-9]          | 3[01])`                     |

### Context Keywords

```
date of birth, dob, born,
birth, birthdate, birthday
```

### Validation Rules

* Invalid calendar dates are rejected
* Future dates are rejected
* Age greater than 120 years is rejected

### Example

> Her DOB is **21/05/1994**.

---

## 4️⃣ Service Number Recognizer (`SERVICE_NUMBER`)

### Description

Detects **Military or Government Service Numbers**.

### Supported Formats

* `ARMY123456`
* `NAV-987654`
* `IAF 123456`

### Regex Rules

| Pattern Name          | Regex                              |
| --------------------- | ---------------------------------- |
| SERVICE_NUMBER        | `\\b[A-Z]{1,3}\\d{6,10}\\b`        |
| SERVICE_NUMBER_HYPHEN | `\\b[A-Z]{1,3}[-\\s]?\\d{6,10}\\b` |

### Context Keywords

```
service, number, military,
army, navy, airforce,
defense, service id
```

### Example

> Service number **ARMY-654321** was confirmed.

---

## 5️⃣ Employee ID Recognizer (`EMPLOYEE_ID`)

### Description

Detects **Employee / Staff Identifier Codes** used in HR and payroll systems.

### Supported Formats

* `EMP12345`
* `HR-98765`
* `AB123456`
* `ab-1234`

### Regex Rules

| Pattern Name         | Regex                 |     |       |                   |
| -------------------- | --------------------- | --- | ----- | ----------------- |
| EMPLOYEE_ID_PREFIXED | `(?:EMP               | EID | STAFF | HR)[-_]?\d{4,10}` |
| EMPLOYEE_ID_GENERIC  | `[A-Z]{2,4}\\d{4,10}` |     |       |                   |
| EMPLOYEE_ID          | `[a-z]{2}-[0-9]{4}`   |     |       |                   |

### Context Keywords

```
employee id, employee code, staff id,
staff code, employee number, hr id,
personnel id, payroll id
```

### Example

> Please provide your Employee ID **EMP-10492**.

---

## 6️⃣ Medical License Recognizer (`MEDICAL_LICENSE`)

### Description

Detects **Medical Staff License Numbers** issued to healthcare professionals.

### Supported Formats

* `MD123456`
* `LIC-987654`
* `DMC/12345`
* `MED678901`

### Regex Rule

| Pattern Name | Regex   |    |     |                    |
| ------------ | ------- | -- | --- | ------------------ |
| MED_LICENSE  | `(?:LIC | MD | DMC | MED)[-/]?\d{4,10}` |

### Context Keywords

```
medical license, license number,
doctor license, physician license,
medical registration
```

### Example

> Doctor’s license **LIC-456789** is valid.

---

## 7️⃣ VA Claim Number Recognizer (`VA_CLAIM_NUMBER`)

### Description

Detects **VA Claim Numbers** associated with Veterans Affairs.

### Supported Formats

* `123456789` (9 digits)
* `123-45-6789` (Hyphen separated)
* `123 456 789` (Space separated)

### Regex Rules

| Pattern Name          | Regex                       | Confidence |
| --------------------- | --------------------------- | ---------- |
| VA_CLAIM_CONTINUOUS   | `\\b\\d{9}\\b`                 | 0.85       |
| VA_CLAIM_SPACED       | `\\b\\d{3}\\s\\d{3}\\s\\d{3}\\b`   | 0.9        |
| VA_CLAIM_HYPHENATED   | `\\b\\d{3}-\\d{2}-\\d{4}\\b`     | 0.9        |

### Context Keywords

```
va claim, va claim number, claim number,
va file number, va file no, claim #,
va benefits, veterans affairs
```

### Validation Rules

* Must be exactly 9 digits
* Cannot be all same digits (e.g., 000000000)
* Reject dummy numbers (123456789, 987654321, 000000000)

### Example

> The VA Claim Number is **123-45-6789**.

---


---

