import json
import subprocess
import sys
from pathlib import Path

# Ensure stdout handles Arabic characters on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent
HACKATHON_DIR = BASE_DIR / "data" / "hackathon"
FIXTURES_DIR = HACKATHON_DIR / "fixtures"
SEPARATE_DIR = FIXTURES_DIR / "separate_docs"
COMBINED_DIR = FIXTURES_DIR / "combined_docs"
TEMP_DIR = BASE_DIR / "data" / "temp_html"

SEPARATE_DIR.mkdir(parents=True, exist_ok=True)
COMBINED_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

SERVICES = [
    {
        "service_id": "service_smart_id",
        "filename": "01_service_smart_id.pdf",
        "title": "دليل إصدار وتجديد وتالف البطاقة الشخصية الذكية",
        "ministry": "وزارة الداخلية | دائرة الأحوال المدنية والجوازات",
        "description": "الخدمة الرسمية لإصدار وتجديد واستبدال البطاقات الشخصية الذكية للمواطنين الأردنيين.",
        "sections": [
            {
                "heading": "أولاً: إصدار البطاقة الشخصية الذكية لأول مرة (سن 16 عاماً)",
                "content": """يعد إصدار البطاقة الشخصية الذكية إلزامياً لكل مواطن أردني أتم السادسة عشرة من عمره.
الوثائق المطلوبة:
1. شهادة الميلاد الأصلية الصادرة عن دائرة الأحوال المدنية وتحمل الرقم الوطني.
2. دفتر عائلة الوالد الأصلي مسجل فيه صاحب الطلب.
3. صورتان شخصيتان حديثتان ملونتان قياس (4×6) بخلفية بيضاء.
4. حضور ولي الأمر (الأب أو الجد لأب في حال وفاة الأب) للتعريف وإعطاء الموافقة الخطية.
5. استيفاء رسم إصدار أولي قدره (2) ديناران أردنيان للبطاقة الصادرة لأول مرة."""
            },
            {
                "heading": "ثانياً: إجراءات تجديد البطاقة الشخصية عند انتهاء الصلاحية",
                "content": """تبلغ مدة صلاحية البطاقة الشخصية الذكية (10) سنوات لمن هم فوق سن الثامنة عشرة، و(5) سنوات لمن هم دون ذلك.
متطلبات التجديد:
1. تقديم البطاقة الشخصية القديمة المنتهية الصلاحية.
2. صورتان شخصيتان حديثتان ملونتان.
3. استيفاء رسم تجديد مقداره (5) دنانير أردنية.
4. إجراء مطابقة البصمة العشرية والصورة الحيوية أمام موظف الاستقبال."""
            },
            {
                "heading": "ثالثاً: إجراءات ورسوم بدل الفاقد وبدل التالف للبطاقة الشخصية",
                "content": """في حال فقدان أو تلف البطاقة الشخصية الذكية، تتبع الإجراءات الرسمية التالية:
1. تنظيم ضبط شرطة أصولي في المركز الأمني المختص في حالة الفقدان أو السرقة.
2. الإعلان في صحيفة يومية محلية أو عبر البوابة الرقمية في حال الفقدان.
3. تسليم البطاقة التالفة في حال كان الطلب لاستبدال بطاقة تالفة.
4. استيفاء رسم بدل تالف بقيمة (10) دنانير أردنية.
5. استيفاء رسم بدل فاقد للمرة الأولى بقيمة (25) ديناراً أردنياً، وللمرة الثانية فما فوق بقيمة (50) ديناراً أردنياً."""
            },
            {
                "heading": "رابعاً: الإعفاءات الخاصة للأسر العفيفة",
                "content": """يعفى الأيتام وأبناء الأسر المنتفعة من صندوق المعونة الوطنية من رسوم الإصدار والتجديد بالكامل بموجب بطاقة معونة وطنية سارية المفعول."""
            }
        ]
    },
    {
        "service_id": "service_passport",
        "filename": "02_service_passport.pdf",
        "title": "دليل إصدار وتجديد جواز السفر الأردني الدائم",
        "ministry": "وزارة الداخلية | دائرة الأحوال المدنية والجوازات",
        "description": "دليل المعاملات الرسمية لإصدار وتجديد جوازات السفر العادية والمستعجلة.",
        "sections": [
            {
                "heading": "أولاً: شروط ومتطلبات إصدار وتجديد جواز السفر الأردني",
                "content": """يشترط لإصدار أو تجديد جواز السفر الأردني الدائم ما يلي:
1. إبراز البطاقة الشخصية الذكية الأصلية وسارية المفعول.
2. صورتان شخصيتان حديثتان ملونتان قياس (4×6) بخلفية بيضاء.
3. موافقة خطية من ولي الأمر لمن هم دون سن (18) عاماً.
4. إبراز دفتر خدمة العلم مؤجلاً أو شهادة إنهاء الخدمة للذكور المكلفين.
5. جواز السفر القديم المنتهي في حال معاملة التجديد."""
            },
            {
                "heading": "ثانياً: جدول الرسوم المقررة والخدمة المستعجلة",
                "content": """تستوفى رسوم جواز السفر الأردني وفق اللائحة الرسمية التالية:
1. رسم إصدار وتجديد جواز السفر العادي داخل المملكة لمن أتم 16 عاماً فما فوق: (50) ديناراً أردنياً.
2. رسم إصدار وتجديد عادي لمن هم دون 16 عاماً: (25) ديناراً أردنياً.
3. رسم إصدار جواز سفر مستعجل (خدمة VIP خلال ساعة واحدة): (100) دينار أردني.
4. رسم بدل فاقد لجواز السفر للمرة الأولى: (100) دينار أردني، وللمرة الثانية فما فوق: (200) دينار أردني."""
            },
            {
                "heading": "ثالثاً: مدة الصلاحية والضوابط القانونية",
                "content": """تبلغ مدة صلاحية جواز السفر (5) سنوات لمن هم فوق 16 عاماً، و(3) سنوات لمن هم دون ذلك.
لا يجوز تجديد جواز السفر إذا كانت المدة المتبقية في صلاحيته تزيد عن سنة واحدة إلا بموافقة المدير العام أو لأسباب تأشيرة سفر مثبتة."""
            }
        ]
    },
    {
        "service_id": "service_family_book",
        "filename": "03_service_family_book.pdf",
        "title": "دليل إصدار وتجديد وتعديل دفتر العائلة",
        "ministry": "وزارة الداخلية | دائرة الأحوال المدنية والجوازات",
        "description": "إصدار وتحديث سجل الأسرة ودفتر العائلة الرسمي وتثبيت واقعات الولادة والزواج.",
        "sections": [
            {
                "heading": "أولاً: إصدار دفتر العائلة لأول مرة عند الزواج",
                "content": """يلزم كل رب أسرة أردني بفتح سجل أسرة وإصدار دفتر عائلة خلال مهلة أقصاها (90) يوماً من تاريخ عقد الزواج.
الوثائق المطلوبة:
1. عقد الزواج الأصلي مصدق من المحكمة الشرعية أو الكنسية المختصة.
2. البطاقات الشخصية الذكية للزوج والزوجة.
3. صورتان شخصيتان حديثتان لرب الأسرة (الزوج).
4. رسم إصدار دفتر العائلة لأول مرة: (2) ديناران أردنيان. يفرض غرامة تأخير قدرها (10) دنانير في حال انقضاء مهلة 90 يوماً دون إصدار."""
            },
            {
                "heading": "ثانياً: تعديل الدفتر وإضافة المواليد الجدد وبدل الفاقد",
                "content": """تستوفى الرسوم المقررة لتعديلات دفتر العائلة كالتالي:
1. إضافة مولود جديد أو تعديل الواقعات: رسم قدره (1) دينار واحد بموجب شهادة ولادة رسمية.
2. إصدار بدل تالف لدفتر العائلة: رسم قدره (5) دنانير أردنية مع تسليم الدفتر التالف.
3. إصدار بدل فاقد لدفتر العائلة: رسم قدره (10) دنانير أردنية بعد توقيع إقرار خطي بالفقدان."""
            }
        ]
    },
    {
        "service_id": "service_vehicle_license",
        "filename": "04_service_vehicle_license.pdf",
        "title": "دليل إجراءات ترخيص ونقل ملكية المركبات والفحص الفني 2026",
        "ministry": "مديرية الأمن العام | إدارة ترخيص السواقين والمركبات",
        "description": "إجراءات ترخيص المركبات الدورية، نقل الملكية، ورسوم الفحص الفني والملصق الإلكتروني.",
        "sections": [
            {
                "heading": "أولاً: متطلبات الفحص الفني والترخيص السنوي للمركبات",
                "content": """يشترط للترخيص السنوي للمركبات:
1. إحضار رخصة اقتناء المركبة الأصلية المنتهية.
2. عقد تأمين إلزامي (ضد الغير) أو شامل ساري المفعول لمدة لا تقل عن سنة كاملة.
3. اجتياز الفحص الفني الدوري للسلامة العامة (المركبات التي يقل عمرها عن 3 سنوات من سنة الصنع معفاة من الفحص الفني).
4. تسديد كافة المخالفات المرورية المسجلة بحق المركبة أو السائق."""
            },
            {
                "heading": "ثانياً: جدول الرسوم السنوية المقررة لترخيص المركبات",
                "content": """تستوفى الرسوم السنوية لترخيص المركبات الخصوصية وفق سعة المحرك:
1. المحركات حتى 1600 سي سي: رسم سنوي قدره (45) ديناراً أردنياً.
2. المحركات من 1601 سي سي حتى 2000 سي سي: رسم سنوي قدره (65) ديناراً أردنياً.
3. المحركات من 2001 سي سي حتى 2500 سي سي: رسم سنوي قدره (130) ديناراً أردنياً.
4. المركبات الكهربائية بالكامل: رسم سنوي موحد قدره (50) ديناراً أردنياً.
5. يضاف رسم فحص فني مقداره (10) دنانير، ورسم ملصق إلكتروني بقيمة (5) دنانير."""
            },
            {
                "heading": "ثالثاً: شروط وإجراءات نقل ملكية المركبة (التنازل والبيع)",
                "content": """لنقل الملكية بين البائع والمشتري:
1. حضور البائع والمشتري شخصياً أمام مأمور تسجيل المركبات مع البطاقة الشخصية الذكية سارية المفعول لكل منهما.
2. أن تكون رخصة المركبة سارية لمدة شهر على الأقل.
3. براءة ذمة من المخالفات المرورية والمسقفات البلدية.
4. استيفاء رسم نقل الملكية القانوني بنسبة (1%) من القيمة التقديرية للمركبة."""
            },
            {
                "heading": "رابعاً: الإعفاءات الخاصة بالأشخاص ذوي الإعاقة",
                "content": """يمنح الأشخاص ذوو الإعاقة الحركية إعفاءً لمركبة واحدة مجهزة طبياً من رسوم التسجيل والترخيص السنوي ونقل الملكية بالكامل بموجب قرار اللجنة الطبية المشتركة."""
            }
        ]
    },
    {
        "service_id": "service_driving_license",
        "filename": "05_service_driving_license.pdf",
        "title": "دليل إصدار وتجديد رخص القيادة للمركبات بمختلف الفئات",
        "ministry": "مديرية الأمن العام | إدارة ترخيص السواقين والمركبات",
        "description": "إجراءات ومتطلبات الحصول على رخص القيادة وتجديدها والفحوصات النظرية والعملية.",
        "sections": [
            {
                "heading": "أولاً: شروط إصدار رخصة القيادة لأول مرة (الفئة الثالثة - خصوصي)",
                "content": """شروط الحصول على رخصة قيادة خصوصية لأول مرة:
1. إتمام سن (18) عاماً كاملة.
2. اجتياز الفحص الطبي المعتمد للنظر والياقة البدنية (رسم الفحص الطبي: 5 دنانير).
3. إتمام دورة تدريبية عملية ونظرية لا تقل عن (40) ساعة في مركز تدريب معتمد.
4. اجتياز الفحص النظري (رسمه: 10 دنانير).
5. اجتياز الفحص العملي الميداني (رسمه: 15 ديناراً).
6. استيفاء رسم إصدار الرخصة لأول مرة بعد النجاح بقيمة (36) ديناراً أردنياً."""
            },
            {
                "heading": "ثانياً: تجديد رخصة القيادة والمدد القانونية",
                "content": """تجدد رخصة القيادة وفق المعايير التالية:
1. تجديد رخصة الفئة الثالثة لمدة (10) سنوات برسم مقداره (27) ديناراً أردنياً.
2. الأشخاص الذين تجاوزوا سن (65) عاماً: تجدد رخصتهم لمدة (سنتين) فقط وبرسم قدره (8) دنانير مع شرط الفحص الطبي الإلزامي.
3. رسم بدل فاقد أو تالف لرخصة القيادة: (15) ديناراً أردنياً."""
            }
        ]
    },
    {
        "service_id": "service_building_permit",
        "filename": "06_service_building_permit.pdf",
        "title": "دليل تعليمات واشتراطات ترخيص الأبنية والمنشآت وإذن الإشغال 2026",
        "ministry": "أمانة عمان الكبرى | وزارة الإدارة المحلية",
        "description": "اشتراطات ترخيص الإنشاءات، الارتدادات القانونية، والرسوم الهندسية والبلدية.",
        "sections": [
            {
                "heading": "المادة 1: المخططات الهندسية والموافقات المسبقة",
                "content": """لا يجوز الشروع في أي أعمال بناء قبل الحصول على ترخيص بناء مصدق.
الوثائق المطلوبة:
1. مخطط موقع وترسيم حديث لا يتجاوز 3 أشهر.
2. سند تسجيل ملكية حديث (إخراج قيد) خالٍ من الحجوزات.
3. مخططات هندسية تنفيذية مصدقة ومختومة من نقابة المهندسين الأردنيين.
4. موافقة مديرية الدفاع المدني على اشتراطات الوقاية والسلامة ومكافحة الحريق."""
            },
            {
                "heading": "المادة 2: الارتدادات والنسب المئوية للبناء (تعديل 2026)",
                "content": """بموجب تعليمات تنظيم الأبنية لعام 2026:
- في سكن (أ): الارتداد الأمامي لا يقل عن (5) أمتار، والجانبي والخلفي لا يقل عن (4) أمتار، والنسبة المئوية القصوى للبناء هي (45%).
- في سكن (ب): الارتداد الأمامي لا يقل عن (4) أمتار، والجانبي والخلفي لا يقل عن (3) أمتار، والنسبة المئوية القصوى للبناء هي (50%).
- ملحق السطح (الروف): يسمح ببناء ملحق سطح بمساحة لا تتجاوز (20%) من مساحة السطح وبدون اشتراط موافقة الجيران وفق نظام 2026 المحدث شريطة عدم تجاوز الارتفاع المقرر."""
            },
            {
                "heading": "المادة 3: الرسوم البلدية والتأمينات الهندسية",
                "content": """تستوفى الرسوم كالتالي:
1. رسم ترخيص البناء السكني: (3) دنانير أردنية لكل متر مربع مرخص.
2. رسم ترخيص البناء التجاري: (8) دنانير أردنية لكل متر مربع مرخص.
3. تأمين حسن تنفيذ وإزالة طمم: (500) دينار للأبنية السكنية، و(1500) دينار للأبنية التجارية، يسترد بالكامل بعد صدور إذن الإشغال المعتمد."""
            }
        ]
    },
    {
        "service_id": "service_non_conviction",
        "filename": "07_service_non_conviction.pdf",
        "title": "دليل إصدار شهادة عدم المحكومية الإلكترونية",
        "ministry": "وزارة العدل | المملكة الأردنية الهاشمية",
        "description": "إجراءات طلب واستخراج شهادة عدم المحكومية الرقمية عبر المنصة الموحدة وتطبيق سند.",
        "sections": [
            {
                "heading": "أولاً: الوثائق والشروط للحصول على شهادة عدم المحكومية",
                "content": """شروط استخراج الشهادة:
1. توفر الرقم الوطني للأردنيين، أو رقم جواز السفر لغير الأردنيين المقيمين.
2. عدم وجود أسبقيات جزائية أو قضايا معلقة أمام المحاكم الجزائية ما لم يرد اعتباره بحكم قضائي.
3. تقديم الطلب إلكترونياً بالكامل عبر بوابة وزارة العدل الإلكترونية أو تطبيق (سند)."""
            },
            {
                "heading": "ثانياً: جدول الرسوم وطرق الدفع الإلكتروني",
                "content": """تستوفى الرسوم إلكترونياً عبر خدمة إي فواتيركم (eFAWATEERcom):
1. رسم إصدار شهادة عدم المحكومية باللغة العربية: (5) دنانير أردنية.
2. رسم إصدار شهادة عدم المحكومية باللغة الإنجليزية: (7) دنانير أردنية."""
            },
            {
                "heading": "ثالثاً: مدة الصلاحية وزمن الإنجاز",
                "content": """1. تصدر الشهادة إلكترونياً خلال زمن قياسي يتراوح بين (15) دقيقة إلى ساعتين كحد أقصى.
2. تبلغ مدة صلاحية شهادة عدم المحكومية (3) أشهر من تاريخ إصدارها، وتزود برمز QR للتحقق الرسمي من صحتها دون الحاجة لأي تصديق يدوي."""
            }
        ]
    },
    {
        "service_id": "service_business_license",
        "filename": "08_service_business_license.pdf",
        "title": "دليل إصدار وتجديد رخص المهن التجارية والصناعية",
        "ministry": "أمانة عمان الكبرى | وزارة الصناعة والتجارة والتموين",
        "description": "ترخيص المحال التجارية والمؤسسات الفردية والصناعية وجداول الرسوم والغرامات السنوية.",
        "sections": [
            {
                "heading": "أولاً: متطلبات إصدار رخصة المهن لأول مرة",
                "content": """الوثائق المطلوبة لترخيص المهن:
1. شهادة تسجيل تجاري سارية المفعول صادرة عن وزارة الصناعة والتجارة.
2. عقد إيجار مصدق من البلدية أو سند ملكية المحل التجاري.
3. إذن إشغال ساري المفعول للمبنى التجاري.
4. موافقة الدفاع المدني للمنشآت والمحال التي تتجاوز مساحتها (150) متراً مربعاً."""
            },
            {
                "heading": "ثانياً: جدول الرسوم السنوية والغرامات المقررة",
                "content": """الرسوم المقررة لرخص المهن:
1. رسم تفتيش ومعاينة موقعية: (20) ديناراً تدفع لمرة واحدة عند التأسيس.
2. رسم لوحة إعلانية تجارية: (15) ديناراً لكل متر مربع من مساحة اللوحة سنوياً.
3. رسم جمع النفايات والخدمات البيئية: (50) ديناراً للمهن التجارية العادية، و(200) دينار للمهن الصناعية والورش الحرفية.
4. غرامات التأخير: يجب تجديد الرخصة قبل نهاية شهر آذار (31 مارس) سنوياً، وتفرض غرامة تأخير بنسبة (20%) في حال التأخير حتى نهاية حزيران، وتصبح (50%) بعد ذلك التاريخ."""
            },
            {
                "heading": "ثالثاً: إعفاءات المهن المنزلية والمشاريع الناشئة",
                "content": """تعفى المهن المنزلية الفكرية والحرف اليدوية المسجلة رسمياً من رسوم جمع النفايات ورسوم اللافتات الإعلانية بنسبة (100%) خلال أول سنتين من الترخيص دعماً للمشاريع الناشئة."""
            }
        ]
    },
    {
        "service_id": "service_social_security",
        "filename": "09_service_social_security.pdf",
        "title": "دليل الاشتراك الاختياري وصرف بدل التعطل عن العمل",
        "ministry": "المؤسسة العامة للضمان الاجتماعي | المملكة الأردنية الهاشمية",
        "description": "قواعد الشمول الاختياري، نسب الاقتطاع، وبدلات التعطل عن العمل ومكافآت نهاية الخدمة.",
        "sections": [
            {
                "heading": "أولاً: شروط الاشتراك الاختياري بالضمان الاجتماعي ونسب الاقتطاع",
                "content": """شروط الاشتراك الاختياري:
1. يحق لأي مواطن أردني غير مشمول بالضمان الإلزامي الاشتراك اختيارياً.
2. يشترط ألا يكون قد أكمل سن (60) عاماً للذكور أو سن (55) عاماً للإناث عند تقديم الطلب.
3. الحد الأدنى للأجر المعتمد للاشتراك هو الحد الأدنى للأجور في المملكة والبالغ (260) ديناراً أردنياً.
4. نسبة الاقتطاع الشهري للاشتراك الاختياري هي (17.5%) من الأجر المعتمد."""
            },
            {
                "heading": "ثانياً: شروط ونسب صرف بدل التعطل عن العمل",
                "content": """شروط صرف بدل التعطل:
1. أن يتوفر للمؤمن عليه ما لا يقل عن (36) اشتراكاً فعلياً في الضمان الاجتماعي قبل تاريخ التعطل.
2. يصرف البدل لعدد لا يتجاوز (3) أشهر خلال الدورة التأمينية الواحدة.
3. تصرف البدلات بالنسب التالية من متوسط أجر آخر سنة: الشهر الأول بنسبة (75%)، الشهر الثاني بنسبة (65%)، والشهر الثالث بنسبة (55%)."""
            },
            {
                "heading": "ثالثاً: صرف تعويض الدفعة الواحدة للمؤمن عليهم",
                "content": """يجوز صرف تعويض الدفعة الواحدة عند بلوغ سن الشيخوخة لمن لم يستكمل مدة التقاعد (15 سنة) بنسبة (15%) من متوسط الأجور لسنوات الاشتراك."""
            }
        ]
    },
    {
        "service_id": "service_health_insurance",
        "filename": "10_service_health_insurance.pdf",
        "title": "دليل إصدار وتجديد بطاقة التأمين الصحي المدني",
        "ministry": "وزارة الصحة | مديرية التأمين الصحي والخدمات الطبية",
        "description": "قواعد إصدار وتجديد بطاقات التأمين الصحي الحكومي، الفئات المعفاة، والرسوم السنوية.",
        "sections": [
            {
                "heading": "أولاً: الفئات المشمولة والوثائق المطلوبة للتأمين الصحي",
                "content": """الفئات المشمولة: موظفو ومتقاعدو الجهاز الحكومي والمدني والمواطنون المشتركون اختيارياً.
الوثائق المطلوبة:
1. البطاقة الشخصية الذكية الأصلية.
2. دفتر العائلة الأصلي مسجل فيه أفراد الأسرة.
3. صورتان شخصيتان لكل فرد من أفراد الأسرة.
4. كتاب عدم تقاضي راتب تقاعدي أو إثبات دخل لطالبي الاشتراك الاختياري."""
            },
            {
                "heading": "ثانياً: الرسوم والاشتراكات المقررة للتأمين الصحي",
                "content": """الرسوم والاشتراكات:
1. يقتطع رسم اشتراك سنوي قدره (3%) من الراتب الإجمالي لموظفي القطاع العام.
2. رسم الاشتراك الاختياري للمواطنين غير المشمولين: (75) ديناراً سنوياً للفرد، أو (150) ديناراً للأسرة كاملة.
3. رسم إصدار البطاقة البلاستيكية: (3) دنانير أردنية.
4. رسم بدل فاقد أو تالف لبطاقة التأمين: (10) دنانير أردنية."""
            },
            {
                "heading": "ثالثاً: الفئات المعفاة كلياً من رسوم التأمين الصحي والعلاج",
                "content": """يعفى من رسوم التأمين الصحي كلياً:
1. الأطفال دون سن (6) سنوات معفون بالكامل من كافة الرسوم بموجب المكرمة الملكية السامية.
2. المواطنون فوق سن (60) عاماً غير المقتدرين معفون تلقائياً من رسوم الاشتراك والعلاج.
3. مرضى السرطان والمتبرعون بالأعضاء يعفون بنسبة (100%) من تكاليف العلاج وإصدار البطاقة."""
            }
        ]
    }
]


