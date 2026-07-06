from services.llm_client import ask_json

SYSTEM = """You are recommending real, well-known public datasets for a
student project. Only suggest datasets that genuinely exist and are
commonly used (Kaggle, UCI, HuggingFace Datasets, government open data,
academic benchmark sets). If unsure a dataset exists, omit it rather than
invent one."""


def recommend_datasets(title: str, description: str, key_technologies: list[str]) -> list[dict]:
    prompt = f"""
Project: {title}
Description: {description}
Key technologies: {', '.join(key_technologies)}

Recommend 3-5 real, existing public datasets suitable for this project.
For each return:
- name
- source (e.g. Kaggle, UCI, HuggingFace, government)
- url (best-known canonical URL)
- size_description (e.g. "50,000 images, 2GB")
- annotation_format (e.g. "CSV labels", "COCO JSON", "none / unlabeled")
- quality_score (1-10, your assessment of suitability + data quality)

Return JSON array of these objects.
"""
    return ask_json(SYSTEM, prompt, max_tokens=1500)
