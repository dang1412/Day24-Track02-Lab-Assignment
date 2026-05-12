# src/pii/detector.py
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_analyzer.nlp_engine import NlpEngineProvider

# Common Vietnamese family names for name detection
VN_FAMILY_NAMES = [
    "Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Võ",
    "Đặng", "Bùi", "Đỗ", "Hồ", "Ngô", "Dương", "Lý", "Đào", "Đinh", "Mai",
    "Trịnh", "Lưu", "Vương", "Hà", "Tô", "Cao", "Tạ", "Quách", "Lâm", "Đoàn",
    "Nguyen", "Tran", "Le", "Pham", "Hoang", "Huynh", "Phan", "Vu", "Vo",
    "Dang", "Bui", "Do", "Ho", "Ngo", "Duong", "Ly", "Dao", "Dinh", "Mai",
]


def build_vietnamese_analyzer() -> AnalyzerEngine:
    """
    Xây dựng AnalyzerEngine với các recognizer tùy chỉnh cho VN.
    Sử dụng language="vi" map tới en_core_web_sm (vi_core_news_lg không available).
    """

    # --- TASK 2.2.1 --- CCCD VN: đúng 12 chữ số
    cccd_recognizer = PatternRecognizer(
        supported_entity="VN_CCCD",
        supported_language="vi",
        patterns=[Pattern(
            name="cccd_pattern",
            regex=r"\b\d{12}\b",
            score=0.9
        )],
        context=["cccd", "căn cước", "chứng minh", "cmnd"]
    )

    # --- TASK 2.2.2 --- Số điện thoại VN: 0[3|5|7|8|9] + 8 chữ số
    phone_recognizer = PatternRecognizer(
        supported_entity="VN_PHONE",
        supported_language="vi",
        patterns=[Pattern(
            name="vn_phone",
            regex=r"\b0[35789]\d{8}\b",
            score=0.85
        )],
        context=["điện thoại", "sdt", "phone", "liên hệ"]
    )

    # Email recognizer cho tiếng Việt
    email_recognizer = PatternRecognizer(
        supported_entity="EMAIL_ADDRESS",
        supported_language="vi",
        patterns=[Pattern(
            name="email_pattern",
            regex=r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b",
            score=0.85
        )],
        context=["email", "thư điện tử", "liên hệ"]
    )

    # Vietnamese name recognizer: match khi xuất hiện bất kỳ họ VN nào trong text
    family_name_pattern = "|".join(VN_FAMILY_NAMES)
    vn_name_recognizer = PatternRecognizer(
        supported_entity="PERSON",
        supported_language="vi",
        patterns=[Pattern(
            name="vn_name",
            regex=r"\b(?:" + family_name_pattern + r")\b",
            score=0.75
        )],
        context=["tên", "họ tên", "bệnh nhân", "bác sĩ", "ông", "bà", "cô"]
    )

    # --- TASK 2.2.3 ---
    # Dùng en_core_web_sm vì vi_core_news_lg không available với spaCy 3.8
    provider = NlpEngineProvider(nlp_configuration={
        "nlp_engine_name": "spacy",
        "models": [{"lang_code": "vi",
                    "model_name": "en_core_web_sm"}]
    })
    nlp_engine = provider.create_engine()

    # --- TASK 2.2.4 ---
    analyzer = AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=["vi"])
    analyzer.registry.add_recognizer(cccd_recognizer)
    analyzer.registry.add_recognizer(phone_recognizer)
    analyzer.registry.add_recognizer(email_recognizer)
    analyzer.registry.add_recognizer(vn_name_recognizer)

    return analyzer


def detect_pii(text: str, analyzer: AnalyzerEngine) -> list:
    """
    Detect PII trong text tiếng Việt.
    Trả về list các RecognizerResult.
    """
    results = analyzer.analyze(
        text=text,
        language="vi",
        entities=["PERSON", "EMAIL_ADDRESS", "VN_CCCD", "VN_PHONE"]
    )
    return results