def render_html_page(title, ministry, description, sections):
    sec_html = ""
    for s in sections:
        body = s["content"].strip().replace("\n", "<br>")
        sec_html += f"""
        <div class="section-box">
            <h2>{s['heading']}</h2>
            <div class="content">{body}</div>
        </div>
        """
    return f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="utf-8">
<style>
@page {{
    size: A4;
    margin: 18mm;
}}
body {{
    font-family: 'Segoe UI', Tahoma, Arial, sans-serif;
    direction: rtl;
    text-align: right;
    color: #0F172A;
    line-height: 1.8;
}}
.header {{
    border-bottom: 3px solid #002D62;
    padding-bottom: 12px;
    margin-bottom: 18px;
}}
h1 {{
    color: #002D62;
    font-size: 17pt;
    margin: 0 0 4px 0;
}}
.ministry {{
    color: #475569;
    font-size: 11pt;
    font-weight: 700;
}}
.badge {{
    display: inline-block;
    background: #EFF6FF;
    color: #002D62;
    border: 1px solid #BFDBFE;
    padding: 3px 10px;
    border-radius: 4px;
    font-size: 9pt;
    font-weight: 800;
    margin-top: 6px;
}}
.desc {{
    font-size: 10pt;
    color: #334155;
    margin-top: 6px;
}}
.section-box {{
    margin-bottom: 18px;
    border-right: 4px solid #002D62;
    padding-right: 12px;
}}
h2 {{
    color: #002D62;
    font-size: 12.5pt;
    margin: 0 0 6px 0;
}}
.content {{
    font-size: 10.5pt;
    color: #1E293B;
}}
.footer {{
    margin-top: 25px;
    border-top: 1px solid #CBD5E1;
    padding-top: 8px;
    font-size: 9pt;
    color: #64748B;
    text-align: center;
}}
</style>
</head>
<body>
<div class="header">
    <h1>{title}</h1>
    <div class="ministry">{ministry}</div>
    <div class="badge">وثيقة حكومية رسمية معتمدة | دليل خدمات المملكة الأردنية الهاشمية 2026</div>
    <div class="desc">{description}</div>
