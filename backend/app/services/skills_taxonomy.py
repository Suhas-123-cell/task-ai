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
