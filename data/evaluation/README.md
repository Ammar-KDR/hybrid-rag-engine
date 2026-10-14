# Jordan government RAG — official source test pack

13 official service-document links and 50 Arabic test questions. Sources checked on 2026-10-14.

> **Important:** This pack contains source URLs and a downloader, **not copies of the official PDFs**. Download the source documents before going offline. Only source document files belong in RAG ingestion; NEVER ingest `gold_answers.*`, `questions_only.csv`, or README.

## Documents

| ID | Service | Type | Group | Official link |
|---|---|---|---|---|
| P01 | إصدار كرت اتجاه لوسائط النقل العام | PDF | core | [Open original](https://www.ammancity.gov.jo/ar/gameservices/docs/daleeldepts/14.pdf?23332=) |
| P02 | طلب صورة طبق الأصل من عقد الإيجار | PDF | core | [Open original](https://www.ammancity.gov.jo/ar/gameservices/docs/daleeldepts/121.pdf?23332=) |
| P03 | تسجيل وتصديق عقد إيجار أو ملحق | PDF | core | [Open original](https://www.ammancity.gov.jo/ar/gameservices/docs/daleeldepts/52.pdf?23332=) |
| P04 | طلب الإعفاء من رسوم نقل وطمر النفايات | PDF | core | [Open original](https://www.ammancity.gov.jo/ar/gameservices/docs/daleeldepts/84.pdf?23332=) |
| P05 | كف الطلب عن مخالفات البيع العشوائي | PDF | core | [Open original](https://www.ammancity.gov.jo/ar/gameservices/docs/daleeldepts/92.pdf?23332=) |
| P06 | ملف الخدمات 130: إعفاء من رسوم سابقة وإصدار رخصة مهن وغيرها | PDF | stress | [Open original](https://www.ammancity.gov.jo/ar/gameservices/docs/daleeldepts/130.pdf?23332=) |
| P07 | طلب رد مبلغ مدفوع بالخطأ | PDF | core | [Open original](https://www.ammancity.gov.jo/ar/gameservices/docs/daleeldepts/138.pdf?23332=) |
| P08 | طلب دفع تأمينات الترشح للانتخابات البرلمانية | PDF | core | [Open original](https://www.ammancity.gov.jo/ar/gameservices/docs/daleeldepts/300.pdf?23332=) |
| P09 | ملف تراخيص الأبنية: عدة بطاقات منها إلغاء ترخيص مقترح | PDF | stress | [Open original](https://www.ammancity.gov.jo/ar/gameservices/docs/daleeldepts/131.pdf?23332=) |
| P10 | ملف خدمات GIS وطلب خرائط وبيانات جغرافية | PDF | stress | [Open original](https://www.ammancity.gov.jo/ar/gameservices/docs/daleeldepts/134.pdf?23332=) |
| H01 | البطاقة الذكية بدل فاقد | HTML | core | [Open original](https://www.cspd.gov.jo/AR/ListDetails/_%D8%AF%D9%84%D9%8A%D9%84__%D8%A7%D9%84%D8%AE%D8%AF%D9%85%D8%A7%D8%AA/41/32) |
| H02 | إصدار البطاقة الذكية لأول مرة | HTML | core | [Open original](https://www.cspd.gov.jo/AR/ListDetails/_%D8%AF%D9%84%D9%8A%D9%84__%D8%A7%D9%84%D8%AE%D8%AF%D9%85%D8%A7%D8%AA/41/34) |
| H03 | تجديد البطاقة الذكية | HTML | core | [Open original](https://www.cspd.gov.jo/AR/ListDetails/_%D8%AF%D9%84%D9%8A%D9%84__%D8%A7%D9%84%D8%AE%D8%AF%D9%85%D8%A7%D8%AA/41/36) |

## How to run

1. While online, run `python download_sources.py` from this directory. Check its summary and open files visually.
2. Only put the downloaded PDFs and downloaded HTML service pages into your `data/raw` or another ingestion directory.
3. Ingest using your current project ingestion script; do **not** include evaluation CSV or gold JSON in your corpus.
4. Ask the questions in `questions_only.csv` and compare responses with `gold_answers.csv` manually or programmatically.
5. Pay particular attention to Arabic table order, multi-service PDFs, conditional eligibility, numeric calculations, evidence/citation correctness and abstentions.

## Caveats

- Government documentation can be updated. These are test fixtures based on the linked official pages as indexed/visually inspected on October 14, 2026, not authoritative legal advice.
- Some Amman PDF pages have malformed extracted Arabic, even when their rendered pages are readable. Specifically check P01’s licence validity condition against the visual page, not the scrambled text.
- P06/P09/P10 are stress-test PDFs containing more than one service; do not presume one file equals one service.
- Some source servers may timeout. The downloader retries and reports files that could not be retrieved.
- The `gold_answers.csv` contains concise expected outcomes and locators, not verbatim copyrighted documents.

## Test distribution

- `abstention`: 4
- `conditional_arithmetic`: 2
- `conditional_discount`: 1
- `conditional_documents`: 7
- `conditional_eligibility`: 4
- `conditional_fee`: 3
- `cross_service_comparison`: 1
- `cross_service_disambiguation`: 3
- `documents`: 1
- `duration`: 6
- `eligibility`: 3
- `fee_formula`: 1
- `fee_lookup`: 6
- `fee_vs_fine`: 1
- `procedural_time`: 1
- `procedure`: 1
- `process`: 1
- `service_disambiguation`: 2
- `service_scope`: 1
- `temporal_scope`: 1

## Suggested evaluation rubric

- Relevant service located? (yes/no)
- Applicable conditional rule found? (yes/no)
- Answer matches expected? (0 / partial / 1)
- Supporting citation actually points to matching service/field? (yes/no)
- Unsupported questions abstained? (yes/no)
- Latency in seconds.

## Detailed question-only list

- **Q001** (easy; fee_lookup): كم رسم كرت الاتجاه للمركبة الصغيرة دون تأخير؟
- **Q002** (hard; conditional_arithmetic): عندي حافلة متوسطة وتأخرت ثلاثة أشهر في كرت الاتجاه. كم أدفع بحسب الوثيقة؟
- **Q003** (medium; conditional_arithmetic): إذا كانت حافلة كبيرة وتأخرت شهرين، كم الرسوم وغرامة التأخير؟
- **Q004** (medium; eligibility): هل يجب أن تكون رخصة المركبة سارية المفعول لإصدار كرت الاتجاه؟
- **Q005** (easy; fee_lookup): ما رسوم الحصول على صورة طبق الأصل من عقد الإيجار؟
- **Q006** (medium; eligibility): هل يمكن استخراج صورة طبق الأصل من عقد إيجار غير مصدق لدى أمانة عمان؟
- **Q007** (medium; duration): كم يستغرق إصدار صورة طبق الأصل من عقد الإيجار وهل يشترط أن يكون العقد بعد 1989؟
- **Q008** (hard; conditional_eligibility): عندي ملكية مشتركة وحصتي 50%، هل أستطيع تقديم طلب تسجيل عقد إيجار وفق الشروط؟
- **Q009** (medium; conditional_eligibility): بدي أعمل ملحق عقد إيجار لكن العقد الأصلي منتهي، هل يقبل؟
- **Q010** (medium; duration): كم الزمن المعياري لتسجيل عقد الإيجار أو ملحقه؟
- **Q011** (hard; fee_formula): كم نسبة رسم تسجيل عقد الإيجار وما الحد الأعلى للجزء المرتبط بقيمة العقد السنوية؟
- **Q012** (medium; conditional_documents): أغلقت منشأتي وأريد الإعفاء من رسوم النفايات. ما المستند الذي يثبت سبب الإغلاق؟
- **Q013** (hard; conditional_documents): إذا متعاقد مع شركة خاصة لنقل النفايات، شو أوراق الإثبات ذات العلاقة؟
- **Q014** (medium; eligibility): هل خدمة الإعفاء من رسوم نقل وطمر النفايات متاحة للأفراد أم لفئة الأعمال؟
- **Q015** (medium; conditional_documents): إذا كنت دفعت رسوم النفايات ضمن فاتورة الكهرباء، ما الوثيقة المتعلقة بهذا السبب؟
- **Q016** (hard; fee_vs_fine): هل يوجد رسم منفصل لتقديم طلب كف الطلب عن مخالفات البيع العشوائي؟
- **Q017** (easy; duration): كم تستغرق خدمة كف الطلب عن مخالفات البيع العشوائي؟
- **Q018** (medium; procedure): ما الذي يحصل بعد دفع المخالفة في خدمة كف الطلب؟
- **Q019** (medium; conditional_documents): ما الإثبات المذكور للإعفاء من رسوم رخصة المهن عن سنوات لم تُمارس فيها المهنة؟
- **Q020** (medium; service_scope): هل خدمة الإعفاء من رسوم سنوات سابقة عليها رسوم طلب؟
- **Q021** (medium; duration): كم الزمن المعياري لخدمة إصدار رخصة المهن في هذا الملف؟
- **Q022** (hard; abstention): أعطني قيمة مالية ثابتة لإصدار رخصة المهن من هذه البطاقة.
- **Q023** (easy; fee_lookup): هل خدمة طلب رد مبلغ مدفوع بالخطأ لها رسوم؟
- **Q024** (medium; process): كيف يُسلّم المبلغ في حال الموافقة على طلب رد مبلغ مدفوع؟
- **Q025** (medium; documents): ما وثيقة إثبات الشخصية المقبولة عند تقديم طلب رد مبلغ مدفوع بالخطأ؟
- **Q026** (easy; fee_lookup): كم تبلغ قيمة تأمينات الترشح للانتخابات البرلمانية في البطاقة؟
- **Q027** (medium; duration): كم الزمن المعياري لإتمام طلب دفع تأمينات الترشح، وما مخرج الخدمة؟
- **Q028** (hard; temporal_scope): هل الخدمة المذكورة متاحة على مدار الساعة طوال السنة؟
- **Q029** (hard; conditional_eligibility): مر 14 شهراً على إصدار ترخيص مقترح، هل يمكنني إلغاء الترخيص بهذه الخدمة؟
- **Q030** (hard; conditional_eligibility): هل يمكن إلغاء ترخيص مقترح مع وجود تصريح حفر ساري؟
- **Q031** (medium; duration): كم يستغرق طلب إلغاء ترخيص مقترح، وهل عليه رسم طلب؟
- **Q032** (hard; service_disambiguation): هل مدة إصدار رخصة إنشائية هي نفسها المدة المعيارية لإلغاء ترخيص مقترح؟
- **Q033** (hard; conditional_discount): كم خصم طلب خارطة جغرافية إذا كان الطالب يستخدمها لأغراض البحث العلمي؟
- **Q034** (hard; service_disambiguation): هل خصم طلب البيانات الرقمية للطلاب يساوي خصم الخارطة للبحث العلمي؟
- **Q035** (medium; conditional_documents): إذا ضاعت بطاقتي الذكية للمرة الثالثة، ما المستند الإضافي المرتبط بالتحقيق؟
- **Q036** (hard; conditional_fee): إذا فقدت البطاقة الذكية للمرة الثالثة، كم قيمة الكفالة المالية وحدها؟
- **Q037** (hard; conditional_fee): إذا فقدتها للمرة الثانية خلال أقل من ثلاث سنوات، هل تُقبل المعاملة دون دفع قيمة التعهد؟
- **Q038** (medium; procedural_time): هل تُسلّم البطاقة الذكية بدل الفاقد فوراً بعد إبلاغ الشرطة؟
- **Q039** (easy; fee_lookup): كم رسوم إصدار البطاقة الشخصية الذكية لأول مرة؟
- **Q040** (hard; conditional_fee): إذا بلغ المتقدم 18 عاماً ولم يصدر البطاقة الذكية، هل توجد غرامة تأخير في الدليل؟
- **Q041** (medium; conditional_documents): ما الشرط الإضافي للمتقدم لإصدار البطاقة الذكية أول مرة إذا كان دون 16 سنة؟
- **Q042** (easy; fee_lookup): ما رسوم تجديد البطاقة الشخصية الذكية؟
- **Q043** (medium; conditional_documents): إذا كانت صورة الهوية القديمة غير واضحة عند التجديد، ما البديل لإثبات الشخصية؟
- **Q044** (hard; cross_service_comparison): قارن الرسوم الأساسية لإصدار البطاقة الذكية أول مرة وتجديدها وبدل فاقد.
- **Q045** (hard; cross_service_disambiguation): بدي أسجل عقد إيجار لأول مرة، هل خدمة طلب صورة طبق الأصل هي نفسها؟
- **Q046** (hard; cross_service_disambiguation): هل أوراق إثبات إغلاق المنشأة للإعفاء من رسوم النفايات هي نفس وثائق الإعفاء من رسوم رخصة المهن لسنوات سابقة؟
- **Q047** (hard; cross_service_disambiguation): هل رد مبلغ مدفوع خطأ هو نفسه استرداد رسوم عند إلغاء ترخيص مقترح؟
- **Q048** (hard; abstention): هل رسوم التأمينات للانتخابات البرلمانية القادمة في 2028 ستكون 500 دينار؟
- **Q049** (hard; abstention): هل يمكن إصدار البطاقة الذكية أول مرة عن طريق واتساب دون مراجعة المكتب؟
- **Q050** (hard; abstention): هل يعفى عقد الإيجار إذا كان أحد الأطراف طالباً جامعياً من الرسوم؟
