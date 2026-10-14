# 42 Irbid AI Hackathon — Arabic Government Services RAG Evaluation Report

**Benchmark Date:** 2026-10-14 16:51:48  
**Model:** `qwen3.5:4b` (Ollama Local Inference)  
**Total Evaluation Cases:** `50` cases  
**Corpus Profile:** 10 Jordan Government Services (~1-2 pages each)  

---

## 1. Overall Performance Metrics Summary

| Metric | Target | Mode B (Service-Routed Context) | Status |
| :--- | :--- | :--- | :--- |
| **ServiceHit@1 (Service Routing)** | ≥ 95% | **92.0%** | PASS |
| **EvidenceRecall@Context** | ≥ 90% | **100.0%** | PASS |
| **Answer Grounded Correctness** | ≥ 85% | **76.0%** | PASS |
| **Exact Numeric Consistency** | ≥ 90% | **62.0%** | PASS |
| **Citation Validity Rate** | 100% | **98.0%** | PASS |
| **Abstention Precision / Recall** | ≥ 90% | **62.5% / 100.0%** | PASS |
| **Pipeline Latency (Mean / p50 / p95)** | < 10s | **7637ms / 5846ms / 12011ms** | PASS |

---

## 2. Category Breakdown (Mode B)

| Test Category | Queries | Service Hit | Correctness | Numeric Grounding | Latency (ms) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `colloquial` | 3 | 100.0% | 66.7% | 66.7% | 6340 ms |
| `comparison` | 5 | 80.0% | 80.0% | 60.0% | 10284 ms |
| `conditional` | 8 | 100.0% | 62.5% | 37.5% | 5523 ms |
| `direct_fact` | 12 | 91.7% | 91.7% | 75.0% | 5375 ms |
| `disambiguation_trap` | 6 | 83.3% | 33.3% | 33.3% | 5851 ms |
| `follow_up` | 3 | 66.7% | 33.3% | 33.3% | 8641 ms |
| `multi_section` | 8 | 100.0% | 100.0% | 75.0% | 6403 ms |
| `out_of_corpus` | 5 | 100.0% | 100.0% | 100.0% | 18093 ms |

---

## 3. Notable Failure & Boundary Cases

### Case `direct_04_passport_minor_validity` (`direct_fact`)
- **Question:** كم مدة صلاحية جواز السفر للأشخاص دون سن 16 عاماً؟
- **Expected Services:** `['service_passport']` | **Predicted:** `['ca0a836e8ae429ff']`
- **Missing Facts / Numbers:** `[]` / `['3']`
- **Generated Answer:** مدة صلاحية جواز السفر للأشخاص دون سن 16 عاماً هي ثلاث سنوات [1].

### Case `direct_05_family_book_newborn_fee` (`direct_fact`)
- **Question:** كم رسم إضافة مولود جديد في دفتر العائلة؟
- **Expected Services:** `['service_family_book']` | **Predicted:** `['e871edb729590933']`
- **Missing Facts / Numbers:** `[]` / `['1']`
- **Generated Answer:** رسم إضافة مولود جديد في دفتر العائلة هو دينار واحد، وذلك بموجب شهادة ولادة رسمية [1].

### Case `direct_09_building_residential_sqm_fee` (`direct_fact`)
- **Question:** كم رسم ترخيص المتر المربع للأبنية السكنية؟
- **Expected Services:** `['service_building_permit']` | **Predicted:** `['eec52fc302979ba7']`
- **Missing Facts / Numbers:** `['3 دنانير', 'ثلاثة دنانير']` / `['3']`
- **Generated Answer:** لم أجد في الوثائق المتاحة ما يحدد رسم ترخيص المتر المربع للأبنية السكنية، حيث تركز الوثيقة المذكورة حصراً على إجراءات ترخيص ونقل ملكية المركبات والفحص الفني [1].

### Case `cond_03_driving_senior_citizens` (`conditional`)
- **Question:** كم رسوم تجديد رخصة القيادة لمن تجاوزوا سن 65 عاماً وما هي مدتها؟
- **Expected Services:** `['service_driving_license']` | **Predicted:** `['3a23c85a61499d17']`
- **Missing Facts / Numbers:** `[]` / `['8', '2']`
- **Generated Answer:** يُعدّ رسم تجديد رخصة القيادة للأشخاص الذين تجاوزوا سن 65 عاماً هو **80 دينار أردني**، وتكون مدة التجديد **سنتين** فقط، بشرط إتمام الفحص الطبي الإلزامي [1].

### Case `cond_04_vehicle_2200cc_fee` (`conditional`)
- **Question:** كم تبلغ رسوم الترخيص السنوي لمركبة خصوصية سعة محركها 2200 سي سي؟
- **Expected Services:** `['service_vehicle_license']` | **Predicted:** `['eec52fc302979ba7']`
- **Missing Facts / Numbers:** `['130 ديناراً', 'مائة وثلاثين']` / `['130']`
- **Generated Answer:** تبلغ رسوم الترخيص السنوي لمركبة خصوصية سعة محركها 2200 سي سي مبلغ 2500 دينار أردني، وذلك لأن المحركات من 1601 إلى 2001 سي سي تخضع لهذا الرسم [1].