</div>
{sec_html}
<div class="footer">
    المملكة الأردنية الهاشمية - بوابة الحكومة الرقمية الموحدة (سند) - وثائق رسمية للاختبار والتقييم 2026
</div>
</body>
</html>"""


def generate_pdfs():
    print("[1/3] Generating 10 individual service PDFs in data/hackathon/fixtures/separate_docs...")
    for svc in SERVICES:
        out_pdf = SEPARATE_DIR / svc["filename"]
        tmp_html = TEMP_DIR / f"{svc['service_id']}.html"
        html_code = render_html_page(svc["title"], svc["ministry"], svc["description"], svc["sections"])
        tmp_html.write_text(html_code, encoding="utf-8")

        subprocess.run(
            [EDGE_PATH, "--headless", "--disable-gpu", f"--print-to-pdf={out_pdf}", f"file:///{tmp_html.as_posix()}"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print(f"  + Generated separate doc: {svc['filename']} ({out_pdf.stat().st_size} bytes)")

    print("\n[2/3] Generating 1 combined multi-service PDF in data/hackathon/fixtures/combined_docs...")
    combined_pdf = COMBINED_DIR / "دليل_الخدمات_الحكومية_الموحد_2026.pdf"
    combined_html_path = TEMP_DIR / "combined_services.html"

    # Merge all services separated by page-break
    pages_html = []
    for idx, svc in enumerate(SERVICES, start=1):
        sec_blocks = ""
        for s in svc["sections"]:
            body = s["content"].strip().replace("\n", "<br>")
            sec_blocks += f"""
            <div class="section-box">
                <h2>{s['heading']}</h2>
                <div class="content">{body}</div>
            </div>
            """
        page_html = f"""
        <div class="service-page" style="page-break-after: always; padding-bottom: 20px;">
            <div class="header">
                <div style="font-size:10pt; color:#64748B; font-weight:bold;">الخدمة رقم {idx} من 10</div>
                <h1>{svc['title']}</h1>
                <div class="ministry">{svc['ministry']}</div>
                <div class="badge">دليل الخدمات الحكومية الموحد 2026</div>
            </div>
            {sec_blocks}
        </div>
        """
        pages_html.append(page_html)

    combined_full_html = f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="utf-8">
<style>
@page {{
    size: A4;
    margin: 18mm;
}}
body {{
    font-family: 'Segoe UI', Tahoma, Arial, sans-serif;
    direction: rtl;
    text-align: right;
    color: #0F172A;
    line-height: 1.8;
}}
.header {{
    border-bottom: 3px solid #002D62;
    padding-bottom: 12px;
    margin-bottom: 18px;
}}
h1 {{
    color: #002D62;
    font-size: 16pt;
    margin: 0 0 4px 0;
}}
.ministry {{
    color: #475569;
    font-size: 11pt;
    font-weight: 700;
}}
.badge {{
    display: inline-block;
    background: #EFF6FF;
    color: #002D62;
    border: 1px solid #BFDBFE;
    padding: 3px 10px;
    border-radius: 4px;
    font-size: 9pt;
    font-weight: 800;
    margin-top: 6px;
}}
.section-box {{
    margin-bottom: 16px;
    border-right: 4px solid #002D62;
    padding-right: 12px;
}}
h2 {{
    color: #002D62;
    font-size: 12pt;
    margin: 0 0 6px 0;
}}
.content {{
    font-size: 10pt;
    color: #1E293B;
}}
</style>
</head>
<body>
{''.join(pages_html)}
</body>
</html>"""

    combined_html_path.write_text(combined_full_html, encoding="utf-8")
    subprocess.run(
        [EDGE_PATH, "--headless", "--disable-gpu", f"--print-to-pdf={combined_pdf}", f"file:///{combined_html_path.as_posix()}"],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print(f"  + Generated combined doc: {combined_pdf.name} ({combined_pdf.stat().st_size} bytes)")


def generate_eval_cases():
    print("\n[3/3] Generating 50 gold synthetic evaluation cases in data/hackathon/eval_cases.jsonl...")
    cases = [
        # --- 12 Direct Facts ---
        {
            "id": "direct_01_smart_id_first_fee",
            "category": "direct_fact",
            "question": "كم رسم إصدار البطاقة الشخصية الذكية لأول مرة؟",
            "expected_service_ids": ["service_smart_id"],
            "required_evidence_section_ids": ["fee", "procedure"],
            "answer_facts": ["ديناران", "2"],
            "numeric_values": ["2"],
            "must_abstain": False,
        },
        {
            "id": "direct_02_smart_id_renew_fee",
            "category": "direct_fact",
            "question": "ما هي رسوم تجديد البطاقة الشخصية الذكية المنتهية؟",
            "expected_service_ids": ["service_smart_id"],
            "required_evidence_section_ids": ["fee"],
            "answer_facts": ["5 دنانير", "خمسة دنانير"],
            "numeric_values": ["5"],
            "must_abstain": False,
        },
        {
            "id": "direct_03_passport_adult_fee",
            "category": "direct_fact",
            "question": "كم تبلغ رسوم إصدار وتجديد جواز السفر العادي لمن هم فوق سن 16 عاماً؟",
            "expected_service_ids": ["service_passport"],
            "required_evidence_section_ids": ["fee"],
            "answer_facts": ["50", "خمسين ديناراً"],
            "numeric_values": ["50"],
            "must_abstain": False,
        },
        {
            "id": "direct_04_passport_minor_validity",
            "category": "direct_fact",
            "question": "كم مدة صلاحية جواز السفر للأشخاص دون سن 16 عاماً؟",
            "expected_service_ids": ["service_passport"],
            "required_evidence_section_ids": ["procedure"],
            "answer_facts": ["3 سنوات", "ثلاث سنوات"],
            "numeric_values": ["3"],
            "must_abstain": False,
        },
        {
            "id": "direct_05_family_book_newborn_fee",
            "category": "direct_fact",
            "question": "كم رسم إضافة مولود جديد في دفتر العائلة؟",
            "expected_service_ids": ["service_family_book"],
            "required_evidence_section_ids": ["fee"],
            "answer_facts": ["دينار واحد", "1"],
            "numeric_values": ["1"],
            "must_abstain": False,
        },
        {
            "id": "direct_06_vehicle_inspection_fee",
            "category": "direct_fact",
            "question": "ما هو رسم الفحص الفني لترخيص المركبة في إدارة الترخيص؟",
            "expected_service_ids": ["service_vehicle_license"],
            "required_evidence_section_ids": ["fee"],
            "answer_facts": ["10 دنانير", "عشرة دنانير"],
            "numeric_values": ["10"],
            "must_abstain": False,
        },
        {
            "id": "direct_07_vehicle_electric_fee",
            "category": "direct_fact",
            "question": "كم رسم الترخيص السنوي للمركبات الكهربائية بالكامل؟",
            "expected_service_ids": ["service_vehicle_license"],
            "required_evidence_section_ids": ["fee"],
            "answer_facts": ["50 ديناراً", "خمسين دينار"],
            "numeric_values": ["50"],
            "must_abstain": False,
        },
        {
            "id": "direct_08_driving_first_license_fee",
            "category": "direct_fact",
            "question": "كم رسم إصدار رخصة القيادة الفئة الثالثة لأول مرة بعد اجتياز الفحص؟",
            "expected_service_ids": ["service_driving_license"],
            "required_evidence_section_ids": ["fee"],
            "answer_facts": ["36 ديناراً", "ستة وثلاثون"],
            "numeric_values": ["36"],
            "must_abstain": False,
        },
        {
            "id": "direct_09_building_residential_sqm_fee",
            "category": "direct_fact",
            "question": "كم رسم ترخيص المتر المربع للأبنية السكنية؟",
            "expected_service_ids": ["service_building_permit"],
            "required_evidence_section_ids": ["fee"],
            "answer_facts": ["3 دنانير", "ثلاثة دنانير"],
            "numeric_values": ["3"],
            "must_abstain": False,
        },
        {
            "id": "direct_10_non_conviction_arabic_fee",
            "category": "direct_fact",
            "question": "ما هي رسوم إصدار شهادة عدم المحكومية باللغة العربية؟",
            "expected_service_ids": ["service_non_conviction"],
            "required_evidence_section_ids": ["fee"],
            "answer_facts": ["5 دنانير", "خمسة دنانير"],
            "numeric_values": ["5"],
            "must_abstain": False,
        },
        {
            "id": "direct_11_social_security_optional_rate",
            "category": "direct_fact",
            "question": "ما هي نسبة الاقتطاع الشهري للاشتراك الاختياري في الضمان الاجتماعي؟",
            "expected_service_ids": ["service_social_security"],
            "required_evidence_section_ids": ["fee"],
            "answer_facts": ["17.5%"],
            "numeric_values": ["17.5"],
            "must_abstain": False,
        },
        {
            "id": "direct_12_health_insurance_card_fee",
            "category": "direct_fact",
            "question": "كم رسم إصدار بطاقة التأمين الصحي المدني البلاستيكية؟",
            "expected_service_ids": ["service_health_insurance"],
            "required_evidence_section_ids": ["fee"],
            "answer_facts": ["3 دنانير", "ثلاثة دنانير"],
            "numeric_values": ["3"],
            "must_abstain": False,
        },

        # --- 8 Conditional Questions ---
        {
            "id": "cond_01_smart_id_second_loss",
            "category": "conditional",
            "question": "كم رسوم بدل فاقد للبطاقة الشخصية الذكية للمرة الثانية فما فوق؟",
            "expected_service_ids": ["service_smart_id"],
            "required_evidence_section_ids": ["fee"],
            "answer_facts": ["50 ديناراً", "خمسين دينار"],
            "numeric_values": ["50"],
            "must_abstain": False,
        },
        {
            "id": "cond_02_passport_vip_urgent",
            "category": "conditional",
            "question": "كم رسوم إصدار جواز السفر المستعجل خلال ساعة واحدة خدمة VIP؟",
            "expected_service_ids": ["service_passport"],
            "required_evidence_section_ids": ["fee"],
            "answer_facts": ["100 دينار", "مائة دينار"],
            "numeric_values": ["100"],
            "must_abstain": False,
        },
        {
            "id": "cond_03_driving_senior_citizens",
            "category": "conditional",
            "question": "كم رسوم تجديد رخصة القيادة لمن تجاوزوا سن 65 عاماً وما هي مدتها؟",
            "expected_service_ids": ["service_driving_license"],
            "required_evidence_section_ids": ["fee", "procedure"],
            "answer_facts": ["8 دنانير", "سنتين", "2"],
            "numeric_values": ["8", "2"],
            "must_abstain": False,
        },
        {
            "id": "cond_04_vehicle_2200cc_fee",
            "category": "conditional",
            "question": "كم تبلغ رسوم الترخيص السنوي لمركبة خصوصية سعة محركها 2200 سي سي؟",
            "expected_service_ids": ["service_vehicle_license"],
            "required_evidence_section_ids": ["fee"],
            "answer_facts": ["130 ديناراً", "مائة وثلاثين"],
            "numeric_values": ["130"],
            "must_abstain": False,
        },
        {
            "id": "cond_05_social_security_min_wage",
            "category": "conditional",
            "question": "ما هو الحد الأدنى للأجر المعتمد للاشتراك الاختياري في الضمان الاجتماعي؟",
            "expected_service_ids": ["service_social_security"],
            "required_evidence_section_ids": ["condition"],
            "answer_facts": ["260 ديناراً", "مائتان وستون"],
            "numeric_values": ["260"],
            "must_abstain": False,
        },
        {
            "id": "cond_06_unemployment_first_month_rate",
            "category": "conditional",
            "question": "كم نسبة بدل التعطل عن العمل في الشهر الأول للمؤمن عليه المتعطل؟",
            "expected_service_ids": ["service_social_security"],
            "required_evidence_section_ids": ["condition"],
            "answer_facts": ["75%"],
            "numeric_values": ["75"],
            "must_abstain": False,
        },
        {
            "id": "cond_07_vehicle_new_exemption",
            "category": "conditional",
            "question": "هل تخضع المركبات الجديدة كلياً للفحص الفني الدوري عند ترخيصها السنوي؟",
            "expected_service_ids": ["service_vehicle_license"],
            "required_evidence_section_ids": ["procedure", "exception"],
            "answer_facts": ["معفاة", "3 سنوات", "يقل عمرها عن 3 سنوات"],
            "numeric_values": ["3"],
            "must_abstain": False,
        },
        {
            "id": "cond_08_health_insurance_exemptions",
            "category": "conditional",
            "question": "من هي الفئات المعفاة كلياً من رسوم الاشتراك والعلاج في التأمين الصحي المدني؟",
            "expected_service_ids": ["service_health_insurance"],
            "required_evidence_section_ids": ["exception"],
            "answer_facts": ["دون سن 6 سنوات", "فوق سن 60", "مرضى السرطان", "المتبرعون بالأعضاء"],
            "numeric_values": ["6", "60"],
            "must_abstain": False,
        },

        # --- 8 Multi-Section Questions ---
        {
            "id": "multi_01_smart_id_docs_and_fee",
            "category": "multi_section",
            "question": "ما هي الوثائق المطلوبة ورسم الإصدار لأول مرة للبطاقة الشخصية الذكية؟",
            "expected_service_ids": ["service_smart_id"],
            "required_evidence_section_ids": ["requirement", "fee"],
            "answer_facts": ["شهادة الميلاد الأصلية", "دفتر عائلة", "صورتان", "حضور ولي الأمر", "ديناران"],
            "numeric_values": ["2"],
            "must_abstain": False,
        },
        {
            "id": "multi_02_vehicle_license_docs_and_sticker",
            "category": "multi_section",
            "question": "ما هي متطلبات ترخيص المركبة ورسم الملصق الإلكتروني المقرر لها؟",
            "expected_service_ids": ["service_vehicle_license"],
            "required_evidence_section_ids": ["requirement", "fee"],
            "answer_facts": ["رخصة المركبة", "تأمين", "فحص فني", "المخالفات", "5 دنانير"],
            "numeric_values": ["5"],
            "must_abstain": False,
        },
        {
            "id": "multi_03_driving_license_exam_fees_and_hours",
            "category": "multi_section",
            "question": "كم عدد ساعات الدورة التدريبية المطلوبة لرخصة القيادة ورسوم الفحص النظري والعملي؟",
            "expected_service_ids": ["service_driving_license"],
            "required_evidence_section_ids": ["requirement", "fee"],
            "answer_facts": ["40 ساعة", "الفحص النظري 10", "الفحص العملي 15"],
            "numeric_values": ["40", "10", "15"],
            "must_abstain": False,
        },
        {
            "id": "multi_04_building_permit_docs_and_deposit",
            "category": "multi_section",
            "question": "ما هي وثائق ترخيص البناء وقيمة تأمين حسن التنفيذ للأبنية السكنية؟",
            "expected_service_ids": ["service_building_permit"],
            "required_evidence_section_ids": ["requirement", "fee"],
            "answer_facts": ["مخطط موقع وترسيم", "إخراج قيد", "مخططات هندسية", "الدفاع المدني", "500 دينار"],
            "numeric_values": ["500"],
            "must_abstain": False,
        },
        {
            "id": "multi_05_family_book_marriage_deadline_fee",
            "category": "multi_section",
            "question": "ما هي مهلة إصدار دفتر العائلة بعد الزواج ورسم إصداره وغرامة التأخير؟",
            "expected_service_ids": ["service_family_book"],
            "required_evidence_section_ids": ["procedure", "fee"],
            "answer_facts": ["90 يوماً", "ديناران", "غرامة تأخير 10 دنانير"],
            "numeric_values": ["90", "2", "10"],
            "must_abstain": False,
        },
        {
            "id": "multi_06_social_security_age_and_rate",
            "category": "multi_section",
            "question": "ما هو الحد الأقصى للعمر للتقديم على الاشتراك الاختياري في الضمان وما هي نسبة الاقتطاع؟",
            "expected_service_ids": ["service_social_security"],
            "required_evidence_section_ids": ["condition", "fee"],
            "answer_facts": ["60 للذكور", "55 للإناث", "17.5%"],
            "numeric_values": ["60", "55", "17.5"],
            "must_abstain": False,
        },
        {
            "id": "multi_07_business_license_docs_and_inspection",
            "category": "multi_section",
            "question": "ما هي شروط ترخيص المهن لأول مرة وما هو رسم التفتيش الموقعي؟",
            "expected_service_ids": ["service_business_license"],
            "required_evidence_section_ids": ["requirement", "fee"],
            "answer_facts": ["سجل تجاري", "عقد إيجار", "إذن إشغال", "رسم تفتيش 20 ديناراً"],
            "numeric_values": ["20"],
            "must_abstain": False,
        },
        {
            "id": "multi_08_minor_passport_approval_and_fee",
            "category": "multi_section",
            "question": "ما هي شروط إصدار جواز السفر لمن هم دون 16 عاماً وما هو رسم إصداره؟",
            "expected_service_ids": ["service_passport"],
            "required_evidence_section_ids": ["requirement", "fee"],
            "answer_facts": ["موافقة خطية من ولي الأمر", "25 ديناراً"],
            "numeric_values": ["25"],
            "must_abstain": False,
        },

        # --- 6 Similar-Service Disambiguation Traps ---
        {
            "id": "trap_01_lost_driving_vs_id",
            "category": "disambiguation_trap",
            "question": "ما هو رسم استخراج بدل فاقد لرخصة القيادة؟",
            "expected_service_ids": ["service_driving_license"],
            "required_evidence_section_ids": ["fee"],
            "answer_facts": ["15 ديناراً", "خمسة عشر ديناراً"],
            "numeric_values": ["15"],
            "must_abstain": False,
        },
        {
            "id": "trap_02_lost_family_book",
            "category": "disambiguation_trap",
            "question": "ما هو رسم استخراج بدل فاقد لدفتر العائلة؟",
            "expected_service_ids": ["service_family_book"],
            "required_evidence_section_ids": ["fee"],
            "answer_facts": ["10 دنانير", "عشرة دنانير"],
            "numeric_values": ["10"],
            "must_abstain": False,
        },
        {
            "id": "trap_03_min_age_license_vs_id",
            "category": "disambiguation_trap",
            "question": "ما هو السن القانوني للحصول على رخصة القيادة الخصوصية مقارنة بسن إصدار البطاقة الشخصية؟",
            "expected_service_ids": ["service_driving_license", "service_smart_id"],
            "required_evidence_section_ids": ["condition", "requirement"],
            "answer_facts": ["18 عاماً لرخصة القيادة", "16 عاماً للبطاقة الشخصية"],
            "numeric_values": ["18", "16"],
            "must_abstain": False,
        },
        {
            "id": "trap_04_driving_renew_normal",
            "category": "disambiguation_trap",
            "question": "كم رسم تجديد رخصة القيادة الفئة الثالثة العادية لمدة 10 سنوات؟",
            "expected_service_ids": ["service_driving_license"],
            "required_evidence_section_ids": ["fee"],
            "answer_facts": ["27 ديناراً", "سبعة وعشرون"],
            "numeric_values": ["27"],
            "must_abstain": False,
        },
        {
            "id": "trap_05_non_conviction_english",
            "category": "disambiguation_trap",
            "question": "كم رسم إصدار شهادة عدم المحكومية باللغة الإنجليزية في وزارة العدل؟",
            "expected_service_ids": ["service_non_conviction"],
            "required_evidence_section_ids": ["fee"],
            "answer_facts": ["7 دنانير", "سبعة دنانير"],
            "numeric_values": ["7"],
            "must_abstain": False,
        },
        {
            "id": "trap_06_building_commercial_sqm_fee",
            "category": "disambiguation_trap",
            "question": "ما هي رسوم ترخيص المتر المربع للأبنية التجارية لدى البلدية أو الأمانة؟",
            "expected_service_ids": ["service_building_permit"],
            "required_evidence_section_ids": ["fee"],
            "answer_facts": ["8 دنانير", "ثمانية دنانير"],
            "numeric_values": ["8"],
            "must_abstain": False,
        },

        # --- 5 Multi-Service Comparisons ---
        {
            "id": "comp_01_id_vs_passport_lost_fee",
            "category": "comparison",
            "question": "قارن بين رسم بدل الفاقد للمرة الأولى بين البطاقة الشخصية الذكية وجواز السفر؟",
            "expected_service_ids": ["service_smart_id", "service_passport"],
            "required_evidence_section_ids": ["fee"],
            "answer_facts": ["البطاقة الشخصية 25 ديناراً", "جواز السفر 100 دينار"],
            "numeric_values": ["25", "100"],
            "must_abstain": False,
        },
        {
            "id": "comp_02_building_res_vs_comm_fee",
            "category": "comparison",
            "question": "ما الفرق في رسم ترخيص المتر المربع بين البناء السكني والبناء التجاري؟",
            "expected_service_ids": ["service_building_permit"],
            "required_evidence_section_ids": ["fee"],
            "answer_facts": ["السكني 3 دنانير", "التجاري 8 دنانير"],
            "numeric_values": ["3", "8"],
            "must_abstain": False,
        },
        {
            "id": "comp_03_first_time_id_vs_family_book",
            "category": "comparison",
            "question": "قارن بين رسم إصدار البطاقة الشخصية لأول مرة ورسم إصدار دفتر العائلة لأول مرة؟",
            "expected_service_ids": ["service_smart_id", "service_family_book"],
            "required_evidence_section_ids": ["fee"],
            "answer_facts": ["ديناران", "2"],
            "numeric_values": ["2"],
            "must_abstain": False,
        },
        {
            "id": "comp_04_building_deposit_res_vs_comm",
            "category": "comparison",
            "question": "ما الفرق بين مبلغ تأمين حسن التنفيذ للأبنية السكنية مقارنة بالأبنية التجارية؟",
            "expected_service_ids": ["service_building_permit"],
            "required_evidence_section_ids": ["fee"],
            "answer_facts": ["السكني 500 دينار", "التجاري 1500 دينار"],
            "numeric_values": ["500", "1500"],
            "must_abstain": False,
        },
        {
            "id": "comp_05_passport_vs_non_conviction_validity",
            "category": "comparison",
            "question": "قارن بين مدة صلاحية جواز السفر للبالغين ومدة صلاحية شهادة عدم المحكومية؟",
            "expected_service_ids": ["service_passport", "service_non_conviction"],
            "required_evidence_section_ids": ["procedure"],
            "answer_facts": ["جواز السفر 5 سنوات", "عدم المحكومية 3 أشهر"],
            "numeric_values": ["5", "3"],
            "must_abstain": False,
        },

        # --- 5 Unanswerable / Out-of-Corpus Questions (Must Abstain) ---
        {
            "id": "out_01_yacht_import_aqaba",
            "category": "out_of_corpus",
            "question": "كم تبلغ رسوم استيراد اليخوت البحرية في منطقة العقبة الاقتصادية الخاصة؟",
            "expected_service_ids": [],
            "required_evidence_section_ids": [],
            "answer_facts": [],
            "numeric_values": [],
            "must_abstain": True,
        },
        {
            "id": "out_02_helicopter_license",
            "category": "out_of_corpus",
            "question": "ما هي شروط ورسوم الحصول على رخصة طيار هليكوبتر مدني في الأردن؟",
            "expected_service_ids": [],
            "required_evidence_section_ids": [],
            "answer_facts": [],
            "numeric_values": [],
            "must_abstain": True,
        },
        {
            "id": "out_03_dubai_property_tax",
            "category": "out_of_corpus",
            "question": "ما هي ضريبة بيع وشراء العقارات في إمارة دبي لعام 2026؟",
            "expected_service_ids": [],
            "required_evidence_section_ids": [],
            "answer_facts": [],
            "numeric_values": [],
            "must_abstain": True,
        },
        {
            "id": "out_04_gold_price_today",
            "category": "out_of_corpus",
            "question": "كم سعر غرام الذهب عيار 21 اليوم في السوق الأردني؟",
            "expected_service_ids": [],
            "required_evidence_section_ids": [],
            "answer_facts": [],
            "numeric_values": [],
            "must_abstain": True,
        },
        {
            "id": "out_05_japan_visa_requirements",
            "category": "out_of_corpus",
            "question": "ما هي متطلبات تأشيرة الدخول السياحية إلى اليابان لحاملي الجواز الأردني؟",
            "expected_service_ids": [],
            "required_evidence_section_ids": [],
            "answer_facts": [],
            "numeric_values": [],
            "must_abstain": True,
        },

        # --- 3 Colloquial / Paraphrased Arabic Questions ---
        {
            "id": "colloq_01_first_smart_id",
            "category": "colloquial",
            "question": "بدي اطلع هوية اول مرة شو اجيب معي وكم بتكلف؟",
            "expected_service_ids": ["service_smart_id"],
            "required_evidence_section_ids": ["requirement", "fee"],
            "answer_facts": ["شهادة ميلاد", "دفتر عائلة", "صورتان", "ديناران"],
            "numeric_values": ["2"],
            "must_abstain": False,
        },
        {
            "id": "colloq_02_urgent_passport",
            "category": "colloquial",
            "question": "قديش بكلفني اطلع جواز سفر بسرعة مستعجل بنفس اليوم؟",
            "expected_service_ids": ["service_passport"],
            "required_evidence_section_ids": ["fee"],
            "answer_facts": ["100 دينار", "مستعجل"],
            "numeric_values": ["100"],
            "must_abstain": False,
        },
        {
            "id": "colloq_03_lost_family_book",
            "category": "colloquial",
            "question": "ضاع مني دفتر العيلة شو الرسوم عشان اطلع بديل؟",
            "expected_service_ids": ["service_family_book"],
            "required_evidence_section_ids": ["fee"],
            "answer_facts": ["10 دنانير", "بدل فاقد"],
            "numeric_values": ["10"],
            "must_abstain": False,
        },

        # --- 3 Follow-Up Pronoun / Context Questions ---
        {
            "id": "follow_01_passport_urgent",
            "category": "follow_up",
            "question": "وكم رسوم المستعجل منه؟",
            "history": [
                {"role": "user", "content": "ما هي رسوم تجديد جواز السفر العادي؟"},
                {"role": "assistant", "content": "تبلغ رسوم تجديد جواز السفر العادي 50 ديناراً لمن هم فوق سن 16 عاماً."}
            ],
            "expected_service_ids": ["service_passport"],
            "required_evidence_section_ids": ["fee"],
            "answer_facts": ["100 دينار"],
            "numeric_values": ["100"],
            "must_abstain": False,
        },
        {
            "id": "follow_02_building_deposit",
            "category": "follow_up",
            "question": "وكم يبلغ التأمين المسترد له؟",
            "history": [
                {"role": "user", "content": "ما هو رسم ترخيص البناء السكني؟"},
                {"role": "assistant", "content": "يبلغ رسم ترخيص البناء السكني 3 دنانير لكل متر مربع مرخص."}
            ],
            "expected_service_ids": ["service_building_permit"],
            "required_evidence_section_ids": ["fee"],
            "answer_facts": ["500 دينار"],
            "numeric_values": ["500"],
            "must_abstain": False,
        },
        {
            "id": "follow_03_smart_id_damaged",
            "category": "follow_up",
            "question": "وماذا عن بدل التالف لها؟",
            "history": [
                {"role": "user", "content": "ما هي رسوم إصدار البطاقة الشخصية أول مرة؟"},
                {"role": "assistant", "content": "رسم إصدار البطاقة الشخصية لأول مرة هو ديناران."}
            ],
            "expected_service_ids": ["service_smart_id"],
            "required_evidence_section_ids": ["fee"],
            "answer_facts": ["10 دنانير"],
            "numeric_values": ["10"],
            "must_abstain": False,
        },
    ]

    eval_file = HACKATHON_DIR / "eval_cases.jsonl"
    with open(eval_file, "w", encoding="utf-8") as f:
        for c in cases:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    print(f"  + Successfully saved {len(cases)} gold evaluation cases to {eval_file}")


def main():
    print("=" * 70)
    print(" [T10/T11 Setup] Building Hackathon Realistic Corpus & Evaluation Set")
    print("=" * 70)
    generate_pdfs()
    generate_eval_cases()
    print("=" * 70)
    print(" Setup Complete! Ready for batch ingestion and benchmark evaluation.")
    print("=" * 70)


if __name__ == "__main__":
    main()
