"""
Keyword taxonomy used for lightweight, dependency-free resume entity
extraction (see `resume_parser.py`).

Design decision: rather than pulling in a heavyweight NER model (spaCy +
transformer pipeline) just to pull "Python" and "Docker" out of a resume, we
match against a curated, role-aware keyword list. This is fast, has zero
cold-start cost, is fully deterministic (easy to unit test), and is "good
enough" because the extracted terms are only used to steer RAG queries and
question difficulty -- not as the final product. If precision needs to
improve later, this module is the single place to swap in a proper NER
model without touching any other layer.
"""

PROGRAMMING_LANGUAGES = [
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "golang",
    "rust", "ruby", "php", "kotlin", "swift", "scala", "r", "sql", "bash",
    "c", "matlab", "julia",
]

ML_AI_SKILLS = [
    "machine learning", "deep learning", "neural network", "cnn", "rnn",
    "lstm", "transformer", "attention mechanism", "reinforcement learning",
    "supervised learning", "unsupervised learning", "decision tree",
    "random forest", "gradient boosting", "xgboost", "svm", "naive bayes",
    "bayesian", "clustering", "k-means", "pca", "dimensionality reduction",
    "feature engineering", "hyperparameter tuning", "cross-validation",
    "overfitting", "regularization", "gan", "generative adversarial",
    "computer vision", "nlp", "natural language processing", "llm",
    "retrieval augmented generation", "rag", "embeddings", "fine-tuning",
    "pytorch", "tensorflow", "keras", "scikit-learn", "sklearn", "huggingface",
    "opencv", "yolo", "mlflow", "pac learning", "concept learning",
]

DATA_SCIENCE_SKILLS = [
    "pandas", "numpy", "matplotlib", "seaborn", "plotly", "statistics",
    "hypothesis testing", "a/b testing", "regression analysis", "eda",
    "exploratory data analysis", "data cleaning", "data wrangling",
    "jupyter", "tableau", "power bi", "etl", "data pipeline",
    "statistical modeling", "time series", "forecasting",
]

BACKEND_SKILLS = [
    "rest api", "restful", "graphql", "microservices", "fastapi", "flask",
    "django", "spring boot", "express", "node.js", "nodejs", "grpc",
    "message queue", "kafka", "rabbitmq", "redis", "caching", "load balancing",
    "docker", "kubernetes", "ci/cd", "system design", "database design",
    "postgresql", "postgres", "mysql", "mongodb", "sqlalchemy", "orm",
    "authentication", "authorization", "oauth", "jwt", "websocket",
    "concurrency", "multithreading", "async", "asyncio", "scalability",
    "distributed systems", "sql injection", "unit testing", "pytest",
]

CLOUD_DEVOPS = [
    "aws", "azure", "gcp", "google cloud", "terraform", "ansible",
    "jenkins", "github actions", "cloudformation", "lambda", "ec2", "s3",
    "cloud run", "vercel", "nginx", "linux",
]

ALL_TECHNOLOGIES = sorted(set(
    PROGRAMMING_LANGUAGES + ML_AI_SKILLS + DATA_SCIENCE_SKILLS + BACKEND_SKILLS + CLOUD_DEVOPS
))

ROLE_SKILL_FOCUS = {
    "ai_ml_engineer": ML_AI_SKILLS + PROGRAMMING_LANGUAGES,
    "data_scientist": DATA_SCIENCE_SKILLS + ML_AI_SKILLS + PROGRAMMING_LANGUAGES,
    "backend_engineer": BACKEND_SKILLS + CLOUD_DEVOPS + PROGRAMMING_LANGUAGES,
}

# Natural-language display forms for taxonomy tokens that read badly verbatim
# (e.g. a raw "c" or "rest api" inserted into a generated sentence looks like a
# typo/fragment, not a topic name). Only entries that actually need correction
# are listed; everything else falls through to a plain .title() in
# display_label(). Found via a real reported bug: a candidate's resume matched
# bare "c" (from "C++"/"C#" adjacency or an abbreviation like "C.S."), and that
# raw lowercase token was quoted directly in a generated question ("...relates
# to c, in your own words...").
DISPLAY_OVERRIDES = {
    "c": "C", "r": "R",
    "rest api": "REST API", "restful": "RESTful", "graphql": "GraphQL",
    "ci/cd": "CI/CD", "sql": "SQL", "nosql": "NoSQL",
    "aws": "AWS", "gcp": "GCP", "azure": "Azure",
    "oauth": "OAuth", "jwt": "JWT", "orm": "ORM", "api": "API",
    "cnn": "CNN", "rnn": "RNN", "lstm": "LSTM", "svm": "SVM", "pca": "PCA",
    "gan": "GAN", "nlp": "NLP", "llm": "LLM", "rag": "RAG",
    "opencv": "OpenCV", "yolo": "YOLO", "mlflow": "MLflow",
    "eda": "EDA", "etl": "ETL", "a/b testing": "A/B Testing",
    "postgresql": "PostgreSQL", "postgres": "PostgreSQL", "mysql": "MySQL",
    "mongodb": "MongoDB", "sqlalchemy": "SQLAlchemy", "fastapi": "FastAPI",
    "grpc": "gRPC", "node.js": "Node.js", "nodejs": "Node.js",
    "kubernetes": "Kubernetes", "pytorch": "PyTorch", "tensorflow": "TensorFlow",
    "scikit-learn": "scikit-learn", "sklearn": "scikit-learn",
}


def display_label(term: str) -> str:
    """Render a taxonomy token (always stored/matched lowercase) for display in
    generated questions and UI badges. See DISPLAY_OVERRIDES docstring above."""
    lowered = term.lower().strip()
    if lowered in DISPLAY_OVERRIDES:
        return DISPLAY_OVERRIDES[lowered]
    if len(lowered) <= 1:
        return lowered.upper()
    return term.title()