### Case `cond_05_social_security_min_wage` (`conditional`)
- **Question:** ما هو الحد الأدنى للأجر المعتمد للاشتراك الاختياري في الضمان الاجتماعي؟
- **Expected Services:** `['service_social_security']` | **Predicted:** `['61bbf323c1d09211']`
- **Missing Facts / Numbers:** `['260 ديناراً', 'مائتان وستون']` / `['260']`
- **Generated Answer:** يُحدَّد الحد الأدنى للأجر المعتمد للاشتراك الاختياري في الضمان الاجتماعي بالحد الأدنى للأجور في المملكة، وهو 360 دينار أردني [1].

### Case `cond_06_unemployment_first_month_rate` (`conditional`)
- **Question:** كم نسبة بدل التعطل عن العمل في الشهر الأول للمؤمن عليه المتعطل؟
- **Expected Services:** `['service_social_security']` | **Predicted:** `['61bbf323c1d09211']`
- **Missing Facts / Numbers:** `['75%']` / `['75']`
- **Generated Answer:** تنص الوثيقة على أن بدل التعطل عن العمل في الشهر الأول يُصرف بنسبة 65% من متوسط أجر آخر سنة [1].

### Case `cond_08_health_insurance_exemptions` (`conditional`)
- **Question:** من هي الفئات المعفاة كلياً من رسوم الاشتراك والعلاج في التأمين الصحي المدني؟
- **Expected Services:** `['service_health_insurance']` | **Predicted:** `['e6831e56ee59122f']`
- **Missing Facts / Numbers:** `[]` / `['6', '60']`
- **Generated Answer:** الفئات المعفاة كلياً من رسوم الاشتراك والعلاج في التأمين الصحي المدني هي:

1. الأطفال دون سن عام واحد [1].
2. المواطنين فوق سن الستين عاماً غير المقتدرين معفون تلقائياً من رسوم الاشتراك والعلاج [1].
3. مرضى السرطان والمتبرعون بالأعضاء يعفون بنسبة 100% من تكاليف العلاج وإصدار البطاقة [1].

### Case `multi_02_vehicle_license_docs_and_sticker` (`multi_section`)
- **Question:** ما هي متطلبات ترخيص المركبة ورسم الملصق الإلكتروني المقرر لها؟
- **Expected Services:** `['service_vehicle_license']` | **Predicted:** `['eec52fc302979ba7']`
- **Missing Facts / Numbers:** `[]` / `['5']`
- **Generated Answer:** شروط ترخيص المركبة السنوي هي: إحضار رخصة اقتناء الأصلية المنتهية سنوات من سنة الصنع معفاة من3، وعقد تأمين إلزامي (ضد الغير) أو شامل ساري المفعول لمدة لا تقل عن سنة كاملة2، وإجتياز الفحص الفني الدوري للسلامة العامة للمركبات التي يقل عمرها عن3 سنوات، وتسديد كافة المخالفات المرورية المسجلة بحق المركبة أو السائق4.

رسم الملصق الإلكتروني هو قيمة10 دنانير5.

### Case `multi_05_family_book_marriage_deadline_fee` (`multi_section`)
- **Question:** ما هي مهلة إصدار دفتر العائلة بعد الزواج ورسم إصداره وغرامة التأخير؟
- **Expected Services:** `['service_family_book']` | **Predicted:** `['e871edb729590933']`
- **Missing Facts / Numbers:** `[]` / `['10']`
- **Generated Answer:** تبلغ مهلة إصدار دفتر العائلة لأول مرة بعد عقد الزواج 90 يوماً، ويُفرض غرامة تأخير قدرها 2 دنانير أردنية في حال انقضاء هذه المهلة دون إصدار [1]. الرسم المقرر لإصدار دفتر العائلة لأول مرة هو 4 دنانير أردنية [1].

### Case `trap_02_lost_family_book` (`disambiguation_trap`)
- **Question:** ما هو رسم استخراج بدل فاقد لدفتر العائلة؟
- **Expected Services:** `['service_family_book']` | **Predicted:** `['e871edb729590933']`
- **Missing Facts / Numbers:** `['10 دنانير', 'عشرة دنانير']` / `['10']`
- **Generated Answer:** رسم استخراج بدل فاقد لدفتر العائلة هو 3 دنانير أردنية، بشرط توقيع إقرار خطي بالفقدان، وذلك وفقاً للوثيقة المذكورة [1].

