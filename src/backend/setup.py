from setuptools import setup, find_packages

setup(
    name="randebu-backend",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.109.0",
        "uvicorn>=0.27.0",
        "sqlalchemy>=2.0.0",
        "pydantic>=2.5.0",
        "pydantic-settings>=2.1.0",
        "python-jose[cryptography]>=3.3.0",
        "passlib[bcrypt]>=1.7.4",
        "crewai>=0.1.0",
        "anthropic>=0.18.0",
        "httpx>=0.26.0",
        "python-multipart>=0.0.6",
    ],
)