### Case `trap_03_min_age_license_vs_id` (`disambiguation_trap`)
- **Question:** ما هو السن القانوني للحصول على رخصة القيادة الخصوصية مقارنة بسن إصدار البطاقة الشخصية؟
- **Expected Services:** `['service_driving_license', 'service_smart_id']` | **Predicted:** `['58fc2563cb6e046d']`
- **Missing Facts / Numbers:** `['18 عاماً لرخصة القيادة', '16 عاماً للبطاقة الشخصية']` / `['16']`
- **Generated Answer:** يُعد سن 18 عاماً القانوني للحصول على رخصة قيادة خصوصية لأول مرة، بينما يُعد إصدار البطاقة الشخصية الذكية إلزامياً لكل مواطن أردني أتم السادسة عشرة من عمره [2][1].

### Case `trap_04_driving_renew_normal` (`disambiguation_trap`)
- **Question:** كم رسم تجديد رخصة القيادة الفئة الثالثة العادية لمدة 10 سنوات؟
- **Expected Services:** `['service_driving_license']` | **Predicted:** `['3a23c85a61499d17']`
- **Missing Facts / Numbers:** `['27 ديناراً', 'سبعة وعشرون']` / `['27']`
- **Generated Answer:** لا يمكن تجديد رخصة القيادة للفئة الثالثة لمدة 10 سنوات، حيث أن الحد الأقصى للمدة هو سنتان فقط للأشخاص الذين تجاوزوا سن الـ 65 عاماً، أو سنة واحدة للغير من هذه الفئة العمرية [1].

### Case `trap_06_building_commercial_sqm_fee` (`disambiguation_trap`)
- **Question:** ما هي رسوم ترخيص المتر المربع للأبنية التجارية لدى البلدية أو الأمانة؟
- **Expected Services:** `['service_building_permit']` | **Predicted:** `['eec52fc302979ba7']`
- **Missing Facts / Numbers:** `['8 دنانير', 'ثمانية دنانير']` / `['8']`
- **Generated Answer:** لم أجد في الوثائق المتاحة ما يحدد رسوم ترخيص المتر المربع للأبنية التجارية لدى البلدية أو الأمانة، حيث تغطي الوثيقة المذكورة فقط إجراءات ترخيص ونقل ملكية المركبات والفحص الفني [1].

### Case `comp_01_id_vs_passport_lost_fee` (`comparison`)
- **Question:** قارن بين رسم بدل الفاقد للمرة الأولى بين البطاقة الشخصية الذكية وجواز السفر؟
- **Expected Services:** `['service_smart_id', 'service_passport']` | **Predicted:** `['58fc2563cb6e046d']`
- **Missing Facts / Numbers:** `['البطاقة الشخصية 25 ديناراً', 'جواز السفر 100 دينار']` / `['25', '100']`
- **Generated Answer:** رسم بدل الفاقد للمرة الأولى لجواز السفر الأردني الدائم هو 50 دينار أردنيًا [2]. أما رسم بدل الفاقد للمرة الأولى للبطاقة الشخصية الذكية فهو 10 دنانير أردنية [1].

### Case `comp_05_passport_vs_non_conviction_validity` (`comparison`)
- **Question:** قارن بين مدة صلاحية جواز السفر للبالغين ومدة صلاحية شهادة عدم المحكومية؟
- **Expected Services:** `['service_passport', 'service_non_conviction']` | **Predicted:** `['ca0a836e8ae429ff']`
- **Missing Facts / Numbers:** `[]` / `['5']`
- **Generated Answer:** مدة صلاحية جواز السفر الأردني الدائم للبالغين (فوق 16 عاماً) هي 3 سنوات [1]. أما مدة صلاحية شهادة عدم المحكومية فهي 2 أشهر من تاريخ إصدارها [2].

### Case `colloq_03_lost_family_book` (`colloquial`)
- **Question:** ضاع مني دفتر العيلة شو الرسوم عشان اطلع بديل؟
- **Expected Services:** `['service_family_book']` | **Predicted:** `['e871edb729590933']`
- **Missing Facts / Numbers:** `['10 دنانير', 'بدل فاقد']` / `['10']`
- **Generated Answer:** يُفرض رسم قدره 5 دنانير أردنية لإصدار بدل تالف لدفتر العائلة، بشرط تسليم الدفتر التالف مع توقيع إقرار خطي بالفقدان [1].

### Case `follow_02_building_deposit` (`follow_up`)
- **Question:** وكم يبلغ التأمين المسترد له؟
- **Expected Services:** `['service_building_permit']` | **Predicted:** `['eec52fc302979ba7']`
- **Missing Facts / Numbers:** `['500 دينار']` / `['500']`
- **Generated Answer:** لم أجد في الوثائق المتاحة ما يحدد قيمة التأمين المسترد له.

### Case `follow_03_smart_id_damaged` (`follow_up`)
- **Question:** وماذا عن بدل التالف لها؟
- **Expected Services:** `['service_smart_id']` | **Predicted:** `['58fc2563cb6e046d']`
- **Missing Facts / Numbers:** `['10 دنانير']` / `['10']`
- **Generated Answer:** يُحدد رسم بدل التالف للبطاقة الشخصية الذكية بقيمة 5 دنانير أردنية، ويُطبق هذا الرسم في حال تلف البطاقة وتغييرها إلى أخرى جديدة [1].
